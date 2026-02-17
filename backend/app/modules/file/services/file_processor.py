"""文件处理器服务"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any


class FileProcessorInterface(ABC):
    """文件处理器接口"""
    
    @abstractmethod
    def can_process(self, file_path: Path, file_type: str) -> bool:
        """判断是否可以处理该文件"""
        pass
    
    @abstractmethod
    def process(self, file_path: Path, file_name: str) -> Dict[str, Any]:
        """处理文件并返回内容"""
        pass


class TextFileProcessor(FileProcessorInterface):
    """文本文件处理器"""
    
    def can_process(self, file_path: Path, file_type: str) -> bool:
        return file_type == 'text' or file_path.suffix in ['.txt', '.md', '.json', '.yaml', '.yml', '.csv']
    
    def process(self, file_path: Path, file_name: str) -> Dict[str, Any]:
        """处理文本文件"""
        content = ""
        error_message = None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except Exception as e:
                error_message = f"编码错误: {str(e)}"
        except Exception as e:
            error_message = f"读取失败: {str(e)}"
        
        if error_message:
            return {
                'filename': file_name,
                'content': f"[文件内容读取失败: {error_message}]",
                'type': 'text',
                'error': error_message
            }
        
        return {
            'filename': file_name,
            'content': content,
            'type': 'text'
        }


class WordFileProcessor(FileProcessorInterface):
    """Word文件处理器"""

    def can_process(self, file_path: Path, file_type: str) -> bool:
        return file_type == 'word' or file_path.suffix in ['.docx', '.doc']

    def process(self, file_path: Path, file_name: str) -> Dict[str, Any]:
        """处理Word文件"""
        content = ""
        error_message = None

        try:
            if file_path.suffix == '.docx':
                import zipfile
                import xml.etree.ElementTree as ET

                word_data = []
                
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    xml_content = zip_ref.read('word/document.xml')
                    root = ET.fromstring(xml_content)

                    for elem in root.iter():
                        if elem.text:
                            word_data.append(elem.text)

                content = '\n'.join(word_data)
            elif file_path.suffix == '.doc':
                content = "[.doc文件格式较旧，建议转换为.docx格式后上传]"
            else:
                content = f"[Word文件内容需要特殊处理: {file_path.suffix}]"
        except Exception as e:
            error_message = f"读取失败: {str(e)}"

        if error_message:
            return {
                'filename': file_name,
                'content': f"[Word文件内容读取失败: {error_message}]",
                'type': 'word',
                'error': error_message
            }

        return {
            'filename': file_name,
            'content': content,
            'type': 'word'
        }


class ExcelFileProcessor(FileProcessorInterface):
    """Excel文件处理器"""

    def can_process(self, file_path: Path, file_type: str) -> bool:
        return file_type == 'excel' or file_path.suffix in ['.xlsx', '.xls']

    def process(self, file_path: Path, file_name: str) -> Dict[str, Any]:
        """处理Excel文件"""
        content = ""
        error_message = None

        try:
            import zipfile
            import xml.etree.ElementTree as ET
            import csv
            import io

            excel_data = []

            if file_path.suffix == '.xlsx':
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    workbook_xml = zip_ref.read('xl/workbook.xml')
                    workbook_root = ET.fromstring(workbook_xml)

                    sheets = []
                    for sheet in workbook_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'):
                        sheet_name = sheet.get('name')
                        sheet_id = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                        sheets.append((sheet_name, sheet_id))

                    for sheet_name, sheet_id in sheets:
                        excel_data.append(f"=== Sheet: {sheet_name} ===")

                        try:
                            worksheet_path = f'xl/worksheets/sheet{int(sheet_id.split("sheet")[-1])}.xml'
                            worksheet_xml = zip_ref.read(worksheet_path)
                            worksheet_root = ET.fromstring(worksheet_xml)

                            shared_strings = {}
                            try:
                                shared_strings_xml = zip_ref.read('xl/sharedStrings.xml')
                                shared_strings_root = ET.fromstring(shared_strings_xml)
                                for i, si in enumerate(shared_strings_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si')):
                                    t = si.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                                    if t is not None and t.text:
                                        shared_strings[str(i)] = t.text
                            except:
                                pass

                            rows = worksheet_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
                            for row in rows:
                                row_data = []
                                cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                                for cell in cells:
                                    cell_value = ""
                                    v = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                                    if v is not None and v.text:
                                        cell_type = cell.get('t')
                                        if cell_type == 's':
                                            cell_value = shared_strings.get(v.text, v.text)
                                        else:
                                            cell_value = v.text
                                    row_data.append(cell_value)
                                if row_data:
                                    excel_data.append('\t'.join(row_data))

                        except Exception as e:
                            excel_data.append(f"[读取Sheet失败: {str(e)}]")

                        excel_data.append("")

            elif file_path.suffix == '.xls':
                excel_data.append("[.xls文件格式较旧，建议转换为.xlsx格式后上传]")

            content = '\n'.join(excel_data)
        except Exception as e:
            error_message = f"读取失败: {str(e)}"

        if error_message:
            return {
                'filename': file_name,
                'content': f"[Excel文件内容读取失败: {error_message}]",
                'type': 'excel',
                'error': error_message
            }

        return {
            'filename': file_name,
            'content': content,
            'type': 'excel'
        }


class PptFileProcessor(FileProcessorInterface):
    """PPT文件处理器"""

    def can_process(self, file_path: Path, file_type: str) -> bool:
        return file_type == 'ppt' or file_path.suffix in ['.pptx']

    def process(self, file_path: Path, file_name: str) -> Dict[str, Any]:
        """处理PPT文件"""
        content = ""
        error_message = None

        try:
            import zipfile
            import xml.etree.ElementTree as ET

            ppt_data = []

            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                slide_files = sorted([f for f in zip_ref.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')])

                for slide_file in slide_files:
                    slide_number = slide_file.split('/')[-1].replace('slide', '').replace('.xml', '')
                    ppt_data.append(f"=== Slide {slide_number} ===")

                    try:
                        slide_xml = zip_ref.read(slide_file)
                        slide_root = ET.fromstring(slide_xml)

                        for elem in slide_root.iter():
                            if elem.text and elem.text.strip():
                                text = elem.text.strip()
                                if text and len(text) > 1:
                                    ppt_data.append(text)

                    except Exception as e:
                        ppt_data.append(f"[读取幻灯片失败: {str(e)}]")

                    ppt_data.append("")

            content = '\n'.join(ppt_data)
        except Exception as e:
            error_message = f"读取失败: {str(e)}"

        if error_message:
            return {
                'filename': file_name,
                'content': f"[PPT文件内容读取失败: {error_message}]",
                'type': 'ppt',
                'error': error_message
            }

        return {
            'filename': file_name,
            'content': content,
            'type': 'ppt'
        }


class PdfFileProcessor(FileProcessorInterface):
    """PDF文件处理器"""

    def can_process(self, file_path: Path, file_type: str) -> bool:
        return file_type == 'pdf' or file_path.suffix == '.pdf'

    def process(self, file_path: Path, file_name: str) -> Dict[str, Any]:
        """处理PDF文件"""
        content = ""
        error_message = None

        try:
            from PyPDF2 import PdfReader

            pdf_reader = PdfReader(file_path)
            pdf_data = []

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        pdf_data.append(f"=== 第 {page_num + 1} 页 ===")
                        pdf_data.append(page_text)
                        pdf_data.append("")
                except Exception as e:
                    pdf_data.append(f"[读取第 {page_num + 1} 页失败: {str(e)}]")

            content = '\n'.join(pdf_data)
        except Exception as e:
            error_message = f"读取失败: {str(e)}"

        if error_message:
            return {
                'filename': file_name,
                'content': f"[PDF文件内容读取失败: {error_message}]",
                'type': 'pdf',
                'error': error_message
            }

        return {
            'filename': file_name,
            'content': content,
            'type': 'pdf'
        }


class DefaultFileProcessor(FileProcessorInterface):
    """默认文件处理器"""
    
    def can_process(self, file_path: Path, file_type: str) -> bool:
        return True  # 默认处理器可以处理任何文件
    
    def process(self, file_path: Path, file_name: str) -> Dict[str, Any]:
        """处理默认文件"""
        file_size = file_path.stat().st_size if file_path.exists() else 0
        return {
            'filename': file_name,
            'content': f"[文件类型: {file_path.suffix.lstrip('.')}, 大小: {file_size} 字节]",
            'type': 'other'
        }


class FileProcessorService:
    """文件处理器服务"""
    
    def __init__(self):
        """初始化文件处理器服务"""
        self.processors: List[FileProcessorInterface] = [
            TextFileProcessor(),
            WordFileProcessor(),
            ExcelFileProcessor(),
            PptFileProcessor(),
            PdfFileProcessor(),
            DefaultFileProcessor()
        ]
    
    def process_file(self, file_path: Path, file_name: str, file_type: str) -> Dict[str, Any]:
        """
        处理文件并返回内容
        
        Args:
            file_path: 文件路径
            file_name: 文件名
            file_type: 文件类型
            
        Returns:
            包含文件内容的字典
        """
        # 查找适合的处理器
        for processor in self.processors:
            if processor.can_process(file_path, file_type):
                print(f"使用 {processor.__class__.__name__} 处理文件: {file_name}")
                return processor.process(file_path, file_name)
        
        # 如果没有找到适合的处理器，使用默认处理器
        default_processor = DefaultFileProcessor()
        print(f"使用 DefaultFileProcessor 处理文件: {file_name}")
        return default_processor.process(file_path, file_name)
    
    def add_processor(self, processor: FileProcessorInterface):
        """
        添加自定义文件处理器
        
        Args:
            processor: 文件处理器实例
        """
        self.processors.insert(0, processor)  # 新处理器优先级更高
    
    def get_supported_file_types(self) -> List[str]:
        """
        获取支持的文件类型
        
        Returns:
            支持的文件类型列表
        """
        return ['text', 'word', 'excel', 'ppt', 'pdf', 'other']


# 创建全局文件处理器服务实例
file_processor_service = FileProcessorService()
