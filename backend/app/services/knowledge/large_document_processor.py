"""
大文档处理优化器

专门处理大文档的优化模块，包括分块策略、增量处理、内存优化等。
"""
import os
import time
import logging
import hashlib
from typing import List, Dict, Any, Optional, Generator, Tuple
from pathlib import Path
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class LargeDocumentProcessor:
    """大文档处理器"""
    
    def __init__(self, 
                 max_chunk_size: int = 2000,  # 最大分块大小（字符）
                 overlap_size: int = 200,     # 重叠大小（字符）
                 max_memory_usage: int = 500 * 1024 * 1024,  # 最大内存使用（500MB）
                 temp_dir: str = None):
        """初始化大文档处理器
        
        Args:
            max_chunk_size: 最大分块大小
            overlap_size: 重叠大小
            max_memory_usage: 最大内存使用
            temp_dir: 临时目录
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.max_memory_usage = max_memory_usage
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # 创建临时目录
        self.process_temp_dir = os.path.join(self.temp_dir, "knowledge_processor")
        os.makedirs(self.process_temp_dir, exist_ok=True)
        
        # 线程池用于并行处理
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        logger.info(f"大文档处理器初始化完成，临时目录: {self.process_temp_dir}")
    
    def process_large_document(self, 
                             content: str, 
                             metadata: Dict[str, Any] = None,
                             use_streaming: bool = True) -> Dict[str, Any]:
        """处理大文档
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            use_streaming: 是否使用流式处理
            
        Returns:
            处理结果
        """
        start_time = time.time()
        
        try:
            document_size = len(content)
            
            # 根据文档大小选择处理策略
            if document_size <= self.max_chunk_size * 10:  # 小于20KB的文档
                # 小文档：直接在内存中处理
                result = self._process_small_document(content, metadata)
            elif use_streaming and document_size > 10 * 1024 * 1024:  # 大于10MB的文档
                # 超大文档：使用流式处理
                result = self._process_very_large_document(content, metadata)
            else:
                # 大文档：使用分块并行处理
                result = self._process_large_document_parallel(content, metadata)
            
            processing_time = time.time() - start_time
            
            logger.info(f"大文档处理完成，大小: {document_size} 字符，耗时: {processing_time:.2f}s")
            
            return {
                "success": True,
                "document_size": document_size,
                "processing_time": processing_time,
                "strategy": result.get("strategy", "unknown"),
                "chunks": result.get("chunks", []),
                "chunk_count": len(result.get("chunks", [])),
                "memory_usage": result.get("memory_usage", 0)
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"大文档处理失败: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
                "document_size": len(content)
            }
    
    def _process_small_document(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """处理小文档
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            处理结果
        """
        # 使用智能分块
        chunks = self._smart_chunking(content, metadata)
        
        return {
            "strategy": "small_document",
            "chunks": chunks,
            "memory_usage": len(content)
        }
    
    def _process_large_document_parallel(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """并行处理大文档
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            处理结果
        """
        # 将文档分割为多个部分进行并行处理
        sections = self._split_into_sections(content)
        
        # 并行处理每个部分
        futures = []
        for i, section in enumerate(sections):
            future = self.thread_pool.submit(self._process_section, section, metadata, i)
            futures.append(future)
        
        # 收集结果
        all_chunks = []
        for future in as_completed(futures):
            try:
                section_chunks = future.result()
                all_chunks.extend(section_chunks)
            except Exception as e:
                logger.error(f"并行处理部分失败: {e}")
        
        # 合并重叠部分
        merged_chunks = self._merge_overlapping_chunks(all_chunks)
        
        return {
            "strategy": "parallel_processing",
            "chunks": merged_chunks,
            "memory_usage": len(content) + sum(len(chunk['content']) for chunk in merged_chunks)
        }
    
    def _process_very_large_document(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """处理超大文档（流式处理）
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            处理结果
        """
        # 将内容写入临时文件
        temp_file_path = self._write_to_temp_file(content)
        
        try:
            # 流式读取和处理
            chunks = []
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                buffer = ""
                chunk_index = 0
                
                for line in f:
                    buffer += line
                    
                    # 当缓冲区达到一定大小时进行处理
                    if len(buffer) >= self.max_chunk_size:
                        section_chunks = self._smart_chunking(buffer, metadata, chunk_index)
                        chunks.extend(section_chunks)
                        
                        # 保留重叠部分
                        if section_chunks:
                            last_chunk = section_chunks[-1]['content']
                            buffer = last_chunk[-self.overlap_size:] if len(last_chunk) > self.overlap_size else last_chunk
                        else:
                            buffer = ""
                        
                        chunk_index += len(section_chunks)
                
                # 处理剩余内容
                if buffer.strip():
                    section_chunks = self._smart_chunking(buffer, metadata, chunk_index)
                    chunks.extend(section_chunks)
            
            return {
                "strategy": "streaming_processing",
                "chunks": chunks,
                "memory_usage": len(content)  # 流式处理内存使用较低
            }
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def _split_into_sections(self, content: str, section_size: int = 10000) -> List[str]:
        """将文档分割为多个部分
        
        Args:
            content: 文档内容
            section_size: 部分大小
            
        Returns:
            部分列表
        """
        sections = []
        
        # 按段落分割，尽量保持语义完整性
        paragraphs = content.split('\n\n')
        
        current_section = ""
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            paragraph_size = len(paragraph)
            
            if current_size + paragraph_size <= section_size:
                if current_section:
                    current_section += "\n\n" + paragraph
                else:
                    current_section = paragraph
                current_size += paragraph_size
            else:
                # 保存当前部分
                if current_section:
                    sections.append(current_section)
                
                # 开始新部分
                current_section = paragraph
                current_size = paragraph_size
        
        # 保存最后一个部分
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _process_section(self, section_content: str, metadata: Dict[str, Any], section_index: int) -> List[Dict[str, Any]]:
        """处理文档部分
        
        Args:
            section_content: 部分内容
            metadata: 文档元数据
            section_index: 部分索引
            
        Returns:
            分块列表
        """
        section_metadata = (metadata or {}).copy()
        section_metadata["section_index"] = section_index
        
        return self._smart_chunking(section_content, section_metadata)
    
    def _smart_chunking(self, content: str, metadata: Dict[str, Any] = None, start_index: int = 0) -> List[Dict[str, Any]]:
        """智能分块策略
        
        Args:
            content: 内容
            metadata: 元数据
            start_index: 起始索引
            
        Returns:
            分块列表
        """
        if not content:
            return []
        
        chunks = []
        
        # 按句子分割
        sentences = content.split('.')
        
        current_chunk = ""
        current_size = 0
        chunk_index = start_index
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence += "."  # 恢复句号
            sentence_size = len(sentence)
            
            if current_size + sentence_size <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_size += sentence_size
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, chunk_index, metadata))
                    chunk_index += 1
                
                # 开始新块
                current_chunk = sentence
                current_size = sentence_size
        
        # 保存最后一个块
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, chunk_index, metadata))
        
        return chunks
    
    def _create_chunk(self, content: str, index: int, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建分块对象
        
        Args:
            content: 分块内容
            index: 分块索引
            metadata: 元数据
            
        Returns:
            分块对象
        """
        chunk_metadata = (metadata or {}).copy()
        chunk_metadata.update({
            "chunk_index": index,
            "chunk_size": len(content),
            "word_count": len(content.split()),
            "sentence_count": content.count('.') + content.count('!') + content.count('?')
        })
        
        return {
            "content": content,
            "metadata": chunk_metadata,
            "summary": self._generate_chunk_summary(content)
        }
    
    def _generate_chunk_summary(self, content: str, max_length: int = 150) -> str:
        """生成分块摘要
        
        Args:
            content: 分块内容
            max_length: 摘要最大长度
            
        Returns:
            分块摘要
        """
        if len(content) <= max_length:
            return content
        
        # 取前几个句子作为摘要
        sentences = content.split('.')
        summary_parts = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence += "."
            if current_length + len(sentence) + 1 <= max_length:
                summary_parts.append(sentence)
                current_length += len(sentence) + 1
            else:
                break
        
        summary = " ".join(summary_parts)
        
        # 如果仍然太长，进行截断
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary
    
    def _merge_overlapping_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并重叠的分块
        
        Args:
            chunks: 分块列表
            
        Returns:
            合并后的分块列表
        """
        if not chunks:
            return []
        
        merged_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                merged_chunks.append(chunk)
                continue
            
            prev_chunk = merged_chunks[-1]
            prev_content = prev_chunk['content']
            current_content = chunk['content']
            
            # 检查是否有重叠
            overlap = self._find_overlap(prev_content, current_content)
            
            if overlap and len(overlap) > self.overlap_size // 2:
                # 合并重叠部分
                merged_content = prev_content + current_content[len(overlap):]
                
                if len(merged_content) <= self.max_chunk_size:
                    # 更新前一个块
                    prev_chunk['content'] = merged_content
                    prev_chunk['metadata']['chunk_size'] = len(merged_content)
                    prev_chunk['metadata']['word_count'] = len(merged_content.split())
                else:
                    # 如果合并后太大，保持原样
                    merged_chunks.append(chunk)
            else:
                merged_chunks.append(chunk)
        
        return merged_chunks
    
    def _find_overlap(self, text1: str, text2: str, max_overlap: int = 500) -> str:
        """查找两个文本的重叠部分
        
        Args:
            text1: 文本1
            text2: 文本2
            max_overlap: 最大重叠长度
            
        Returns:
            重叠部分
        """
        # 简单的重叠检测
        overlap_size = min(len(text1), len(text2), max_overlap)
        
        for i in range(overlap_size, 0, -1):
            if text1[-i:] == text2[:i]:
                return text1[-i:]
        
        return ""
    
    def _write_to_temp_file(self, content: str) -> str:
        """将内容写入临时文件
        
        Args:
            content: 内容
            
        Returns:
            临时文件路径
        """
        # 生成唯一文件名
        content_hash = hashlib.md5(content.encode()).hexdigest()
        temp_file_path = os.path.join(self.process_temp_dir, f"doc_{content_hash}.txt")
        
        # 写入文件
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return temp_file_path
    
    def cleanup_temp_files(self) -> None:
        """清理临时文件"""
        try:
            for file_path in Path(self.process_temp_dir).glob("*.txt"):
                file_path.unlink()
            logger.info("临时文件清理完成")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def get_memory_usage(self) -> int:
        """获取当前内存使用情况（估算）
        
        Returns:
            内存使用量（字节）
        """
        # 简化实现：返回临时目录大小
        try:
            total_size = 0
            for file_path in Path(self.process_temp_dir).rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except:
            return 0
    
    def __del__(self):
        """析构函数，清理资源"""
        try:
            self.thread_pool.shutdown(wait=False)
            self.cleanup_temp_files()
        except:
            pass


class DocumentProcessingPipeline:
    """文档处理管道"""
    
    def __init__(self):
        """初始化文档处理管道"""
        self.processors = {
            "small": LargeDocumentProcessor(max_chunk_size=1000),
            "medium": LargeDocumentProcessor(max_chunk_size=2000),
            "large": LargeDocumentProcessor(max_chunk_size=3000, use_streaming=True)
        }
    
    def process_document(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理文档
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            
        Returns:
            处理结果
        """
        document_size = len(content)
        
        # 根据文档大小选择合适的处理器
        if document_size <= 100 * 1024:  # 小于100KB
            processor = self.processors["small"]
            strategy = "small"
        elif document_size <= 10 * 1024 * 1024:  # 小于10MB
            processor = self.processors["medium"]
            strategy = "medium"
        else:
            processor = self.processors["large"]
            strategy = "large"
        
        result = processor.process_large_document(content, metadata)
        result["processing_strategy"] = strategy
        
        return result