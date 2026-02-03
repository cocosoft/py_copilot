"""话题标题生成服务"""
from typing import Optional, Dict, AsyncGenerator
from sqlalchemy.orm import Session
import hashlib
import asyncio

from app.models.conversation import Message
from app.core.logging_config import logger
from app.modules.llm.services.llm_service_enhanced import enhanced_llm_service


class TopicTitleGenerator:
    """话题标题生成器"""
    
    # 标题缓存，键为用户输入内容的哈希值，值为生成的标题
    _title_cache: Dict[str, str] = {}
    # 缓存大小限制
    _cache_size_limit = 1000
    
    @classmethod
    def _get_cache_key(cls, content: str) -> str:
        """
        生成缓存键
        
        Args:
            content: 用户消息内容
            
        Returns:
            缓存键（内容的MD5哈希值）
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @classmethod
    def _get_from_cache(cls, content: str) -> Optional[str]:
        """
        从缓存获取标题
        
        Args:
            content: 用户消息内容
            
        Returns:
            缓存的标题，如果不存在则返回None
        """
        cache_key = cls._get_cache_key(content)
        if cache_key in cls._title_cache:
            logger.info(f"从缓存获取标题成功")
            return cls._title_cache[cache_key]
        return None
    
    @classmethod
    def _add_to_cache(cls, content: str, title: str) -> None:
        """
        添加标题到缓存
        
        Args:
            content: 用户消息内容
            title: 生成的标题
        """
        if len(cls._title_cache) >= cls._cache_size_limit:
            # 当缓存达到上限时，删除最早的条目
            oldest_key = next(iter(cls._title_cache))
            del cls._title_cache[oldest_key]
        
        cache_key = cls._get_cache_key(content)
        cls._title_cache[cache_key] = title
        logger.info(f"标题已添加到缓存")
    
    @classmethod
    def generate_title_from_messages(
        cls, 
        db: Session, 
        conversation_id: int,
        topic_id: Optional[int] = None,
        message_limit: int = 10
    ) -> str:
        """
        根据对话消息生成话题标题
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            topic_id: 话题ID（可选，如果提供则只获取该话题的消息）
            message_limit: 用于生成标题的消息数量限制
            
        Returns:
            生成的话题标题
        """
        print(f"=== 开始生成话题标题 === conversation_id={conversation_id}, topic_id={topic_id}")
        logger.info(f"开始生成话题标题: conversation_id={conversation_id}, topic_id={topic_id}")
        
        try:
            # 构建查询条件
            query = db.query(Message).filter(Message.conversation_id == conversation_id)
            
            # 如果指定了话题ID，只获取该话题的消息
            if topic_id:
                query = query.filter(Message.topic_id == topic_id)
            
            # 获取最近的对话消息（按创建时间升序排列）
            messages = query.order_by(Message.created_at.asc()).limit(message_limit).all()
            
            print(f"查询到的消息数量: {len(messages)}")
            logger.info(f"查询到的消息数量: {len(messages)}")
            
            if not messages:
                print("没有消息，返回默认标题: 新对话")
                return "新对话"
            
            # 获取用户消息
            user_messages = [msg for msg in messages if msg.role == "user"]
            
            print(f"用户消息数量: {len(user_messages)}")
            logger.info(f"用户消息数量: {len(user_messages)}")
            
            if not user_messages:
                print("没有用户消息，返回默认标题: 新对话")
                return "新对话"
            
            # 使用第一条用户消息生成标题（最早的用户消息）
            first_user_message = user_messages[0]
            content = first_user_message.content.strip()
            
            print(f"第一条用户消息内容: {content[:100]}...")
            logger.info(f"第一条用户消息内容: {content[:100]}...")
            
            # 先尝试从缓存获取标题
            cached_title = cls._get_from_cache(content)
            if cached_title:
                print(f"从缓存获取标题成功: {cached_title}")
                return cached_title
            
            # 尝试使用 LLM 生成标题
            print("开始尝试使用LLM生成标题...")
            logger.info("开始尝试使用LLM生成标题")
            llm_title = cls._generate_with_llm(content, db)
            
            if llm_title:
                print(f"LLM生成标题成功: {llm_title}")
                logger.info(f"LLM生成标题成功: {llm_title}")
                # 添加到缓存
                cls._add_to_cache(content, llm_title)
                return llm_title
            
            # LLM 生成失败，使用规则生成
            print("LLM生成失败，使用规则生成...")
            logger.info("LLM生成失败，使用规则生成")
            fallback_title = cls._generate_with_rules(content)
            print(f"规则生成标题: {fallback_title}")
            logger.info(f"规则生成标题: {fallback_title}")
            # 添加到缓存
            cls._add_to_cache(content, fallback_title)
            return fallback_title
            
        except Exception as e:
            print(f"生成话题标题异常: {e}")
            logger.error(f"生成话题标题失败: {e}")
            import traceback
            print(f"异常堆栈: {traceback.format_exc()}")
            return "新对话"
    
    @classmethod
    def _generate_with_llm(cls, content: str, db: Session) -> Optional[str]:
        """
        使用 LLM 生成话题标题
        
        Args:
            content: 用户消息内容
            db: 数据库会话
            
        Returns:
            生成的话题标题，如果失败则返回None
        """
        try:
            # 构建提示词，要求LLM生成简洁的话题标题
            prompt = f"""请根据以下用户消息，生成一个简洁的话题标题（不超过20个字）。
要求：
1. 标题应该准确概括消息的主要内容
2. 标题应该简洁明了，不超过20个字
3. 只返回标题，不要包含任何其他文字或标点符号
4. 不要使用引号或其他符号
5. 快速生成，不要使用思考模式

用户消息：{content}"""

            # 调用LLM服务生成标题
            messages = [{"role": "user", "content": prompt}]
            
            try:
                logger.info(f"开始调用LLM生成话题标题，用户消息内容: {content[:50]}...")
                
                # 使用DeepSeek模型，明确指定模型名称
                # 优化参数：减少max_tokens，设置合理的timeout
                # 标题生成不需要流式响应和思考模式，以减少生成时间
                llm_response = enhanced_llm_service.chat_completion(
                    messages=messages,
                    model_name="DeepSeek-V3.2",  # 明确指定模型
                    max_tokens=20,  # 标题最多20字，减少token数
                    temperature=0.1,  # 使用更低的temperature以获得更稳定的标题
                    db=db
                )
                
                logger.info(f"LLM响应类型: {type(llm_response)}")
                
                # 检查是否是流式响应（生成器）
                if hasattr(llm_response, '__iter__') and not isinstance(llm_response, (list, dict)):
                    # 处理流式响应
                    logger.warning("检测到流式响应，正在收集完整标题...")
                    full_title = ""
                    try:
                        for chunk in llm_response:
                            if chunk and isinstance(chunk, dict):
                                if chunk.get("type") == "content":
                                    content_chunk = chunk.get("content", "")
                                    if content_chunk:
                                        full_title += content_chunk
                                        logger.debug(f"收集到标题片段: {content_chunk}")
                                # 忽略思维链信息，只处理最终的内容
                    except Exception as e:
                        logger.warning(f"处理流式响应失败: {e}")
                        return None
                    
                    title = full_title.strip()
                    logger.info(f"从流式响应收集到完整标题: {title}")
                else:
                    # 处理普通响应
                    if isinstance(llm_response, dict) and llm_response.get("success", True):
                        title = llm_response.get("generated_text", "").strip()
                        logger.info(f"从普通响应获取到标题: {title}")
                    else:
                        error_msg = llm_response.get('error', '未知错误') if isinstance(llm_response, dict) else '响应格式错误'
                        logger.warning(f"LLM生成话题标题失败: {error_msg}")
                        return None
                
                # 清理标题，移除多余的标点符号
                title = title.strip('"\'')
                title = title.strip('。，、；：？！""''（）【】《》')
                
                # 确保标题不超过20个字
                if len(title) > 20:
                    title = title[:20]
                
                if title:
                    logger.info(f"LLM生成话题标题成功: {title}")
                    return title
                else:
                    logger.warning("LLM生成的标题为空")
                    return None
                    
            except Exception as e:
                logger.warning(f"LLM服务调用失败: {e}")
                import traceback
                logger.warning(f"LLM调用失败堆栈: {traceback.format_exc()}")
                # 尝试使用规则生成作为备用
                fallback_title = cls._generate_with_rules(content)
                logger.info(f"回退到规则生成标题: {fallback_title}")
                return fallback_title
                
        except Exception as e:
            logger.warning(f"LLM 生成话题标题失败: {e}")
            import traceback
            logger.warning(f"生成标题失败堆栈: {traceback.format_exc()}")
            # 尝试使用规则生成作为备用
            fallback_title = cls._generate_with_rules(content)
            logger.info(f"回退到规则生成标题: {fallback_title}")
            return fallback_title
    
    @classmethod
    def _generate_with_rules(cls, content: str) -> str:
        """
        使用规则生成话题标题
        
        Args:
            content: 用户消息内容
            
        Returns:
            生成的话题标题
        """
        # 移除多余的空白字符
        content = content.strip()
        
        # 移除无意义的开头短语
        meaningless_prefixes = ["请问", "你好", "您好", "请问一下", "想请教", "想咨询", "请问你", "你好，", "您好，"]
        for prefix in meaningless_prefixes:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()
                break
        
        # 移除开头的标点符号
        if content and content[0] in ["，", "。", "？", "！", "；", "：", "、"]:
            content = content[1:].strip()
        
        # 如果内容为空，返回默认标题
        if not content:
            return "新对话"
        
        # 截取前 20 个字符作为标题
        if len(content) <= 20:
            return content
        
        # 如果超过 20 字，截取并优化
        title = content[:20]
        
        # 尝试在词边界处截断，支持更多标点符号
        punctuation_marks = ["。", "？", "！", "，", "；", "：", "、", " "]
        original_title = title
        for punctuation in punctuation_marks:
            if punctuation in title:
                title = title.split(punctuation)[0]
                # 确保截断后不为空
                if not title:
                    title = original_title
                break
        
        # 确保不超过 20 字
        if len(title) > 20:
            title = title[:20]
        
        # 如果标题太短（少于5字），尝试获取更多内容
        if len(title) < 5 and len(content) > 20:
            extended_title = content[:30]
            for punctuation in punctuation_marks:
                if punctuation in extended_title:
                    temp_title = extended_title.split(punctuation)[0]
                    # 确保截断后不为空
                    if temp_title:
                        extended_title = temp_title
                    break
            if len(extended_title) > len(title) and len(extended_title) <= 20:
                title = extended_title
        
        # 最终确保标题不为空
        if not title:
            return "新对话"
        
        return title
    
    @classmethod
    def generate_summary_from_messages(
        cls,
        db: Session,
        conversation_id: int,
        message_limit: int = 20
    ) -> Optional[str]:
        """
        根据对话消息生成话题摘要
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            message_limit: 用于生成摘要的消息数量限制
            
        Returns:
            生成的话题摘要，如果失败则返回None
        """
        try:
            # 获取最近的对话消息
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(message_limit).all()
            
            if not messages:
                return None
            
            # 合并消息内容
            content_list = []
            for msg in messages:
                role = "用户" if msg.role == "user" else "助手"
                content_list.append(f"{role}: {msg.content}")
            
            full_content = "\n".join(content_list)
            
            # 尝试使用 LLM 生成摘要
            summary = cls._generate_summary_with_llm(full_content)
            if summary:
                return summary
            
            # LLM 生成失败，返回 None
            return None
            
        except Exception as e:
            logger.error(f"生成话题摘要失败: {e}")
            return None
    
    @classmethod
    async def async_generate_title_from_messages(
        cls,
        db: Session,
        conversation_id: int,
        topic_id: Optional[int] = None,
        message_limit: int = 10
    ) -> str:
        """
        异步根据对话消息生成话题标题
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            topic_id: 话题ID（可选，如果提供则只获取该话题的消息）
            message_limit: 用于生成标题的消息数量限制
            
        Returns:
            生成的话题标题
        """
        # 在后台线程中执行同步操作，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        title = await loop.run_in_executor(
            None,
            cls.generate_title_from_messages,
            db,
            conversation_id,
            topic_id,
            message_limit
        )
        return title
    
    @classmethod
    def _generate_summary_with_llm(cls, content: str) -> Optional[str]:
        """
        使用 LLM 生成话题摘要
        
        Args:
            content: 对话消息内容
            
        Returns:
            生成的话题摘要，如果失败则返回None
        """
        try:
            # TODO: 集成 LLM 服务生成摘要
            # 这里需要调用 LLM 服务，传入对话内容
            # 要求 LLM 生成一个简洁的对话摘要
            
            # 暂时返回 None
            return None
            
        except Exception as e:
            logger.warning(f"LLM 生成话题摘要失败: {e}")
            return None
