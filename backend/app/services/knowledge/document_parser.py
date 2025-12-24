import PyPDF2
import docx
import openpyxl
import pptx
import pandas as pd
from PIL import Image
import io
import os
from pathlib import Path
from typing import Optional

class DocumentParser:
    SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls', '.pptx', '.ppt', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.wps', '.et', '.dps']
    
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
    def parse_excel(file_path: str) -> str:
        """解析Excel文件"""
        try:
            # 使用pandas读取Excel文件
            excel_file = pd.ExcelFile(file_path)
            text = ""
            
            # 遍历所有工作表
            for sheet_name in excel_file.sheet_names:
                df = excel_file.parse(sheet_name)
                text += f"=== 工作表: {sheet_name} ===\n"
                
                # 添加列名
                text += "\t".join([str(col) for col in df.columns]) + "\n"
                
                # 添加数据行
                for _, row in df.iterrows():
                    text += "\t".join([str(cell) for cell in row]) + "\n"
                
                text += "\n"
            
            return text
        except Exception as e:
            raise ValueError(f"Excel文件解析失败: {str(e)}")
    
    @staticmethod
    def parse_powerpoint(file_path: str) -> str:
        """解析PowerPoint文件"""
        try:
            prs = pptx.Presentation(file_path)
            text = ""
            
            # 遍历所有幻灯片
            for slide_num, slide in enumerate(prs.slides, 1):
                text += f"=== 幻灯片 {slide_num} ===\n"
                
                # 获取幻灯片中的文本
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        if shape.text.strip():
                            text += shape.text + "\n"
                
                text += "\n"
            
            return text
        except Exception as e:
            raise ValueError(f"PowerPoint文件解析失败: {str(e)}")
    
    @staticmethod
    def parse_image(file_path: str) -> str:
        """解析图片文件"""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                format = img.format
                mode = img.mode
                
                # 返回图片基本信息
                return f"=== 图片信息 ===\n" \
                       f"文件名: {os.path.basename(file_path)}\n" \
                       f"格式: {format}\n" \
                       f"尺寸: {width} x {height} 像素\n" \
                       f"色彩模式: {mode}\n"
        except Exception as e:
            raise ValueError(f"图片文件解析失败: {str(e)}")

    @staticmethod
    def parse_wps(file_path: str) -> str:
        """解析WPS文件"""
        try:
            suffix = Path(file_path).suffix.lower()
            
            if suffix == '.wps':
                # WPS文字文档 - 尝试使用docx库解析
                try:
                    doc = docx.Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    return f"=== WPS文字文档内容 ===\n{text}"
                except Exception:
                    # 如果docx库无法解析，返回文件信息
                    file_size = os.path.getsize(file_path)
                    return f"=== WPS文字文档信息 ===\n" \
                           f"文件名: {os.path.basename(file_path)}\n" \
                           f"文件大小: {file_size} 字节\n" \
                           f"说明: 此WPS文件格式需要特殊处理\n"
            
            elif suffix == '.et':
                # WPS表格文档 - 尝试使用openpyxl库解析
                try:
                    workbook = openpyxl.load_workbook(file_path)
                    text = ""
                    for sheet_name in workbook.sheetnames:
                        sheet = workbook[sheet_name]
                        text += f"=== 工作表: {sheet_name} ===\n"
                        for row in sheet.iter_rows(values_only=True):
                            row_text = " | ".join(str(cell) if cell is not None else "" for cell in row)
                            text += row_text + "\n"
                        text += "\n"
                    return text
                except Exception:
                    # 如果openpyxl库无法解析，返回文件信息
                    file_size = os.path.getsize(file_path)
                    return f"=== WPS表格文档信息 ===\n" \
                           f"文件名: {os.path.basename(file_path)}\n" \
                           f"文件大小: {file_size} 字节\n" \
                           f"说明: 此WPS表格文件格式需要特殊处理\n"
            
            elif suffix == '.dps':
                # WPS演示文档 - 尝试使用pptx库解析
                try:
                    presentation = pptx.Presentation(file_path)
                    text = ""
                    for i, slide in enumerate(presentation.slides):
                        text += f"=== 幻灯片 {i+1} ===\n"
                        for shape in slide.shapes:
                            if hasattr(shape, "text") and shape.text:
                                text += shape.text + "\n"
                        text += "\n"
                    return text
                except Exception:
                    # 如果pptx库无法解析，返回文件信息
                    file_size = os.path.getsize(file_path)
                    return f"=== WPS演示文档信息 ===\n" \
                           f"文件名: {os.path.basename(file_path)}\n" \
                           f"文件大小: {file_size} 字节\n" \
                           f"说明: 此WPS演示文件格式需要特殊处理\n"
            
            else:
                raise ValueError(f"不支持的WPS文件格式: {suffix}")
                
        except Exception as e:
            raise ValueError(f"WPS文件解析失败: {str(e)}")
    
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
        elif suffix in ['.xlsx', '.xls']:
            return DocumentParser.parse_excel(file_path)
        elif suffix in ['.pptx', '.ppt']:
            return DocumentParser.parse_powerpoint(file_path)
        elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return DocumentParser.parse_image(file_path)
        elif suffix in ['.wps', '.et', '.dps']:
            return DocumentParser.parse_wps(file_path)
        else:
            raise ValueError(f"不支持的文档格式: {suffix}")