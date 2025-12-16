import PyPDF2
import docx
from pathlib import Path
from typing import Optional

class DocumentParser:
    SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt']
    
    @staticmethod
    def is_supported_format(file_path: str) -> bool:
        """检查文件格式是否支持"""
        return Path(file_path).suffix.lower() in DocumentParser.SUPPORTED_FORMATS
    
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """解析PDF文档"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            raise ValueError(f"PDF解析失败: {str(e)}")
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """解析Word文档"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Word文档解析失败: {str(e)}")
    
    @staticmethod
    def parse_txt(file_path: str) -> str:
        """解析文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    return file.read()
            except Exception as e:
                raise ValueError(f"文本文件解析失败: {str(e)}")
    
    @staticmethod
    def parse_document(file_path: str) -> str:
        """统一文档解析入口"""
        suffix = Path(file_path).suffix.lower()
        if suffix == '.pdf':
            return DocumentParser.parse_pdf(file_path)
        elif suffix in ['.docx', '.doc']:
            return DocumentParser.parse_docx(file_path)
        elif suffix == '.txt':
            return DocumentParser.parse_txt(file_path)
        else:
            raise ValueError(f"不支持的文档格式: {suffix}")