"""
统一处理流水线 - 向量化管理模块优化

实现文档处理的统一流水线，包含7个处理阶段。

任务编号: BE-010
阶段: Phase 3 - 一体化建设期
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import traceback

from sqlalchemy.orm import Session

from app.core.database import get_db_pool
from app.modules.knowledge.models.unified_knowledge_unit import (
    UnifiedKnowledgeUnit,
    ProcessingPipelineRun,
    KnowledgeUnitType,
    KnowledgeUnitStatus
)
from app.services.knowledge.unified_knowledge_service import UnifiedKnowledgeService
from app.services.knowledge.transactional_vector_manager import (
    TransactionalVectorManager,
    VectorOperationType
)

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """流水线处理阶段"""
    DOCUMENT_PARSE = "document_parse"           # 文档解析
    TEXT_CLEAN = "text_clean"                   # 文本清理
    SEMANTIC_CHUNK = "semantic_chunk"           # 语义分块
    ENTITY_EXTRACT = "entity_extract"           # 实体识别
    RELATION_EXTRACT = "relation_extract"       # 关系提取
    VECTORIZE = "vectorize"                     # 向量化
    KNOWLEDGE_GRAPH = "knowledge_graph"         # 知识图谱构建


class PipelineStatus(Enum):
    """流水线状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


@dataclass
class StageResult:
    """阶段处理结果"""
    stage: PipelineStage
    success: bool
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    
    @property
    def is_success(self) -> bool:
        return self.success and self.error_message is None


@dataclass
class PipelineContext:
    """流水线上下文"""
    document_id: str
    knowledge_base_id: int
    file_path: str
    file_type: str
    
    # 阶段间共享数据
    shared_data: Dict[str, Any] = field(default_factory=dict)
    
    # 阶段结果
    stage_results: Dict[PipelineStage, StageResult] = field(default_factory=dict)
    
    # 当前状态
    current_stage: Optional[PipelineStage] = None
    status: PipelineStatus = PipelineStatus.PENDING
    
    # 错误信息
    error_message: Optional[str] = None
    failed_stage: Optional[PipelineStage] = None
    
    def set_data(self, key: str, value: Any):
        """设置共享数据"""
        self.shared_data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取共享数据"""
        return self.shared_data.get(key, default)
    
    def add_stage_result(self, result: StageResult):
        """添加阶段结果"""
        self.stage_results[result.stage] = result
    
    def get_stage_result(self, stage: PipelineStage) -> Optional[StageResult]:
        """获取阶段结果"""
        return self.stage_results.get(stage)
    
    def is_stage_completed(self, stage: PipelineStage) -> bool:
        """检查阶段是否完成"""
        result = self.get_stage_result(stage)
        return result is not None and result.is_success
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document_id": self.document_id,
            "knowledge_base_id": self.knowledge_base_id,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "status": self.status.value,
            "shared_data_keys": list(self.shared_data.keys()),
            "completed_stages": [s.value for s in self.stage_results.keys()],
            "error_message": self.error_message,
            "failed_stage": self.failed_stage.value if self.failed_stage else None
        }


class PipelineStageHandler(ABC):
    """流水线阶段处理器基类"""
    
    def __init__(self, stage: PipelineStage):
        self.stage = stage
        self.logger = logging.getLogger(f"{__name__}.{stage.value}")
    
    @abstractmethod
    async def process(self, context: PipelineContext) -> StageResult:
        """
        处理阶段
        
        Args:
            context: 流水线上下文
            
        Returns:
            阶段处理结果
        """
        pass
    
    @abstractmethod
    async def rollback(self, context: PipelineContext, stage_result: StageResult) -> bool:
        """
        回滚阶段
        
        Args:
            context: 流水线上下文
            stage_result: 阶段结果
            
        Returns:
            是否回滚成功
        """
        pass


class DocumentParseHandler(PipelineStageHandler):
    """文档解析处理器"""
    
    def __init__(self):
        super().__init__(PipelineStage.DOCUMENT_PARSE)
        from app.services.knowledge.core.document_parser import DocumentParser
        self.parser = DocumentParser()
    
    async def process(self, context: PipelineContext) -> StageResult:
        """解析文档"""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"解析文档: {context.file_path}")
            
            # 解析文档
            raw_text = self.parser.parse_document(context.file_path)
            
            if not raw_text:
                raise ValueError(f"无法解析文档: {context.file_path}")
            
            # 保存到上下文
            context.set_data("raw_text", raw_text)
            context.set_data("text_length", len(raw_text))
            
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds() * 1000)
            
            self.logger.info(f"文档解析完成: {len(raw_text)} 字符")
            
            return StageResult(
                stage=self.stage,
                success=True,
                output_data={"text_length": len(raw_text)},
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration
            )
            
        except Exception as e:
            self.logger.error(f"文档解析失败: {e}")
            return StageResult(
                stage=self.stage,
                success=False,
                error_message=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )
    
    async def rollback(self, context: PipelineContext, stage_result: StageResult) -> bool:
        """回滚文档解析"""
        # 文档解析阶段无需回滚
        return True


class TextCleanHandler(PipelineStageHandler):
    """文本清理处理器"""
    
    def __init__(self):
        super().__init__(PipelineStage.TEXT_CLEAN)
        from app.services.knowledge.core.advanced_text_processor import AdvancedTextProcessor
        self.text_processor = AdvancedTextProcessor()
    
    async def process(self, context: PipelineContext) -> StageResult:
        """清理文本"""
        start_time = datetime.now()
        
        try:
            raw_text = context.get_data("raw_text")
            if not raw_text:
                raise ValueError("没有原始文本可供清理")
            
            self.logger.info(f"清理文本: {len(raw_text)} 字符")
            
            # 清理文本
            cleaned_text = self.text_processor.clean_text(raw_text)
            
            # 保存到上下文
            context.set_data("cleaned_text", cleaned_text)
            context.set_data("cleaned_length", len(cleaned_text))
            
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds() * 1000)
            
            self.logger.info(f"文本清理完成: {len(cleaned_text)} 字符")
            
            return StageResult(
                stage=self.stage,
                success=True,
                output_data={
                    "original_length": len(raw_text),
                    "cleaned_length": len(cleaned_text)
                },
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration
            )
            
        except Exception as e:
            self.logger.error(f"文本清理失败: {e}")
            return StageResult(
                stage=self.stage,
                success=False,
                error_message=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )
    
    async def rollback(self, context: PipelineContext, stage_result: StageResult) -> bool:
        """回滚文本清理"""
        context.shared_data.pop("cleaned_text", None)
        context.shared_data.pop("cleaned_length", None)
        return True


class SemanticChunkHandler(PipelineStageHandler):
    """语义分块处理器"""
    
    def __init__(self):
        super().__init__(PipelineStage.SEMANTIC_CHUNK)
        from app.services.knowledge.core.advanced_text_processor import AdvancedTextProcessor
        self.text_processor = AdvancedTextProcessor()
    
    async def process(self, context: PipelineContext) -> StageResult:
        """语义分块"""
        start_time = datetime.now()
        
        try:
            cleaned_text = context.get_data("cleaned_text")
            if not cleaned_text:
                raise ValueError("没有清理后的文本可供分块")
            
            self.logger.info(f"语义分块: {len(cleaned_text)} 字符")
            
            # 语义分块（同步方法转异步）
            loop = asyncio.get_event_loop()
            chunks = await loop.run_in_executor(
                None,
                self.text_processor.semantic_chunking_sync,
                cleaned_text
            )
            
            # 保存到上下文
            context.set_data("chunks", chunks)
            context.set_data("chunk_count", len(chunks))
            
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds() * 1000)
            
            self.logger.info(f"语义分块完成: {len(chunks)} 个块")
            
            return StageResult(
                stage=self.stage,
                success=True,
                output_data={"chunk_count": len(chunks)},
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration
            )
            
        except Exception as e:
            self.logger.error(f"语义分块失败: {e}")
            return StageResult(
                stage=self.stage,
                success=False,
                error_message=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )
    
    async def rollback(self, context: PipelineContext, stage_result: StageResult) -> bool:
        """回滚语义分块"""
        context.shared_data.pop("chunks", None)
        context.shared_data.pop("chunk_count", None)
        return True


class EntityExtractHandler(PipelineStageHandler):
    """实体识别处理器"""
    
    def __init__(self):
        super().__init__(PipelineStage.ENTITY_EXTRACT)
        from app.services.knowledge.core.advanced_text_processor import AdvancedTextProcessor
        self.text_processor = AdvancedTextProcessor()
    
    async def process(self, context: PipelineContext) -> StageResult:
        """识别实体"""
        start_time = datetime.now()
        
        try:
            cleaned_text = context.get_data("cleaned_text")
            if not cleaned_text:
                raise ValueError("没有清理后的文本可供处理")
            
            self.logger.info(f"实体识别: {len(cleaned_text)} 字符")
            
            # 实体识别（同步方法转异步）
            loop = asyncio.get_event_loop()
            entities, _ = await loop.run_in_executor(
                None,
                self.text_processor.extract_entities_relationships_sync,
                cleaned_text
            )
            
            # 保存到上下文
            context.set_data("entities", entities)
            context.set_data("entity_count", len(entities))
            
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds() * 1000)
            
            self.logger.info(f"实体识别完成: {len(entities)} 个实体")
            
            return StageResult(
                stage=self.stage,
                success=True,
                output_data={"entity_count": len(entities)},
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration
            )
            
        except Exception as e:
            self.logger.error(f"实体识别失败: {e}")
            return StageResult(
                stage=self.stage,
                success=False,
                error_message=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )
    
    async def rollback(self, context: PipelineContext, stage_result: StageResult) -> bool:
        """回滚实体识别"""
        context.shared_data.pop("entities", None)
        context.shared_data.pop("entity_count", None)
        return True


class RelationExtractHandler(PipelineStageHandler):
    """关系提取处理器"""
    
    def __init__(self):
        super().__init__(PipelineStage.RELATION_EXTRACT)
        from app.services.knowledge.core.advanced_text_processor import AdvancedTextProcessor
        self.text_processor = AdvancedTextProcessor()
    
    async def process(self, context: PipelineContext) -> StageResult:
        """提取关系"""
        start_time = datetime.now()
        
        try:
            cleaned_text = context.get_data("cleaned_text")
            entities = context.get_data("entities", [])
            
            if not cleaned_text:
                raise ValueError("没有清理后的文本可供处理")
            
            self.logger.info(f"关系提取: {len(entities)} 个实体")
            
            # 关系提取（同步方法转异步）
            loop = asyncio.get_event_loop()
            _, relationships = await loop.run_in_executor(
                None,
                self.text_processor.extract_entities_relationships_sync,
                cleaned_text
            )
            
            # 保存到上下文
            context.set_data("relationships", relationships)
            context.set_data("relationship_count", len(relationships))
            
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds() * 1000)
            
            self.logger.info(f"关系提取完成: {len(relationships)} 个关系")
            
            return StageResult(
                stage=self.stage,
                success=True,
                output_data={"relationship_count": len(relationships)},
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration
            )
            
        except Exception as e:
            self.logger.error(f"关系提取失败: {e}")
            return StageResult(
                stage=self.stage,
                success=False,
                error_message=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )
    
    async def rollback(self, context: PipelineContext, stage_result: StageResult) -> bool:
        """回滚关系提取"""
        context.shared_data.pop("relationships", None)
        context.shared_data.pop("relationship_count", None)
        return True


class VectorizeHandler(PipelineStageHandler):
    """向量化处理器"""
    
    def __init__(self):
        super().__init__(PipelineStage.VECTORIZE)
        from app.services.knowledge.vectorization.chroma_service import ChromaService
        self.chroma_service = ChromaService()
        self.vector_manager = TransactionalVectorManager()
    
    async def process(self, context: PipelineContext) -> StageResult:
        """向量化处理"""
        start_time = datetime.now()
        
        try:
            chunks = context.get_data("chunks", [])
            if not chunks:
                raise ValueError("没有文本块可供向量化")
            
            self.logger.info(f"向量化处理: {len(chunks)} 个块")
            
            # 准备文档数据
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{context.document_id}_chunk_{i}"
                metadata = {
                    "document_id": context.document_id,
                    "knowledge_base_id": context.knowledge_base_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                documents.append({
                    "document_id": chunk_id,
                    "text": chunk,
                    "metadata": metadata
                })
            
            # 使用事务性向量管理器
            success_count = 0
            failed_chunks = []
            
            with self.vector_manager.transaction() as txn:
                for doc in documents:
                    txn.add_operation(
                        operation_type=VectorOperationType.ADD,
                        document_id=doc["document_id"],
                        data={"text": doc["text"], "metadata": doc["metadata"]}
                    )
                
                # 提交向量事务
                txn_success = await txn.commit()
                
                if txn_success:
                    success_count = len(documents)
                else:
                    failed_chunks = [doc["document_id"] for doc in documents]
            
            # 保存到上下文
            context.set_data("vectorized_count", success_count)
            context.set_data("failed_vectors", failed_chunks)
            
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds() * 1000)
            
            success_rate = success_count / len(chunks) if chunks else 0
            self.logger.info(f"向量化完成: {success_count}/{len(chunks)} ({success_rate:.1%})")
            
            return StageResult(
                stage=self.stage,
                success=success_rate > 0.8,  # 成功率>80%算成功
                output_data={
                    "total_chunks": len(chunks),
                    "success_count": success_count,
                    "failed_count": len(failed_chunks),
                    "success_rate": success_rate
                },
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration
            )
            
        except Exception as e:
            self.logger.error(f"向量化失败: {e}")
            return StageResult(
                stage=self.stage,
                success=False,
                error_message=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )
    
    async def rollback(self, context: PipelineContext, stage_result: StageResult) -> bool:
        """回滚向量化"""
        try:
            chunks = context.get_data("chunks", [])
            for i in range(len(chunks)):
                chunk_id = f"{context.document_id}_chunk_{i}"
                self.chroma_service.delete_documents([chunk_id])
            
            context.shared_data.pop("vectorized_count", None)
            context.shared_data.pop("failed_vectors", None)
            return True
        except Exception as e:
            self.logger.error(f"回滚向量化失败: {e}")
            return False


class KnowledgeGraphHandler(PipelineStageHandler):
    """知识图谱构建处理器"""
    
    def __init__(self):
        super().__init__(PipelineStage.KNOWLEDGE_GRAPH)
        from app.services.knowledge.graph.knowledge_graph_service import KnowledgeGraphService
        self.kg_service = KnowledgeGraphService()
    
    async def process(self, context: PipelineContext) -> StageResult:
        """构建知识图谱"""
        start_time = datetime.now()
        
        try:
            entities = context.get_data("entities", [])
            relationships = context.get_data("relationships", [])
            
            if not entities:
                self.logger.warning("没有实体，跳过知识图谱构建")
                return StageResult(
                    stage=self.stage,
                    success=True,
                    output_data={"entity_count": 0, "relationship_count": 0},
                    start_time=start_time,
                    end_time=datetime.now(),
                    duration_ms=0
                )
            
            self.logger.info(f"构建知识图谱: {len(entities)} 个实体, {len(relationships)} 个关系")
            
            # 构建知识图谱
            # 这里简化处理，实际应该调用知识图谱服务
            kg_data = {
                "entities": entities,
                "relationships": relationships,
                "document_id": context.document_id
            }
            
            # 保存到上下文
            context.set_data("knowledge_graph", kg_data)
            
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds() * 1000)
            
            self.logger.info(f"知识图谱构建完成")
            
            return StageResult(
                stage=self.stage,
                success=True,
                output_data={
                    "entity_count": len(entities),
                    "relationship_count": len(relationships)
                },
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration
            )
            
        except Exception as e:
            self.logger.error(f"知识图谱构建失败: {e}")
            return StageResult(
                stage=self.stage,
                success=False,
                error_message=str(e),
                start_time=start_time,
                end_time=datetime.now()
            )
    
    async def rollback(self, context: PipelineContext, stage_result: StageResult) -> bool:
        """回滚知识图谱构建"""
        context.shared_data.pop("knowledge_graph", None)
        return True


class UnifiedProcessingPipeline:
    """
    统一处理流水线
    
    实现文档处理的7个阶段：
    1. 文档解析 (DOCUMENT_PARSE)
    2. 文本清理 (TEXT_CLEAN)
    3. 语义分块 (SEMANTIC_CHUNK)
    4. 实体识别 (ENTITY_EXTRACT)
    5. 关系提取 (RELATION_EXTRACT)
    6. 向量化 (VECTORIZE)
    7. 知识图谱构建 (KNOWLEDGE_GRAPH)
    
    特性：
    - 阶段间数据共享
    - 事务管理
    - 失败回滚
    - 进度追踪
    """
    
    # 默认阶段顺序
    DEFAULT_STAGES = [
        PipelineStage.DOCUMENT_PARSE,
        PipelineStage.TEXT_CLEAN,
        PipelineStage.SEMANTIC_CHUNK,
        PipelineStage.ENTITY_EXTRACT,
        PipelineStage.RELATION_EXTRACT,
        PipelineStage.VECTORIZE,
        PipelineStage.KNOWLEDGE_GRAPH
    ]
    
    def __init__(
        self,
        stages: Optional[List[PipelineStage]] = None,
        enable_rollback: bool = True,
        stop_on_error: bool = True
    ):
        """
        初始化统一处理流水线
        
        Args:
            stages: 阶段列表，默认使用全部7个阶段
            enable_rollback: 是否启用回滚
            stop_on_error: 出错时是否停止
        """
        self.stages = stages or self.DEFAULT_STAGES.copy()
        self.enable_rollback = enable_rollback
        self.stop_on_error = stop_on_error
        
        # 初始化阶段处理器
        self.handlers: Dict[PipelineStage, PipelineStageHandler] = {
            PipelineStage.DOCUMENT_PARSE: DocumentParseHandler(),
            PipelineStage.TEXT_CLEAN: TextCleanHandler(),
            PipelineStage.SEMANTIC_CHUNK: SemanticChunkHandler(),
            PipelineStage.ENTITY_EXTRACT: EntityExtractHandler(),
            PipelineStage.RELATION_EXTRACT: RelationExtractHandler(),
            PipelineStage.VECTORIZE: VectorizeHandler(),
            PipelineStage.KNOWLEDGE_GRAPH: KnowledgeGraphHandler()
        }
        
        # 知识服务
        self.knowledge_service = UnifiedKnowledgeService()
        
        # 进度回调
        self.progress_callbacks: List[Callable[[str, int, str, str, Dict], None]] = []
        
        logger.info(f"统一处理流水线初始化完成: {len(self.stages)} 个阶段")
    
    def register_progress_callback(
        self,
        callback: Callable[[str, int, str, str, Dict], None]
    ):
        """
        注册进度回调函数
        
        Args:
            callback: 回调函数，参数为 (document_id, progress, stage, message, metadata)
        """
        self.progress_callbacks.append(callback)
    
    def _notify_progress(
        self,
        document_id: str,
        progress: int,
        stage: str,
        message: str,
        metadata: Dict[str, Any] = None
    ):
        """通知进度更新"""
        for callback in self.progress_callbacks:
            try:
                callback(document_id, progress, stage, message, metadata or {})
            except Exception as e:
                logger.error(f"进度回调失败: {e}")
    
    async def process(
        self,
        document_id: str,
        knowledge_base_id: int,
        file_path: str,
        file_type: str
    ) -> PipelineContext:
        """
        执行流水线处理
        
        Args:
            document_id: 文档ID
            knowledge_base_id: 知识库ID
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            流水线上下文
        """
        # 创建上下文
        context = PipelineContext(
            document_id=document_id,
            knowledge_base_id=knowledge_base_id,
            file_path=file_path,
            file_type=file_type
        )
        
        context.status = PipelineStatus.RUNNING
        
        # 创建流水线运行记录
        db_pool = get_db_pool()
        run_id = None
        
        with db_pool.get_db_session() as db:
            run = self.knowledge_service.create_pipeline_run(
                db=db,
                knowledge_unit_id=int(document_id) if document_id.isdigit() else 0,
                pipeline_name="unified_processing",
                pipeline_version="1.0.0"
            )
            run_id = run.id
        
        # 执行各阶段
        total_stages = len(self.stages)
        
        try:
            for i, stage in enumerate(self.stages):
                progress = int((i / total_stages) * 100)
                context.current_stage = stage
                
                # 通知进度
                self._notify_progress(
                    document_id,
                    progress,
                    stage.value,
                    f"开始处理阶段: {stage.value}",
                    {"stage_index": i, "total_stages": total_stages}
                )
                
                # 更新运行记录
                if run_id:
                    with db_pool.get_db_session() as db:
                        self.knowledge_service.update_pipeline_run_status(
                            db=db,
                            run_id=run_id,
                            status="running",
                            current_stage=stage.value
                        )
                
                # 获取处理器
                handler = self.handlers.get(stage)
                if not handler:
                    raise ValueError(f"未找到阶段处理器: {stage}")
                
                # 执行阶段
                result = await handler.process(context)
                context.add_stage_result(result)
                
                if not result.is_success:
                    # 阶段失败
                    context.status = PipelineStatus.FAILED
                    context.error_message = result.error_message
                    context.failed_stage = stage
                    
                    logger.error(f"阶段 {stage.value} 失败: {result.error_message}")
                    
                    # 更新运行记录
                    if run_id:
                        with db_pool.get_db_session() as db:
                            self.knowledge_service.update_pipeline_run_status(
                                db=db,
                                run_id=run_id,
                                status="failed",
                                error_message=result.error_message,
                                error_stage=stage.value
                            )
                    
                    # 回滚
                    if self.enable_rollback:
                        await self.rollback(context)
                    
                    if self.stop_on_error:
                        break
                else:
                    # 阶段成功
                    logger.info(f"阶段 {stage.value} 完成: {result.duration_ms}ms")
            
            # 检查是否全部成功
            if context.status != PipelineStatus.FAILED:
                context.status = PipelineStatus.COMPLETED
                
                # 更新运行记录
                if run_id:
                    with db_pool.get_db_session() as db:
                        self.knowledge_service.update_pipeline_run_status(
                            db=db,
                            run_id=run_id,
                            status="completed"
                        )
                
                # 通知完成
                self._notify_progress(
                    document_id,
                    100,
                    "completed",
                    "处理完成",
                    {"completed_stages": [s.value for s in context.stage_results.keys()]}
                )
        
        except Exception as e:
            logger.error(f"流水线执行异常: {e}")
            context.status = PipelineStatus.FAILED
            context.error_message = str(e)
            
            # 更新运行记录
            if run_id:
                with db_pool.get_db_session() as db:
                    self.knowledge_service.update_pipeline_run_status(
                        db=db,
                        run_id=run_id,
                        status="failed",
                        error_message=str(e)
                    )
            
            # 回滚
            if self.enable_rollback:
                await self.rollback(context)
        
        return context
    
    async def rollback(self, context: PipelineContext) -> bool:
        """
        回滚流水线
        
        Args:
            context: 流水线上下文
            
        Returns:
            是否回滚成功
        """
        logger.info(f"开始回滚流水线: {context.document_id}")
        
        context.status = PipelineStatus.ROLLING_BACK
        
        # 逆序回滚各阶段
        for stage in reversed(self.stages):
            result = context.get_stage_result(stage)
            if result and result.is_success:
                handler = self.handlers.get(stage)
                if handler:
                    try:
                        success = await handler.rollback(context, result)
                        if not success:
                            logger.warning(f"阶段 {stage.value} 回滚失败")
                    except Exception as e:
                        logger.error(f"阶段 {stage.value} 回滚异常: {e}")
        
        context.status = PipelineStatus.ROLLED_BACK
        
        logger.info(f"流水线回滚完成: {context.document_id}")
        
        return True
    
    def get_pipeline_stats(self, context: PipelineContext) -> Dict[str, Any]:
        """
        获取流水线统计信息
        
        Args:
            context: 流水线上下文
            
        Returns:
            统计信息
        """
        total_duration = 0
        stage_stats = []
        
        for stage in self.stages:
            result = context.get_stage_result(stage)
            if result:
                total_duration += result.duration_ms
                stage_stats.append({
                    "stage": stage.value,
                    "success": result.is_success,
                    "duration_ms": result.duration_ms,
                    "output": result.output_data
                })
        
        return {
            "document_id": context.document_id,
            "status": context.status.value,
            "total_duration_ms": total_duration,
            "stage_count": len(self.stages),
            "completed_stages": len([s for s in stage_stats if s["success"]]),
            "failed_stages": len([s for s in stage_stats if not s["success"]]),
            "stage_stats": stage_stats
        }


# 便捷函数

async def process_document_with_pipeline(
    document_id: str,
    knowledge_base_id: int,
    file_path: str,
    file_type: str,
    stages: Optional[List[PipelineStage]] = None
) -> PipelineContext:
    """
    使用流水线处理文档
    
    Args:
        document_id: 文档ID
        knowledge_base_id: 知识库ID
        file_path: 文件路径
        file_type: 文件类型
        stages: 阶段列表，默认全部
        
    Returns:
        流水线上下文
    """
    pipeline = UnifiedProcessingPipeline(stages=stages)
    return await pipeline.process(document_id, knowledge_base_id, file_path, file_type)


# 全局流水线实例
unified_processing_pipeline = UnifiedProcessingPipeline()
