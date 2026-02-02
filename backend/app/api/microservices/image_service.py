"""图像服务微服务

提供图像处理、分析和识别功能
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import uuid
import io
import os
from pathlib import Path

from app.core.microservices import MicroserviceConfig, get_service_registry, get_message_queue


class ImageAnalysisResponse(BaseModel):
    """图像分析响应模型"""
    image_id: str
    analysis_type: str
    results: Dict[str, Any]
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None


class ImageProcessRequest(BaseModel):
    """图像处理请求模型"""
    image_id: str
    operations: List[Dict[str, Any]]
    output_format: str = "jpg"


class ImageProcessResponse(BaseModel):
    """图像处理响应模型"""
    processed_image_id: str
    original_image_id: str
    operations: List[Dict[str, Any]]
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None


class ImageService:
    """图像服务管理器"""
    
    def __init__(self):
        self.service_registry = get_service_registry()
        self.message_queue = get_message_queue()
        self.upload_dir = Path("uploads/images")
        self.upload_dir.mkdir(exist_ok=True, parents=True)
        self.processed_dir = Path("uploads/processed_images")
        self.processed_dir.mkdir(exist_ok=True, parents=True)
    
    async def analyze_image(self, image_file: UploadFile, analysis_type: str = "general") -> ImageAnalysisResponse:
        """分析图像"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 读取图像文件
            image_content = await image_file.read()
            
            # 验证图像格式
            if not self._validate_image_format(image_content):
                raise HTTPException(status_code=400, detail="不支持的图像格式")
            
            # 保存图像
            image_id = str(uuid.uuid4())
            image_path = self.upload_dir / f"{image_id}.{self._get_image_extension(image_file.filename)}"
            
            with open(image_path, "wb") as f:
                f.write(image_content)
            
            # 分析图像
            analysis_results = await self._analyze_image_content(image_content, analysis_type)
            
            # 处理图像分析结果（异步）
            asyncio.create_task(self._process_analysis_results(
                image_id, analysis_type, analysis_results
            ))
            
            # 计算处理时间
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # 创建图像记录
            from app.models.chat_enhancements import AnalyzedImage
            from app.core.database import get_db
            
            db = next(get_db())
            try:
                analyzed_image = AnalyzedImage(
                    image_id=image_id,
                    filename=image_file.filename or "unknown",
                    file_path=str(image_path),
                    analysis_type=analysis_type,
                    analysis_results=str(analysis_results),
                    processing_status="completed"
                )
                db.add(analyzed_image)
                db.commit()
                db.refresh(analyzed_image)
                
                return ImageAnalysisResponse(
                    image_id=image_id,
                    analysis_type=analysis_type,
                    results=analysis_results,
                    processing_time=processing_time,
                    metadata={
                        "filename": image_file.filename,
                        "image_size": len(image_content)
                    }
                )
            finally:
                db.close()
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"图像分析失败: {str(e)}")
    
    async def process_image(self, process_request: ImageProcessRequest) -> ImageProcessResponse:
        """处理图像"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 查找原始图像
            original_image_path = None
            for ext in ["jpg", "jpeg", "png", "gif"]:
                candidate_path = self.upload_dir / f"{process_request.image_id}.{ext}"
                if candidate_path.exists():
                    original_image_path = candidate_path
                    break
            
            if not original_image_path:
                raise HTTPException(status_code=404, detail="原始图像未找到")
            
            # 读取原始图像
            with open(original_image_path, "rb") as f:
                image_content = f.read()
            
            # 执行图像处理操作
            processed_content = await self._apply_image_operations(
                image_content, process_request.operations
            )
            
            # 保存处理后的图像
            processed_image_id = str(uuid.uuid4())
            processed_path = self.processed_dir / f"{processed_image_id}.{process_request.output_format}"
            
            with open(processed_path, "wb") as f:
                f.write(processed_content)
            
            # 计算处理时间
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return ImageProcessResponse(
                processed_image_id=processed_image_id,
                original_image_id=process_request.image_id,
                operations=process_request.operations,
                processing_time=processing_time,
                metadata={
                    "output_format": process_request.output_format,
                    "output_size": len(processed_content)
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"图像处理失败: {str(e)}")
    
    async def get_image_info(self, image_id: str) -> Optional[Dict[str, Any]]:
        """获取图像信息"""
        from app.models.chat_enhancements import AnalyzedImage
        from app.core.database import get_db
        
        db = next(get_db())
        try:
            image_record = db.query(AnalyzedImage).filter(
                AnalyzedImage.image_id == image_id
            ).first()
            
            if image_record:
                return {
                    "image_id": image_record.image_id,
                    "filename": image_record.filename,
                    "file_path": image_record.file_path,
                    "analysis_type": image_record.analysis_type,
                    "analysis_results": eval(image_record.analysis_results),
                    "processing_status": image_record.processing_status,
                    "created_at": image_record.created_at.isoformat() if image_record.created_at else None
                }
        finally:
            db.close()
        
        return None
    
    def _validate_image_format(self, image_content: bytes) -> bool:
        """验证图像格式"""
        # 检查常见图像格式的文件头
        if len(image_content) > 8:
            # JPEG
            if image_content[:2] == b'\xff\xd8':
                return True
            # PNG
            if image_content[:8] == b'\x89PNG\r\n\x1a\n':
                return True
            # GIF
            if image_content[:6] in [b'GIF87a', b'GIF89a']:
                return True
            # BMP
            if image_content[:2] == b'BM':
                return True
        
        return False
    
    def _get_image_extension(self, filename: Optional[str]) -> str:
        """获取图像扩展名"""
        if filename:
            ext = Path(filename).suffix.lower()
            if ext in [".jpg", ".jpeg"]:
                return "jpg"
            elif ext == ".png":
                return "png"
            elif ext == ".gif":
                return "gif"
            elif ext == ".bmp":
                return "bmp"
        
        return "jpg"
    
    async def _analyze_image_content(self, image_content: bytes, analysis_type: str) -> Dict[str, Any]:
        """分析图像内容"""
        # 模拟图像分析
        await asyncio.sleep(1)  # 模拟处理时间
        
        if analysis_type == "general":
            return {
                "objects": [
                    {"name": "person", "confidence": 0.95, "bounding_box": [10, 20, 100, 200]},
                    {"name": "chair", "confidence": 0.85, "bounding_box": [150, 100, 250, 180]}
                ],
                "scenes": ["indoor", "office"],
                "colors": ["blue", "white", "gray"],
                "description": "室内办公场景，有一个人和一把椅子"
            }
        elif analysis_type == "text":
            return {
                "text_blocks": [
                    {"text": "Hello World", "confidence": 0.98, "bounding_box": [50, 50, 150, 80]},
                    {"text": "Py Copilot", "confidence": 0.95, "bounding_box": [50, 100, 120, 130]}
                ],
                "language": "en",
                "total_text_lines": 2
            }
        elif analysis_type == "face":
            return {
                "faces": [
                    {
                        "face_id": "face1",
                        "confidence": 0.99,
                        "bounding_box": [30, 30, 120, 150],
                        "attributes": {
                            "age": 30,
                            "gender": "male",
                            "emotion": "neutral"
                        }
                    }
                ],
                "total_faces": 1
            }
        else:
            return {
                "message": f"Analysis type {analysis_type} not supported",
                "supported_types": ["general", "text", "face"]
            }
    
    async def _apply_image_operations(self, image_content: bytes, operations: List[Dict[str, Any]]) -> bytes:
        """应用图像处理操作"""
        # 模拟图像处理
        await asyncio.sleep(0.5)  # 模拟处理时间
        
        # 对于模拟，我们只是返回原始内容
        # 实际应用中应该根据操作类型进行处理
        return image_content
    
    async def _process_analysis_results(self, image_id: str, analysis_type: str, results: Dict[str, Any]):
        """处理分析结果"""
        try:
            # 发布分析完成事件
            event_data = {
                "event_type": "image_analyzed",
                "image_id": image_id,
                "analysis_type": analysis_type,
                "results": results,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            await self.message_queue.publish_message("image_events", event_data)
            
        except Exception as e:
            print(f"处理分析结果错误: {e}")
    
    async def get_supported_analysis_types(self) -> List[Dict[str, Any]]:
        """获取支持的分析类型"""
        return [
            {
                "type": "general",
                "name": "通用分析",
                "description": "分析图像中的对象、场景和颜色"
            },
            {
                "type": "text",
                "name": "文本识别",
                "description": "识别图像中的文本内容"
            },
            {
                "type": "face",
                "name": "人脸分析",
                "description": "分析图像中的人脸和属性"
            }
        ]
    
    async def get_supported_operations(self) -> List[Dict[str, Any]]:
        """获取支持的操作类型"""
        return [
            {
                "operation": "resize",
                "name": "调整大小",
                "parameters": ["width", "height"]
            },
            {
                "operation": "crop",
                "name": "裁剪",
                "parameters": ["x", "y", "width", "height"]
            },
            {
                "operation": "rotate",
                "name": "旋转",
                "parameters": ["angle"]
            },
            {
                "operation": "filter",
                "name": "滤镜",
                "parameters": ["filter_type"]
            }
        ]


# 创建图像服务实例
image_service = ImageService()


# 创建图像微服务应用
image_app = FastAPI(
    title="Py Copilot Image Service",
    version="1.0.0",
    description="图像处理和分析微服务"
)


@image_app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "image"}


@image_app.post("/analyze")
async def analyze_image(
    image_file: UploadFile = File(...),
    analysis_type: str = "general"
):
    """图像分析接口"""
    response = await image_service.analyze_image(image_file, analysis_type)
    return response


@image_app.post("/process")
async def process_image(process_request: ImageProcessRequest):
    """图像处理接口"""
    response = await image_service.process_image(process_request)
    return response


@image_app.get("/images/{image_id}")
async def get_image_info(image_id: str):
    """获取图像信息接口"""
    image_info = await image_service.get_image_info(image_id)
    if not image_info:
        raise HTTPException(status_code=404, detail="图像未找到")
    return image_info


@image_app.get("/analysis-types")
async def get_analysis_types():
    """获取支持的分析类型"""
    types = await image_service.get_supported_analysis_types()
    return {"types": types}


@image_app.get("/operations")
async def get_operations():
    """获取支持的操作类型"""
    operations = await image_service.get_supported_operations()
    return {"operations": operations}


@image_app.get("/statistics")
async def get_statistics():
    """获取图像服务统计信息"""
    return {
        "total_analyses": 0,
        "average_processing_time": 0,
        "processed_images": 0
    }


@image_app.on_event("startup")
async def startup_event():
    """服务启动事件"""
    # 注册服务到服务注册中心
    config = MicroserviceConfig(
        name="image-service",
        host="localhost",
        port=8005,
        description="图像处理和分析微服务"
    )
    
    await image_service.service_registry.register_service(config)
    print("图像微服务启动完成")


@image_app.on_event("shutdown")
async def shutdown_event():
    """服务关闭事件"""
    print("图像微服务已关闭")
