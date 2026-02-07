from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import json
from datetime import datetime, timedelta
import time

# 导入本地记忆分析服务
from app.services.local_llm.memory_analysis import LocalMemoryAnalysisService

from app.models.memory import GlobalMemory, UserMemoryConfig, MemoryAccessLog, ConversationMemoryMapping, KnowledgeMemoryMapping, MemoryAssociation
from app.schemas.memory import MemoryCreate, MemoryUpdate, MemoryStats, MemoryPatterns
from app.services.knowledge.chroma_service import ChromaService
from app.services.memory_cache_service import memory_cache_service
import app.log_system.structured_logger
memory_logger = app.log_system.structured_logger.memory_logger
from app.monitoring.alert_system import alert_manager, MetricType

# 初始化Chroma服务
chroma_service = ChromaService(default_collection="memories")


class MemoryService:
    """记忆服务类"""
    
    # 类变量：缓存字典
    _cache = {}
    _cache_expiry = {}
    _cache_ttl = 300  # 缓存过期时间（秒），默认5分钟
    
    # 本地记忆分析服务实例
    _local_memory_analysis_service = None
    
    @classmethod
    def get_local_memory_analysis_service(cls):
        """获取本地记忆分析服务实例"""
        if cls._local_memory_analysis_service is None:
            cls._local_memory_analysis_service = LocalMemoryAnalysisService()
        return cls._local_memory_analysis_service
    
    @staticmethod
    def _get_cache_key(prefix: str, user_id: int, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix, str(user_id)]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
    
    @staticmethod
    def _is_cache_valid(cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in MemoryService._cache:
            return False
        if cache_key not in MemoryService._cache_expiry:
            return False
        return time.time() < MemoryService._cache_expiry[cache_key]
    
    @staticmethod
    def _set_cache(cache_key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        MemoryService._cache[cache_key] = value
        ttl = ttl or MemoryService._cache_ttl
        MemoryService._cache_expiry[cache_key] = time.time() + ttl
    
    @staticmethod
    def _get_cache(cache_key: str) -> Optional[Any]:
        """获取缓存"""
        if MemoryService._is_cache_valid(cache_key):
            return MemoryService._cache[cache_key]
        return None
    
    @staticmethod
    def _clear_cache(cache_key: str) -> None:
        """清除缓存"""
        if cache_key in MemoryService._cache:
            del MemoryService._cache[cache_key]
        if cache_key in MemoryService._cache_expiry:
            del MemoryService._cache_expiry[cache_key]
    
    @staticmethod
    def clear_user_cache(user_id: int) -> None:
        """清除用户的所有缓存"""
        keys_to_delete = []
        for key in MemoryService._cache.keys():
            if key.startswith(f"stats:{user_id}:") or key.startswith(f"patterns:{user_id}:"):
                keys_to_delete.append(key)
        for key in keys_to_delete:
            MemoryService._clear_cache(key)
    
    @staticmethod
    async def create_memory(db: Session, memory_data: MemoryCreate, user_id: int) -> GlobalMemory:
        """创建新的记忆条目"""
        start_time = time.time()
        
        try:
            # 处理向量嵌入（JSON序列化）
            embedding_json = json.dumps(memory_data.embedding) if hasattr(memory_data, 'embedding') and memory_data.embedding else None
            
            # 创建记忆记录
            db_memory = GlobalMemory(
                user_id=user_id,
                session_id=memory_data.session_id,
                memory_type=memory_data.memory_type,
                memory_category=memory_data.memory_category,
                title=memory_data.title,
                content=memory_data.content,
                summary=memory_data.summary,
                importance_score=memory_data.importance_score,
                relevance_score=memory_data.relevance_score,
                tags=memory_data.tags,
                memory_metadata=memory_data.memory_metadata,
                embedding=embedding_json,
                source_info=memory_data.source_info,
                source_type=memory_data.source_type,
                source_id=memory_data.source_id,
                source_reference=memory_data.source_reference,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
            
            db.add(db_memory)
            db.commit()
            db.refresh(db_memory)
            
            # 创建访问日志
            db_access_log = MemoryAccessLog(
                memory_id=db_memory.id,
                user_id=user_id,
                access_type="WRITE",
                created_at=datetime.now()
            )
            db.add(db_access_log)
            db.commit()
            
            # 将记忆添加到Chroma向量数据库
            try:
                chroma_service.add_document(
                    document_id=str(db_memory.id),
                    text=db_memory.content,
                    metadata={
                        "memory_id": db_memory.id,
                        "user_id": user_id,
                        "memory_type": db_memory.memory_type,
                        "memory_category": db_memory.memory_category,
                        "title": db_memory.title,
                        "importance_score": db_memory.importance_score,
                        "created_at": db_memory.created_at.isoformat()
                    }
                )
            except Exception as e:
                memory_logger.error(f"向量数据库添加失败: {str(e)}", extra_fields={
                    "memory_id": db_memory.id,
                    "user_id": user_id
                }, exc_info=e)
            
            # 建立记忆关联关系
            try:
                MemoryService.build_memory_associations(db, db_memory.id, user_id)
            except Exception as e:
                memory_logger.error(f"建立记忆关联失败: {str(e)}", extra_fields={
                    "memory_id": db_memory.id,
                    "user_id": user_id
                }, exc_info=e)
            
            # 使用本地记忆分析服务进行记忆分析
            try:
                local_analysis_service = MemoryService.get_local_memory_analysis_service()
                analysis_result = await local_analysis_service.analyze_memory_content(
                    db=db,
                    memory_content=db_memory.content,
                    user_id=user_id
                )
                
                # 更新记忆元数据
                if analysis_result.get('metadata'):
                    db_memory.memory_metadata = analysis_result['metadata']
                    db.commit()
                    db.refresh(db_memory)
                
                # 增强记忆关联关系
                if analysis_result.get('associations'):
                    for assoc in analysis_result['associations']:
                        # 这里可以根据需要建立更丰富的关联关系
                        pass
            except Exception as e:
                memory_logger.error(f"本地记忆分析失败: {str(e)}", extra_fields={
                    "memory_id": db_memory.id,
                    "user_id": user_id
                }, exc_info=e)
            
            # 更新用户偏好（基于写入操作）
            try:
                MemoryService.update_preferences_based_on_access(db, db_memory.id, user_id, access_type="WRITE")
            except Exception as e:
                memory_logger.error(f"更新用户偏好失败: {str(e)}", extra_fields={
                    "memory_id": db_memory.id,
                    "user_id": user_id
                }, exc_info=e)
            
            # 清除相关缓存
            try:
                await memory_cache_service.clear_user_cache(user_id)
            except Exception as e:
                memory_logger.error(f"清除缓存失败: {str(e)}", extra_fields={
                    "user_id": user_id
                }, exc_info=e)
            
            # 记录性能指标
            response_time = (time.time() - start_time) * 1000  # 毫秒
            alert_manager.check_metric(
                metric_type=MetricType.RESPONSE_TIME,
                metric_value=response_time,
                metadata={"endpoint": "create_memory", "user_id": user_id}
            )
            
            # 记录成功日志
            memory_logger.info("创建记忆成功", extra_fields={
                "memory_id": db_memory.id,
                "user_id": user_id,
                "memory_type": db_memory.memory_type,
                "response_time": response_time
            })
            
            return db_memory
            
        except Exception as e:
            # 记录错误日志
            memory_logger.error("创建记忆失败", extra_fields={
                "user_id": user_id,
                "memory_data": memory_data.dict() if hasattr(memory_data, 'dict') else str(memory_data)
            }, exc_info=e)
            
            # 回滚数据库事务
            db.rollback()
            
            raise
    
    @staticmethod
    def get_memory(db: Session, memory_id: int, user_id: int) -> Optional[GlobalMemory]:
        """获取特定记忆条目"""
        memory = db.query(GlobalMemory).filter(
            GlobalMemory.id == memory_id,
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).first()
        
        if memory:
            # 更新访问计数、最后访问时间和用户偏好
            MemoryService.update_preferences_based_on_access(db, memory_id, user_id, access_type="READ")
            
            # 创建访问日志
            db_access_log = MemoryAccessLog(
                memory_id=memory.id,
                user_id=user_id,
                access_type="READ",
                created_at=datetime.now()
            )
            db.add(db_access_log)
            db.commit()
        
        return memory
    
    @staticmethod
    def update_memory(db: Session, memory_id: int, memory_update: MemoryUpdate, user_id: int) -> Optional[GlobalMemory]:
        """更新记忆条目"""
        db_memory = db.query(GlobalMemory).filter(
            GlobalMemory.id == memory_id,
            GlobalMemory.user_id == user_id
        ).first()
        
        if not db_memory:
            return None
        
        # 更新字段
        update_data = memory_update.model_dump(exclude_unset=True)
        
        # 检查内容是否有变化
        content_changed = 'content' in update_data
        title_changed = 'title' in update_data
        
        # 处理向量嵌入（JSON序列化）
        if 'embedding' in update_data:
            update_data['embedding'] = json.dumps(update_data['embedding']) if update_data['embedding'] else None
        
        # 处理元数据字段名（避免与SQLAlchemy保留字冲突）
        if 'metadata' in update_data:
            update_data['memory_metadata'] = update_data.pop('metadata')
        
        for key, value in update_data.items():
            setattr(db_memory, key, value)
        
        db_memory.updated_at = datetime.now()
        
        # 如果内容或标题发生变化，重新生成向量嵌入
        if content_changed or title_changed:
            try:
                # 生成新的向量嵌入
                from app.services.llm_service import llm_service
                embedding_result = llm_service.generate_embeddings(
                    text=f"{db_memory.title or ''} {db_memory.content}",
                    model_name="text-embedding-ada-002"
                )
                
                # 更新向量嵌入
                db_memory.embedding = json.dumps(embedding_result['embedding']) if embedding_result.get('embedding') else None
                
                # 更新向量数据库
                from app.services.vector_store_service import chroma_service
                chroma_service.update_document(
                    document_id=str(db_memory.id),
                    document=db_memory.content,
                    metadata={
                        "memory_id": str(db_memory.id),
                        "user_id": user_id,
                        "memory_type": db_memory.memory_type,
                        "memory_category": db_memory.memory_category,
                        "title": db_memory.title,
                        "created_at": db_memory.created_at.isoformat()
                    },
                    embedding=embedding_result.get('embedding')
                )
            except Exception as e:
                # 向量嵌入更新失败不影响记忆更新
                import logging
                logging.warning(f"向量嵌入更新失败: {str(e)}")
        
        db.commit()
        db.refresh(db_memory)
        
        # 更新用户偏好
        MemoryService.update_preferences_based_on_access(db, memory_id, user_id, access_type="UPDATE")
        
        # 创建访问日志
        db_access_log = MemoryAccessLog(
            memory_id=db_memory.id,
            user_id=user_id,
            access_type="UPDATE",
            created_at=datetime.now()
        )
        db.add(db_access_log)
        db.commit()
        
        # 更新记忆关联关系
        MemoryService.build_memory_associations(db, db_memory.id, user_id)
        
        return db_memory
    
    @staticmethod
    def delete_memory(db: Session, memory_id: int, user_id: int) -> bool:
        """删除记忆条目"""
        db_memory = db.query(GlobalMemory).filter(
            GlobalMemory.id == memory_id,
            GlobalMemory.user_id == user_id
        ).first()
        
        if not db_memory:
            return False
        
        # 更新用户偏好（基于删除操作）
        MemoryService.update_preferences_based_on_access(db, memory_id, user_id, access_type="DELETE")
        
        # 创建访问日志
        db_access_log = MemoryAccessLog(
            memory_id=db_memory.id,
            user_id=user_id,
            access_type="DELETE",
            created_at=datetime.now()
        )
        db.add(db_access_log)
        db.commit()
        
        # 从Chroma向量数据库中删除记忆
        chroma_service.delete_document(document_id=str(db_memory.id))
        
        return True
    
    @staticmethod
    def delete_all_memories(db: Session, user_id: int) -> int:
        """清空用户所有记忆"""
        # 获取用户的所有记忆
        user_memories = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).all()
        
        deleted_count = 0
        
        # 遍历所有记忆并删除
        for memory in user_memories:
            # 从Chroma向量数据库中删除记忆
            chroma_service.delete_document(document_id=str(memory.id))
            deleted_count += 1
        
        # 批量删除数据库中的记忆
        db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).delete()
        
        db.commit()
        
        return deleted_count
    
    @staticmethod
    async def search_memories(db: Session, query: str, user_id: int, memory_types: Optional[List[str]] = None,
                       memory_categories: Optional[List[str]] = None, limit: int = 10,
                       session_id: Optional[str] = None, context_ids: Optional[List[int]] = None) -> List[GlobalMemory]:
        """搜索记忆条目（上下文感知版本）"""
        # 1. 构建基础搜索过滤器
        chroma_filter = {"user_id": user_id}
        if memory_types:
            chroma_filter["memory_type"] = {"$in": memory_types}
        if memory_categories:
            chroma_filter["memory_category"] = {"$in": memory_categories}
        
        # 2. 上下文增强处理
        enhanced_query = query
        
        # 如果有session_id，获取会话上下文并增强查询
        if session_id:
            # 获取会话相关的记忆
            session_memories = db.query(GlobalMemory).filter(
                GlobalMemory.user_id == user_id,
                GlobalMemory.session_id == session_id,
                GlobalMemory.is_active == True
            ).order_by(desc(GlobalMemory.created_at)).limit(5).all()  # 获取最近5条会话记忆
            
            # 使用会话记忆增强查询
            if session_memories:
                session_context = " ".join([mem.content[:100] for mem in session_memories if mem.content])
                enhanced_query = f"{query} [上下文: {session_context}]"
        
        # 使用本地记忆分析服务增强查询理解
        try:
            local_analysis_service = MemoryService.get_local_memory_analysis_service()
            enhanced_query_result = await local_analysis_service.enhance_query_understanding(
                query=query,
                context=session_context if 'session_context' in locals() else None,
                db=db
            )
            if enhanced_query_result.get('enhanced_query'):
                enhanced_query = enhanced_query_result['enhanced_query']
        except Exception as e:
            memory_logger.error(f"本地查询理解增强失败: {str(e)}", extra_fields={
                "user_id": user_id,
                "query": query[:100]
            }, exc_info=e)
        
        # 3. 使用Chroma进行向量相似性搜索
        search_results = chroma_service.search_similar(
            query=enhanced_query,
            n_results=limit * 2,  # 获取更多结果以便过滤和排序
            where_filter=chroma_filter
        )
        
        # 4. 提取匹配的记忆ID和相似度
        memory_candidates = {}
        for i, doc_id in enumerate(search_results["ids"][0]):
            try:
                memory_id = int(doc_id)
                distance = search_results["distances"][0][i]
                similarity = 1 - distance  # 转换为相似度（0-1）
                memory_candidates[memory_id] = similarity
            except (ValueError, TypeError):
                continue
        
        # 如果有上下文ID，增强相关记忆的权重
        if context_ids and memory_candidates:
            # 获取上下文相关的记忆ID
            context_related_ids = set()
            for mem_id in context_ids:
                # 查找与上下文记忆相关联的其他记忆
                related_memories = db.query(GlobalMemory).join(
                    MemoryAssociation, 
                    (MemoryAssociation.source_memory_id == mem_id) | (MemoryAssociation.target_memory_id == mem_id)
                ).filter(
                    GlobalMemory.id == MemoryAssociation.source_memory_id,
                    GlobalMemory.user_id == user_id,
                    GlobalMemory.is_active == True
                ).all()
                
                for related_mem in related_memories:
                    if related_mem.id in memory_candidates:
                        # 提高相关记忆的权重
                        memory_candidates[related_mem.id] *= 1.2
        
        # 如果有向量搜索结果，按搜索结果排序返回
        if memory_candidates:
            # 获取所有候选记忆的详细信息
            candidate_ids = list(memory_candidates.keys())
            memory_dict = {}
            for memory in db.query(GlobalMemory).filter(
                GlobalMemory.id.in_(candidate_ids),
                GlobalMemory.user_id == user_id,
                GlobalMemory.is_active == True
            ).all():
                memory_dict[memory.id] = memory
            
            # 综合排序：相似度 * 重要性 * 新鲜度权重
            def sort_key(memory_id):
                memory = memory_dict.get(memory_id)
                if not memory:
                    return 0
                
                similarity = memory_candidates[memory_id]
                importance = memory.importance_score or 0.5
                
                # 计算新鲜度权重（最近7天的记忆权重更高）
                days_since_created = (datetime.now() - memory.created_at).days
                freshness = 1.0 if days_since_created <= 1 else \
                          0.9 if days_since_created <= 3 else \
                          0.8 if days_since_created <= 7 else \
                          0.5
                
                # 如果是当前会话的记忆，进一步提高权重
                session_bonus = 1.5 if memory.session_id == session_id else 1.0
                
                return similarity * importance * freshness * session_bonus
            
            # 按综合评分排序
            sorted_memory_ids = sorted(candidate_ids, key=sort_key, reverse=True)
            
            # 限制结果数量
            ordered_memories = [memory_dict[mid] for mid in sorted_memory_ids if mid in memory_dict][:limit]
            return ordered_memories
        
        # 5. 如果没有向量搜索结果，回退到传统的文本搜索
        db_query = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        )
        
        # 过滤条件
        if memory_types:
            db_query = db_query.filter(GlobalMemory.memory_type.in_(memory_types))
        
        if memory_categories:
            db_query = db_query.filter(GlobalMemory.memory_category.in_(memory_categories))
        
        if session_id:
            db_query = db_query.filter(GlobalMemory.session_id == session_id)
        
        if query:
            # 使用更灵活的文本搜索
            db_query = db_query.filter(
                (GlobalMemory.content.ilike(f"%{query}%")) |
                (GlobalMemory.title.ilike(f"%{query}%")) |
                (GlobalMemory.summary.ilike(f"%{query}%"))
            )
        
        # 排序和限制
        db_query = db_query.order_by(
            desc(GlobalMemory.created_at),
            desc(GlobalMemory.importance_score)
        ).limit(limit)
        
        return db_query.all()
    
    @staticmethod
    async def get_user_memories(db: Session, user_id: int, memory_types: Optional[List[str]] = None,
                         memory_categories: Optional[List[str]] = None, limit: int = 20,
                         offset: int = 0, session_id: Optional[str] = None) -> List[GlobalMemory]:
        """获取用户的所有记忆条目，使用缓存优化"""
        return await memory_cache_service.get_user_memories(db, user_id, memory_types, memory_categories, limit, offset, session_id)

    @staticmethod
    async def get_intelligent_context_memories(
        db: Session,
        user_id: int,
        conversation_id: int,
        query: Optional[str] = None,
        limit: int = 10,
        use_semantic_search: bool = True,
        use_recency_boost: bool = True,
        use_importance_boost: bool = True
    ) -> List[GlobalMemory]:
        """智能上下文记忆检索 - 根据对话上下文智能检索相关记忆"""
        
        # 1. 获取当前对话相关的记忆作为基础上下文
        conversation_memories = await MemoryService.get_conversation_memories(
            db, conversation_id, user_id, limit=20, offset=0
        )
        
        # 如果没有查询词，直接返回对话相关记忆
        if not query:
            return conversation_memories[:limit]
        
        # 2. 构建智能搜索查询
        enhanced_query = query
        
        # 使用对话上下文增强查询
        if conversation_memories:
            # 提取对话记忆的关键内容
            conversation_context = " ".join([
                f"{mem.content[:100]}" for mem in conversation_memories[:5] if mem.content
            ])
            enhanced_query = f"{query} [对话上下文: {conversation_context}]"
        
        # 3. 执行语义搜索，使用缓存优化
        semantic_results = []
        if use_semantic_search:
            # 尝试从缓存获取语义搜索结果
            cached_results = memory_cache_service.get_cached_semantic_search_sync(enhanced_query, user_id)
            if cached_results:
                semantic_results = cached_results
            else:
                try:
                    # 使用Chroma向量数据库进行语义搜索
                    search_results = chroma_service.search_similar(
                        query=enhanced_query,
                        where_filter={"user_id": user_id},
                        n_results=limit * 2  # 获取更多结果用于后续排序
                    )
                    
                    # 将搜索结果转换为记忆对象
                    memory_ids = [int(result["metadata"]["memory_id"]) for result in search_results if "metadata" in result and "memory_id" in result["metadata"]]
                    if memory_ids:
                        semantic_results = db.query(GlobalMemory).filter(
                            GlobalMemory.id.in_(memory_ids),
                            GlobalMemory.user_id == user_id,
                            GlobalMemory.is_active == True
                        ).all()
                        # 缓存语义搜索结果
                        memory_cache_service.cache_semantic_search_sync(enhanced_query, user_id, semantic_results)
                except Exception as e:
                    # 如果向量搜索失败，回退到文本搜索
                    import logging
                    logging.warning(f"语义搜索失败: {str(e)}, 回退到文本搜索")
                    semantic_results = MemoryService.search_memories_by_text(
                        db, query, user_id, limit=limit * 2
                    )
        else:
            # 不使用语义搜索，直接进行文本搜索
            semantic_results = MemoryService.search_memories_by_text(
                db, query, user_id, limit=limit * 2
            )
        
        # 4. 智能排序算法
        all_results = list(set(conversation_memories + semantic_results))
        
        # 计算每个记忆的智能分数
        scored_memories = []
        for memory in all_results:
            score = MemoryService.calculate_context_relevance_score(
                memory, query, conversation_memories,
                use_recency_boost=use_recency_boost,
                use_importance_boost=use_importance_boost
            )
            scored_memories.append((memory, score))
        
        # 按分数排序
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前limit个结果
        return [memory for memory, score in scored_memories[:limit]]

    @staticmethod
    def search_memories_by_text(db: Session, query: str, user_id: int, limit: int = 10) -> List[GlobalMemory]:
        """基于文本内容搜索记忆"""
        from sqlalchemy import or_
        
        return db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True,
            or_(
                GlobalMemory.title.ilike(f"%{query}%"),
                GlobalMemory.content.ilike(f"%{query}%"),
                GlobalMemory.summary.ilike(f"%{query}%")
            )
        ).order_by(desc(GlobalMemory.created_at)).limit(limit).all()
    
    @staticmethod
    async def retrieve_relevant_memories(db: Session, user_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """检索用户的相关记忆，用于聊天增强"""
        # 使用智能上下文记忆检索功能
        memories = await MemoryService.get_intelligent_context_memories(
            db=db,
            user_id=user_id,
            conversation_id=0,  # 临时值，不影响搜索
            query=query,
            limit=limit,
            use_semantic_search=True,
            use_recency_boost=True,
            use_importance_boost=True
        )
        
        # 转换为字典格式返回
        return [{
            "id": mem.id,
            "title": mem.title or "无标题记忆",
            "content": mem.content,
            "memory_type": mem.memory_type,
            "memory_category": mem.memory_category,
            "importance_score": mem.importance_score,
            "created_at": mem.created_at.isoformat()
        } for mem in memories]

    @staticmethod
    def calculate_context_relevance_score(
        memory: GlobalMemory,
        query: str,
        conversation_memories: List[GlobalMemory],
        use_recency_boost: bool = True,
        use_importance_boost: bool = True
    ) -> float:
        """计算记忆在特定上下文中的相关性分数"""
        base_score = 0.5
        
        # 1. 文本匹配分数
        query_terms = query.lower().split()
        memory_text = f"{memory.title or ''} {memory.content or ''} {memory.summary or ''}".lower()
        
        # 计算查询词在记忆中的出现频率
        term_matches = sum(1 for term in query_terms if term in memory_text)
        text_match_score = term_matches / len(query_terms) if query_terms else 0
        base_score += text_match_score * 0.3
        
        # 2. 时间相关性（最近性）
        if use_recency_boost and memory.created_at:
            # 计算记忆的新鲜度（越新分数越高）
            days_ago = (datetime.now() - memory.created_at).days
            recency_score = max(0, 1 - (days_ago / 30))  # 30天内线性衰减
            base_score += recency_score * 0.2
        
        # 3. 重要性分数
        if use_importance_boost and memory.importance_score:
            base_score += memory.importance_score * 0.2
        
        # 4. 对话上下文相关性
        conversation_memory_ids = [m.id for m in conversation_memories]
        if memory.id in conversation_memory_ids:
            base_score += 0.3  # 属于当前对话的记忆加分
        
        # 5. 会话ID匹配（如果属于同一会话）
        if conversation_memories and memory.session_id:
            current_session_ids = set(m.session_id for m in conversation_memories if m.session_id)
            if memory.session_id in current_session_ids:
                base_score += 0.2
        
        return min(base_score, 1.0)  # 确保分数不超过1.0

    @staticmethod
    def get_user_memory_stats(db: Session, user_id: int, time_range: str = "30d") -> MemoryStats:
        """获取用户记忆统计信息"""
        # 检查缓存
        cache_key = MemoryService._get_cache_key("stats", user_id, time_range=time_range)
        cached_stats = MemoryService._get_cache(cache_key)
        if cached_stats is not None:
            memory_logger.info("从缓存获取记忆统计信息", extra_fields={
                "user_id": user_id,
                "time_range": time_range
            })
            return cached_stats
        
        # 计算统计数据
        stats = MemoryService._calculate_user_memory_stats(db, user_id, time_range)
        
        # 设置缓存
        MemoryService._set_cache(cache_key, stats)
        
        return stats
    
    @staticmethod
    def _calculate_user_memory_stats(db: Session, user_id: int, time_range: str) -> MemoryStats:
        """计算用户记忆统计信息（内部方法）"""
        # 计算时间范围
        if time_range.endswith("d"):
            days = int(time_range[:-1])
            start_date = datetime.now() - timedelta(days=days)
        else:
            start_date = datetime.min
        
        # 基础查询
        db_query = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.created_at >= start_date
        )
        
        # 统计数据
        total_count = db_query.count()
        
        # 按类型统计
        by_type = {}
        type_query = db_query.with_entities(GlobalMemory.memory_type, db_query.count()).group_by(GlobalMemory.memory_type).all()
        for memory_type, count in type_query:
            by_type[memory_type] = count
        
        # 按类别统计
        by_category = {}
        category_query = db_query.with_entities(GlobalMemory.memory_category, db_query.count()).group_by(GlobalMemory.memory_category).all()
        for memory_category, count in category_query:
            # 将None转换为默认字符串"UNCATEGORIZED"
            category_key = memory_category if memory_category is not None else "UNCATEGORIZED"
            by_category[category_key] = count
        
        # 活跃记忆数量
        active_count = db_query.filter(GlobalMemory.is_active == True).count()
        
        # 总访问次数
        access_query = db.query(func.sum(GlobalMemory.access_count)).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.created_at >= start_date,
            GlobalMemory.is_active == True
        ).scalar() or 0
        total_access_count = int(access_query)
        
        # 平均重要性
        importance_query = db.query(func.avg(GlobalMemory.importance_score)).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.created_at >= start_date,
            GlobalMemory.is_active == True
        ).scalar() or 0.0
        average_importance = float(importance_query)
        
        # 向量数据库统计
        vector_db_count = 0
        
        return MemoryStats(
            total_count=total_count,
            by_type=by_type,
            by_category=by_category,
            active_count=active_count,
            total_access_count=total_access_count,
            average_importance=average_importance,
            time_range=time_range,
            vector_db_count=vector_db_count
        )
    
    @staticmethod
    def analyze_user_patterns(db: Session, user_id: int) -> MemoryPatterns:
        """分析用户记忆模式"""
        start_time = time.time()
        
        try:
            # 获取用户的所有活跃记忆（限制数量以避免内存问题）
            user_memories = db.query(GlobalMemory).filter(
                GlobalMemory.user_id == user_id,
                GlobalMemory.is_active == True
            ).order_by(desc(GlobalMemory.created_at)).limit(1000).all()
            
            # 时间模式分析
            temporal_patterns = {
                "daily": {"morning": 0, "afternoon": 0, "evening": 0},
                "weekly": {}
            }
            
            # 按小时统计
            hourly_stats = [0] * 24
            for memory in user_memories:
                hour = memory.created_at.hour
                hourly_stats[hour] += 1
            
            # 按时间段分类
            temporal_patterns["daily"]["morning"] = sum(hourly_stats[6:12])  # 6-12点
            temporal_patterns["daily"]["afternoon"] = sum(hourly_stats[12:18])  # 12-18点
            temporal_patterns["daily"]["evening"] = sum(hourly_stats[18:24]) + sum(hourly_stats[0:6])  # 18-24点和0-6点
            
            # 按星期几统计
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for day in days:
                temporal_patterns["weekly"][day] = 0
            
            for memory in user_memories:
                weekday = memory.created_at.weekday()  # 0-6, 0=周一
                day_name = days[weekday]
                temporal_patterns["weekly"][day_name] += 1
            
            # 主题模式分析（基于记忆类别）
            topic_patterns = []
            category_counts = {}
            category_importance = {}
            
            for memory in user_memories:
                category = memory.memory_category or "UNCATEGORIZED"
                if category not in category_counts:
                    category_counts[category] = 0
                    category_importance[category] = []
                category_counts[category] += 1
                if memory.importance_score:
                    category_importance[category].append(memory.importance_score)
            
            # 计算每个类别的平均重要性
            for category, count in category_counts.items():
                avg_importance = 0.0
                if category_importance[category]:
                    avg_importance = sum(category_importance[category]) / len(category_importance[category])
                topic_patterns.append({
                    "topic": category,
                    "count": count,
                    "average_importance": round(avg_importance, 2)
                })
            
            # 按数量排序
            topic_patterns.sort(key=lambda x: x["count"], reverse=True)
            
            # 访问模式分析
            if user_memories:
                total_access_count = sum(memory.access_count for memory in user_memories)
                average_access_frequency = round(total_access_count / len(user_memories), 2)
                most_accessed = max(user_memories, key=lambda x: x.access_count)
                peak_access_hour = hourly_stats.index(max(hourly_stats)) if max(hourly_stats) > 0 else 14
                peak_access_time = f"{peak_access_hour:02d}:00-{peak_access_hour + 2:02d}:00"
            else:
                total_access_count = 0
                average_access_frequency = 0.0
                most_accessed = None
                peak_access_time = "14:00-16:00"
            
            access_patterns = {
                "most_accessed": most_accessed.id if most_accessed else 0,
                "average_access_frequency": average_access_frequency,
                "peak_access_time": peak_access_time
            }
            
            # 关联模式分析（使用持久化的关联数据）
            association_patterns = []
            
            # 查询用户的所有记忆关联（限制数量）
            user_associations = db.query(MemoryAssociation).join(
                GlobalMemory, 
                GlobalMemory.id == MemoryAssociation.source_memory_id
            ).filter(
                GlobalMemory.user_id == user_id,
                GlobalMemory.is_active == True
            ).order_by(desc(MemoryAssociation.strength)).limit(100).all()
            
            # 提取关联模式
            for association in user_associations:
                # 获取目标记忆信息
                target_memory = db.query(GlobalMemory).filter(
                    GlobalMemory.id == association.target_memory_id,
                    GlobalMemory.user_id == user_id,
                    GlobalMemory.is_active == True
                ).first()
                
                if target_memory:
                    association_patterns.append({
                        "source_memory_id": association.source_memory_id,
                        "target_memory_id": association.target_memory_id,
                        "association_type": association.association_type,
                        "strength": association.strength,
                        "created_at": association.created_at.isoformat()
                    })
            
            # 如果没有持久化的关联，回退到临时相似性搜索
            # 暂时禁用向量搜索，以避免服务器崩溃
            # if not association_patterns and len(user_memories) > 1:
            #     # 随机选择5个记忆作为查询，查找相似记忆
            #     import random
            #     sample_size = min(5, len(user_memories))
            #     sample_memories = random.sample(user_memories, sample_size)
            #     
            #     for source_memory in sample_memories:
            #         if source_memory.content:
            #             try:
            #                 # 搜索相似记忆
            #                 similar_results = chroma_service.search_similar(
            #                     query=source_memory.content,
            #                     n_results=2,  # 找最相似的1个
            #                     where_filter={"user_id": user_id},
            #                     collection_name="memories"
            #                 )
            #                 
            #                 for i, doc_id in enumerate(similar_results["ids"][0]):
            #                     if str(doc_id) != str(source_memory.id):  # 排除自己
            #                         try:
            #                             target_memory_id = int(doc_id)
            #                             similarity = round(1 - similar_results["distances"][0][i], 2)  # 转换为相似度（0-1）
            #                             
            #                             # 只添加相似度大于0.7的关联
            #                             if similarity > 0.7:
            #                                 association_patterns.append({
            #                                     "source_memory_id": source_memory.id,
            #                                     "target_memory_id": target_memory_id,
            #                                     "association_type": "SEMANTIC",
            #                                     "strength": similarity
            #                                 })
            #                         except (ValueError, TypeError):
            #                             continue
            #             except Exception as e:
            #                 memory_logger.error(f"向量搜索失败: {str(e)}", extra_fields={
            #                     "user_id": user_id,
            #                     "source_memory_id": source_memory.id
            #                 }, exc_info=e)
            
            # 记录性能指标
            response_time = (time.time() - start_time) * 1000  # 毫秒
            alert_manager.check_metric(
                metric_type=MetricType.RESPONSE_TIME,
                metric_value=response_time,
                metadata={"endpoint": "analyze_user_patterns", "user_id": user_id}
            )
            
            memory_logger.info("分析用户记忆模式成功", extra_fields={
                "user_id": user_id,
                "memory_count": len(user_memories),
                "response_time": response_time
            })
            
            return MemoryPatterns(
                temporal_patterns=temporal_patterns,
                topic_patterns=topic_patterns,
                access_patterns=access_patterns,
                association_patterns=association_patterns
            )
            
        except Exception as e:
            memory_logger.error(f"分析用户记忆模式失败: {str(e)}", extra_fields={
                "user_id": user_id
            }, exc_info=e)
            
            # 返回默认值，避免服务器崩溃
            return MemoryPatterns(
                temporal_patterns={
                    "daily": {"morning": 0, "afternoon": 0, "evening": 0},
                    "weekly": {}
                },
                topic_patterns=[],
                access_patterns={
                    "most_accessed": 0,
                    "average_access_frequency": 0.0,
                    "peak_access_time": "14:00-16:00"
                },
                association_patterns=[]
            )
    
    @staticmethod
    def cleanup_expired_memories(db: Session, user_id: int) -> int:
        """清理过期记忆"""
        # 获取用户记忆配置
        user_config = MemoryService.get_user_memory_config(db, user_id)
        if not user_config:
            return 0
        
        # 计算过期时间点
        short_term_days = user_config.short_term_retention_days or 7
        expire_date = datetime.now() - timedelta(days=short_term_days)
        
        # 查找过期的短期记忆
        expired_memories = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.memory_type == "SHORT_TERM",
            GlobalMemory.created_at < expire_date,
            GlobalMemory.is_active == True
        ).all()
        
        if not expired_memories:
            return 0
        
        # 软删除过期记忆并从向量数据库中删除
        deleted_count = 0
        for memory in expired_memories:
            # 软删除数据库中的记忆
            memory.is_active = False
            memory.updated_at = datetime.now()
            
            # 从向量数据库中删除
            chroma_service.delete_document(document_id=str(memory.id), collection_name="memories")
            
            deleted_count += 1
        
        db.commit()
        return deleted_count
    
    @staticmethod
    def compress_similar_memories(db: Session, user_id: int) -> Dict[str, int]:
        """压缩相似记忆"""
        # 获取用户的所有活跃短期记忆
        short_term_memories = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.memory_type == "SHORT_TERM",
            GlobalMemory.is_active == True
        ).all()
        
        if len(short_term_memories) < 2:
            return {"processed": 0, "compressed": 0, "created": 0}
        
        processed_count = 0
        compressed_count = 0
        created_count = 0
        
        # 标记已处理的记忆
        processed_ids = set()
        
        # 使用向量相似性查找并压缩相似记忆
        for i, memory in enumerate(short_term_memories):
            if memory.id in processed_ids or not memory.content:
                continue
            
            # 搜索相似记忆
            similar_results = chroma_service.search_similar(
                query=memory.content,
                n_results=5,  # 最多查找5个相似记忆
                where_filter={"user_id": user_id, "memory_type": "SHORT_TERM"},
                collection_name="memories"
            )
            
            processed_ids.add(memory.id)
            processed_count += 1
            
            # 收集相似记忆ID
            similar_memory_ids = []
            for j, doc_id in enumerate(similar_results["ids"][0]):
                if str(doc_id) == str(memory.id):
                    continue
                    
                similarity = 1 - similar_results["distances"][0][j]
                if similarity > 0.8:  # 相似度大于0.8
                    try:
                        similar_memory_ids.append(int(doc_id))
                    except (ValueError, TypeError):
                        continue
            
            if not similar_memory_ids:
                continue
            
            # 获取所有相似记忆的详细信息
            similar_memories = db.query(GlobalMemory).filter(
                GlobalMemory.id.in_(similar_memory_ids),
                GlobalMemory.user_id == user_id,
                GlobalMemory.is_active == True
            ).all()
            
            if len(similar_memories) < 1:
                continue
            
            # 合并相似记忆
            all_content = [memory.content] + [m.content for m in similar_memories]
            all_summaries = [memory.summary] + [m.summary for m in similar_memories if m.summary]
            all_tags = set(memory.tags or [])
            all_importance = [memory.importance_score or 0] + [m.importance_score or 0 for m in similar_memories]
            
            for m in similar_memories:
                all_tags.update(m.tags or [])
                processed_ids.add(m.id)
            
            # 创建压缩后的记忆
            compressed_content = "\n".join(all_content)
            compressed_summary = "\n".join([s for s in all_summaries if s]) if all_summaries else None
            avg_importance = sum(all_importance) / len(all_importance)
            
            # 创建新的长期记忆
            compressed_memory = MemoryCreate(
                title=f"Compressed: {memory.title}" if memory.title else "Compressed Memory",
                content=compressed_content,
                memory_type="LONG_TERM",
                memory_category=memory.memory_category,
                summary=compressed_summary,
                importance_score=round(avg_importance, 2),
                tags=list(all_tags),
                memory_metadata={"compressed_from": [memory.id] + similar_memory_ids},
                session_id=memory.session_id,
                source_type=memory.source_type,
                source_id=memory.source_id,
                source_reference=memory.source_reference
            )
            
            # 保存压缩后的记忆
            new_compressed_memory = MemoryService.create_memory(db, compressed_memory, user_id)
            created_count += 1
            
            # 软删除原记忆并从向量数据库中删除
            for m in similar_memories + [memory]:
                m.is_active = False
                m.updated_at = datetime.now()
                chroma_service.delete_document(document_id=str(m.id), collection_name="memories")
                compressed_count += 1
        
        db.commit()
        
        return {
            "processed": processed_count,
            "compressed": compressed_count,
            "created": created_count
        }
    
    @staticmethod
    def get_user_memory_config(db: Session, user_id: int) -> Optional[UserMemoryConfig]:
        """获取用户记忆配置"""
        return db.query(UserMemoryConfig).filter(UserMemoryConfig.user_id == user_id).first()
    
    @staticmethod
    def update_user_memory_config(db: Session, user_id: int, config_data: Dict[str, Any]) -> UserMemoryConfig:
        """更新用户记忆配置"""
        db_config = db.query(UserMemoryConfig).filter(UserMemoryConfig.user_id == user_id).first()
        
        if not db_config:
            # 创建新配置
            db_config = UserMemoryConfig(user_id=user_id, **config_data)
            db.add(db_config)
        else:
            # 更新现有配置
            for key, value in config_data.items():
                setattr(db_config, key, value)
            db_config.updated_at = datetime.now()
        
        db.commit()
        db.refresh(db_config)
        
        return db_config
    
    @staticmethod
    def build_memory_associations(db: Session, memory_id: int, user_id: int, association_types: Optional[List[str]] = None) -> int:
        """建立记忆关联关系"""
        start_time = time.time()
        
        try:
            # 获取要建立关联的记忆
            source_memory = db.query(GlobalMemory).filter(
                GlobalMemory.id == memory_id,
                GlobalMemory.user_id == user_id,
                GlobalMemory.is_active == True
            ).first()
            
            if not source_memory or not source_memory.content:
                return 0
            
            # 默认关联类型
            if not association_types:
                association_types = ["SEMANTIC"]
            
            # 1. 语义关联：基于向量相似性
            if "SEMANTIC" in association_types:
                try:
                    # 搜索相似记忆
                    similar_results = chroma_service.search_similar(
                        query=source_memory.content,
                        n_results=10,
                        where_filter={"user_id": user_id, "memory_type": ["SHORT_TERM", "LONG_TERM", "SEMANTIC"]},
                        collection_name="memories"
                    )
                    
                    # 批量收集要创建的关联
                    new_associations = []
                    existing_pairs = set()
                    
                    # 先查询所有已存在的关联
                    existing_associations = db.query(MemoryAssociation).filter(
                        MemoryAssociation.source_memory_id == source_memory.id
                    ).all()
                    for assoc in existing_associations:
                        existing_pairs.add(assoc.target_memory_id)
                    
                    # 遍历搜索结果
                    for i, doc_id in enumerate(similar_results["ids"][0]):
                        try:
                            target_memory_id = int(doc_id)
                            if target_memory_id == source_memory.id:
                                continue
                            
                            # 检查是否已存在关联
                            if target_memory_id in existing_pairs:
                                continue
                            
                            distance = similar_results["distances"][0][i]
                            similarity = 1 - distance  # 转换为相似度（0-1）
                            
                            # 只建立相似度高的关联
                            if similarity > 0.7:
                                # 创建新关联对象（不立即添加到数据库）
                                new_association = MemoryAssociation(
                                    source_memory_id=source_memory.id,
                                    target_memory_id=target_memory_id,
                                    association_type="SEMANTIC",
                                    strength=round(similarity, 2),
                                    bidirectional=True
                                )
                                new_associations.append(new_association)
                                existing_pairs.add(target_memory_id)
                        except (ValueError, TypeError):
                            continue
                    
                    # 批量添加到数据库
                    if new_associations:
                        db.bulk_save_objects(new_associations)
                        db.commit()
                        created_count = len(new_associations)
                    else:
                        created_count = 0
                    
                    # 记录性能指标
                    response_time = (time.time() - start_time) * 1000  # 毫秒
                    alert_manager.check_metric(
                        metric_type=MetricType.RESPONSE_TIME,
                        metric_value=response_time,
                        metadata={"endpoint": "build_memory_associations", "user_id": user_id, "memory_id": memory_id}
                    )
                    
                    memory_logger.info("建立记忆关联成功", extra_fields={
                        "user_id": user_id,
                        "memory_id": memory_id,
                        "created_count": created_count,
                        "response_time": response_time
                    })
                    
                    return created_count
                    
                except Exception as e:
                    memory_logger.error(f"向量搜索失败: {str(e)}", extra_fields={
                        "user_id": user_id,
                        "memory_id": memory_id
                    }, exc_info=e)
                    return 0
            
            return 0
            
        except Exception as e:
            memory_logger.error("建立记忆关联失败", extra_fields={
                "user_id": user_id,
                "memory_id": memory_id
            }, exc_info=e)
            raise
    
    @staticmethod
    def build_knowledge_graph(db: Session, user_id: int, max_nodes: int = 100) -> Dict[str, Any]:
        """构建用户记忆的知识图谱"""
        # 1. 获取用户的活跃记忆作为节点
        user_memories = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).order_by(desc(GlobalMemory.created_at)).limit(max_nodes).all()
        
        if not user_memories:
            return {
                "nodes": [],
                "edges": [],
                "total_nodes": 0,
                "total_edges": 0
            }
        
        # 2. 构建节点映射
        memory_id_map = {mem.id: mem for mem in user_memories}
        
        # 3. 获取所有关联作为边
        memory_ids = list(memory_id_map.keys())
        
        # 查询所有与这些记忆相关的关联
        associations = db.query(MemoryAssociation).filter(
            (MemoryAssociation.source_memory_id.in_(memory_ids)) |
            (MemoryAssociation.target_memory_id.in_(memory_ids))
        ).all()
        
        # 4. 构建节点列表
        nodes = []
        for mem in user_memories:
            node = {
                "id": mem.id,
                "type": mem.memory_type,
                "category": mem.memory_category,
                "title": mem.title if mem.title else f"记忆_{mem.id}",
                "importance": mem.importance_score or 0.5,
                "created_at": mem.created_at.isoformat(),
                "content_preview": mem.content[:100] + "..." if mem.content and len(mem.content) > 100 else mem.content
            }
            nodes.append(node)
        
        # 5. 构建边列表
        edges = []
        for assoc in associations:
            # 只包含在节点映射中的记忆关联
            if assoc.source_memory_id in memory_id_map and assoc.target_memory_id in memory_id_map:
                edge = {
                    "id": assoc.id,
                    "source": assoc.source_memory_id,
                    "target": assoc.target_memory_id,
                    "type": assoc.association_type,
                    "strength": assoc.strength,
                    "bidirectional": assoc.bidirectional,
                    "created_at": assoc.created_at.isoformat()
                }
                edges.append(edge)
        
        # 6. 计算节点的中心性（基于连接数量）
        node_degree = {node["id"]: 0 for node in nodes}
        for edge in edges:
            node_degree[edge["source"]] += 1
            if edge["bidirectional"]:
                node_degree[edge["target"]] += 1
        
        # 更新节点的中心性属性
        for node in nodes:
            node["degree"] = node_degree.get(node["id"], 0)
            node["centrality"] = min(node_degree.get(node["id"], 0) / len(nodes) * 2, 1.0)  # 归一化到0-1
        
        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": list(set(node["type"] for node in nodes)),
            "edge_types": list(set(edge["type"] for edge in edges)),
            "max_degree": max(node_degree.values()) if node_degree else 0
        }
    
    @staticmethod
    def traverse_knowledge_graph(db: Session, user_id: int, start_memory_id: int, max_depth: int = 3) -> Dict[str, Any]:
        """遍历知识图谱，获取与起始记忆相关的所有记忆"""
        # 验证起始记忆存在且属于用户
        start_memory = db.query(GlobalMemory).filter(
            GlobalMemory.id == start_memory_id,
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).first()
        
        if not start_memory:
            return {
                "error": "起始记忆不存在或无访问权限",
                "nodes": [],
                "edges": []
            }
        
        # 使用广度优先搜索遍历知识图谱
        visited_nodes = set()
        visited_edges = set()
        queue = [(start_memory_id, 0)]  # (memory_id, depth)
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if current_id in visited_nodes or depth > max_depth:
                continue
            
            visited_nodes.add(current_id)
            
            # 获取当前节点的所有关联
            current_associations = db.query(MemoryAssociation).filter(
                ((MemoryAssociation.source_memory_id == current_id) |
                 (MemoryAssociation.target_memory_id == current_id)) &
                ((MemoryAssociation.source_memory_id.in_(visited_nodes)) |
                 (MemoryAssociation.target_memory_id.in_(visited_nodes)))
            ).all()
            
            for assoc in current_associations:
                edge_id = f"{assoc.source_memory_id}-{assoc.target_memory_id}-{assoc.association_type}"
                if edge_id not in visited_edges:
                    visited_edges.add(edge_id)
                    
                    # 将关联的另一端加入队列
                    if assoc.source_memory_id == current_id and assoc.target_memory_id not in visited_nodes:
                        queue.append((assoc.target_memory_id, depth + 1))
                    elif assoc.target_memory_id == current_id and assoc.source_memory_id not in visited_nodes:
                        queue.append((assoc.source_memory_id, depth + 1))
        
        # 获取所有节点和边的数据
        nodes = []
        for mem_id in visited_nodes:
            memory = db.query(GlobalMemory).filter(GlobalMemory.id == mem_id).first()
            if memory:
                nodes.append({
                    "id": memory.id,
                    "type": memory.memory_type,
                    "category": memory.memory_category,
                    "title": memory.title if memory.title else f"记忆_{memory.id}",
                    "importance": memory.importance_score or 0.5,
                    "created_at": memory.created_at.isoformat(),
                    "content_preview": memory.content[:100] + "..." if memory.content and len(memory.content) > 100 else memory.content
                })
        
        edges = []
        for edge_id in visited_edges:
            source_id, target_id, assoc_type = edge_id.split("-", 2)
            source_id = int(source_id)
            target_id = int(target_id)
            
            association = db.query(MemoryAssociation).filter(
                MemoryAssociation.source_memory_id == source_id,
                MemoryAssociation.target_memory_id == target_id,
                MemoryAssociation.association_type == assoc_type
            ).first()
            
            if association:
                edges.append({
                    "id": association.id,
                    "source": association.source_memory_id,
                    "target": association.target_memory_id,
                    "type": association.association_type,
                    "strength": association.strength,
                    "bidirectional": association.bidirectional,
                    "created_at": association.created_at.isoformat()
                })
        
        return {
            "start_node": start_memory_id,
            "max_depth": max_depth,
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }
    
    @staticmethod
    def analyze_user_preferences(db: Session, user_id: int) -> Dict[str, Any]:
        """分析用户的记忆偏好模式"""
        # 获取用户的所有活跃记忆
        user_memories = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).all()
        
        if not user_memories:
            return {
                "preferred_categories": {},
                "preferred_types": {},
                "time_based_preferences": {},
                "access_patterns": {}
            }
        
        # 1. 类别偏好分析
        category_counts = {}
        category_importance = {}
        for memory in user_memories:
            category = memory.memory_category or "UNCATEGORIZED"
            if category not in category_counts:
                category_counts[category] = 0
                category_importance[category] = []
            category_counts[category] += 1
            if memory.importance_score:
                category_importance[category].append(memory.importance_score)
        
        # 计算每个类别的平均重要性
        preferred_categories = {}
        for category, count in category_counts.items():
            avg_importance = 0.0
            if category_importance[category]:
                avg_importance = sum(category_importance[category]) / len(category_importance[category])
            preferred_categories[category] = {
                "count": count,
                "average_importance": round(avg_importance, 2),
                "preference_score": round((count / len(user_memories)) * 0.6 + avg_importance * 0.4, 2)
            }
        
        # 2. 类型偏好分析
        type_counts = {}
        type_importance = {}
        for memory in user_memories:
            memory_type = memory.memory_type
            if memory_type not in type_counts:
                type_counts[memory_type] = 0
                type_importance[memory_type] = []
            type_counts[memory_type] += 1
            if memory.importance_score:
                type_importance[memory_type].append(memory.importance_score)
        
        preferred_types = {}
        for memory_type, count in type_counts.items():
            avg_importance = 0.0
            if type_importance[memory_type]:
                avg_importance = sum(type_importance[memory_type]) / len(type_importance[memory_type])
            preferred_types[memory_type] = {
                "count": count,
                "average_importance": round(avg_importance, 2),
                "preference_score": round((count / len(user_memories)) * 0.6 + avg_importance * 0.4, 2)
            }
        
        # 3. 时间偏好分析
        hourly_counts = [0] * 24
        for memory in user_memories:
            if memory.created_at:
                hour = memory.created_at.hour
                hourly_counts[hour] += 1
        
        time_based_preferences = {
            "hourly_distribution": hourly_counts,
            "peak_hour": hourly_counts.index(max(hourly_counts)) if max(hourly_counts) > 0 else 14
        }
        
        # 4. 访问模式分析
        total_access_count = sum(memory.access_count for memory in user_memories if memory.access_count)
        average_access_frequency = total_access_count / len(user_memories) if user_memories else 0
        
        most_accessed = max(user_memories, key=lambda x: x.access_count) if user_memories else None
        
        access_patterns = {
            "average_access_frequency": round(average_access_frequency, 2),
            "most_accessed_memory_id": most_accessed.id if most_accessed else None,
            "most_accessed_memory_title": most_accessed.title if most_accessed else None
        }
        
        return {
            "preferred_categories": preferred_categories,
            "preferred_types": preferred_types,
            "time_based_preferences": time_based_preferences,
            "access_patterns": access_patterns
        }
    
    @staticmethod
    def analyze_memory_sentiment(db: Session, memory_id: int, user_id: int) -> Dict[str, Any]:
        """分析记忆的情感倾向"""
        # 获取记忆
        memory = db.query(GlobalMemory).filter(
            GlobalMemory.id == memory_id,
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).first()
        
        if not memory:
            raise ValueError("记忆不存在或无访问权限")
        
        # 简单的情感分析实现
        # 实际应用中可以使用更复杂的NLP模型
        positive_words = ["好", "棒", "优秀", "喜欢", "高兴", "开心", "满意", "成功", "完美", "赞"]
        negative_words = ["差", "糟糕", "讨厌", "难过", "生气", "失望", "失败", "错误", "麻烦", "问题"]
        
        content = (memory.content or "") + " " + (memory.summary or "")
        content_lower = content.lower()
        
        positive_score = sum(1 for word in positive_words if word in content_lower)
        negative_score = sum(1 for word in negative_words if word in content_lower)
        
        total_score = positive_score + negative_score
        sentiment_score = (positive_score - negative_score) / (total_score if total_score > 0 else 1)
        
        sentiment_label = "中性"
        if sentiment_score > 0.3:
            sentiment_label = "积极"
        elif sentiment_score < -0.3:
            sentiment_label = "消极"
        
        return {
            "memory_id": memory_id,
            "sentiment_score": round(sentiment_score, 2),
            "sentiment_label": sentiment_label,
            "positive_score": positive_score,
            "negative_score": negative_score
        }
    
    @staticmethod
    def auto_adjust_memory_priority(db: Session, user_id: int) -> Dict[str, int]:
        """自动调整记忆优先级"""
        # 获取用户的所有活跃记忆
        user_memories = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).all()
        
        if not user_memories:
            return {"updated_count": 0}
        
        updated_count = 0
        
        for memory in user_memories:
            # 计算新的优先级分数
            # 基于访问频率、时间衰减和情感倾向
            base_score = memory.importance_score or 0.5
            
            # 访问频率因子（访问次数越多，分数越高）
            access_factor = min(memory.access_count / 10, 1.0) if memory.access_count else 0
            
            # 时间衰减因子（越新的记忆，分数越高）
            days_since_created = (datetime.now() - memory.created_at).days
            time_factor = max(0, 1 - (days_since_created / 30))  # 30天内线性衰减
            
            # 情感因子（积极情感的记忆，分数略高）
            try:
                sentiment_result = MemoryService.analyze_memory_sentiment(db, memory.id, user_id)
                sentiment_factor = 1 + (sentiment_result["sentiment_score"] * 0.1)
            except:
                sentiment_factor = 1.0
            
            # 计算新的重要性分数
            new_importance_score = base_score * 0.5 + access_factor * 0.2 + time_factor * 0.2 + sentiment_factor * 0.1
            new_importance_score = min(max(new_importance_score, 0.1), 1.0)  # 限制在0.1-1.0之间
            
            # 更新分数
            if abs(new_importance_score - (memory.importance_score or 0.5)) > 0.1:
                memory.importance_score = round(new_importance_score, 2)
                memory.updated_at = datetime.now()
                updated_count += 1
        
        db.commit()
        return {"updated_count": updated_count}
    
    @staticmethod
    def auto_generate_memory_tags(db: Session, memory_id: int, user_id: int) -> List[str]:
        """自动生成记忆标签"""
        # 获取记忆
        memory = db.query(GlobalMemory).filter(
            GlobalMemory.id == memory_id,
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).first()
        
        if not memory:
            raise ValueError("记忆不存在或无访问权限")
        
        # 从内容中提取关键词作为标签
        content = (memory.content or "") + " " + (memory.summary or "") + " " + (memory.title or "")
        
        # 简单的关键词提取实现
        # 实际应用中可以使用更复杂的NLP模型
        stop_words = set(["的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"])
        
        # 分词（简单空格分词）
        words = content.split()
        
        # 过滤停用词和短词
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 计算词频
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 提取频率最高的前5个词作为标签
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        tags = [word for word, freq in sorted_words]
        
        # 更新记忆标签
        if tags:
            memory.tags = tags
            memory.updated_at = datetime.now()
            db.commit()
        
        return tags
    
    @staticmethod
    def build_cross_session_associations(db: Session, user_id: int) -> Dict[str, int]:
        """建立跨会话记忆关联"""
        # 获取用户的所有活跃记忆
        user_memories = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).all()
        
        if len(user_memories) < 2:
            return {"created_associations": 0}
        
        # 按会话分组
        session_memories = {}
        for memory in user_memories:
            session_id = memory.session_id or "default"
            if session_id not in session_memories:
                session_memories[session_id] = []
            session_memories[session_id].append(memory)
        
        # 如果只有一个会话，不需要建立跨会话关联
        if len(session_memories) < 2:
            return {"created_associations": 0}
        
        created_associations = 0
        
        # 遍历所有会话对
        session_ids = list(session_memories.keys())
        for i in range(len(session_ids)):
            for j in range(i + 1, len(session_ids)):
                session1 = session_ids[i]
                session2 = session_ids[j]
                
                # 从每个会话中获取最近的记忆
                recent_memories1 = sorted(session_memories[session1], key=lambda x: x.created_at, reverse=True)[:3]
                recent_memories2 = sorted(session_memories[session2], key=lambda x: x.created_at, reverse=True)[:3]
                
                # 计算跨会话记忆的相似度并建立关联
                for mem1 in recent_memories1:
                    if not mem1.content:
                        continue
                    
                    for mem2 in recent_memories2:
                        if not mem2.content:
                            continue
                        
                        # 检查是否已存在关联
                        existing_association = db.query(MemoryAssociation).filter(
                            ((MemoryAssociation.source_memory_id == mem1.id) &
                             (MemoryAssociation.target_memory_id == mem2.id)) |
                            ((MemoryAssociation.source_memory_id == mem2.id) &
                             (MemoryAssociation.target_memory_id == mem1.id))
                        ).first()
                        
                        if existing_association:
                            continue
                        
                        # 计算相似度
                        try:
                            # 使用Chroma计算相似度
                            results = chroma_service.search_similar(
                                query=mem1.content,
                                n_results=1,
                                where_filter={"user_id": user_id, "memory_id": mem2.id},
                                collection_name="memories"
                            )
                            
                            if results["ids"] and str(mem2.id) in results["ids"][0]:
                                index = results["ids"][0].index(str(mem2.id))
                                distance = results["distances"][0][index]
                                similarity = 1 - distance
                                
                                # 只建立相似度高的关联
                                if similarity > 0.7:
                                    new_association = MemoryAssociation(
                                        source_memory_id=mem1.id,
                                        target_memory_id=mem2.id,
                                        association_type="CROSS_SESSION",
                                        strength=round(similarity, 2),
                                        bidirectional=True
                                    )
                                    db.add(new_association)
                                    created_associations += 1
                        except:
                            pass
        
        db.commit()
        return {"created_associations": created_associations}
    
    @staticmethod
    def get_memory_review_suggestions(db: Session, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取记忆复习建议"""
        # 获取用户的所有活跃记忆
        user_memories = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).all()
        
        if not user_memories:
            return []
        
        # 计算每个记忆的复习分数
        review_candidates = []
        for memory in user_memories:
            # 基于重要性、时间衰减和访问频率计算复习分数
            importance_score = memory.importance_score or 0.5
            
            # 时间衰减因子（越久未复习，分数越高）
            days_since_created = (datetime.now() - memory.created_at).days
            time_factor = min(days_since_created / 7, 5)  # 7天内线性增加，最大5
            
            # 访问频率因子（访问次数越少，分数越高）
            access_factor = max(0, 1 - (memory.access_count / 5))  # 访问5次以上的记忆分数降低
            
            # 计算复习分数
            review_score = importance_score * 0.5 + time_factor * 0.3 + access_factor * 0.2
            
            review_candidates.append((memory, review_score))
        
        # 按复习分数排序
        review_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前limit个建议
        suggestions = []
        for memory, score in review_candidates[:limit]:
            suggestions.append({
                "memory_id": memory.id,
                "title": memory.title or "无标题",
                "content_preview": memory.content[:100] + "..." if len(memory.content) > 100 else memory.content,
                "importance_score": memory.importance_score,
                "review_score": round(score, 2),
                "created_at": memory.created_at.isoformat(),
                "last_accessed": memory.last_accessed.isoformat() if memory.last_accessed else None,
                "access_count": memory.access_count
            })
        
        return suggestions
    
    @staticmethod
    def update_preferences_based_on_access(db: Session, memory_id: int, user_id: int, access_type: str = "READ"):
        """根据记忆访问更新用户偏好"""
        # 获取记忆
        memory = db.query(GlobalMemory).filter(
            GlobalMemory.id == memory_id,
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).first()
        
        if not memory:
            return
        
        # 分析用户当前偏好
        preferences = MemoryService.analyze_user_preferences(db, user_id)
        
        # 调整记忆的重要性评分
        importance_score = memory.importance_score or 0.0
        
        # 1. 基于访问类型调整
        if access_type == "READ":
            importance_score += 0.02  # 阅读增加0.02
        elif access_type == "WRITE" or access_type == "UPDATE":
            importance_score += 0.05  # 写入/更新增加0.05
        elif access_type == "DELETE":
            importance_score -= 0.1   # 删除减少0.1
        
        # 2. 基于用户偏好调整
        category = memory.memory_category or "UNCATEGORIZED"
        memory_type = memory.memory_type
        
        # 类别偏好加成
        if category in preferences["preferred_categories"]:
            category_preference = preferences["preferred_categories"][category]["preference_score"]
            importance_score += category_preference * 0.03
        
        # 类型偏好加成
        if memory_type in preferences["preferred_types"]:
            type_preference = preferences["preferred_types"][memory_type]["preference_score"]
            importance_score += type_preference * 0.02
        
        # 3. 基于时间调整（如果当前时间是用户活跃时间）
        current_hour = datetime.now().hour
        peak_hour = preferences["time_based_preferences"].get("peak_hour", 14)
        if current_hour == peak_hour:
            importance_score += 0.01
        
        # 限制重要性评分在0.0-1.0之间
        importance_score = max(0.0, min(1.0, importance_score))
        
        # 更新记忆的重要性评分
        memory.importance_score = importance_score
        memory.last_accessed = datetime.now()
        memory.access_count += 1
        
        # 更新向量数据库中的记忆信息
        try:
            chroma_service.update_document(
                document_id=str(memory.id),
                text=memory.content,
                metadata={
                    "memory_id": memory.id,
                    "user_id": user_id,
                    "memory_type": memory.memory_type,
                    "memory_category": memory.memory_category,
                    "title": memory.title,
                    "importance_score": memory.importance_score,
                    "created_at": memory.created_at.isoformat()
                }
            )
        except Exception as e:
            import logging
            logging.warning(f"向量数据库更新失败: {str(e)}")
        
        db.commit()
    
    @staticmethod
    def evaluate_importance(memory: GlobalMemory, config: Optional[UserMemoryConfig] = None) -> float:
        """评估记忆的重要性分数（0.0-1.0）"""
        score = 0.0
        
        # 默认配置
        default_config = {
            "long_term_threshold": 0.7
        }
        
        # 合并用户配置和默认配置
        user_config = config.__dict__ if config else default_config
        config_data = {**default_config, **user_config}
        
        # 1. 访问频率权重 (0.3)
        access_weight = 0.3
        if memory.access_count > 0:
            # 访问次数越多，分数越高，最高1.0
            access_score = min(memory.access_count / 100.0, 1.0)
            score += access_score * access_weight
        
        # 2. 重要性评分初始值权重 (0.2)
        if memory.importance_score:
            score += memory.importance_score * 0.2
        
        # 3. 记忆类型权重 (0.2)
        type_weights = {
            "LONG_TERM": 1.0,
            "SEMANTIC": 0.9,
            "PROCEDURAL": 0.8,
            "SHORT_TERM": 0.5
        }
        score += type_weights.get(memory.memory_type, 0.5) * 0.2
        
        # 4. 记忆类别权重 (0.15)
        category_weights = {
            "PREFERENCE": 1.0,
            "KNOWLEDGE": 0.9,
            "CONTEXT": 0.7,
            "CONVERSATION": 0.5
        }
        score += category_weights.get(memory.memory_category, 0.5) * 0.15
        
        # 5. 新鲜度权重 (0.15)
        age_days = (datetime.now() - memory.created_at).days
        if age_days < 1:
            freshness_score = 1.0
        elif age_days < 7:
            freshness_score = 0.8
        elif age_days < 30:
            freshness_score = 0.6
        elif age_days < 90:
            freshness_score = 0.4
        else:
            freshness_score = 0.2
        score += freshness_score * 0.15
        
        # 确保分数在0.0-1.0范围内
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def manage_memory_lifecycle(db: Session, user_id: int) -> Dict[str, int]:
        """管理记忆的生命周期（短期转长期、过期清理等）"""
        result = {
            "promoted_count": 0,
            "archived_count": 0,
            "deleted_count": 0
        }
        
        # 获取用户配置
        config = MemoryService.get_user_memory_config(db, user_id)
        
        # 默认配置
        default_config = {
            "short_term_retention_days": 7,
            "long_term_threshold": 0.7,
            "auto_cleanup_enabled": True
        }
        
        # 合并用户配置和默认配置
        user_config = config.__dict__ if config else default_config
        config_data = {**default_config, **user_config}
        
        # 如果自动清理功能未启用，直接返回
        if not config_data["auto_cleanup_enabled"]:
            return result
        
        # 计算时间阈值
        short_term_retention_days = config_data["short_term_retention_days"]
        long_term_threshold = config_data["long_term_threshold"]
        short_term_threshold_date = datetime.now() - timedelta(days=short_term_retention_days)
        
        # 1. 将重要的短期记忆转换为长期记忆
        short_term_memories = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.memory_type == "SHORT_TERM",
            GlobalMemory.is_active == True,
            GlobalMemory.created_at < short_term_threshold_date
        ).all()
        
        for memory in short_term_memories:
            # 评估记忆的重要性
            importance_score = MemoryService.evaluate_importance(memory, config)
            
            # 更新记忆的重要性分数
            memory.importance_score = importance_score
            
            # 如果重要性分数超过阈值，将短期记忆转换为长期记忆
            if importance_score >= long_term_threshold:
                memory.memory_type = "LONG_TERM"
                result["promoted_count"] += 1
            
            # 更新记忆的访问次数和最后访问时间
            if memory.access_count > 0:
                memory.access_count -= 1  # 降低访问次数的影响
            
            memory.updated_at = datetime.now()
        
        # 2. 清理过期的记忆
        expired_memories = db.query(GlobalMemory).filter(
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True,
            GlobalMemory.expires_at < datetime.now()
        ).all()
        
        for memory in expired_memories:
            memory.is_active = False
            result["archived_count"] += 1
        
        db.commit()
        
        return result
    
    @staticmethod
    async def get_conversation_memories(db: Session, conversation_id: int, user_id: int, limit: int = 20, offset: int = 0) -> List[GlobalMemory]:
        """获取特定对话关联的所有记忆条目，使用缓存优化"""
        return await memory_cache_service.get_conversation_memories(db, conversation_id, user_id, limit, offset)
    
    @staticmethod
    def get_knowledge_memories(db: Session, knowledge_base_id: int, user_id: int, limit: int = 20, offset: int = 0) -> List[GlobalMemory]:
        """获取特定知识库关联的所有记忆条目"""
        # 通过映射表查询知识库相关的记忆
        db_query = db.query(GlobalMemory).join(
            KnowledgeMemoryMapping, KnowledgeMemoryMapping.memory_id == GlobalMemory.id
        ).filter(
            KnowledgeMemoryMapping.knowledge_base_id == knowledge_base_id,
            GlobalMemory.user_id == user_id,
            GlobalMemory.is_active == True
        ).order_by(desc(GlobalMemory.created_at))
        
        return db_query.offset(offset).limit(limit).all()