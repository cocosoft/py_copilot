"""数据库查询优化服务

提供优化的数据库查询方法，包括批量查询、预加载、索引优化等。
"""
import logging
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from sqlalchemy.orm import joinedload, selectinload, Session
from sqlalchemy import text, func, desc, asc
from contextlib import contextmanager
from functools import wraps
import time

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

T = TypeVar('T')


class QueryOptimizer:
    """查询优化器
    
    提供各种查询优化策略，提高数据库查询性能。
    """
    
    @staticmethod
    def batch_query(
        session: Session,
        model_class,
        ids: List[int],
        batch_size: int = 100,
        eager_load: Optional[List] = None
    ) -> List[Any]:
        """批量查询优化
        
        使用IN语句批量查询，减少数据库往返次数。
        
        Args:
            session: 数据库会话
            model_class: 模型类
            ids: ID列表
            batch_size: 批次大小
            eager_load: 预加载的关系
            
        Returns:
            查询结果列表
        """
        if not ids:
            return []
        
        results = []
        
        # 分批查询
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            
            query = session.query(model_class).filter(model_class.id.in_(batch_ids))
            
            # 添加预加载
            if eager_load:
                for relationship in eager_load:
                    query = query.options(selectinload(relationship))
            
            batch_results = query.all()
            results.extend(batch_results)
            
            logger.debug(f"批量查询: {len(batch_ids)} 个ID, 返回 {len(batch_results)} 条记录")
        
        return results
    
    @staticmethod
    def paginated_query(
        session: Session,
        query,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ) -> Dict[str, Any]:
        """分页查询优化
        
        提供高效的分页查询，支持游标分页和偏移分页。
        
        Args:
            session: 数据库会话
            query: 基础查询
            page: 页码（从1开始）
            page_size: 每页大小
            max_page_size: 最大每页大小
            
        Returns:
            包含数据和分页信息的结果
        """
        # 限制每页大小
        page_size = min(page_size, max_page_size)
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取总数
        total = query.count()
        
        # 执行分页查询
        items = query.offset(offset).limit(page_size).all()
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    
    @staticmethod
    def cursor_paginated_query(
        session: Session,
        query,
        cursor: Optional[str] = None,
        page_size: int = 20,
        sort_field: str = 'id',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """游标分页查询
        
        使用游标进行高效分页，适用于大数据量场景。
        
        Args:
            session: 数据库会话
            query: 基础查询
            cursor: 游标（上一页最后一条记录的ID）
            page_size: 每页大小
            sort_field: 排序字段
            sort_order: 排序方向（asc/desc）
            
        Returns:
            包含数据和游标信息的结果
        """
        # 获取模型类
        model_class = query.column_descriptions[0]['type']
        
        # 应用游标过滤
        if cursor:
            cursor_value = int(cursor)
            sort_column = getattr(model_class, sort_field)
            
            if sort_order == 'desc':
                query = query.filter(sort_column < cursor_value)
            else:
                query = query.filter(sort_column > cursor_value)
        
        # 应用排序
        sort_column = getattr(model_class, sort_field)
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # 获取多一条记录用于判断是否有下一页
        items = query.limit(page_size + 1).all()
        
        # 判断是否有下一页
        has_next = len(items) > page_size
        if has_next:
            items = items[:-1]  # 移除多获取的那条记录
        
        # 生成下一页游标
        next_cursor = None
        if has_next and items:
            next_cursor = str(getattr(items[-1], sort_field))
        
        return {
            'items': items,
            'next_cursor': next_cursor,
            'has_next': has_next,
            'page_size': page_size
        }
    
    @staticmethod
    def optimized_count(
        session: Session,
        query,
        use_approximate: bool = False,
        approximate_threshold: int = 100000
    ) -> int:
        """优化的计数查询
        
        对于大数据表，使用近似计数提高性能。
        
        Args:
            session: 数据库会话
            query: 基础查询
            use_approximate: 是否使用近似计数
            approximate_threshold: 使用近似计数的阈值
            
        Returns:
            记录数
        """
        if use_approximate:
            # 获取模型类
            model_class = query.column_descriptions[0]['type']
            table_name = model_class.__tablename__
            
            # 使用PostgreSQL的统计信息获取近似计数
            sql = text(f"""
                SELECT reltuples::BIGINT as estimate
                FROM pg_class
                WHERE relname = :table_name
            """)
            
            result = session.execute(sql, {'table_name': table_name})
            estimate = result.scalar()
            
            if estimate and estimate > approximate_threshold:
                logger.debug(f"使用近似计数: {estimate}")
                return int(estimate)
        
        # 使用精确计数
        return query.count()
    
    @staticmethod
    def bulk_insert(
        session: Session,
        model_class,
        data_list: List[Dict[str, Any]],
        batch_size: int = 1000,
        return_defaults: bool = False
    ) -> List[Any]:
        """批量插入优化
        
        使用批量插入提高性能。
        
        Args:
            session: 数据库会话
            model_class: 模型类
            data_list: 数据列表
            batch_size: 批次大小
            return_defaults: 是否返回默认值
            
        Returns:
            插入的记录列表
        """
        if not data_list:
            return []
        
        results = []
        
        # 分批插入
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            
            # 创建模型实例
            instances = [model_class(**data) for data in batch]
            
            # 批量添加
            session.bulk_save_objects(instances, return_defaults=return_defaults)
            
            results.extend(instances)
            
            logger.debug(f"批量插入: {len(batch)} 条记录")
        
        return results
    
    @staticmethod
    def bulk_update(
        session: Session,
        model_class,
        updates: List[Dict[str, Any]],
        id_field: str = 'id',
        batch_size: int = 1000
    ) -> int:
        """批量更新优化
        
        使用批量更新提高性能。
        
        Args:
            session: 数据库会话
            model_class: 模型类
            updates: 更新数据列表，每项必须包含id_field
            id_field: ID字段名
            batch_size: 批次大小
            
        Returns:
            更新的记录数
        """
        if not updates:
            return 0
        
        total_updated = 0
        
        # 分批更新
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            for update_data in batch:
                record_id = update_data.pop(id_field, None)
                if record_id is None:
                    continue
                
                # 构建更新语句
                session.query(model_class).filter(
                    getattr(model_class, id_field) == record_id
                ).update(update_data, synchronize_session=False)
                
                total_updated += 1
            
            logger.debug(f"批量更新: {len(batch)} 条记录")
        
        return total_updated
    
    @staticmethod
    def select_related(
        session: Session,
        query,
        relationships: List[str],
        strategy: str = 'selectin'
    ):
        """预加载关联数据
        
        使用预加载策略避免N+1查询问题。
        
        Args:
            session: 数据库会话
            query: 基础查询
            relationships: 关系字段名列表
            strategy: 加载策略（joined/selectin/subquery）
            
        Returns:
            优化后的查询
        """
        for relation in relationships:
            if strategy == 'joined':
                query = query.options(joinedload(relation))
            elif strategy == 'selectin':
                query = query.options(selectinload(relation))
            # subquery策略在SQLAlchemy 1.4+中已被弃用
        
        return query


def query_timer(func: Callable) -> Callable:
    """查询计时装饰器
    
    记录查询执行时间，用于性能监控。
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed_time = time.time() - start_time
            if elapsed_time > 1.0:  # 记录慢查询（超过1秒）
                logger.warning(f"慢查询: {func.__name__} 耗时 {elapsed_time:.2f}秒")
            else:
                logger.debug(f"查询: {func.__name__} 耗时 {elapsed_time:.3f}秒")
    
    return wrapper


class QueryCache:
    """查询缓存
    
    提供查询结果缓存功能。
    """
    
    def __init__(self):
        self._cache = {}
        self._ttl = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            if time.time() < self._ttl.get(key, 0):
                return self._cache[key]
            else:
                # 过期，删除缓存
                del self._cache[key]
                del self._ttl[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存值"""
        self._cache[key] = value
        self._ttl[key] = time.time() + ttl
    
    def invalidate(self, key: str):
        """使缓存失效"""
        if key in self._cache:
            del self._cache[key]
            del self._ttl[key]
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._ttl.clear()


# 全局查询缓存实例
query_cache = QueryCache()


# 便捷函数

@query_timer
def get_documents_by_ids(
    document_ids: List[int],
    include_content: bool = False,
    include_knowledge_base: bool = False
) -> List[Any]:
    """根据ID批量获取文档
    
    Args:
        document_ids: 文档ID列表
        include_content: 是否包含内容
        include_knowledge_base: 是否包含知识库信息
        
    Returns:
        文档列表
    """
    from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
    
    with SessionLocal() as session:
        eager_load = []
        
        if include_knowledge_base:
            eager_load.append(KnowledgeDocument.knowledge_base)
        
        return QueryOptimizer.batch_query(
            session,
            KnowledgeDocument,
            document_ids,
            eager_load=eager_load if eager_load else None
        )


@query_timer
def get_entities_by_document_ids(
    document_ids: List[int],
    batch_size: int = 100
) -> Dict[int, List[Any]]:
    """根据文档ID批量获取实体
    
    Args:
        document_ids: 文档ID列表
        batch_size: 批次大小
        
    Returns:
        文档ID到实体列表的映射
    """
    from app.modules.knowledge.models.document_entity import DocumentEntity
    
    results = {}
    
    with SessionLocal() as session:
        for i in range(0, len(document_ids), batch_size):
            batch_ids = document_ids[i:i + batch_size]
            
            entities = session.query(DocumentEntity).filter(
                DocumentEntity.document_id.in_(batch_ids)
            ).all()
            
            for entity in entities:
                if entity.document_id not in results:
                    results[entity.document_id] = []
                results[entity.document_id].append(entity)
    
    return results


@query_timer
def get_knowledge_graph_stats(knowledge_base_id: int) -> Dict[str, int]:
    """获取知识图谱统计信息
    
    Args:
        knowledge_base_id: 知识库ID
        
    Returns:
        统计信息字典
    """
    from app.modules.knowledge.models.knowledge_graph import KnowledgeGraph
    from app.modules.knowledge.models.graph_node import GraphNode
    from app.modules.knowledge.models.graph_edge import GraphEdge
    
    cache_key = f"kg_stats:{knowledge_base_id}"
    cached = query_cache.get(cache_key)
    
    if cached:
        return cached
    
    with SessionLocal() as session:
        # 获取图谱数量
        graph_count = session.query(KnowledgeGraph).filter(
            KnowledgeGraph.knowledge_base_id == knowledge_base_id
        ).count()
        
        # 获取节点数量
        node_count = session.query(GraphNode).filter(
            GraphNode.knowledge_base_id == knowledge_base_id
        ).count()
        
        # 获取边数量
        edge_count = session.query(GraphEdge).filter(
            GraphEdge.knowledge_base_id == knowledge_base_id
        ).count()
        
        stats = {
            'graph_count': graph_count,
            'node_count': node_count,
            'edge_count': edge_count
        }
        
        # 缓存结果（5分钟）
        query_cache.set(cache_key, stats, ttl=300)
        
        return stats


@query_timer
def search_documents_optimized(
    knowledge_base_id: int,
    keyword: str,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """优化的文档搜索
    
    Args:
        knowledge_base_id: 知识库ID
        keyword: 搜索关键词
        page: 页码
        page_size: 每页大小
        status: 文档状态过滤
        
    Returns:
        搜索结果
    """
    from app.modules.knowledge.models.knowledge_document import KnowledgeDocument
    
    with SessionLocal() as session:
        query = session.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id
        )
        
        # 添加关键词过滤
        if keyword:
            query = query.filter(
                KnowledgeDocument.title.ilike(f'%{keyword}%')
            )
        
        # 添加状态过滤
        if status:
            query = query.filter(KnowledgeDocument.status == status)
        
        # 排序
        query = query.order_by(desc(KnowledgeDocument.updated_at))
        
        # 分页
        return QueryOptimizer.paginated_query(
            session,
            query,
            page=page,
            page_size=page_size
        )