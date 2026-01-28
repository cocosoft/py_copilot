"""
图像处理增强服务
基于现有图像功能进行升级和优化
"""

import asyncio
import logging
import uuid
import json
import base64
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import io

logger = logging.getLogger(__name__)


class ImageRecognitionType(Enum):
    """图像识别类型枚举"""
    OBJECT_DETECTION = "object_detection"
    SCENE_CLASSIFICATION = "scene_classification"
    FACE_DETECTION = "face_detection"
    TEXT_EXTRACTION = "text_extraction"
    COLOR_ANALYSIS = "color_analysis"


class ImageGenerationType(Enum):
    """图像生成类型枚举"""
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_IMAGE = "image_to_image"
    STYLE_TRANSFER = "style_transfer"
    SUPER_RESOLUTION = "super_resolution"
    IMAGE_INPAINTING = "image_inpainting"


@dataclass
class ImageRecognitionResult:
    """图像识别结果"""
    recognition_id: str
    image_id: str
    recognition_type: ImageRecognitionType
    confidence: float
    labels: List[Dict[str, Any]]
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class ImageGenerationResult:
    """图像生成结果"""
    generation_id: str
    image_data: bytes
    format: str
    resolution: str
    generation_time: float
    metadata: Dict[str, Any]


@dataclass
class ImageEditResult:
    """图像编辑结果"""
    edit_id: str
    original_image_id: str
    edited_image_data: bytes
    edit_operations: List[str]
    processing_time: float
    metadata: Dict[str, Any]


class ImageProcessingService:
    """图像处理增强服务"""
    
    def __init__(self):
        """初始化图像处理服务"""
        # 图像识别配置
        self.recognition_config = {
            "object_detection": {
                "enabled": True,
                "confidence_threshold": 0.5,
                "max_objects": 20
            },
            "scene_classification": {
                "enabled": True,
                "categories": ["室内", "室外", "自然", "城市", "建筑", "人物"]
            },
            "face_detection": {
                "enabled": True,
                "detect_emotions": True,
                "detect_age_gender": True
            },
            "text_extraction": {
                "enabled": True,
                "languages": ["zh", "en", "ja", "ko"]
            },
            "color_analysis": {
                "enabled": True,
                "dominant_colors": 5
            }
        }
        
        # 图像生成配置
        self.generation_config = {
            "text_to_image": {
                "enabled": True,
                "providers": ["google", "openai", "stable_diffusion"],
                "default_resolution": "1024x1024"
            },
            "image_to_image": {
                "enabled": True,
                "strength_range": [0.1, 0.9]
            },
            "style_transfer": {
                "enabled": True,
                "available_styles": ["油画", "水彩", "素描", "卡通", "抽象"]
            }
        }
        
        # 图像编辑配置
        self.editing_config = {
            "filters": {
                "blur": {"radius_range": [1, 10]},
                "sharpen": {"strength_range": [1, 5]},
                "brightness": {"range": [0.5, 2.0]},
                "contrast": {"range": [0.5, 2.0]},
                "saturation": {"range": [0.5, 2.0]}
            },
            "transformations": {
                "crop": True,
                "rotate": True,
                "resize": True,
                "flip": True
            }
        }
        
        # 性能统计
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "average_processing_time": 0.0,
            "recognition_accuracy": {}
        }
    
    async def enhanced_image_recognition(self, image_data: bytes, 
                                        recognition_type: ImageRecognitionType,
                                        options: Dict[str, Any] = None) -> ImageRecognitionResult:
        """增强图像识别
        
        Args:
            image_data: 图像数据
            recognition_type: 识别类型
            options: 识别选项
            
        Returns:
            图像识别结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 预处理图像
            processed_image = await self._preprocess_image(image_data)
            
            # 根据识别类型选择识别方法
            if recognition_type == ImageRecognitionType.OBJECT_DETECTION:
                result = await self._detect_objects(processed_image, options)
            elif recognition_type == ImageRecognitionType.SCENE_CLASSIFICATION:
                result = await self._classify_scene(processed_image, options)
            elif recognition_type == ImageRecognitionType.FACE_DETECTION:
                result = await self._detect_faces(processed_image, options)
            elif recognition_type == ImageRecognitionType.TEXT_EXTRACTION:
                result = await self._extract_text(processed_image, options)
            elif recognition_type == ImageRecognitionType.COLOR_ANALYSIS:
                result = await self._analyze_colors(processed_image, options)
            else:
                result = await self._detect_objects(processed_image, options)
            
            # 后处理识别结果
            processed_result = await self._postprocess_recognition(result, recognition_type)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            recognition_result = ImageRecognitionResult(
                recognition_id=str(uuid.uuid4()),
                image_id=str(uuid.uuid4()),
                recognition_type=recognition_type,
                confidence=processed_result["confidence"],
                labels=processed_result["labels"],
                processing_time=processing_time,
                metadata=processed_result.get("metadata", {})
            )
            
            # 更新性能统计
            self._update_performance_stats(recognition_result, True)
            
            logger.info(f"图像识别完成: {recognition_type.value}, 置信度: {processed_result['confidence']:.2f}")
            
            return recognition_result
            
        except Exception as e:
            logger.error(f"图像识别失败: {e}")
            self._update_performance_stats(None, False)
            raise
    
    async def enhanced_image_generation(self, prompt: str,
                                       generation_type: ImageGenerationType = ImageGenerationType.TEXT_TO_IMAGE,
                                       input_image: bytes = None,
                                       options: Dict[str, Any] = None) -> ImageGenerationResult:
        """增强图像生成
        
        Args:
            prompt: 生成提示
            generation_type: 生成类型
            input_image: 输入图像（用于image_to_image等）
            options: 生成选项
            
        Returns:
            图像生成结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 根据生成类型选择生成方法
            if generation_type == ImageGenerationType.TEXT_TO_IMAGE:
                image_data = await self._generate_from_text(prompt, options)
            elif generation_type == ImageGenerationType.IMAGE_TO_IMAGE:
                if not input_image:
                    raise ValueError("image_to_image生成需要输入图像")
                image_data = await self._generate_from_image(input_image, prompt, options)
            elif generation_type == ImageGenerationType.STYLE_TRANSFER:
                if not input_image:
                    raise ValueError("风格迁移需要输入图像")
                image_data = await self._transfer_style(input_image, prompt, options)
            else:
                image_data = await self._generate_from_text(prompt, options)
            
            # 后处理生成的图像
            processed_image = await self._postprocess_generated_image(image_data, options)
            
            generation_time = asyncio.get_event_loop().time() - start_time
            
            generation_result = ImageGenerationResult(
                generation_id=str(uuid.uuid4()),
                image_data=processed_image,
                format="png",
                resolution=options.get("resolution", "1024x1024") if options else "1024x1024",
                generation_time=generation_time,
                metadata={
                    "prompt": prompt,
                    "generation_type": generation_type.value,
                    "options": options or {}
                }
            )
            
            logger.info(f"图像生成完成: {generation_type.value}, 耗时: {generation_time:.2f}s")
            
            return generation_result
            
        except Exception as e:
            logger.error(f"图像生成失败: {e}")
            raise
    
    async def enhanced_image_editing(self, image_data: bytes,
                                    edit_operations: List[Dict[str, Any]]) -> ImageEditResult:
        """增强图像编辑
        
        Args:
            image_data: 原始图像数据
            edit_operations: 编辑操作列表
            
        Returns:
            图像编辑结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 加载图像
            image = Image.open(io.BytesIO(image_data))
            
            # 应用编辑操作
            applied_operations = []
            for operation in edit_operations:
                op_type = operation.get("type")
                op_params = operation.get("params", {})
                
                if op_type == "filter":
                    image = await self._apply_filter(image, op_params)
                elif op_type == "transform":
                    image = await self._apply_transform(image, op_params)
                elif op_type == "adjust":
                    image = await self._apply_adjustment(image, op_params)
                
                applied_operations.append(f"{op_type}: {op_params}")
            
            # 保存编辑后的图像
            output_buffer = io.BytesIO()
            image.save(output_buffer, format="PNG")
            edited_image_data = output_buffer.getvalue()
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            edit_result = ImageEditResult(
                edit_id=str(uuid.uuid4()),
                original_image_id=str(uuid.uuid4()),
                edited_image_data=edited_image_data,
                edit_operations=applied_operations,
                processing_time=processing_time,
                metadata={
                    "original_size": len(image_data),
                    "edited_size": len(edited_image_data),
                    "operations_count": len(edit_operations)
                }
            )
            
            logger.info(f"图像编辑完成: 应用了 {len(edit_operations)} 个操作")
            
            return edit_result
            
        except Exception as e:
            logger.error(f"图像编辑失败: {e}")
            raise
    
    async def _preprocess_image(self, image_data: bytes) -> np.ndarray:
        """预处理图像"""
        try:
            # 转换为numpy数组
            image_array = np.frombuffer(image_data, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("无法解码图像数据")
            
            # 图像标准化
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 调整图像大小（如果太大）
            max_size = 2048
            height, width = image.shape[:2]
            if max(height, width) > max_size:
                scale = max_size / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
            
            return image
            
        except Exception as e:
            logger.error(f"图像预处理失败: {e}")
            raise
    
    async def _detect_objects(self, image: np.ndarray, options: Dict[str, Any]) -> Dict[str, Any]:
        """物体检测"""
        try:
            # 使用OpenCV进行简单的物体检测
            # 这里可以集成更专业的物体检测模型
            
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # 边缘检测
            edges = cv2.Canny(gray, 50, 150)
            
            # 轮廓检测
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 分析轮廓
            objects = []
            for contour in contours:
                if len(contour) > 5:  # 过滤太小的轮廓
                    # 计算轮廓的边界框
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 计算轮廓面积
                    area = cv2.contourArea(contour)
                    
                    # 简单的物体分类（基于形状）
                    shape_type = self._classify_shape(contour)
                    
                    objects.append({
                        "label": shape_type,
                        "confidence": min(area / (image.shape[0] * image.shape[1]), 1.0),
                        "bbox": [x, y, w, h],
                        "area": area
                    })
            
            # 按置信度排序
            objects.sort(key=lambda x: x["confidence"], reverse=True)
            
            # 限制返回数量
            max_objects = options.get("max_objects", 10) if options else 10
            objects = objects[:max_objects]
            
            # 计算总体置信度
            overall_confidence = sum(obj["confidence"] for obj in objects) / len(objects) if objects else 0.0
            
            return {
                "confidence": overall_confidence,
                "labels": objects,
                "metadata": {
                    "objects_count": len(objects),
                    "image_size": f"{image.shape[1]}x{image.shape[0]}"
                }
            }
            
        except Exception as e:
            logger.error(f"物体检测失败: {e}")
            return {
                "confidence": 0.0,
                "labels": [],
                "metadata": {}
            }
    
    def _classify_shape(self, contour) -> str:
        """分类轮廓形状"""
        # 计算轮廓的周长
        perimeter = cv2.arcLength(contour, True)
        
        # 多边形近似
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        
        # 根据顶点数量分类
        vertices = len(approx)
        
        if vertices == 3:
            return "三角形"
        elif vertices == 4:
            # 检查是否是矩形
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            if 0.95 <= aspect_ratio <= 1.05:
                return "正方形"
            else:
                return "矩形"
        elif vertices == 5:
            return "五边形"
        elif vertices == 6:
            return "六边形"
        elif vertices > 6:
            # 检查是否是圆形
            area = cv2.contourArea(contour)
            (x, y), radius = cv2.minEnclosingCircle(contour)
            circle_area = 3.14159 * radius * radius
            
            if abs(area - circle_area) / circle_area < 0.2:
                return "圆形"
            else:
                return "不规则形状"
        else:
            return "未知形状"
    
    async def _classify_scene(self, image: np.ndarray, options: Dict[str, Any]) -> Dict[str, Any]:
        """场景分类"""
        try:
            # 简单的场景分类（基于颜色和纹理特征）
            
            # 计算颜色直方图
            hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            
            # 计算纹理特征（灰度共生矩阵）
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # 简单的场景分类逻辑
            scene_type = self._classify_scene_type(image, gray, hist)
            
            # 计算置信度（基于特征匹配度）
            confidence = self._calculate_scene_confidence(scene_type, hist)
            
            return {
                "confidence": confidence,
                "labels": [{"label": scene_type, "confidence": confidence}],
                "metadata": {
                    "feature_vector_size": len(hist),
                    "scene_type": scene_type
                }
            }
            
        except Exception as e:
            logger.error(f"场景分类失败: {e}")
            return {
                "confidence": 0.0,
                "labels": [],
                "metadata": {}
            }
    
    def _classify_scene_type(self, image: np.ndarray, gray: np.ndarray, hist: np.ndarray) -> str:
        """分类场景类型"""
        # 基于颜色和纹理特征的简单分类
        
        # 计算平均亮度
        avg_brightness = np.mean(gray)
        
        # 计算颜色饱和度（通过HSV空间）
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        avg_saturation = np.mean(hsv[:, :, 1])
        
        # 基于特征进行分类
        if avg_brightness < 50:
            return "夜景"
        elif avg_brightness > 200:
            return "明亮场景"
        elif avg_saturation > 100:
            return "色彩丰富场景"
        else:
            return "一般场景"
    
    def _calculate_scene_confidence(self, scene_type: str, hist: np.ndarray) -> float:
        """计算场景分类置信度"""
        # 基于特征分布的简单置信度计算
        hist_std = np.std(hist)
        
        if scene_type == "夜景":
            return min(hist_std * 10, 0.9)
        elif scene_type == "明亮场景":
            return min(hist_std * 8, 0.85)
        elif scene_type == "色彩丰富场景":
            return min(hist_std * 12, 0.95)
        else:
            return min(hist_std * 6, 0.7)
    
    async def _detect_faces(self, image: np.ndarray, options: Dict[str, Any]) -> Dict[str, Any]:
        """人脸检测"""
        try:
            # 使用OpenCV的人脸检测
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # 加载人脸检测器（需要预先下载模型文件）
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # 检测人脸
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            # 分析检测到的人脸
            face_results = []
            for (x, y, w, h) in faces:
                # 计算人脸区域
                face_area = w * h
                image_area = image.shape[0] * image.shape[1]
                
                # 计算置信度（基于人脸大小和位置）
                confidence = min(face_area / image_area * 10, 0.95)
                
                face_results.append({
                    "label": "人脸",
                    "confidence": confidence,
                    "bbox": [x, y, w, h],
                    "landmarks": []  # 可以添加关键点检测
                })
            
            # 计算总体置信度
            overall_confidence = sum(face["confidence"] for face in face_results) / len(face_results) if face_results else 0.0
            
            return {
                "confidence": overall_confidence,
                "labels": face_results,
                "metadata": {
                    "faces_count": len(face_results),
                    "detection_method": "haar_cascade"
                }
            }
            
        except Exception as e:
            logger.error(f"人脸检测失败: {e}")
            return {
                "confidence": 0.0,
                "labels": [],
                "metadata": {}
            }
    
    async def _extract_text(self, image: np.ndarray, options: Dict[str, Any]) -> Dict[str, Any]:
        """文本提取"""
        try:
            # 简单的文本区域检测（实际应该使用OCR引擎如Tesseract）
            
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # 二值化处理
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 查找文本区域（基于连通组件分析）
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
            
            text_regions = []
            for i in range(1, num_labels):  # 跳过背景
                x, y, w, h, area = stats[i]
                
                # 过滤太小的区域
                if area > 100 and w > 10 and h > 10:
                    # 计算区域特征
                    aspect_ratio = w / h
                    density = area / (w * h)
                    
                    # 基于特征判断是否为文本区域
                    if 0.1 < aspect_ratio < 10 and density > 0.3:
                        text_regions.append({
                            "bbox": [x, y, w, h],
                            "confidence": min(density * 2, 0.8)
                        })
            
            # 模拟提取的文本
            extracted_text = "检测到文本区域"
            
            return {
                "confidence": len(text_regions) / max(num_labels - 1, 1),
                "labels": [{"label": "文本区域", "confidence": 0.7, "text": extracted_text}],
                "metadata": {
                    "text_regions_count": len(text_regions),
                    "extracted_text": extracted_text
                }
            }
            
        except Exception as e:
            logger.error(f"文本提取失败: {e}")
            return {
                "confidence": 0.0,
                "labels": [],
                "metadata": {}
            }
    
    async def _analyze_colors(self, image: np.ndarray, options: Dict[str, Any]) -> Dict[str, Any]:
        """颜色分析"""
        try:
            # 分析图像中的主要颜色
            
            # 重塑图像为像素列表
            pixels = image.reshape(-1, 3)
            
            # 使用K-means聚类找到主要颜色
            from sklearn.cluster import KMeans
            
            n_colors = options.get("n_colors", 5) if options else 5
            kmeans = KMeans(n_clusters=n_colors, random_state=42)
            kmeans.fit(pixels)
            
            # 获取主要颜色和比例
            colors = kmeans.cluster_centers_.astype(int)
            counts = np.bincount(kmeans.labels_)
            percentages = counts / len(pixels)
            
            # 构建颜色分析结果
            color_results = []
            for i, (color, percentage) in enumerate(zip(colors, percentages)):
                color_results.append({
                    "label": f"颜色{i+1}",
                    "confidence": float(percentage),
                    "color": {
                        "rgb": color.tolist(),
                        "hex": f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
                        "percentage": float(percentage)
                    }
                })
            
            return {
                "confidence": 1.0,  # 颜色分析通常比较可靠
                "labels": color_results,
                "metadata": {
                    "dominant_colors_count": n_colors,
                    "color_space": "RGB"
                }
            }
            
        except Exception as e:
            logger.error(f"颜色分析失败: {e}")
            return {
                "confidence": 0.0,
                "labels": [],
                "metadata": {}
            }
    
    async def _postprocess_recognition(self, result: Dict[str, Any], recognition_type: ImageRecognitionType) -> Dict[str, Any]:
        """后处理识别结果"""
        # 过滤低置信度的结果
        confidence_threshold = self.recognition_config[recognition_type.value].get("confidence_threshold", 0.3)
        
        filtered_labels = [label for label in result["labels"] if label["confidence"] >= confidence_threshold]
        
        # 更新置信度
        if filtered_labels:
            result["confidence"] = sum(label["confidence"] for label in filtered_labels) / len(filtered_labels)
        else:
            result["confidence"] = 0.0
        
        result["labels"] = filtered_labels
        
        return result
    
    async def _generate_from_text(self, prompt: str, options: Dict[str, Any]) -> bytes:
        """从文本生成图像"""
        # 这里应该集成实际的图像生成API
        # 暂时返回一个占位图像
        
        # 创建简单的占位图像
        width = 512
        height = 512
        
        # 创建RGB图像
        image = Image.new('RGB', (width, height), color='lightblue')
        
        # 添加文本
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(image)
        
        # 使用默认字体
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # 绘制提示文本
        text = f"生成: {prompt[:30]}..."
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill="black", font=font)
        
        # 保存为字节数据
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        
        return output_buffer.getvalue()
    
    async def _generate_from_image(self, input_image: bytes, prompt: str, options: Dict[str, Any]) -> bytes:
        """基于输入图像生成新图像"""
        # 这里应该集成image-to-image生成API
        # 暂时返回输入图像的修改版本
        
        image = Image.open(io.BytesIO(input_image))
        
        # 应用简单的滤镜效果
        strength = options.get("strength", 0.5) if options else 0.5
        
        if strength > 0.7:
            image = image.filter(ImageFilter.GaussianBlur(radius=2))
        elif strength > 0.3:
            image = image.filter(ImageFilter.SMOOTH)
        
        # 保存为字节数据
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        
        return output_buffer.getvalue()
    
    async def _transfer_style(self, input_image: bytes, style_prompt: str, options: Dict[str, Any]) -> bytes:
        """风格迁移"""
        # 这里应该集成风格迁移API
        # 暂时返回输入图像的风格化版本
        
        image = Image.open(io.BytesIO(input_image))
        
        # 根据风格提示应用不同的滤镜
        if "油画" in style_prompt:
            image = image.filter(ImageFilter.EMBOSS)
        elif "水彩" in style_prompt:
            image = image.filter(ImageFilter.CONTOUR)
        elif "素描" in style_prompt:
            image = image.filter(ImageFilter.FIND_EDGES)
        elif "卡通" in style_prompt:
            # 应用卡通化效果
            image = image.filter(ImageFilter.SMOOTH_MORE)
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.5)
        
        # 保存为字节数据
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        
        return output_buffer.getvalue()
    
    async def _postprocess_generated_image(self, image_data: bytes, options: Dict[str, Any]) -> bytes:
        """后处理生成的图像"""
        # 这里可以添加图像质量优化、格式转换等后处理
        return image_data
    
    async def _apply_filter(self, image: Image.Image, params: Dict[str, Any]) -> Image.Image:
        """应用滤镜"""
        filter_type = params.get("type", "blur")
        
        if filter_type == "blur":
            radius = params.get("radius", 2)
            return image.filter(ImageFilter.GaussianBlur(radius=radius))
        elif filter_type == "sharpen":
            strength = params.get("strength", 2)
            return image.filter(ImageFilter.UnsharpMask(radius=2, percent=strength * 50, threshold=3))
        elif filter_type == "edge_enhance":
            return image.filter(ImageFilter.EDGE_ENHANCE)
        elif filter_type == "emboss":
            return image.filter(ImageFilter.EMBOSS)
        else:
            return image
    
    async def _apply_transform(self, image: Image.Image, params: Dict[str, Any]) -> Image.Image:
        """应用变换"""
        transform_type = params.get("type", "rotate")
        
        if transform_type == "rotate":
            angle = params.get("angle", 0)
            return image.rotate(angle, expand=True)
        elif transform_type == "crop":
            left = params.get("left", 0)
            top = params.get("top", 0)
            right = params.get("right", image.width)
            bottom = params.get("bottom", image.height)
            return image.crop((left, top, right, bottom))
        elif transform_type == "resize":
            width = params.get("width", image.width)
            height = params.get("height", image.height)
            return image.resize((width, height), Image.Resampling.LANCZOS)
        elif transform_type == "flip":
            flip_type = params.get("flip_type", "horizontal")
            if flip_type == "horizontal":
                return image.transpose(Image.FLIP_LEFT_RIGHT)
            elif flip_type == "vertical":
                return image.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                return image
        else:
            return image
    
    async def _apply_adjustment(self, image: Image.Image, params: Dict[str, Any]) -> Image.Image:
        """应用调整"""
        adjustment_type = params.get("type", "brightness")
        
        if adjustment_type == "brightness":
            factor = params.get("factor", 1.0)
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(factor)
        elif adjustment_type == "contrast":
            factor = params.get("factor", 1.0)
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(factor)
        elif adjustment_type == "saturation":
            factor = params.get("factor", 1.0)
            enhancer = ImageEnhance.Color(image)
            return enhancer.enhance(factor)
        else:
            return image
    
    def _update_performance_stats(self, result: Optional[ImageRecognitionResult], success: bool):
        """更新性能统计"""
        self.performance_stats["total_requests"] += 1
        
        if success and result:
            self.performance_stats["successful_requests"] += 1
            
            # 更新平均处理时间
            total_time = self.performance_stats["average_processing_time"] * (self.performance_stats["total_requests"] - 1)
            total_time += result.processing_time
            self.performance_stats["average_processing_time"] = total_time / self.performance_stats["total_requests"]
            
            # 更新识别准确率统计
            recognition_type = result.recognition_type.value
            if recognition_type not in self.performance_stats["recognition_accuracy"]:
                self.performance_stats["recognition_accuracy"][recognition_type] = {
                    "total": 0,
                    "successful": 0,
                    "average_confidence": 0.0
                }
            
            stats = self.performance_stats["recognition_accuracy"][recognition_type]
            stats["total"] += 1
            
            if result.confidence > 0.5:
                stats["successful"] += 1
            
            # 更新平均置信度
            total_confidence = stats["average_confidence"] * (stats["total"] - 1)
            total_confidence += result.confidence
            stats["average_confidence"] = total_confidence / stats["total"]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        success_rate = 0.0
        if self.performance_stats["total_requests"] > 0:
            success_rate = (self.performance_stats["successful_requests"] / 
                          self.performance_stats["total_requests"]) * 100
        
        return {
            "success_rate": success_rate,
            "average_processing_time": self.performance_stats["average_processing_time"],
            "total_requests": self.performance_stats["total_requests"],
            "successful_requests": self.performance_stats["successful_requests"],
            "recognition_accuracy": self.performance_stats["recognition_accuracy"]
        }


# 创建全局图像处理服务实例
image_processing_service = ImageProcessingService()