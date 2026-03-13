import logging
from typing import List, Dict, Any, Optional, Tuple
import os

# 确保环境变量已设置（如果通过其他方式导入）
try:
    from app.core.env_config import *
except ImportError:
    pass  # 环境变量可能已在其他地方设置

logger = logging.getLogger(__name__)


class RerankService:
    """重排序服务，使用CrossEncoder模型对搜索结果进行精排"""
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-large"):
        """初始化重排序服务
        
        Args:
            model_name: 重排序模型名称，默认使用BAAI/bge-reranker-large
        """
        self.model_name = model_name
        self.model = None
        self.available = False
        
        # 延迟加载模型
        self._initialize_model()
    
    def _get_device(self) -> str:
        """自动检测可用设备"""
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except:
            return "cpu"
    
    def _get_model_path(self):
        """获取模型路径"""
        model_name = self.model_name
        
        # 首先检查应用模型目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(current_dir, "../../../.."))
        app_model_path = os.path.join(backend_dir, "models", model_name.replace("/", os.sep))
        
        if os.path.exists(app_model_path):
            return app_model_path
        
        # 回退到HuggingFace缓存目录
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        model_id = model_name.replace("/", "--")
        cache_path = os.path.join(cache_dir, f"models--{model_id}")
        
        if os.path.exists(cache_path):
            # 查找snapshots目录
            snapshots_dir = os.path.join(cache_path, "snapshots")
            if os.path.exists(snapshots_dir):
                snapshots = os.listdir(snapshots_dir)
                if snapshots:
                    return os.path.join(snapshots_dir, snapshots[0])
        
        return None
    
    def _initialize_model(self):
        """延迟初始化重排序模型"""
        if self.model is not None:
            return
        
        try:
            # 设置离线模式环境变量
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            from sentence_transformers import CrossEncoder
            
            # 获取模型路径
            model_path = self._get_model_path()
            
            if not model_path or not os.path.exists(model_path):
                logger.warning("重排序模型未找到，重排序功能将不可用")
                logger.warning("请运行: python scripts/download_models.py")
                self.available = False
                self.model = None
                return
            
            logger.info(f"从本地加载重排序模型: {model_path}")
            self.model = CrossEncoder(
                model_path,
                max_length=512,
                device=self._get_device()
            )
            self.available = True
            logger.info("重排序模型加载成功")
        except Exception as e:
            logger.error(f"重排序模型加载失败: {e}")
            self.available = False
            self.model = None
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], 
               top_k: int = 5) -> List[Dict[str, Any]]:
        """对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 待重排序的文档列表，每个文档应包含'content'字段
            top_k: 返回前k个结果
            
        Returns:
            重排序后的文档列表，包含重排序分数
        """
        if not self.available:
            logger.warning("重排序模型不可用，返回原始排序结果")
            return documents[:top_k]
        
        if not documents:
            return []
        
        try:
            # 准备输入对 (query, document)
            pairs = []
            for doc in documents:
                content = doc.get('content', doc.get('document', ''))
                pairs.append([query, content])
            
            # 使用CrossEncoder计算相关性分数
            scores = self.model.predict(pairs)
            
            # 将分数与文档关联
            scored_documents = []
            for i, (doc, score) in enumerate(zip(documents, scores)):
                scored_doc = {
                    **doc,
                    'rerank_score': float(score),
                    'original_rank': i
                }
                scored_documents.append(scored_doc)
            
            # 按重排序分数降序排序
            scored_documents.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            # 返回前top_k个结果
            return scored_documents[:top_k]
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            # 失败时返回原始排序的前top_k个结果
            return documents[:top_k]
    
    def rerank_with_threshold(self, query: str, documents: List[Dict[str, Any]], 
                              top_k: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """对文档进行重排序，并应用分数阈值过滤
        
        Args:
            query: 查询文本
            documents: 待重排序的文档列表
            top_k: 返回前k个结果
            threshold: 分数阈值，低于此分数的文档将被过滤
            
        Returns:
            重排序并过滤后的文档列表
        """
        reranked = self.rerank(query, documents, top_k=len(documents))
        
        # 应用阈值过滤
        filtered = [doc for doc in reranked if doc.get('rerank_score', 0) >= threshold]
        
        # 返回前top_k个结果
        return filtered[:top_k]
    
    def batch_rerank(self, queries: List[str], 
                     documents_list: List[List[Dict[str, Any]]],
                     top_k: int = 5) -> List[List[Dict[str, Any]]]:
        """批量重排序
        
        Args:
            queries: 查询文本列表
            documents_list: 每个查询对应的文档列表
            top_k: 每个查询返回前k个结果
            
        Returns:
            重排序后的文档列表的列表
        """
        if not self.available:
            logger.warning("重排序模型不可用，返回原始排序结果")
            return [docs[:top_k] for docs in documents_list]
        
        results = []
        for query, documents in zip(queries, documents_list):
            reranked = self.rerank(query, documents, top_k)
            results.append(reranked)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "available": self.available,
            "device": self._get_device() if self.available else None
        }
