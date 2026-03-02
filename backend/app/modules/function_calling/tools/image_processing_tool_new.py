"""
图像处理工具

复用服务：ImageProcessingService
提供图像调整、转换、分析功能
"""

from typing import Dict, Any, List, Optional
import time
import logging

from app.modules.function_calling.base_tool import ServiceTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)

logger = logging.getLogger(__name__)


class ImageProcessingTool(ServiceTool):
    """
    图像处理工具
    
    复用服务：ImageProcessingService
    提供图像调整、格式转换、OCR识别等功能
    """
    
    def __init__(self):
        """初始化图像处理工具"""
        self._image_service = None
        super().__init__()
    
    def _get_service(self):
        """
        获取图像处理服务实例
        
        Returns:
            ImageProcessingService: 图像处理服务实例
        """
        # 延迟导入避免循环依赖
        from app.services.image_processing_service import image_processing_service
        return image_processing_service
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="image_processing",
            display_name="图像处理",
            description="提供图像调整、格式转换、OCR识别等功能",
            category=ToolCategory.IMAGE.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="🖼️",
            tags=["图像", "处理", "OCR", "转换"],
            is_active=True
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        """
        获取工具参数定义
        
        Returns:
            List[ToolParameter]: 参数定义列表
        """
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型",
                required=True,
                enum=[
                    "resize", "crop", "rotate", "flip",
                    "adjust_brightness", "adjust_contrast", "adjust_saturation",
                    "blur", "sharpen",
                    "convert_format", "get_info", "extract_text"
                ]
            ),
            ToolParameter(
                name="image_path",
                type="string",
                description="图像文件路径",
                required=True
            ),
            ToolParameter(
                name="width",
                type="integer",
                description="目标宽度（action=resize时使用）",
                required=False
            ),
            ToolParameter(
                name="height",
                type="integer",
                description="目标高度（action=resize时使用）",
                required=False
            ),
            ToolParameter(
                name="angle",
                type="integer",
                description="旋转角度（action=rotate时使用）",
                required=False,
                default=90
            ),
            ToolParameter(
                name="format",
                type="string",
                description="目标格式（action=convert_format时使用）",
                required=False,
                default="JPEG",
                enum=["JPEG", "PNG", "WEBP", "BMP", "GIF"]
            ),
            ToolParameter(
                name="output_path",
                type="string",
                description="输出文件路径（可选，不提供则生成临时文件）",
                required=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行图像处理
        
        Args:
            **kwargs: 处理参数
                - action: 操作类型（必需）
                - image_path: 图像路径（必需）
                - 其他参数根据action不同而不同
        
        Returns:
            ToolExecutionResult: 执行结果
        """
        start_time = time.time()
        tool_name = self._metadata.name
        
        try:
            # 验证参数
            validation_result = self.validate_parameters(**kwargs)
            if not validation_result.is_valid:
                errors = [e.message for e in validation_result.errors]
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"参数验证失败: {'; '.join(errors)}",
                    error_code="VALIDATION_ERROR",
                    execution_time=time.time() - start_time
                )
            
            action = kwargs.get("action")
            image_path = kwargs.get("image_path")
            
            logger.info(f"执行图像处理: action={action}, image_path={image_path}")
            
            # 根据操作类型执行不同逻辑
            if action == "get_info":
                return await self._handle_get_info(image_path, start_time)
            elif action == "resize":
                return await self._handle_resize(kwargs, start_time)
            elif action == "rotate":
                return await self._handle_rotate(kwargs, start_time)
            elif action == "convert_format":
                return await self._handle_convert_format(kwargs, start_time)
            elif action == "extract_text":
                return await self._handle_extract_text(image_path, start_time)
            else:
                # 其他操作返回功能待实现提示
                return ToolExecutionResult.success_result(
                    tool_name=tool_name,
                    result={
                        "message": f"操作 '{action}' 已记录，功能待实现",
                        "image_path": image_path,
                        "action": action
                    },
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"图像处理失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"处理失败: {str(e)}",
                error_code="PROCESSING_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def _handle_get_info(self, image_path: str, start_time: float) -> ToolExecutionResult:
        """处理获取信息操作"""
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                info = {
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "size": f"{img.width}x{img.height}",
                    "aspect_ratio": round(img.width / img.height, 2) if img.height > 0 else 0,
                    "file_path": image_path
                }
                
                return ToolExecutionResult.success_result(
                    tool_name=self._metadata.name,
                    result=info,
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"获取图像信息失败: {str(e)}",
                error_code="INFO_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def _handle_resize(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理调整大小操作"""
        image_path = kwargs.get("image_path")
        width = kwargs.get("width")
        height = kwargs.get("height")
        output_path = kwargs.get("output_path")
        
        if not width and not height:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error="调整大小需要提供width或height参数",
                error_code="MISSING_PARAMETER",
                execution_time=time.time() - start_time
            )
        
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                # 计算新尺寸
                if width and height:
                    new_size = (width, height)
                elif width:
                    ratio = width / img.width
                    new_size = (width, int(img.height * ratio))
                else:
                    ratio = height / img.height
                    new_size = (int(img.width * ratio), height)
                
                # 调整大小
                resized = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 保存
                if not output_path:
                    import os
                    import tempfile
                    output_path = os.path.join(tempfile.gettempdir(), f"resized_{int(time.time())}.jpg")
                
                resized.save(output_path)
                
                return ToolExecutionResult.success_result(
                    tool_name=self._metadata.name,
                    result={
                        "original_size": f"{img.width}x{img.height}",
                        "new_size": f"{new_size[0]}x{new_size[1]}",
                        "output_path": output_path
                    },
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"调整大小失败: {str(e)}",
                error_code="RESIZE_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def _handle_rotate(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理旋转操作"""
        image_path = kwargs.get("image_path")
        angle = kwargs.get("angle", 90)
        output_path = kwargs.get("output_path")
        
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                # 旋转
                rotated = img.rotate(angle, expand=True)
                
                # 保存
                if not output_path:
                    import os
                    import tempfile
                    output_path = os.path.join(tempfile.gettempdir(), f"rotated_{int(time.time())}.jpg")
                
                rotated.save(output_path)
                
                return ToolExecutionResult.success_result(
                    tool_name=self._metadata.name,
                    result={
                        "original_size": f"{img.width}x{img.height}",
                        "angle": angle,
                        "output_path": output_path
                    },
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"旋转失败: {str(e)}",
                error_code="ROTATE_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def _handle_convert_format(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理格式转换操作"""
        image_path = kwargs.get("image_path")
        format_name = kwargs.get("format", "JPEG")
        output_path = kwargs.get("output_path")
        
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                # 转换格式
                if img.mode in ('RGBA', 'LA', 'P') and format_name == 'JPEG':
                    # JPEG不支持透明，需要转换
                    img = img.convert('RGB')
                
                # 保存
                if not output_path:
                    import os
                    import tempfile
                    ext = format_name.lower()
                    if ext == "jpeg":
                        ext = "jpg"
                    output_path = os.path.join(tempfile.gettempdir(), f"converted_{int(time.time())}.{ext}")
                
                img.save(output_path, format=format_name)
                
                return ToolExecutionResult.success_result(
                    tool_name=self._metadata.name,
                    result={
                        "original_format": img.format,
                        "new_format": format_name,
                        "output_path": output_path
                    },
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"格式转换失败: {str(e)}",
                error_code="CONVERT_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def _handle_extract_text(self, image_path: str, start_time: float) -> ToolExecutionResult:
        """处理OCR文字提取操作"""
        try:
            # 尝试使用pytesseract进行OCR
            try:
                import pytesseract
                from PIL import Image
                
                with Image.open(image_path) as img:
                    # 转换为RGB（如果需要）
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # 提取文字
                    text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                    
                    return ToolExecutionResult.success_result(
                        tool_name=self._metadata.name,
                        result={
                            "extracted_text": text,
                            "text_length": len(text),
                            "image_path": image_path
                        },
                        execution_time=time.time() - start_time
                    )
                    
            except ImportError:
                # 如果没有安装pytesseract，返回提示
                return ToolExecutionResult.success_result(
                    tool_name=self._metadata.name,
                    result={
                        "message": "OCR功能需要安装pytesseract和Tesseract-OCR引擎",
                        "image_path": image_path,
                        "installation_guide": "pip install pytesseract pillow"
                    },
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"文字提取失败: {str(e)}",
                error_code="OCR_ERROR",
                execution_time=time.time() - start_time
            )
