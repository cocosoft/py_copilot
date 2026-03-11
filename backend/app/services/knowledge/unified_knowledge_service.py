"""
统一知识服务 - 向量化管理模块优化

提供统一知识单元的CRUD操作、关联管理和查询功能。

任务编号: BE-009
阶段: Phase 3 - 一体化建设期
"""

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func

from app.core.database import get_db_pool
from app.modules.knowledge.models.unified_knowledge_unit import (
    UnifiedKnowledgeUnit,
    KnowledgeUnitAssociation,
    ProcessingPipelineRun,
    KnowledgeUnitIndex,
    KnowledgeUnitType,
    KnowledgeUnitStatus,
    AssociationType
)
from app.services.knowledge.transactional_vector_manager import (
    TransactionalVectorManager,
    VectorOperationType
)

logger = logging.getLogger(__name__)


class UnifiedKnowledgeService:
    """
    统一知识服务
    
    提供统一知识单元的完整生命周期管理：
    - CRUD操作
    - 关联管理
    - 版本控制
    - 向量操作
    - 查询检索
    """
    
    def __init__(self):
        """初始化统一知识服务"""
        self.vector_manager = TransactionalVectorManager()
        logger.info("统一知识服务初始化完成")
    
    # ==================== CRUD 操作 ====================
    
    def create_knowledge_unit(
        self,
        db: Session,
        unit_type: KnowledgeUnitType,
        knowledge_base_id: int,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        vector_embedding: Optional[List[float]] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        source_location: Optional[str] = None,
        status: KnowledgeUnitStatus = KnowledgeUnitStatus.PENDING
    ) -> UnifiedKnowledgeUnit:
        """
        创建知识单元
        
        Args:
            db: 数据库会话
            unit_type: 知识单元类型
            knowledge_base_id: 知识库ID
            content: 内容
            metadata: 元数据
            vector_embedding: 向量嵌入
            source_type: 来源类型
            source_id: 来源ID
            source_location: 来源位置
            status: 初始状态
            
        Returns:
            创建的知识单元
        """
        # 计算内容哈希
        content_hash = None
        if content:
            content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # 创建知识单元
        unit = UnifiedKnowledgeUnit(
            unit_type=unit_type,
            status=status,
            knowledge_base_id=knowledge_base_id,
            content=content,
            content_hash=content_hash,
            vector_embedding=vector_embedding,
            vector_dimension=len(vector_embedding) if vector_embedding else None,
            metadata=metadata or {},
            source_type=source_type,
            source_id=source_id,
            source_location=source_location,
            version=1,
            is_current=True
        )
        
        db.add(unit)
        db.flush()
        
        logger.info(f"创建知识单元: id={unit.id}, type={unit_type.value}")
        
        return unit
    
    def get_knowledge_unit(
        self,
        db: Session,
        unit_id: int,
        include_associations: bool = False
    ) -> Optional[UnifiedKnowledgeUnit]:
        """
        获取知识单元
        
        Args:
            db: 数据库会话
            unit_id: 知识单元ID
            include_associations: 是否包含关联
            
        Returns:
            知识单元，如果不存在则返回None
        """
        query = db.query(UnifiedKnowledgeUnit)
        
        if include_associations:
            query = query.options(
                joinedload(UnifiedKnowledgeUnit.outgoing_associations),
                joinedload(UnifiedKnowledgeUnit.incoming_associations)
            )
        
        unit = query.filter(UnifiedKnowledgeUnit.id == unit_id).first()
        
        if unit:
            # 更新访问计数
            unit.access_count += 1
            db.flush()
        
        return unit
    
    def update_knowledge_unit(
        self,
        db: Session,
        unit_id: int,
        updates: Dict[str, Any],
        create_version: bool = True
    ) -> Optional[UnifiedKnowledgeUnit]:
        """
        更新知识单元
        
        Args:
            db: 数据库会话
            unit_id: 知识单元ID
            updates: 更新字段
            create_version: 是否创建新版本
            
        Returns:
            更新后的知识单元
        """
        unit = self.get_knowledge_unit(db, unit_id)
        if not unit:
            return None
        
        if create_version:
            # 创建新版本
            new_unit = self._create_new_version(db, unit, updates)
            return new_unit
        else:
            # 直接更新
            for key, value in updates.items():
                if hasattr(unit, key) and key != 'id':
                    setattr(unit, key, value)
            
            # 更新内容哈希
            if 'content' in updates:
                unit.content_hash = hashlib.md5(updates['content'].encode()).hexdigest()
            
            unit.updated_at = datetime.now()
            db.flush()
            
            logger.info(f"更新知识单元: id={unit_id}")
            return unit
    
    def delete_knowledge_unit(
        self,
        db: Session,
        unit_id: int,
        soft_delete: bool = True
    ) -> bool:
        """
        删除知识单元
        
        Args:
            db: 数据库会话
            unit_id: 知识单元ID
            soft_delete: 是否软删除
            
        Returns:
            是否删除成功
        """
        unit = self.get_knowledge_unit(db, unit_id)
        if not unit:
            return False
        
        if soft_delete:
            unit.status = KnowledgeUnitStatus.DEPRECATED
            unit.is_current = False
            db.flush()
            logger.info(f"软删除知识单元: id={unit_id}")
        else:
            db.delete(unit)
            db.flush()
            logger.info(f"硬删除知识单元: id={unit_id}")
        
        return True
    
    def _create_new_version(
        self,
        db: Session,
        old_unit: UnifiedKnowledgeUnit,
        updates: Dict[str, Any]
    ) -> UnifiedKnowledgeUnit:
        """
        创建新版本的知识单元
        
        Args:
            db: 数据库会话
            old_unit: 旧版本单元
            updates: 更新内容
            
        Returns:
            新版本单元
        """
        # 标记旧版本为非当前
        old_unit.is_current = False
        
        # 创建新版本
        new_unit = UnifiedKnowledgeUnit(
            unit_type=old_unit.unit_type,
            status=KnowledgeUnitStatus.ACTIVE,
            knowledge_base_id=old_unit.knowledge_base_id,
            content=updates.get('content', old_unit.content),
            content_hash=old_unit.content_hash,
            vector_embedding=updates.get('vector_embedding', old_unit.vector_embedding),
            vector_dimension=old_unit.vector_dimension,
            metadata={**old_unit.metadata, **updates.get('metadata', {})},
            source_type=old_unit.source_type,
            source_id=old_unit.source_id,
            source_location=old_unit.source_location,
            version=old_unit.version + 1,
            is_current=True,
            parent_unit_id=old_unit.id
        )
        
        # 更新内容哈希
        if 'content' in updates:
            new_unit.content_hash = hashlib.md5(updates['content'].encode()).hexdigest()
        
        if 'vector_embedding' in updates:
            new_unit.vector_dimension = len(updates['vector_embedding'])
        
        db.add(new_unit)
        db.flush()
        
        # 复制关联关系
        self._copy_associations(db, old_unit.id, new_unit.id)
        
        logger.info(f"创建新版本: old_id={old_unit.id}, new_id={new_unit.id}, version={new_unit.version}")
        
        return new_unit
    
    def _copy_associations(
        self,
        db: Session,
        old_unit_id: int,
        new_unit_id: int
    ):
        """复制关联关系到新版本"""
        # 获取旧单元的关联
        old_associations = db.query(KnowledgeUnitAssociation).filter(
            or_(
                KnowledgeUnitAssociation.source_unit_id == old_unit_id,
                KnowledgeUnitAssociation.target_unit_id == old_unit_id
            )
        ).all()
        
        # 创建新关联
        for assoc in old_associations:
            new_assoc = KnowledgeUnitAssociation(
                association_type=assoc.association_type,
                source_unit_id=new_unit_id if assoc.source_unit_id == old_unit_id else assoc.source_unit_id,
                target_unit_id=new_unit_id if assoc.target_unit_id == old_unit_id else assoc.target_unit_id,
                weight=assoc.weight,
                properties=assoc.properties,
                is_bidirectional=assoc.is_bidirectional
            )
            db.add(new_assoc)
    
    # ==================== 关联管理 ====================
    
    def create_association(
        self,
        db: Session,
        source_unit_id: int,
        target_unit_id: int,
        association_type: AssociationType,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
        is_bidirectional: bool = False
    ) -> KnowledgeUnitAssociation:
        """
        创建关联
        
        Args:
            db: 数据库会话
            source_unit_id: 源单元ID
            target_unit_id: 目标单元ID
            association_type: 关联类型
            weight: 权重
            properties: 属性
            is_bidirectional: 是否双向
            
        Returns:
            创建的关联
        """
        association = KnowledgeUnitAssociation(
            association_type=association_type,
            source_unit_id=source_unit_id,
            target_unit_id=target_unit_id,
            weight=weight,
            properties=properties or {},
            is_bidirectional=is_bidirectional
        )
        
        db.add(association)
        db.flush()
        
        logger.info(f"创建关联: {source_unit_id} -> {target_unit_id}, type={association_type.value}")
        
        # 如果是双向关联，创建反向关联
        if is_bidirectional:
            reverse_assoc = KnowledgeUnitAssociation(
                association_type=association_type,
                source_unit_id=target_unit_id,
                target_unit_id=source_unit_id,
                weight=weight,
                properties=properties or {},
                is_bidirectional=True
            )
            db.add(reverse_assoc)
            db.flush()
        
        return association
    
    def delete_association(
        self,
        db: Session,
        association_id: int
    ) -> bool:
        """
        删除关联
        
        Args:
            db: 数据库会话
            association_id: 关联ID
            
        Returns:
            是否删除成功
        """
        association = db.query(KnowledgeUnitAssociation).filter(
            KnowledgeUnitAssociation.id == association_id
        ).first()
        
        if not association:
            return False
        
        db.delete(association)
        db.flush()
        
        logger.info(f"删除关联: id={association_id}")
        return True
    
    def get_related_units(
        self,
        db: Session,
        unit_id: int,
        association_type: Optional[AssociationType] = None,
        min_weight: float = 0.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取相关的知识单元
        
        Args:
            db: 数据库会话
            unit_id: 知识单元ID
            association_type: 关联类型过滤
            min_weight: 最小权重
            limit: 返回数量限制
            
        Returns:
            相关单元列表
        """
        query = db.query(
            KnowledgeUnitAssociation,
            UnifiedKnowledgeUnit
        ).join(
            UnifiedKnowledgeUnit,
            KnowledgeUnitAssociation.target_unit_id == UnifiedKnowledgeUnit.id
        ).filter(
            KnowledgeUnitAssociation.source_unit_id == unit_id,
            KnowledgeUnitAssociation.weight >= min_weight
        )
        
        if association_type:
            query = query.filter(KnowledgeUnitAssociation.association_type == association_type)
        
        query = query.order_by(desc(KnowledgeUnitAssociation.weight)).limit(limit)
        
        results = []
        for assoc, unit in query.all():
            results.append({
                "association": assoc.to_dict(),
                "unit": unit.to_dict()
            })
        
        return results
    
    # ==================== 查询检索 ====================
    
    def search_knowledge_units(
        self,
        db: Session,
        knowledge_base_id: Optional[int] = None,
        unit_type: Optional[KnowledgeUnitType] = None,
        status: Optional[KnowledgeUnitStatus] = None,
        content_query: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[UnifiedKnowledgeUnit], int]:
        """
        搜索知识单元
        
        Args:
            db: 数据库会话
            knowledge_base_id: 知识库ID过滤
            unit_type: 类型过滤
            status: 状态过滤
            content_query: 内容查询
            metadata_filters: 元数据过滤
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            (知识单元列表, 总数)
        """
        query = db.query(UnifiedKnowledgeUnit)
        
        # 应用过滤条件
        if knowledge_base_id:
            query = query.filter(UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id)
        
        if unit_type:
            query = query.filter(UnifiedKnowledgeUnit.unit_type == unit_type)
        
        if status:
            query = query.filter(UnifiedKnowledgeUnit.status == status)
        else:
            # 默认只查询活跃单元
            query = query.filter(UnifiedKnowledgeUnit.status == KnowledgeUnitStatus.ACTIVE)
        
        if content_query:
            query = query.filter(
                UnifiedKnowledgeUnit.content.contains(content_query)
            )
        
        # 元数据过滤
        if metadata_filters:
            for key, value in metadata_filters.items():
                query = query.filter(
                    UnifiedKnowledgeUnit.metadata.contains({key: value})
                )
        
        # 获取总数
        total = query.count()
        
        # 分页
        units = query.order_by(desc(UnifiedKnowledgeUnit.created_at)).offset(offset).limit(limit).all()
        
        return units, total
    
    def find_by_content_hash(
        self,
        db: Session,
        content_hash: str,
        knowledge_base_id: Optional[int] = None
    ) -> Optional[UnifiedKnowledgeUnit]:
        """
        通过内容哈希查找知识单元（用于去重）
        
        Args:
            db: 数据库会话
            content_hash: 内容哈希
            knowledge_base_id: 知识库ID过滤
            
        Returns:
            知识单元，如果不存在则返回None
        """
        query = db.query(UnifiedKnowledgeUnit).filter(
            UnifiedKnowledgeUnit.content_hash == content_hash
        )
        
        if knowledge_base_id:
            query = query.filter(UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id)
        
        return query.first()
    
    def find_duplicates(
        self,
        db: Session,
        knowledge_base_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        查找重复的知识单元
        
        Args:
            db: 数据库会话
            knowledge_base_id: 知识库ID过滤
            
        Returns:
            重复单元列表
        """
        query = db.query(
            UnifiedKnowledgeUnit.content_hash,
            func.count(UnifiedKnowledgeUnit.id).label('count')
        ).filter(
            UnifiedKnowledgeUnit.content_hash.isnot(None)
        )
        
        if knowledge_base_id:
            query = query.filter(UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id)
        
        query = query.group_by(UnifiedKnowledgeUnit.content_hash).having(
            func.count(UnifiedKnowledgeUnit.id) > 1
        )
        
        duplicates = []
        for content_hash, count in query.all():
            units = db.query(UnifiedKnowledgeUnit).filter(
                UnifiedKnowledgeUnit.content_hash == content_hash
            ).all()
            
            duplicates.append({
                "content_hash": content_hash,
                "count": count,
                "units": [unit.to_dict() for unit in units]
            })
        
        return duplicates
    
    # ==================== 流水线运行记录 ====================
    
    def create_pipeline_run(
        self,
        db: Session,
        knowledge_unit_id: int,
        pipeline_name: str,
        pipeline_version: Optional[str] = None,
        input_data_hash: Optional[str] = None
    ) -> ProcessingPipelineRun:
        """
        创建流水线运行记录
        
        Args:
            db: 数据库会话
            knowledge_unit_id: 知识单元ID
            pipeline_name: 流水线名称
            pipeline_version: 流水线版本
            input_data_hash: 输入数据哈希
            
        Returns:
            运行记录
        """
        run = ProcessingPipelineRun(
            knowledge_unit_id=knowledge_unit_id,
            pipeline_name=pipeline_name,
            pipeline_version=pipeline_version,
            status="pending",
            input_data_hash=input_data_hash,
            started_at=datetime.now()
        )
        
        db.add(run)
        db.flush()
        
        logger.info(f"创建流水线运行记录: id={run.id}, pipeline={pipeline_name}")
        
        return run
    
    def update_pipeline_run_status(
        self,
        db: Session,
        run_id: int,
        status: str,
        current_stage: Optional[str] = None,
        error_message: Optional[str] = None,
        error_stage: Optional[str] = None
    ) -> Optional[ProcessingPipelineRun]:
        """
        更新流水线运行状态
        
        Args:
            db: 数据库会话
            run_id: 运行记录ID
            status: 新状态
            current_stage: 当前阶段
            error_message: 错误信息
            error_stage: 错误阶段
            
        Returns:
            更新后的运行记录
        """
        run = db.query(ProcessingPipelineRun).filter(
            ProcessingPipelineRun.id == run_id
        ).first()
        
        if not run:
            return None
        
        run.status = status
        
        if current_stage:
            run.current_stage = current_stage
            run.mark_stage_complete(current_stage)
        
        if error_message:
            run.error_message = error_message
            run.error_stage = error_stage
        
        if status in ["completed", "failed"]:
            run.completed_at = datetime.now()
            run.calculate_duration()
        
        db.flush()
        
        return run
    
    # ==================== 批量操作 ====================
    
    def batch_create_units(
        self,
        db: Session,
        units_data: List[Dict[str, Any]]
    ) -> Tuple[List[UnifiedKnowledgeUnit], List[Dict[str, Any]]]:
        """
        批量创建知识单元
        
        Args:
            db: 数据库会话
            units_data: 单元数据列表
            
        Returns:
            (成功创建的单元列表, 失败记录列表)
        """
        created_units = []
        failed_records = []
        
        for i, data in enumerate(units_data):
            try:
                unit = self.create_knowledge_unit(
                    db=db,
                    unit_type=data.get('unit_type', KnowledgeUnitType.DOCUMENT),
                    knowledge_base_id=data['knowledge_base_id'],
                    content=data.get('content'),
                    metadata=data.get('metadata'),
                    vector_embedding=data.get('vector_embedding'),
                    source_type=data.get('source_type'),
                    source_id=data.get('source_id'),
                    source_location=data.get('source_location'),
                    status=data.get('status', KnowledgeUnitStatus.PENDING)
                )
                created_units.append(unit)
            except Exception as e:
                logger.error(f"批量创建第 {i} 个单元失败: {e}")
                failed_records.append({"index": i, "error": str(e), "data": data})
        
        return created_units, failed_records
    
    def batch_update_status(
        self,
        db: Session,
        unit_ids: List[int],
        new_status: KnowledgeUnitStatus
    ) -> int:
        """
        批量更新状态
        
        Args:
            db: 数据库会话
            unit_ids: 单元ID列表
            new_status: 新状态
            
        Returns:
            更新的单元数量
        """
        count = db.query(UnifiedKnowledgeUnit).filter(
            UnifiedKnowledgeUnit.id.in_(unit_ids)
        ).update({
            UnifiedKnowledgeUnit.status: new_status,
            UnifiedKnowledgeUnit.updated_at: datetime.now()
        }, synchronize_session=False)
        
        db.flush()
        
        logger.info(f"批量更新状态: {count} 个单元 -> {new_status.value}")
        
        return count
    
    # ==================== 统计信息 ====================
    
    def get_statistics(
        self,
        db: Session,
        knowledge_base_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            db: 数据库会话
            knowledge_base_id: 知识库ID过滤
            
        Returns:
            统计信息字典
        """
        query = db.query(UnifiedKnowledgeUnit)
        
        if knowledge_base_id:
            query = query.filter(UnifiedKnowledgeUnit.knowledge_base_id == knowledge_base_id)
        
        # 总数
        total_count = query.count()
        
        # 按类型统计
        type_counts = {}
        for unit_type in KnowledgeUnitType:
            count = query.filter(UnifiedKnowledgeUnit.unit_type == unit_type).count()
            type_counts[unit_type.value] = count
        
        # 按状态统计
        status_counts = {}
        for status in KnowledgeUnitStatus:
            count = query.filter(UnifiedKnowledgeUnit.status == status).count()
            status_counts[status.value] = count
        
        # 有向量的单元数
        vector_count = query.filter(
            UnifiedKnowledgeUnit.vector_embedding.isnot(None)
        ).count()
        
        return {
            "total_count": total_count,
            "type_counts": type_counts,
            "status_counts": status_counts,
            "vector_count": vector_count,
            "vector_rate": vector_count / total_count if total_count > 0 else 0
        }


# 便捷函数

def create_knowledge_unit(
    unit_type: KnowledgeUnitType,
    knowledge_base_id: int,
    content: Optional[str] = None,
    **kwargs
) -> UnifiedKnowledgeUnit:
    """
    便捷函数：创建知识单元
    
    Args:
        unit_type: 知识单元类型
        knowledge_base_id: 知识库ID
        content: 内容
        **kwargs: 其他参数
        
    Returns:
        创建的知识单元
    """
    db_pool = get_db_pool()
    service = UnifiedKnowledgeService()
    
    with db_pool.get_db_session() as db:
        return service.create_knowledge_unit(
            db=db,
            unit_type=unit_type,
            knowledge_base_id=knowledge_base_id,
            content=content,
            **kwargs
        )


def get_knowledge_unit(unit_id: int, include_associations: bool = False) -> Optional[UnifiedKnowledgeUnit]:
    """
    便捷函数：获取知识单元
    
    Args:
        unit_id: 知识单元ID
        include_associations: 是否包含关联
        
    Returns:
        知识单元
    """
    db_pool = get_db_pool()
    service = UnifiedKnowledgeService()
    
    with db_pool.get_db_session() as db:
        return service.get_knowledge_unit(db, unit_id, include_associations)


def search_knowledge_units(
    knowledge_base_id: Optional[int] = None,
    **filters
) -> Tuple[List[UnifiedKnowledgeUnit], int]:
    """
    便捷函数：搜索知识单元
    
    Args:
        knowledge_base_id: 知识库ID
        **filters: 过滤条件
        
    Returns:
        (知识单元列表, 总数)
    """
    db_pool = get_db_pool()
    service = UnifiedKnowledgeService()
    
    with db_pool.get_db_session() as db:
        return service.search_knowledge_units(db, knowledge_base_id=knowledge_base_id, **filters)


# 全局服务实例
unified_knowledge_service = UnifiedKnowledgeService()
