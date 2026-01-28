"""
记忆-知识库联动机制

实现记忆系统与知识库系统的协同工作，包括知识提取、记忆增强、双向同步等功能。
"""
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from sqlalchemy.orm import Session

from .memory_models import Memory, MemoryType, MemoryPriority, memory_manager
from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.services.knowledge.retrieval_service import RetrievalService, AdvancedRetrievalService

logger = logging.getLogger(__name__)


class MemoryKnowledgeLinker:
    """记忆-知识库联动器"""
    
    def __init__(self, db_session: Session):
        """初始化联动器
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self.memory_manager = memory_manager
        self.knowledge_service = KnowledgeService()
        self.retrieval_service = RetrievalService()
        self.advanced_retrieval = AdvancedRetrievalService()
    
    def extract_knowledge_from_memory(self, 
                                    memory_id: int, 
                                    knowledge_base_id: Optional[int] = None) -> Dict[str, Any]:
        """从记忆中提取知识
        
        Args:
            memory_id: 记忆ID
            knowledge_base_id: 目标知识库ID（可选）
            
        Returns:
            提取结果
        """
        try:
            # 获取记忆
            memory = self.memory_manager.get_memory(memory_id, self.db)
            if not memory:
                return {"success": False, "error": "记忆不存在"}
            
            # 检查记忆类型是否适合提取知识
            if not self._is_knowledge_extractable(memory):
                return {"success": False, "error": "该记忆类型不适合提取知识"}
            
            # 提取知识内容
            knowledge_content = self._extract_knowledge_content(memory)
            if not knowledge_content:
                return {"success": False, "error": "无法提取有效知识内容"}
            
            # 构建知识文档
            knowledge_doc = self._build_knowledge_document(memory, knowledge_content)
            
            # 如果指定了知识库，保存到知识库
            if knowledge_base_id:
                save_result = self._save_to_knowledge_base(knowledge_doc, knowledge_base_id)
                knowledge_doc.update(save_result)
            
            # 标记记忆为已提取知识
            memory.metadata = memory.metadata or {}
            memory.metadata['knowledge_extracted'] = True
            memory.metadata['knowledge_extraction_time'] = datetime.now().isoformat()
            if knowledge_base_id:
                memory.metadata['target_knowledge_base'] = knowledge_base_id
            
            self.db.commit()
            
            logger.info(f"从记忆 {memory_id} 成功提取知识")
            
            return {
                "success": True,
                "memory_id": memory_id,
                "knowledge_content": knowledge_content,
                "knowledge_document": knowledge_doc,
                "knowledge_base_id": knowledge_base_id
            }
            
        except Exception as e:
            logger.error(f"从记忆提取知识失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _is_knowledge_extractable(self, memory: Memory) -> bool:
        """检查记忆是否适合提取知识
        
        Args:
            memory: 记忆对象
            
        Returns:
            是否适合提取知识
        """
        # 高优先级的记忆更适合提取知识
        if memory.priority in [MemoryPriority.HIGH, MemoryPriority.CRITICAL]:
            return True
        
        # 特定类型的记忆适合提取知识
        extractable_types = [
            MemoryType.FACT,
            MemoryType.KNOWLEDGE,
            MemoryType.PREFERENCE,
            MemoryType.BEHAVIOR
        ]
        
        return memory.memory_type in extractable_types
    
    def _extract_knowledge_content(self, memory: Memory) -> Optional[str]:
        """从记忆中提取知识内容
        
        Args:
            memory: 记忆对象
            
        Returns:
            提取的知识内容
        """
        # 根据记忆类型采用不同的提取策略
        if memory.memory_type == MemoryType.FACT:
            # 事实型记忆：直接使用内容
            return memory.content
        
        elif memory.memory_type == MemoryType.KNOWLEDGE:
            # 知识型记忆：使用内容和摘要
            return f"{memory.content}\n\n{memory.summary}"
        
        elif memory.memory_type == MemoryType.PREFERENCE:
            # 偏好型记忆：结构化提取
            return f"偏好信息: {memory.content}\n上下文: {memory.summary}"
        
        elif memory.memory_type == MemoryType.BEHAVIOR:
            # 行为型记忆：提取行为模式
            return f"行为模式: {memory.content}\n触发条件: {memory.summary}"
        
        else:
            # 其他类型：使用通用提取
            return memory.content
    
    def _build_knowledge_document(self, memory: Memory, content: str) -> Dict[str, Any]:
        """构建知识文档
        
        Args:
            memory: 记忆对象
            content: 知识内容
            
        Returns:
            知识文档
        """
        return {
            "title": f"记忆知识 - {memory.memory_type.value} - {memory.created_at.strftime('%Y-%m-%d')}",
            "content": content,
            "source_type": "memory",
            "source_id": memory.id,
            "memory_type": memory.memory_type.value,
            "priority": memory.priority.value,
            "created_at": memory.created_at.isoformat(),
            "tags": ["记忆提取", memory.memory_type.value],
            "metadata": {
                "memory_priority": memory.priority.value,
                "memory_access_count": memory.access_count,
                "memory_relevance_score": memory.calculate_relevance_score()
            }
        }
    
    def _save_to_knowledge_base(self, knowledge_doc: Dict[str, Any], knowledge_base_id: int) -> Dict[str, Any]:
        """保存到知识库
        
        Args:
            knowledge_doc: 知识文档
            knowledge_base_id: 知识库ID
            
        Returns:
            保存结果
        """
        try:
            # 这里应该调用知识库服务的API来保存文档
            # 由于知识库服务已存在，这里简化实现
            
            # 模拟保存到知识库
            doc_id = f"memory_{knowledge_doc['source_id']}_{datetime.now().timestamp()}"
            
            # 添加到向量索引
            self.retrieval_service.add_document_to_index(
                document_id=doc_id,
                text=knowledge_doc['content'],
                metadata={
                    "title": knowledge_doc['title'],
                    "source_type": knowledge_doc['source_type'],
                    "source_id": knowledge_doc['source_id'],
                    "knowledge_base_id": knowledge_base_id,
                    "memory_type": knowledge_doc['memory_type'],
                    "created_at": knowledge_doc['created_at']
                }
            )
            
            return {
                "saved": True,
                "document_id": doc_id,
                "knowledge_base_id": knowledge_base_id
            }
            
        except Exception as e:
            logger.error(f"保存到知识库失败: {e}")
            return {"saved": False, "error": str(e)}
    
    def enhance_memory_with_knowledge(self, 
                                     memory_id: int, 
                                     query: Optional[str] = None,
                                     knowledge_base_id: Optional[int] = None,
                                     limit: int = 3) -> Dict[str, Any]:
        """使用知识库增强记忆
        
        Args:
            memory_id: 记忆ID
            query: 搜索查询（可选，默认使用记忆内容）
            knowledge_base_id: 知识库ID（可选）
            limit: 返回结果数量限制
            
        Returns:
            增强结果
        """
        try:
            # 获取记忆
            memory = self.memory_manager.get_memory(memory_id, self.db)
            if not memory:
                return {"success": False, "error": "记忆不存在"}
            
            # 构建搜索查询
            search_query = query or memory.content
            
            # 搜索相关知识
            if knowledge_base_id:
                knowledge_results = self.retrieval_service.search_documents(
                    query=search_query,
                    limit=limit,
                    knowledge_base_id=knowledge_base_id
                )
            else:
                knowledge_results = self.retrieval_service.search_documents(
                    query=search_query,
                    limit=limit
                )
            
            # 过滤相关结果
            relevant_results = self._filter_relevant_knowledge(knowledge_results, memory)
            
            # 构建增强内容
            enhanced_content = self._build_enhanced_memory(memory, relevant_results)
            
            # 更新记忆元数据
            memory.metadata = memory.metadata or {}
            memory.metadata['knowledge_enhanced'] = True
            memory.metadata['knowledge_enhancement_time'] = datetime.now().isoformat()
            memory.metadata['relevant_knowledge_count'] = len(relevant_results)
            
            self.db.commit()
            
            logger.info(f"记忆 {memory_id} 已使用知识库增强，相关结果数: {len(relevant_results)}")
            
            return {
                "success": True,
                "memory_id": memory_id,
                "original_content": memory.content,
                "enhanced_content": enhanced_content,
                "relevant_knowledge": relevant_results,
                "enhancement_count": len(relevant_results)
            }
            
        except Exception as e:
            logger.error(f"记忆增强失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _filter_relevant_knowledge(self, 
                                 knowledge_results: List[Dict[str, Any]], 
                                 memory: Memory) -> List[Dict[str, Any]]:
        """过滤相关知识结果
        
        Args:
            knowledge_results: 知识结果列表
            memory: 记忆对象
            
        Returns:
            相关结果列表
        """
        if not knowledge_results:
            return []
        
        relevant_results = []
        
        for result in knowledge_results:
            # 计算相关性分数
            relevance_score = self._calculate_knowledge_relevance(result, memory)
            
            if relevance_score > 0.3:  # 相关性阈值
                result['relevance_to_memory'] = relevance_score
                relevant_results.append(result)
        
        # 按相关性排序
        relevant_results.sort(key=lambda x: x.get('relevance_to_memory', 0), reverse=True)
        
        return relevant_results
    
    def _calculate_knowledge_relevance(self, 
                                     knowledge: Dict[str, Any], 
                                     memory: Memory) -> float:
        """计算知识与记忆的相关性
        
        Args:
            knowledge: 知识文档
            memory: 记忆对象
            
        Returns:
            相关性分数（0-1）
        """
        # 基础分数基于向量检索分数
        base_score = knowledge.get('score', 0.0)
        
        # 类型匹配分数
        knowledge_type = knowledge.get('metadata', {}).get('memory_type')
        if knowledge_type and knowledge_type == memory.memory_type.value:
            type_score = 0.3
        else:
            type_score = 0.0
        
        # 时间接近性分数（简化实现）
        time_score = 0.1  # 基础时间分数
        
        return min(1.0, base_score + type_score + time_score)
    
    def _build_enhanced_memory(self, 
                             memory: Memory, 
                             relevant_knowledge: List[Dict[str, Any]]) -> str:
        """构建增强的记忆内容
        
        Args:
            memory: 原始记忆
            relevant_knowledge: 相关知识列表
            
        Returns:
            增强后的记忆内容
        """
        if not relevant_knowledge:
            return memory.content
        
        enhanced_parts = [memory.content]
        
        # 添加相关知识引用
        enhanced_parts.append("\n\n--- 相关知识增强 ---\n")
        
        for i, knowledge in enumerate(relevant_knowledge[:3], 1):  # 最多使用3个知识
            title = knowledge.get('title', '无标题')
            content_snippet = knowledge.get('content', '')[:100]  # 限制长度
            relevance = knowledge.get('relevance_to_memory', 0)
            
            enhanced_parts.append(f"{i}. [{title}] (相关性: {relevance:.2f})\n")
            enhanced_parts.append(f"   {content_snippet}...\n\n")
        
        return "".join(enhanced_parts)
    
    def sync_memory_knowledge(self, 
                            memory_id: int, 
                            knowledge_base_id: int) -> Dict[str, Any]:
        """同步记忆与知识库
        
        Args:
            memory_id: 记忆ID
            knowledge_base_id: 知识库ID
            
        Returns:
            同步结果
        """
        try:
            # 获取记忆
            memory = self.memory_manager.get_memory(memory_id, self.db)
            if not memory:
                return {"success": False, "error": "记忆不存在"}
            
            # 检查是否已经同步
            if memory.metadata and memory.metadata.get('knowledge_synced'):
                return {"success": False, "error": "记忆已同步"}
            
            # 执行知识提取
            extraction_result = self.extract_knowledge_from_memory(
                memory_id=memory_id,
                knowledge_base_id=knowledge_base_id
            )
            
            if not extraction_result.get('success'):
                return extraction_result
            
            # 执行记忆增强
            enhancement_result = self.enhance_memory_with_knowledge(
                memory_id=memory_id,
                knowledge_base_id=knowledge_base_id
            )
            
            # 标记为已同步
            memory.metadata = memory.metadata or {}
            memory.metadata['knowledge_synced'] = True
            memory.metadata['sync_time'] = datetime.now().isoformat()
            memory.metadata['target_knowledge_base'] = knowledge_base_id
            
            self.db.commit()
            
            logger.info(f"记忆 {memory_id} 与知识库 {knowledge_base_id} 同步完成")
            
            return {
                "success": True,
                "memory_id": memory_id,
                "knowledge_base_id": knowledge_base_id,
                "extraction_result": extraction_result,
                "enhancement_result": enhancement_result,
                "sync_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"记忆-知识库同步失败: {e}")
            return {"success": False, "error": str(e)}


class MemoryKnowledgeWorkflow:
    """记忆-知识库工作流"""
    
    def __init__(self, db_session: Session):
        """初始化工作流
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self.linker = MemoryKnowledgeLinker(db_session)
    
    def auto_extract_high_value_memories(self, 
                                       knowledge_base_id: int,
                                       priority_threshold: MemoryPriority = MemoryPriority.HIGH,
                                       batch_size: int = 10) -> Dict[str, Any]:
        """自动提取高价值记忆到知识库
        
        Args:
            knowledge_base_id: 目标知识库ID
            priority_threshold: 优先级阈值
            batch_size: 批量处理大小
            
        Returns:
            提取结果
        """
        try:
            # 获取高价值记忆
            high_value_memories = self._get_high_value_memories(
                priority_threshold=priority_threshold,
                limit=batch_size
            )
            
            extraction_results = []
            
            for memory in high_value_memories:
                result = self.linker.extract_knowledge_from_memory(
                    memory_id=memory.id,
                    knowledge_base_id=knowledge_base_id
                )
                
                extraction_results.append({
                    "memory_id": memory.id,
                    "success": result.get('success', False),
                    "error": result.get('error')
                })
            
            success_count = sum(1 for r in extraction_results if r['success'])
            
            logger.info(f"自动提取完成，成功: {success_count}/{len(extraction_results)}")
            
            return {
                "success": True,
                "total_memories": len(extraction_results),
                "successful_extractions": success_count,
                "results": extraction_results
            }
            
        except Exception as e:
            logger.error(f"自动提取高价值记忆失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_high_value_memories(self, 
                               priority_threshold: MemoryPriority,
                               limit: int = 10) -> List[Memory]:
        """获取高价值记忆
        
        Args:
            priority_threshold: 优先级阈值
            limit: 限制数量
            
        Returns:
            高价值记忆列表
        """
        # 获取满足优先级阈值的记忆
        memories = self.db.query(Memory).filter(
            Memory.priority >= priority_threshold.value
        ).limit(limit).all()
        
        # 按相关性分数排序
        memories_with_score = []
        for memory in memories:
            relevance_score = memory.calculate_relevance_score()
            memories_with_score.append((memory, relevance_score))
        
        # 按相关性排序
        memories_with_score.sort(key=lambda x: x[1], reverse=True)
        
        return [memory for memory, score in memories_with_score[:limit]]