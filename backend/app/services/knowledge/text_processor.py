import re
from typing import List

class KnowledgeTextProcessor:
    def __init__(self):
        pass
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空格和换行
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:]', '', text)
        return text.strip()
    
    def chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """文本分块"""
        # 按句子分割
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def process_document_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """处理文档文本：清理并分块"""
        cleaned_text = self.clean_text(text)
        chunks = self.chunk_text(cleaned_text, chunk_size)
        return chunks