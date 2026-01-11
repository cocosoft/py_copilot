"""对话管理相关API路由（优化版）"""
import asyncio
import time
from datetime import datetime
from typing import Any, List, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status, Body, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.schemas.conversation import SendMessageRequest
from app.modules.llm.services.llm_service_enhanced import enhanced_llm_service

# 简单的内存缓存
class ResponseCache:
    def __init__(self, max_size=1000, ttl=300):  # 5分钟TTL
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key, data):
        if len(self.cache) >= self.max_size:
            # 简单的LRU淘汰
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        self.cache[key] = (data, time.time())

# 创建缓存实例
response_cache = ResponseCache()

# 创建直接连接到py_copilot_iv.db的数据库会话
def get_db():
    print("get_db函数被调用")
    # 使用绝对路径连接到项目根目录下的数据库文件
    db_path = 'sqlite:///e:\\PY\\CODES\\py copilot IV\\backend\\py_copilot.db'
    print(f"数据库路径: {db_path}")
    engine = create_engine(db_path)
    print(f"创建的数据库引擎: {engine}")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print(f"创建的会话工厂: {SessionLocal}")
    db = SessionLocal()
    print(f"创建的数据库会话: {db}")
    try:
        yield db
    finally:
        db.close()
        print("数据库会话已关闭")

router = APIRouter()


# 模拟内存存储
class MockStorage:
    def __init__(self):
        self.conversations = []
        self.messages = []
        self.conversation_id_counter = 1
        self.message_id_counter = 1
        self.topics = []  # 话题列表
        self.topic_id_counter = 1
    
    def create_conversation(self, title: str = "新对话", description: str = "") -> Dict[str, Any]:
        conversation = {
            "id": self.conversation_id_counter,
            "title": title,
            "description": description,
            "is_active": True,
            "message_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_message_at": None
        }
        self.conversations.append(conversation)
        self.conversation_id_counter += 1
        return conversation
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        for conv in self.conversations:
            if conv["id"] == conversation_id:
                return conv
        return None
    
    def update_conversation(self, conversation_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        conv = self.get_conversation(conversation_id)
        if conv:
            for field, value in update_data.items():
                if field in conv:
                    conv[field] = value
            conv["updated_at"] = datetime.utcnow()
        return conv
    
    def delete_conversation(self, conversation_id: int) -> None:
        self.conversations = [conv for conv in self.conversations if conv["id"] != conversation_id]
        self.messages = [msg for msg in self.messages if msg["conversation_id"] != conversation_id]
    
    def create_message(self, conversation_id: int, content: str, role: str) -> Dict[str, Any]:
        message = {
            "id": self.message_id_counter,
            "conversation_id": conversation_id,
            "content": content,
            "role": role,
            "is_visible": True,
            "created_at": datetime.utcnow()
        }
        self.messages.append(message)
        self.message_id_counter += 1
        
        # 更新对话消息计数和最后消息时间
        conv = self.get_conversation(conversation_id)
        if conv:
            conv["message_count"] = sum(1 for msg in self.messages if msg["conversation_id"] == conversation_id)
            conv["last_message_at"] = datetime.utcnow()
        
        return message
    
    def get_conversation_messages(self, conversation_id: int, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        messages = [msg for msg in self.messages if msg["conversation_id"] == conversation_id and msg["is_visible"]]
        messages.sort(key=lambda x: x["created_at"])
        return messages[skip:skip+limit]
    
    def get_all_conversations(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        conversations = sorted(
            self.conversations,
            key=lambda x: (x["last_message_at"] or datetime.min, x["created_at"]),
            reverse=True
        )
        return conversations[skip:skip+limit]
    
    # 话题管理方法
    def create_topic(self, title: str, description: str = "", conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """创建话题"""
        topic = {
            "id": self.topic_id_counter,
            "title": title,
            "description": description,
            "conversation_id": conversation_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        self.topics.append(topic)
        self.topic_id_counter += 1
        return topic
    
    def get_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """获取话题"""
        for topic in self.topics:
            if topic["id"] == topic_id:
                return topic
        return None
    
    def get_topics_by_conversation(self, conversation_id: int) -> List[Dict[str, Any]]:
        """获取对话的所有话题"""
        return [topic for topic in self.topics if topic["conversation_id"] == conversation_id]
    
    def update_topic(self, topic_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新话题"""
        topic = self.get_topic(topic_id)
        if topic:
            for field, value in update_data.items():
                if field in topic:
                    topic[field] = value
            topic["updated_at"] = datetime.utcnow()
        return topic
    
    def delete_topic(self, topic_id: int) -> None:
        """删除话题"""
        self.topics = [topic for topic in self.topics if topic["id"] != topic_id]
    
    def switch_topic(self, conversation_id: int, topic_id: int) -> bool:
        """切换到指定话题"""
        # 将所有话题设置为非活跃状态
        for topic in self.topics:
            if topic["conversation_id"] == conversation_id:
                topic["is_active"] = False
        
        # 激活指定话题
        target_topic = self.get_topic(topic_id)
        if target_topic and target_topic["conversation_id"] == conversation_id:
            target_topic["is_active"] = True
            target_topic["updated_at"] = datetime.utcnow()
            return True
        return False
    
    def get_active_topic(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """获取当前活跃话题"""
        for topic in self.topics:
            if topic["conversation_id"] == conversation_id and topic["is_active"]:
                return topic
        return None

# 创建模拟存储实例
mock_storage = MockStorage()


@router.post("/")
async def create_conversation(
    title: str = "新对话",
    description: str = "",
    initial_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建新对话
    """
    conversation = mock_storage.create_conversation(title, description)
    
    # 如果提供了初始消息
    if initial_message:
        mock_storage.create_message(conversation["id"], initial_message, "user")
        conversation = mock_storage.get_conversation(conversation["id"])
    
    return conversation


@router.get("/")
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """
    获取对话列表
    """
    offset = (page - 1) * page_size
    conversations = mock_storage.get_all_conversations(skip=offset, limit=page_size)
    total = len(mock_storage.conversations)
    
    return {
        "conversations": conversations,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{conversation_id}")
async def get_conversation_detail(conversation_id: int) -> Dict[str, Any]:
    """
    获取对话详情及消息历史
    """
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取所有消息
    messages = mock_storage.get_conversation_messages(conversation_id, limit=1000)
    
    return {
        **conversation,
        "messages": messages
    }


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Dict[str, Any]:
    """
    更新对话信息
    """
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if is_active is not None:
        update_data["is_active"] = is_active
    
    updated_conversation = mock_storage.update_conversation(conversation_id, update_data)
    return updated_conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: int) -> None:
    """
    删除对话
    """
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    mock_storage.delete_conversation(conversation_id)


async def generate_ai_response(conversation_id: int, content: str, model_name: str) -> str:
    """异步生成AI回复"""
    try:
        # 获取对话历史
        conversation_history = mock_storage.get_conversation_messages(conversation_id)
        
        # 构建聊天消息列表
        chat_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_history
        ]
        chat_messages.append({"role": "user", "content": content})
        
        # 使用增强版LLM服务
        llm_response = enhanced_llm_service.chat_completion(
            messages=chat_messages,
            model_name=model_name or "gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7
        )
        
        if llm_response.get("success", False):
            return llm_response.get("generated_text", "抱歉，我无法生成回复。")
        else:
            return f"LLM调用失败: {llm_response.get('error', '未知错误')}"
            
    except Exception as e:
        return f"系统提示: 处理您的请求时发生异常。\n\n错误详情: {str(e)}\n\n请检查API配置或稍后重试。"


async def generate_streaming_ai_response(conversation_id: int, content: str, model_name: str, enable_thinking_chain: bool = False):
    """生成流式AI回复"""
    try:
        # 生成智能回复内容
        response_text = generate_intelligent_response(content, [])
        
        # 先发送思考中消息
        yield "data: {\"type\": \"thinking\", \"content\": \"正在思考您的问题...\"}\n\n"
        await asyncio.sleep(0.5)
        
        # 简单的分块方式 - 按单词或字符分割
        if len(response_text) < 10:
            # 非常短的回复
            yield f"data: {{\"type\": \"content\", \"content\": \"{response_text}\"}}\n\n"
            await asyncio.sleep(0.2)
        else:
            # 按字符逐个发送，确保分块正确
            for i in range(1, len(response_text) + 1):
                current_text = response_text[:i]
                yield f"data: {{\"type\": \"content\", \"content\": \"{current_text}\"}}\n\n"
                # 控制发送速度
                await asyncio.sleep(0.05)
        
        # 发送完成信号
        yield "data: {\"type\": \"complete\", \"content\": \"\"}\n\n"
        
    except Exception as e:
        error_msg = f"流式响应生成失败: {str(e)}"
        yield f"data: {{\"type\": \"error\", \"content\": \"{error_msg}\"}}\n\n"


def generate_thinking_chain_steps(content: str) -> List[str]:
    """根据消息内容生成思维链步骤"""
    content_lower = content.lower()
    
    if any(word in content_lower for word in ['计算', '数学', '公式', '等于', '加', '减', '乘', '除']):
        return [
            "🧮 识别数学计算问题...",
            "🔢 解析数学表达式...",
            "📊 执行计算步骤...",
            "✅ 验证计算结果..."
        ]
    elif any(word in content_lower for word in ['解释', '什么是', '定义', '概念']):
        return [
            "📚 识别概念解释需求...",
            "🔍 检索相关知识库...",
            "💡 构建解释框架...",
            "📝 组织解释内容..."
        ]
    elif any(word in content_lower for word in ['代码', '编程', '函数', '变量']):
        return [
            "💻 分析编程问题...",
            "🔧 设计解决方案...",
            "📋 编写代码逻辑...",
            "✅ 验证代码正确性..."
        ]
    elif any(word in content_lower for word in ['翻译', '语言', '英文', '中文']):
        return [
            "🌐 识别翻译需求...",
            "📖 分析原文语义...",
            "🔄 构建翻译映射...",
            "✍️ 优化翻译表达..."
        ]
    else:
        return [
            "🤔 正在分析您的问题意图...",
            "🔍 检索相关知识信息...", 
            "💭 构建推理逻辑链条...",
            "✨ 生成最终回答内容..."
        ]


def generate_intelligent_response(content: str, conversation_history: List[Dict]) -> str:
    """根据消息内容和对话历史生成智能回复"""
    content_lower = content.lower()
    
    # 简单的智能回复生成逻辑
    if '你好' in content_lower or 'hello' in content_lower:
        return "你好！我是Py Copilot智能助手，很高兴为您服务！我可以帮助您解答问题、编写代码、分析问题等。请告诉我您需要什么帮助？"
    
    elif '时间' in content_lower or '现在几点' in content_lower:
        from datetime import datetime
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        return f"现在时间是：{current_time}"
    
    elif any(word in content_lower for word in ['天气', '温度', '气候']):
        return "我目前无法获取实时天气信息，但您可以尝试使用专门的天气查询应用或网站来获取准确的天气数据。"
    
    elif any(word in content_lower for word in ['计算', '数学', '等于']):
        # 简单的数学计算
        try:
            import re
            # 提取数字和运算符
            numbers = re.findall(r'\d+', content)
            if len(numbers) >= 2:
                a, b = int(numbers[0]), int(numbers[1])
                if '加' in content_lower or '+' in content:
                    result = a + b
                    return f"计算结果：{a} + {b} = {result}"
                elif '减' in content_lower or '-' in content:
                    result = a - b
                    return f"计算结果：{a} - {b} = {result}"
                elif '乘' in content_lower or '*' in content:
                    result = a * b
                    return f"计算结果：{a} × {b} = {result}"
                elif '除' in content_lower or '/' in content:
                    if b != 0:
                        result = a / b
                        return f"计算结果：{a} ÷ {b} = {result:.2f}"
                    else:
                        return "错误：除数不能为零"
        except:
            pass
        
        return "这是一个数学计算问题。我可以帮助您进行简单的加减乘除运算，请提供具体的数字和运算符。"
    
    elif len(conversation_history) > 0:
        # 基于对话历史的上下文回复
        return f"基于我们的对话历史，我对您的问题有了更深入的理解。您提到的内容让我想到了一些相关的信息。对于{content[:50]}...这个问题，我认为这是一个很好的讨论点。"
    
    else:
        return f"感谢您的提问！{content} 这是一个很有意思的话题。让我为您提供一些相关的信息和见解..."


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    request: SendMessageRequest = Body(...),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    在对话中发送消息（优化版）
    """
    start_time = time.time()
    
    # 查询对话
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    if not conversation.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话已被关闭"
        )
    
    # 创建用户消息
    user_message = mock_storage.create_message(conversation_id, request.content, "user")
    
    # 如果需要使用LLM生成回复
    assistant_message = None
    if request.use_llm:
        # 检查缓存
        cache_key = f"{conversation_id}:{request.content}:{request.model_name}"
        cached_response = response_cache.get(cache_key)
        
        if cached_response:
            # 使用缓存回复
            ai_content = cached_response
        else:
            # 异步生成AI回复
            try:
                # 设置超时控制
                ai_content = await asyncio.wait_for(
                    generate_ai_response(conversation_id, request.content, request.model_name),
                    timeout=30.0  # 30秒超时
                )
                # 缓存成功结果
                response_cache.set(cache_key, ai_content)
            except asyncio.TimeoutError:
                ai_content = "系统提示: 请求超时，请稍后重试。"
            except Exception as e:
                ai_content = f"这是一条模拟回复，基于您的消息：{request.content[:50]}..."
        
        # 创建助手回复消息
        assistant_message = mock_storage.create_message(conversation_id, ai_content, "assistant")
    
    # 构建响应
    response_time = time.time() - start_time
    response = {
        "conversation_id": conversation_id,
        "user_message": user_message,
        "generated_at": datetime.utcnow(),
        "response_time": round(response_time, 3)
    }
    
    if assistant_message:
        response["assistant_message"] = assistant_message
    
    return response


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
) -> Dict[str, Any]:
    """
    获取对话的消息历史（分页）
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 获取消息列表
    messages = mock_storage.get_conversation_messages(conversation_id, skip=offset, limit=page_size)
    total = sum(1 for msg in mock_storage.messages if msg["conversation_id"] == conversation_id and msg["is_visible"])
    
    return {
        "messages": messages,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: int,
    request: SendMessageRequest = Body(...),
    enable_thinking_chain: bool = Body(False, description="是否启用思维链显示")
) -> StreamingResponse:
    """
    在对话中发送消息（流式响应版本）
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    if not conversation.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话已被关闭"
        )
    
    # 创建用户消息
    user_message = mock_storage.create_message(conversation_id, request.content, "user")
    
    async def stream_generator():
        try:
            # 发送用户消息确认
            yield f"data: {{\"type\": \"user_message\", \"content\": \"{request.content}\", \"message_id\": {user_message['id']}}}\n\n"
            
            # 收集流式响应的完整内容
            full_response = ""
            # 生成流式AI回复
            async for chunk in generate_streaming_ai_response(
                conversation_id, 
                request.content, 
                request.model_name or "gpt-3.5-turbo",
                enable_thinking_chain
            ):
                # 提取content部分用于创建最终消息
                if "\"type\": \"content\"" in chunk and "\"content\"" in chunk:
                    import json
                    try:
                        data_part = chunk.replace("data: ", "").strip()
                        if data_part:
                            data = json.loads(data_part)
                            if "content" in data:
                                full_response = data["content"]
                    except json.JSONDecodeError:
                        pass
                yield chunk
                
            # 创建最终的助手消息（使用完整的流式响应内容）
            if full_response:
                assistant_message = mock_storage.create_message(conversation_id, full_response, "assistant")
                yield f"data: {{\"type\": \"final_message\", \"message_id\": {assistant_message['id']}}}\n\n"
        except Exception as e:
            # 确保在任何异常情况下都能正确发送错误信息
            yield f"data: {{\"type\": \"error\", \"content\": \"流式响应处理失败: {str(e)}\"}}\n\n"
        
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control, Content-Type",
            "X-Accel-Buffering": "no"  # 禁用代理缓冲
        }
    )


# 话题管理API
@router.post("/{conversation_id}/topics")
async def create_topic(
    conversation_id: int,
    title: str = Body(..., description="话题标题"),
    description: str = Body("", description="话题描述")
) -> Dict[str, Any]:
    """
    为对话创建新话题
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 创建话题
    topic = mock_storage.create_topic(title, description, conversation_id)
    return {
        "status": "success",
        "topic": topic
    }


@router.get("/{conversation_id}/topics")
async def list_topics(conversation_id: int) -> Dict[str, Any]:
    """
    获取对话的所有话题
    """
    # 即使对话不存在，也返回空话题列表而不是404
    # 获取话题列表
    topics = mock_storage.get_topics_by_conversation(conversation_id)
    return {
        "status": "success",
        "topics": topics
    }


@router.put("/{conversation_id}/topics/{topic_id}")
async def update_topic(
    conversation_id: int,
    topic_id: int,
    title: Optional[str] = Body(None, description="新标题"),
    description: Optional[str] = Body(None, description="新描述")
) -> Dict[str, Any]:
    """
    更新话题信息
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 验证话题存在且属于该对话
    topic = mock_storage.get_topic(topic_id)
    if not topic or topic["conversation_id"] != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    # 更新话题
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    
    updated_topic = mock_storage.update_topic(topic_id, update_data)
    return {
        "status": "success",
        "topic": updated_topic
    }


@router.delete("/{conversation_id}/topics/{topic_id}")
async def delete_topic(conversation_id: int, topic_id: int) -> Dict[str, Any]:
    """
    删除话题
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 验证话题存在且属于该对话
    topic = mock_storage.get_topic(topic_id)
    if not topic or topic["conversation_id"] != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    # 删除话题
    mock_storage.delete_topic(topic_id)
    return {
        "status": "success",
        "message": "话题删除成功"
    }


@router.post("/{conversation_id}/topics/{topic_id}/switch")
async def switch_topic(conversation_id: int, topic_id: int) -> Dict[str, Any]:
    """
    切换到指定话题
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 验证话题存在且属于该对话
    topic = mock_storage.get_topic(topic_id)
    if not topic or topic["conversation_id"] != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )
    
    # 切换话题
    success = mock_storage.switch_topic(conversation_id, topic_id)
    if success:
        return {
            "status": "success",
            "message": "话题切换成功",
            "active_topic": mock_storage.get_active_topic(conversation_id)
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="话题切换失败"
        )


@router.get("/{conversation_id}/active_topic")
async def get_active_topic(conversation_id: int) -> Dict[str, Any]:
    """
    获取当前活跃话题
    """
    # 即使对话不存在，也返回None而不是404
    # 获取活跃话题
    active_topic = mock_storage.get_active_topic(conversation_id)
    return {
        "status": "success",
        "active_topic": active_topic
    }