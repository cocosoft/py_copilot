#!/usr/bin/env python3
"""
BERT模型管理器

提供BERT模型的优化加载和管理，包括：
- 延迟加载（Lazy Loading）
- 模型缓存
- 批量推理优化
- 内存管理
"""

import os
import gc
import logging
import threading
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'
    max_seq_length: int = 256
    batch_size: int = 32
    device: str = 'cpu'  # 'cpu' 或 'cuda'
    cache_dir: Optional[str] = None
    lazy_load: bool = True  # 是否延迟加载


class BERTModelManager:
    """
    BERT模型管理器
    
    单例模式管理BERT模型，提供：
    1. 延迟加载 - 首次使用时才加载模型
    2. 模型缓存 - 避免重复加载
    3. 批量推理 - 提高吞吐量
    4. 内存管理 - 自动清理和优化
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[ModelConfig] = None):
        if self._initialized:
            return
        
        self.config = config or ModelConfig()
        self._model = None
        self._is_loaded = False
        self._load_lock = threading.Lock()
        self._usage_count = 0
        self._last_used = None
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._cache_max_size = 1000
        
        self._initialized = True
        logger.info(f"BERT模型管理器初始化完成 (延迟加载: {self.config.lazy_load})")
    
    @property
    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._is_loaded
    
    def _load_model(self) -> bool:
        """
        加载BERT模型
        
        Returns:
            是否加载成功
        """
        if self._is_loaded:
            return True
        
        with self._load_lock:
            if self._is_loaded:  # 双重检查
                return True
            
            try:
                logger.info(f"正在加载BERT模型: {self.config.model_name}")
                
                # 尝试导入sentence-transformers
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError:
                    logger.error("sentence-transformers未安装，无法加载BERT模型")
                    return False
                
                # 设置缓存目录
                cache_dir = self.config.cache_dir or os.path.expanduser('~/.cache/torch/sentence_transformers')
                os.makedirs(cache_dir, exist_ok=True)
                
                # 加载模型
                self._model = SentenceTransformer(
                    self.config.model_name,
                    cache_folder=cache_dir,
                    device=self.config.device
                )
                
                # 设置最大序列长度
                self._model.max_seq_length = self.config.max_seq_length
                
                self._is_loaded = True
                self._last_used = datetime.now()
                
                logger.info(f"BERT模型加载成功: {self.config.model_name}")
                logger.info(f"  设备: {self.config.device}")
                logger.info(f"  最大序列长度: {self.config.max_seq_length}")
                
                return True
                
            except Exception as e:
                logger.error(f"BERT模型加载失败: {e}")
                return False
    
    def ensure_loaded(self) -> bool:
        """
        确保模型已加载
        
        Returns:
            模型是否可用
        """
        if not self._is_loaded:
            return self._load_model()
        return True
    
    def encode(self, 
               texts: Union[str, List[str]], 
               batch_size: Optional[int] = None,
               show_progress: bool = False,
               normalize_embeddings: bool = True) -> Optional[np.ndarray]:
        """
        编码文本为向量
        
        Args:
            texts: 单个文本或文本列表
            batch_size: 批大小
            show_progress: 是否显示进度
            normalize_embeddings: 是否归一化向量
        
        Returns:
            文本向量
        """
        # 确保模型已加载
        if not self.ensure_loaded():
            logger.error("模型未加载，无法编码")
            return None
        
        # 标准化输入
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        # 检查缓存
        cache_key = None
        if len(texts) == 1:
            cache_key = texts[0]
            if cache_key in self._embedding_cache:
                self._usage_count += 1
                self._last_used = datetime.now()
                return self._embedding_cache[cache_key].reshape(1, -1)
        
        try:
            # 使用配置的批大小
            batch_size = batch_size or self.config.batch_size
            
            # 编码
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=normalize_embeddings
            )
            
            # 更新统计
            self._usage_count += len(texts)
            self._last_used = datetime.now()
            
            # 缓存结果
            if len(texts) == 1 and cache_key:
                self._add_to_cache(cache_key, embeddings[0])
            
            return embeddings
            
        except Exception as e:
            logger.error(f"编码失败: {e}")
            return None
    
    def _add_to_cache(self, text: str, embedding: np.ndarray):
        """添加向量到缓存"""
        # 清理缓存
        if len(self._embedding_cache) >= self._cache_max_size:
            # 移除最早的10%缓存
            keys_to_remove = list(self._embedding_cache.keys())[:self._cache_max_size // 10]
            for key in keys_to_remove:
                del self._embedding_cache[key]
        
        self._embedding_cache[text] = embedding
    
    def encode_batch(self, 
                     texts: List[str],
                     batch_size: Optional[int] = None) -> Optional[np.ndarray]:
        """
        批量编码（优化版本）
        
        Args:
            texts: 文本列表
            batch_size: 批大小
        
        Returns:
            向量数组
        """
        if not texts:
            return np.array([])
        
        batch_size = batch_size or self.config.batch_size
        
        # 分批处理
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.encode(batch, batch_size=len(batch))
            if embeddings is not None:
                all_embeddings.append(embeddings)
        
        if all_embeddings:
            return np.vstack(all_embeddings)
        return None
    
    def compute_similarity(self, 
                          text1: Union[str, List[str]], 
                          text2: Union[str, List[str]]) -> Optional[np.ndarray]:
        """
        计算文本相似度
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            相似度矩阵
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        
        if emb1 is None or emb2 is None:
            return None
        
        # 计算余弦相似度
        similarity = np.dot(emb1, emb2.T)
        return similarity
    
    def unload_model(self):
        """卸载模型释放内存"""
        if self._model is not None:
            logger.info("卸载BERT模型...")
            self._model = None
            self._is_loaded = False
            self._embedding_cache.clear()
            gc.collect()
            
            # 如果使用CUDA，清理缓存
            if self.config.device == 'cuda':
                try:
                    import torch
                    torch.cuda.empty_cache()
                except:
                    pass
            
            logger.info("BERT模型已卸载")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取模型使用统计"""
        return {
            'is_loaded': self._is_loaded,
            'model_name': self.config.model_name,
            'device': self.config.device,
            'usage_count': self._usage_count,
            'last_used': self._last_used.isoformat() if self._last_used else None,
            'cache_size': len(self._embedding_cache),
            'cache_max_size': self._cache_max_size,
        }
    
    def optimize_memory(self):
        """优化内存使用"""
        logger.info("优化BERT模型内存使用...")
        
        # 清理缓存
        if len(self._embedding_cache) > self._cache_max_size * 0.8:
            self._embedding_cache.clear()
            logger.info("已清理向量缓存")
        
        # 强制垃圾回收
        gc.collect()
        
        # 如果使用CUDA，清理显存
        if self.config.device == 'cuda':
            try:
                import torch
                torch.cuda.empty_cache()
                logger.info("已清理CUDA缓存")
            except:
                pass
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.unload_model()


# 便捷函数
def get_bert_manager(config: Optional[ModelConfig] = None) -> BERTModelManager:
    """获取BERT模型管理器实例"""
    return BERTModelManager(config)


def encode_texts(texts: Union[str, List[str]], 
                 batch_size: int = 32,
                 normalize: bool = True) -> Optional[np.ndarray]:
    """便捷函数：编码文本"""
    manager = get_bert_manager()
    return manager.encode(texts, batch_size=batch_size, normalize_embeddings=normalize)


def compute_text_similarity(text1: str, text2: str) -> Optional[float]:
    """便捷函数：计算两个文本的相似度"""
    manager = get_bert_manager()
    similarity = manager.compute_similarity(text1, text2)
    if similarity is not None:
        return float(similarity[0, 0])
    return None


# 模型预热（在应用启动时调用）
def warmup_model():
    """预热BERT模型"""
    logger.info("预热BERT模型...")
    manager = get_bert_manager()
    
    # 使用简单文本预热
    warmup_texts = [
        "这是一个测试文本",
        "This is a test text",
        "BERT模型预热",
    ]
    
    embeddings = manager.encode(warmup_texts, show_progress=False)
    
    if embeddings is not None:
        logger.info(f"BERT模型预热完成，输出维度: {embeddings.shape}")
    else:
        logger.warning("BERT模型预热失败")
    
    return manager.is_loaded


if __name__ == '__main__':
    # 测试模型管理器
    config = ModelConfig(
        model_name='paraphrase-multilingual-MiniLM-L12-v2',
        lazy_load=True,
        batch_size=16
    )
    
    manager = BERTModelManager(config)
    
    print("模型状态:", manager.get_stats())
    
    # 测试编码
    texts = [
        "这是一个测试句子",
        "这是另一个测试句子",
        " completely different text",
    ]
    
    print("\n编码测试:")
    embeddings = manager.encode(texts, show_progress=True)
    
    if embeddings is not None:
        print(f"编码成功，形状: {embeddings.shape}")
        
        # 计算相似度
        print("\n相似度矩阵:")
        similarity = manager.compute_similarity(texts, texts)
        print(similarity)
    
    print("\n最终状态:", manager.get_stats())
