"""
图像编辑工具
提供完整的图像编辑功能，基于现有功能进行升级
"""

import asyncio
import logging
import uuid
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import io

logger = logging.getLogger(__name__)


class EditOperationType(Enum):
    """编辑操作类型枚举"""
    FILTER = "filter"
    TRANSFORM = "transform"
    ADJUSTMENT = "adjustment"
    DRAW = "draw"
    COMPOSITE = "composite"


class FilterType(Enum):
    """滤镜类型枚举"""
    BLUR = "blur"
    SHARPEN = "sharpen"
    EDGE_ENHANCE = "edge_enhance"
    EMBOSS = "emboss"
    CONTOUR = "contour"
    DETAIL = "detail"
    SMOOTH = "smooth"
    GAUSSIAN_BLUR = "gaussian_blur"
    MEDIAN_BLUR = "median_blur"
    BILATERAL_FILTER = "bilateral_filter"


class TransformType(Enum):
    """变换类型枚举"""
    ROTATE = "rotate"
    CROP = "crop"
    RESIZE = "resize"
    FLIP = "flip"
    PERSPECTIVE = "perspective"
    SKEW = "skew"
    SCALE = "scale"


class AdjustmentType(Enum):
    """调整类型枚举"""
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    SATURATION = "saturation"
    HUE = "hue"
    GAMMA = "gamma"
    EXPOSURE = "exposure"
    TEMPERATURE = "temperature"
    VIBRANCE = "vibrance"


class DrawType(Enum):
    """绘制类型枚举"""
    TEXT = "text"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    LINE = "line"
    ARROW = "arrow"
    POLYGON = "polygon"
    FREEHAND = "freehand"


@dataclass
class EditOperation:
    """编辑操作"""
    operation_id: str
    operation_type: EditOperationType
    parameters: Dict[str, Any]
    order: int


@dataclass
class EditResult:
    """编辑结果"""
    edit_id: str
    original_image_id: str
    edited_image_data: bytes
    applied_operations: List[EditOperation]
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class BatchEditResult:
    """批量编辑结果"""
    batch_id: str
    results: List[EditResult]
    total_images: int
    total_time: float
    success_rate: float


class ImageEditor:
    """图像编辑器"""
    
    def __init__(self):
        """初始化图像编辑器"""
        # 滤镜配置
        self.filter_config = {
            FilterType.BLUR: {
                "radius_range": [1, 10],
                "default_radius": 2
            },
            FilterType.SHARPEN: {
                "strength_range": [1, 5],
                "default_strength": 2
            },
            FilterType.GAUSSIAN_BLUR: {
                "radius_range": [1, 15],
                "default_radius": 3
            },
            FilterType.MEDIAN_BLUR: {
                "radius_range": [1, 7],
                "default_radius": 3
            },
            FilterType.BILATERAL_FILTER: {
                "d_range": [5, 15],
                "sigma_color_range": [25, 75],
                "sigma_space_range": [25, 75],
                "default_d": 9,
                "default_sigma_color": 75,
                "default_sigma_space": 75
            }
        }
        
        # 变换配置
        self.transform_config = {
            TransformType.ROTATE: {
                "angle_range": [-360, 360],
                "default_angle": 0
            },
            TransformType.RESIZE: {
                "max_width": 4096,
                "max_height": 4096,
                "min_width": 16,
                "min_height": 16
            },
            TransformType.CROP: {
                "min_size": 16
            }
        }
        
        # 调整配置
        self.adjustment_config = {
            AdjustmentType.BRIGHTNESS: {
                "factor_range": [0.1, 3.0],
                "default_factor": 1.0
            },
            AdjustmentType.CONTRAST: {
                "factor_range": [0.1, 3.0],
                "default_factor": 1.0
            },
            AdjustmentType.SATURATION: {
                "factor_range": [0.1, 3.0],
                "default_factor": 1.0
            },
            AdjustmentType.GAMMA: {
                "gamma_range": [0.1, 5.0],
                "default_gamma": 1.0
            }
        }
        
        # 绘制配置
        self.draw_config = {
            DrawType.TEXT: {
                "font_sizes": [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64],
                "default_font_size": 24,
                "colors": ["black", "white", "red", "green", "blue", "yellow", "cyan", "magenta"]
            },
            DrawType.RECTANGLE: {
                "line_width_range": [1, 20],
                "default_line_width": 2
            }
        }
        
        # 编辑统计
        self.edit_stats = {
            "total_edits": 0,
            "successful_edits": 0,
            "total_images_edited": 0,
            "average_edit_time": 0.0,
            "operation_usage": {},
            "filter_usage": {}
        }
    
    async def enhanced_image_editing(self, image_data: bytes,
                                    operations: List[EditOperation]) -> EditResult:
        """增强图像编辑
        
        Args:
            image_data: 原始图像数据
            operations: 编辑操作列表
            
        Returns:
            编辑结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 验证操作参数
            self._validate_edit_operations(operations)
            
            # 加载图像
            image = Image.open(io.BytesIO(image_data))
            
            # 按顺序应用编辑操作
            applied_operations = []
            for operation in sorted(operations, key=lambda x: x.order):
                try:
                    image = await self._apply_operation(image, operation)
                    applied_operations.append(operation)
                    
                    logger.debug(f"应用操作成功: {operation.operation_type.value}")
                    
                except Exception as e:
                    logger.warning(f"应用操作失败: {operation.operation_type.value}, 错误: {e}")
                    # 继续应用其他操作
                    continue
            
            # 保存编辑后的图像
            output_buffer = io.BytesIO()
            image.save(output_buffer, format="PNG", optimize=True)
            edited_image_data = output_buffer.getvalue()
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = EditResult(
                edit_id=str(uuid.uuid4()),
                original_image_id=str(uuid.uuid4()),
                edited_image_data=edited_image_data,
                applied_operations=applied_operations,
                processing_time=processing_time,
                metadata={
                    "original_size": len(image_data),
                    "edited_size": len(edited_image_data),
                    "operations_applied": len(applied_operations),
                    "operations_total": len(operations),
                    "success_rate": len(applied_operations) / len(operations) if operations else 1.0,
                    "format": "PNG"
                }
            )
            
            # 更新统计信息
            self._update_edit_stats(result, True)
            
            logger.info(f"图像编辑完成: 应用了 {len(applied_operations)}/{len(operations)} 个操作, 耗时: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"图像编辑失败: {e}")
            self._update_edit_stats(None, False)
            raise
    
    async def batch_image_editing(self, image_data_list: List[bytes],
                                 operations_list: List[List[EditOperation]]) -> BatchEditResult:
        """批量图像编辑
        
        Args:
            image_data_list: 图像数据列表
            operations_list: 编辑操作列表的列表
            
        Returns:
            批量编辑结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 验证输入
            if len(image_data_list) != len(operations_list):
                raise ValueError("图像数据列表和操作列表长度不匹配")
            
            # 并发执行编辑操作
            tasks = []
            for i, (image_data, operations) in enumerate(zip(image_data_list, operations_list)):
                task = self.enhanced_image_editing(image_data, operations)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            successful_results = []
            total_images = 0
            
            for result in results:
                if isinstance(result, EditResult):
                    successful_results.append(result)
                    total_images += 1
            
            total_time = asyncio.get_event_loop().time() - start_time
            success_rate = len(successful_results) / len(image_data_list) if image_data_list else 0.0
            
            batch_result = BatchEditResult(
                batch_id=str(uuid.uuid4()),
                results=successful_results,
                total_images=total_images,
                total_time=total_time,
                success_rate=success_rate
            )
            
            logger.info(f"批量图像编辑完成: {len(successful_results)}/{len(image_data_list)} 成功")
            
            return batch_result
            
        except Exception as e:
            logger.error(f"批量图像编辑失败: {e}")
            raise
    
    async def apply_quick_filter(self, image_data: bytes, filter_type: FilterType,
                                parameters: Dict[str, Any] = None) -> EditResult:
        """应用快速滤镜
        
        Args:
            image_data: 图像数据
            filter_type: 滤镜类型
            parameters: 滤镜参数
            
        Returns:
            编辑结果
        """
        # 创建滤镜操作
        operation = EditOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=EditOperationType.FILTER,
            parameters={
                "filter_type": filter_type.value,
                ** (parameters or {})
            },
            order=0
        )
        
        return await self.enhanced_image_editing(image_data, [operation])
    
    async def apply_basic_adjustment(self, image_data: bytes, adjustment_type: AdjustmentType,
                                    value: float) -> EditResult:
        """应用基础调整
        
        Args:
            image_data: 图像数据
            adjustment_type: 调整类型
            value: 调整值
            
        Returns:
            编辑结果
        """
        # 创建调整操作
        operation = EditOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=EditOperationType.ADJUSTMENT,
            parameters={
                "adjustment_type": adjustment_type.value,
                "value": value
            },
            order=0
        )
        
        return await self.enhanced_image_editing(image_data, [operation])
    
    def _validate_edit_operations(self, operations: List[EditOperation]):
        """验证编辑操作"""
        if not operations:
            raise ValueError("编辑操作列表不能为空")
        
        for operation in operations:
            # 验证操作类型
            if not isinstance(operation.operation_type, EditOperationType):
                raise ValueError(f"无效的操作类型: {operation.operation_type}")
            
            # 验证参数
            self._validate_operation_parameters(operation)
    
    def _validate_operation_parameters(self, operation: EditOperation):
        """验证操作参数"""
        if operation.operation_type == EditOperationType.FILTER:
            self._validate_filter_parameters(operation.parameters)
        elif operation.operation_type == EditOperationType.TRANSFORM:
            self._validate_transform_parameters(operation.parameters)
        elif operation.operation_type == EditOperationType.ADJUSTMENT:
            self._validate_adjustment_parameters(operation.parameters)
        elif operation.operation_type == EditOperationType.DRAW:
            self._validate_draw_parameters(operation.parameters)
    
    def _validate_filter_parameters(self, parameters: Dict[str, Any]):
        """验证滤镜参数"""
        filter_type = parameters.get("filter_type")
        if not filter_type:
            raise ValueError("滤镜类型不能为空")
        
        try:
            FilterType(filter_type)
        except ValueError:
            raise ValueError(f"无效的滤镜类型: {filter_type}")
    
    def _validate_transform_parameters(self, parameters: Dict[str, Any]):
        """验证变换参数"""
        transform_type = parameters.get("transform_type")
        if not transform_type:
            raise ValueError("变换类型不能为空")
        
        try:
            TransformType(transform_type)
        except ValueError:
            raise ValueError(f"无效的变换类型: {transform_type}")
    
    def _validate_adjustment_parameters(self, parameters: Dict[str, Any]):
        """验证调整参数"""
        adjustment_type = parameters.get("adjustment_type")
        if not adjustment_type:
            raise ValueError("调整类型不能为空")
        
        try:
            AdjustmentType(adjustment_type)
        except ValueError:
            raise ValueError(f"无效的调整类型: {adjustment_type}")
    
    def _validate_draw_parameters(self, parameters: Dict[str, Any]):
        """验证绘制参数"""
        draw_type = parameters.get("draw_type")
        if not draw_type:
            raise ValueError("绘制类型不能为空")
        
        try:
            DrawType(draw_type)
        except ValueError:
            raise ValueError(f"无效的绘制类型: {draw_type}")
    
    async def _apply_operation(self, image: Image.Image, operation: EditOperation) -> Image.Image:
        """应用单个操作"""
        if operation.operation_type == EditOperationType.FILTER:
            return await self._apply_filter(image, operation.parameters)
        elif operation.operation_type == EditOperationType.TRANSFORM:
            return await self._apply_transform(image, operation.parameters)
        elif operation.operation_type == EditOperationType.ADJUSTMENT:
            return await self._apply_adjustment(image, operation.parameters)
        elif operation.operation_type == EditOperationType.DRAW:
            return await self._apply_draw(image, operation.parameters)
        elif operation.operation_type == EditOperationType.COMPOSITE:
            return await self._apply_composite(image, operation.parameters)
        else:
            raise ValueError(f"不支持的操作类型: {operation.operation_type}")
    
    async def _apply_filter(self, image: Image.Image, parameters: Dict[str, Any]) -> Image.Image:
        """应用滤镜"""
        filter_type = FilterType(parameters.get("filter_type"))
        
        if filter_type == FilterType.BLUR:
            radius = parameters.get("radius", self.filter_config[FilterType.BLUR]["default_radius"])
            return image.filter(ImageFilter.BLUR)
        
        elif filter_type == FilterType.SHARPEN:
            strength = parameters.get("strength", self.filter_config[FilterType.SHARPEN]["default_strength"])
            return image.filter(ImageFilter.SHARPEN)
        
        elif filter_type == FilterType.EDGE_ENHANCE:
            return image.filter(ImageFilter.EDGE_ENHANCE)
        
        elif filter_type == FilterType.EMBOSS:
            return image.filter(ImageFilter.EMBOSS)
        
        elif filter_type == FilterType.CONTOUR:
            return image.filter(ImageFilter.CONTOUR)
        
        elif filter_type == FilterType.DETAIL:
            return image.filter(ImageFilter.DETAIL)
        
        elif filter_type == FilterType.SMOOTH:
            return image.filter(ImageFilter.SMOOTH)
        
        elif filter_type == FilterType.GAUSSIAN_BLUR:
            radius = parameters.get("radius", self.filter_config[FilterType.GAUSSIAN_BLUR]["default_radius"])
            return image.filter(ImageFilter.GaussianBlur(radius=radius))
        
        elif filter_type == FilterType.MEDIAN_BLUR:
            # 使用OpenCV实现中值滤波
            cv_image = np.array(image)
            radius = parameters.get("radius", self.filter_config[FilterType.MEDIAN_BLUR]["default_radius"])
            ksize = max(1, radius * 2 + 1)  # 确保为奇数
            filtered = cv2.medianBlur(cv_image, ksize)
            return Image.fromarray(filtered)
        
        elif filter_type == FilterType.BILATERAL_FILTER:
            # 使用OpenCV实现双边滤波
            cv_image = np.array(image)
            d = parameters.get("d", self.filter_config[FilterType.BILATERAL_FILTER]["default_d"])
            sigma_color = parameters.get("sigma_color", self.filter_config[FilterType.BILATERAL_FILTER]["default_sigma_color"])
            sigma_space = parameters.get("sigma_space", self.filter_config[FilterType.BILATERAL_FILTER]["default_sigma_space"])
            filtered = cv2.bilateralFilter(cv_image, d, sigma_color, sigma_space)
            return Image.fromarray(filtered)
        
        else:
            return image
    
    async def _apply_transform(self, image: Image.Image, parameters: Dict[str, Any]) -> Image.Image:
        """应用变换"""
        transform_type = TransformType(parameters.get("transform_type"))
        
        if transform_type == TransformType.ROTATE:
            angle = parameters.get("angle", self.transform_config[TransformType.ROTATE]["default_angle"])
            expand = parameters.get("expand", True)
            return image.rotate(angle, expand=expand, resample=Image.Resampling.BICUBIC)
        
        elif transform_type == TransformType.CROP:
            left = parameters.get("left", 0)
            top = parameters.get("top", 0)
            right = parameters.get("right", image.width)
            bottom = parameters.get("bottom", image.height)
            
            # 验证裁剪区域
            if left < 0 or top < 0 or right > image.width or bottom > image.height:
                raise ValueError("裁剪区域超出图像边界")
            
            if right - left < self.transform_config[TransformType.CROP]["min_size"]:
                raise ValueError("裁剪宽度太小")
            
            if bottom - top < self.transform_config[TransformType.CROP]["min_size"]:
                raise ValueError("裁剪高度太小")
            
            return image.crop((left, top, right, bottom))
        
        elif transform_type == TransformType.RESIZE:
            width = parameters.get("width", image.width)
            height = parameters.get("height", image.height)
            
            # 验证尺寸
            max_width = self.transform_config[TransformType.RESIZE]["max_width"]
            max_height = self.transform_config[TransformType.RESIZE]["max_height"]
            min_width = self.transform_config[TransformType.RESIZE]["min_width"]
            min_height = self.transform_config[TransformType.RESIZE]["min_height"]
            
            if width < min_width or height < min_height:
                raise ValueError("目标尺寸太小")
            
            if width > max_width or height > max_height:
                raise ValueError("目标尺寸太大")
            
            return image.resize((width, height), Image.Resampling.LANCZOS)
        
        elif transform_type == TransformType.FLIP:
            flip_type = parameters.get("flip_type", "horizontal")
            if flip_type == "horizontal":
                return image.transpose(Image.FLIP_LEFT_RIGHT)
            elif flip_type == "vertical":
                return image.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                return image
        
        elif transform_type == TransformType.PERSPECTIVE:
            # 透视变换（使用OpenCV）
            cv_image = np.array(image)
            
            # 获取源点和目标点
            src_points = parameters.get("src_points", [[0, 0], [image.width, 0], [image.width, image.height], [0, image.height]])
            dst_points = parameters.get("dst_points", [[0, 0], [image.width, 0], [image.width, image.height], [0, image.height]])
            
            src_pts = np.array(src_points, dtype=np.float32)
            dst_pts = np.array(dst_points, dtype=np.float32)
            
            # 计算透视变换矩阵
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            
            # 应用透视变换
            transformed = cv2.warpPerspective(cv_image, matrix, (image.width, image.height))
            
            return Image.fromarray(transformed)
        
        else:
            return image
    
    async def _apply_adjustment(self, image: Image.Image, parameters: Dict[str, Any]) -> Image.Image:
        """应用调整"""
        adjustment_type = AdjustmentType(parameters.get("adjustment_type"))
        
        if adjustment_type == AdjustmentType.BRIGHTNESS:
            factor = parameters.get("factor", self.adjustment_config[AdjustmentType.BRIGHTNESS]["default_factor"])
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(factor)
        
        elif adjustment_type == AdjustmentType.CONTRAST:
            factor = parameters.get("factor", self.adjustment_config[AdjustmentType.CONTRAST]["default_factor"])
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(factor)
        
        elif adjustment_type == AdjustmentType.SATURATION:
            factor = parameters.get("factor", self.adjustment_config[AdjustmentType.SATURATION]["default_factor"])
            enhancer = ImageEnhance.Color(image)
            return enhancer.enhance(factor)
        
        elif adjustment_type == AdjustmentType.GAMMA:
            gamma = parameters.get("gamma", self.adjustment_config[AdjustmentType.GAMMA]["default_gamma"])
            
            # 伽马校正
            gamma_corrected = np.array(image, dtype=np.float32) / 255.0
            gamma_corrected = np.power(gamma_corrected, gamma)
            gamma_corrected = (gamma_corrected * 255).astype(np.uint8)
            
            return Image.fromarray(gamma_corrected)
        
        elif adjustment_type == AdjustmentType.EXPOSURE:
            # 曝光调整（使用OpenCV）
            cv_image = np.array(image)
            exposure = parameters.get("exposure", 0.0)
            
            # 转换为HSV空间调整亮度
            hsv = cv2.cvtColor(cv_image, cv2.COLOR_RGB2HSV)
            h, s, v = cv2.split(hsv)
            
            # 调整亮度（V通道）
            v = cv2.add(v, exposure)
            v = np.clip(v, 0, 255)
            
            hsv = cv2.merge([h, s, v])
            adjusted = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            
            return Image.fromarray(adjusted)
        
        else:
            return image
    
    async def _apply_draw(self, image: Image.Image, parameters: Dict[str, Any]) -> Image.Image:
        """应用绘制"""
        draw_type = DrawType(parameters.get("draw_type"))
        draw = ImageDraw.Draw(image)
        
        if draw_type == DrawType.TEXT:
            text = parameters.get("text", "")
            position = parameters.get("position", [10, 10])
            font_size = parameters.get("font_size", self.draw_config[DrawType.TEXT]["default_font_size"])
            color = parameters.get("color", "black")
            
            # 加载字体
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            draw.text(position, text, fill=color, font=font)
            
        elif draw_type == DrawType.RECTANGLE:
            bbox = parameters.get("bbox", [10, 10, 100, 100])
            outline = parameters.get("outline", "black")
            fill = parameters.get("fill", None)
            width = parameters.get("width", self.draw_config[DrawType.RECTANGLE]["default_line_width"])
            
            draw.rectangle(bbox, outline=outline, fill=fill, width=width)
        
        elif draw_type == DrawType.CIRCLE:
            center = parameters.get("center", [50, 50])
            radius = parameters.get("radius", 25)
            outline = parameters.get("outline", "black")
            fill = parameters.get("fill", None)
            width = parameters.get("width", 2)
            
            bbox = [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius]
            draw.ellipse(bbox, outline=outline, fill=fill, width=width)
        
        elif draw_type == DrawType.LINE:
            points = parameters.get("points", [[10, 10], [100, 100]])
            color = parameters.get("color", "black")
            width = parameters.get("width", 2)
            
            draw.line(points, fill=color, width=width)
        
        return image
    
    async def _apply_composite(self, image: Image.Image, parameters: Dict[str, Any]) -> Image.Image:
        """应用合成"""
        # 这里可以实现图像合成功能
        # 暂时返回原始图像
        return image
    
    def _update_edit_stats(self, result: Optional[EditResult], success: bool):
        """更新编辑统计"""
        self.edit_stats["total_edits"] += 1
        
        if success and result:
            self.edit_stats["successful_edits"] += 1
            self.edit_stats["total_images_edited"] += 1
            
            # 更新平均编辑时间
            total_time = self.edit_stats["average_edit_time"] * (self.edit_stats["total_edits"] - 1)
            total_time += result.processing_time
            self.edit_stats["average_edit_time"] = total_time / self.edit_stats["total_edits"]
            
            # 更新操作使用统计
            for operation in result.applied_operations:
                op_type = operation.operation_type.value
                if op_type not in self.edit_stats["operation_usage"]:
                    self.edit_stats["operation_usage"][op_type] = 0
                self.edit_stats["operation_usage"][op_type] += 1
                
                # 如果是滤镜操作，更新滤镜使用统计
                if op_type == "filter":
                    filter_type = operation.parameters.get("filter_type")
                    if filter_type not in self.edit_stats["filter_usage"]:
                        self.edit_stats["filter_usage"][filter_type] = 0
                    self.edit_stats["filter_usage"][filter_type] += 1
    
    def get_edit_report(self) -> Dict[str, Any]:
        """获取编辑报告"""
        success_rate = 0.0
        if self.edit_stats["total_edits"] > 0:
            success_rate = (self.edit_stats["successful_edits"] / 
                          self.edit_stats["total_edits"]) * 100
        
        return {
            "success_rate": success_rate,
            "average_edit_time": self.edit_stats["average_edit_time"],
            "total_edits": self.edit_stats["total_edits"],
            "successful_edits": self.edit_stats["successful_edits"],
            "total_images_edited": self.edit_stats["total_images_edited"],
            "operation_usage": self.edit_stats["operation_usage"],
            "filter_usage": self.edit_stats["filter_usage"]
        }
    
    def create_filter_operation(self, filter_type: FilterType, parameters: Dict[str, Any] = None) -> EditOperation:
        """创建滤镜操作"""
        return EditOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=EditOperationType.FILTER,
            parameters={
                "filter_type": filter_type.value,
                ** (parameters or {})
            },
            order=0
        )
    
    def create_adjustment_operation(self, adjustment_type: AdjustmentType, value: float) -> EditOperation:
        """创建调整操作"""
        return EditOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=EditOperationType.ADJUSTMENT,
            parameters={
                "adjustment_type": adjustment_type.value,
                "value": value
            },
            order=0
        )
    
    def create_transform_operation(self, transform_type: TransformType, parameters: Dict[str, Any]) -> EditOperation:
        """创建变换操作"""
        return EditOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=EditOperationType.TRANSFORM,
            parameters={
                "transform_type": transform_type.value,
                **parameters
            },
            order=0
        )


# 创建全局图像编辑器实例
image_editor = ImageEditor()