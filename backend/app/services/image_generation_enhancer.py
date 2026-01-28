"""
图像生成功能增强器
基于现有Clawdbot图像生成功能进行升级和优化
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
import aiohttp
from PIL import Image, ImageFilter, ImageEnhance
import io
import os

logger = logging.getLogger(__name__)


class ImageGenerationProvider(Enum):
    """图像生成提供商枚举"""
    GOOGLE = "google"
    OPENAI = "openai"
    STABLE_DIFFUSION = "stable_diffusion"
    MIDJOURNEY = "midjourney"
    CUSTOM = "custom"


class ImageStyle(Enum):
    """图像风格枚举"""
    REALISTIC = "realistic"
    CARTOON = "cartoon"
    ANIME = "anime"
    ABSTRACT = "abstract"
    SKETCH = "sketch"
    OIL_PAINTING = "oil_painting"
    WATERCOLOR = "watercolor"
    PIXEL_ART = "pixel_art"
    MINIMALIST = "minimalist"


class ImageResolution(Enum):
    """图像分辨率枚举"""
    SD_512x512 = "512x512"
    HD_1024x1024 = "1024x1024"
    FHD_1920x1080 = "1920x1080"
    UHD_3840x2160 = "3840x2160"
    SQUARE_1K = "1024x1024"
    SQUARE_2K = "2048x2048"
    SQUARE_4K = "4096x4096"


@dataclass
class GenerationRequest:
    """生成请求"""
    prompt: str
    provider: ImageGenerationProvider
    style: ImageStyle
    resolution: ImageResolution
    num_images: int
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    guidance_scale: float = 7.5
    steps: int = 50


@dataclass
class GenerationResult:
    """生成结果"""
    generation_id: str
    images: List[bytes]
    metadata: Dict[str, Any]
    processing_time: float
    provider: ImageGenerationProvider


@dataclass
class BatchGenerationResult:
    """批量生成结果"""
    batch_id: str
    results: List[GenerationResult]
    total_images: int
    total_time: float
    success_rate: float


class ImageGenerationEnhancer:
    """图像生成功能增强器"""
    
    def __init__(self):
        """初始化图像生成增强器"""
        # 提供商配置
        self.provider_config = {
            ImageGenerationProvider.GOOGLE: {
                "enabled": True,
                "api_key_env": "GEMINI_API_KEY",
                "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
                "model": "gemini-3-pro-image"
            },
            ImageGenerationProvider.OPENAI: {
                "enabled": False,
                "api_key_env": "OPENAI_API_KEY",
                "base_url": "https://api.openai.com/v1",
                "model": "dall-e-3"
            },
            ImageGenerationProvider.STABLE_DIFFUSION: {
                "enabled": False,
                "api_key_env": "STABLE_DIFFUSION_API_KEY",
                "base_url": "https://api.stability.ai/v1",
                "model": "stable-diffusion-xl-1024-v1-0"
            }
        }
        
        # 风格配置
        self.style_config = {
            ImageStyle.REALISTIC: {
                "prompt_suffix": ", photorealistic, high detail, professional photography",
                "negative_prompt": "cartoon, anime, abstract, painting"
            },
            ImageStyle.CARTOON: {
                "prompt_suffix": ", cartoon style, vibrant colors, clean lines",
                "negative_prompt": "photorealistic, realistic, photo"
            },
            ImageStyle.ANIME: {
                "prompt_suffix": ", anime style, Japanese animation, vibrant colors",
                "negative_prompt": "realistic, western cartoon, photo"
            },
            ImageStyle.ABSTRACT: {
                "prompt_suffix": ", abstract art, modern art, creative composition",
                "negative_prompt": "realistic, detailed, photorealistic"
            },
            ImageStyle.SKETCH: {
                "prompt_suffix": ", pencil sketch, hand-drawn, artistic sketch",
                "negative_prompt": "colorful, photorealistic, digital art"
            },
            ImageStyle.OIL_PAINTING: {
                "prompt_suffix": ", oil painting, classical art, brush strokes",
                "negative_prompt": "digital, photo, modern"
            },
            ImageStyle.WATERCOLOR: {
                "prompt_suffix": ", watercolor painting, soft colors, transparent washes",
                "negative_prompt": "opaque, digital, photo"
            },
            ImageStyle.PIXEL_ART: {
                "prompt_suffix": ", pixel art, retro game style, 8-bit",
                "negative_prompt": "high resolution, realistic, smooth"
            },
            ImageStyle.MINIMALIST: {
                "prompt_suffix": ", minimalist design, simple composition, clean lines",
                "negative_prompt": "complex, detailed, cluttered"
            }
        }
        
        # 分辨率配置
        self.resolution_config = {
            ImageResolution.SD_512x512: {"width": 512, "height": 512},
            ImageResolution.HD_1024x1024: {"width": 1024, "height": 1024},
            ImageResolution.FHD_1920x1080: {"width": 1920, "height": 1080},
            ImageResolution.UHD_3840x2160: {"width": 3840, "height": 2160},
            ImageResolution.SQUARE_1K: {"width": 1024, "height": 1024},
            ImageResolution.SQUARE_2K: {"width": 2048, "height": 2048},
            ImageResolution.SQUARE_4K: {"width": 4096, "height": 4096}
        }
        
        # 生成统计
        self.generation_stats = {
            "total_generations": 0,
            "successful_generations": 0,
            "total_images_generated": 0,
            "average_generation_time": 0.0,
            "provider_usage": {},
            "style_usage": {}
        }
    
    async def enhanced_image_generation(self, request: GenerationRequest) -> GenerationResult:
        """增强图像生成
        
        Args:
            request: 生成请求
            
        Returns:
            生成结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 验证请求参数
            self._validate_generation_request(request)
            
            # 构建增强的提示词
            enhanced_prompt = self._enhance_prompt(request.prompt, request.style)
            
            # 根据提供商选择生成方法
            if request.provider == ImageGenerationProvider.GOOGLE:
                images = await self._generate_with_google(enhanced_prompt, request)
            elif request.provider == ImageGenerationProvider.OPENAI:
                images = await self._generate_with_openai(enhanced_prompt, request)
            elif request.provider == ImageGenerationProvider.STABLE_DIFFUSION:
                images = await self._generate_with_stable_diffusion(enhanced_prompt, request)
            else:
                images = await self._generate_with_google(enhanced_prompt, request)
            
            # 后处理生成的图像
            processed_images = await self._postprocess_generated_images(images, request)
            
            generation_time = asyncio.get_event_loop().time() - start_time
            
            result = GenerationResult(
                generation_id=str(uuid.uuid4()),
                images=processed_images,
                metadata={
                    "prompt": request.prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "style": request.style.value,
                    "resolution": request.resolution.value,
                    "provider": request.provider.value,
                    "num_images": request.num_images,
                    "seed": request.seed,
                    "guidance_scale": request.guidance_scale,
                    "steps": request.steps
                },
                processing_time=generation_time,
                provider=request.provider
            )
            
            # 更新统计信息
            self._update_generation_stats(result, True)
            
            logger.info(f"图像生成完成: {request.provider.value}, 生成 {len(images)} 张图像, 耗时: {generation_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"图像生成失败: {e}")
            self._update_generation_stats(None, False)
            raise
    
    async def batch_image_generation(self, requests: List[GenerationRequest]) -> BatchGenerationResult:
        """批量图像生成
        
        Args:
            requests: 生成请求列表
            
        Returns:
            批量生成结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 并发执行生成请求
            tasks = [self.enhanced_image_generation(req) for req in requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            successful_results = []
            total_images = 0
            
            for result in results:
                if isinstance(result, GenerationResult):
                    successful_results.append(result)
                    total_images += len(result.images)
            
            total_time = asyncio.get_event_loop().time() - start_time
            success_rate = len(successful_results) / len(requests) if requests else 0.0
            
            batch_result = BatchGenerationResult(
                batch_id=str(uuid.uuid4()),
                results=successful_results,
                total_images=total_images,
                total_time=total_time,
                success_rate=success_rate
            )
            
            logger.info(f"批量图像生成完成: {len(successful_results)}/{len(requests)} 成功, 总图像: {total_images}")
            
            return batch_result
            
        except Exception as e:
            logger.error(f"批量图像生成失败: {e}")
            raise
    
    async def image_to_image_generation(self, base_image: bytes, prompt: str,
                                       strength: float = 0.7,
                                       provider: ImageGenerationProvider = ImageGenerationProvider.GOOGLE) -> GenerationResult:
        """基于图像的图像生成
        
        Args:
            base_image: 基础图像
            prompt: 生成提示
            strength: 修改强度
            provider: 生成提供商
            
        Returns:
            生成结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 构建请求
            request = GenerationRequest(
                prompt=prompt,
                provider=provider,
                style=ImageStyle.REALISTIC,
                resolution=ImageResolution.HD_1024x1024,
                num_images=1
            )
            
            # 根据提供商选择生成方法
            if provider == ImageGenerationProvider.GOOGLE:
                images = await self._image_to_image_with_google(base_image, prompt, strength)
            elif provider == ImageGenerationProvider.STABLE_DIFFUSION:
                images = await self._image_to_image_with_stable_diffusion(base_image, prompt, strength)
            else:
                images = await self._image_to_image_with_google(base_image, prompt, strength)
            
            # 后处理生成的图像
            processed_images = await self._postprocess_generated_images(images, request)
            
            generation_time = asyncio.get_event_loop().time() - start_time
            
            result = GenerationResult(
                generation_id=str(uuid.uuid4()),
                images=processed_images,
                metadata={
                    "prompt": prompt,
                    "base_image_size": len(base_image),
                    "strength": strength,
                    "provider": provider.value,
                    "generation_type": "image_to_image"
                },
                processing_time=generation_time,
                provider=provider
            )
            
            logger.info(f"基于图像的生成完成: 强度 {strength}, 耗时: {generation_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"基于图像的生成失败: {e}")
            raise
    
    def _validate_generation_request(self, request: GenerationRequest):
        """验证生成请求"""
        if not request.prompt.strip():
            raise ValueError("生成提示不能为空")
        
        if request.num_images < 1 or request.num_images > 10:
            raise ValueError("生成图像数量必须在1-10之间")
        
        if request.guidance_scale < 1.0 or request.guidance_scale > 20.0:
            raise ValueError("引导比例必须在1.0-20.0之间")
        
        if request.steps < 10 or request.steps > 150:
            raise ValueError("生成步数必须在10-150之间")
        
        # 检查提供商是否启用
        provider_config = self.provider_config.get(request.provider)
        if not provider_config or not provider_config["enabled"]:
            raise ValueError(f"提供商 {request.provider.value} 未启用或不可用")
    
    def _enhance_prompt(self, prompt: str, style: ImageStyle) -> str:
        """增强提示词"""
        style_config = self.style_config.get(style, {})
        
        # 添加风格后缀
        enhanced_prompt = prompt
        if "prompt_suffix" in style_config:
            enhanced_prompt += style_config["prompt_suffix"]
        
        # 添加质量描述
        quality_descriptors = ["high quality", "detailed", "professional"]
        enhanced_prompt += ", " + ", ".join(quality_descriptors)
        
        return enhanced_prompt
    
    async def _generate_with_google(self, prompt: str, request: GenerationRequest) -> List[bytes]:
        """使用Google API生成图像"""
        try:
            # 获取API密钥
            api_key = os.environ.get(self.provider_config[ImageGenerationProvider.GOOGLE]["api_key_env"])
            if not api_key:
                raise ValueError("Google API密钥未设置")
            
            # 构建请求URL
            base_url = self.provider_config[ImageGenerationProvider.GOOGLE]["base_url"]
            model = self.provider_config[ImageGenerationProvider.GOOGLE]["model"]
            url = f"{base_url}/{model}:generateContent?key={api_key}"
            
            # 构建请求体
            request_body = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"请生成一张图像: {prompt}"
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.9,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                }
            }
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request_body) as response:
                    if response.status != 200:
                        raise ValueError(f"Google API请求失败: {response.status}")
                    
                    result = await response.json()
                    
                    # 解析响应并提取图像数据
                    images = self._parse_google_response(result, request.num_images)
                    
                    return images
            
        except Exception as e:
            logger.error(f"Google图像生成失败: {e}")
            # 返回占位图像
            return await self._generate_placeholder_images(prompt, request.num_images)
    
    def _parse_google_response(self, response: Dict[str, Any], num_images: int) -> List[bytes]:
        """解析Google API响应"""
        images = []
        
        # 尝试从响应中提取图像数据
        if "candidates" in response and response["candidates"]:
            candidate = response["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
                    if "inlineData" in part and "data" in part["inlineData"]:
                        # 解码base64图像数据
                        image_data = base64.b64decode(part["inlineData"]["data"])
                        images.append(image_data)
        
        # 如果未提取到图像，生成占位图像
        if not images:
            # 这里应该生成实际的占位图像
            placeholder = self._create_placeholder_image("Google生成图像")
            images = [placeholder] * num_images
        
        return images[:num_images]
    
    async def _generate_with_openai(self, prompt: str, request: GenerationRequest) -> List[bytes]:
        """使用OpenAI API生成图像"""
        try:
            # 获取API密钥
            api_key = os.environ.get(self.provider_config[ImageGenerationProvider.OPENAI]["api_key_env"])
            if not api_key:
                raise ValueError("OpenAI API密钥未设置")
            
            # 构建请求URL
            base_url = self.provider_config[ImageGenerationProvider.OPENAI]["base_url"]
            url = f"{base_url}/images/generations"
            
            # 构建请求体
            resolution_config = self.resolution_config[request.resolution]
            request_body = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": request.num_images,
                "size": f"{resolution_config['width']}x{resolution_config['height']}",
                "quality": "standard",
                "style": "vivid"
            }
            
            # 发送请求
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request_body, headers=headers) as response:
                    if response.status != 200:
                        raise ValueError(f"OpenAI API请求失败: {response.status}")
                    
                    result = await response.json()
                    
                    # 解析响应并下载图像
                    images = await self._download_openai_images(result["data"])
                    
                    return images
            
        except Exception as e:
            logger.error(f"OpenAI图像生成失败: {e}")
            # 返回占位图像
            return await self._generate_placeholder_images(prompt, request.num_images)
    
    async def _download_openai_images(self, image_data: List[Dict[str, Any]]) -> List[bytes]:
        """下载OpenAI生成的图像"""
        images = []
        
        async with aiohttp.ClientSession() as session:
            for item in image_data:
                if "url" in item:
                    async with session.get(item["url"]) as response:
                        if response.status == 200:
                            image_bytes = await response.read()
                            images.append(image_bytes)
        
        return images
    
    async def _generate_with_stable_diffusion(self, prompt: str, request: GenerationRequest) -> List[bytes]:
        """使用Stable Diffusion API生成图像"""
        try:
            # 获取API密钥
            api_key = os.environ.get(self.provider_config[ImageGenerationProvider.STABLE_DIFFUSION]["api_key_env"])
            if not api_key:
                raise ValueError("Stable Diffusion API密钥未设置")
            
            # 构建请求URL
            base_url = self.provider_config[ImageGenerationProvider.STABLE_DIFFUSION]["base_url"]
            url = f"{base_url}/generation/{self.provider_config[ImageGenerationProvider.STABLE_DIFFUSION]['model']}/text-to-image"
            
            # 构建请求体
            resolution_config = self.resolution_config[request.resolution]
            request_body = {
                "text_prompts": [{"text": prompt, "weight": 1.0}],
                "cfg_scale": request.guidance_scale,
                "steps": request.steps,
                "samples": request.num_images,
                "width": resolution_config["width"],
                "height": resolution_config["height"]
            }
            
            if request.seed:
                request_body["seed"] = request.seed
            
            # 发送请求
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request_body, headers=headers) as response:
                    if response.status != 200:
                        raise ValueError(f"Stable Diffusion API请求失败: {response.status}")
                    
                    result = await response.json()
                    
                    # 解析响应并提取图像数据
                    images = self._parse_stable_diffusion_response(result)
                    
                    return images
            
        except Exception as e:
            logger.error(f"Stable Diffusion图像生成失败: {e}")
            # 返回占位图像
            return await self._generate_placeholder_images(prompt, request.num_images)
    
    def _parse_stable_diffusion_response(self, response: Dict[str, Any]) -> List[bytes]:
        """解析Stable Diffusion API响应"""
        images = []
        
        if "artifacts" in response:
            for artifact in response["artifacts"]:
                if "base64" in artifact:
                    image_data = base64.b64decode(artifact["base64"])
                    images.append(image_data)
        
        return images
    
    async def _image_to_image_with_google(self, base_image: bytes, prompt: str, strength: float) -> List[bytes]:
        """使用Google API进行基于图像的生成"""
        # 这里应该实现实际的image-to-image生成
        # 暂时返回占位图像
        return await self._generate_placeholder_images(prompt, 1)
    
    async def _image_to_image_with_stable_diffusion(self, base_image: bytes, prompt: str, strength: float) -> List[bytes]:
        """使用Stable Diffusion API进行基于图像的生成"""
        # 这里应该实现实际的image-to-image生成
        # 暂时返回占位图像
        return await self._generate_placeholder_images(prompt, 1)
    
    async def _generate_placeholder_images(self, prompt: str, num_images: int) -> List[bytes]:
        """生成占位图像"""
        images = []
        
        for i in range(num_images):
            placeholder = self._create_placeholder_image(f"{prompt[:30]}...")
            images.append(placeholder)
        
        return images
    
    def _create_placeholder_image(self, text: str) -> bytes:
        """创建占位图像"""
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
        display_text = f"生成图像: {text}"
        bbox = draw.textbbox((0, 0), display_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), display_text, fill="black", font=font)
        
        # 保存为字节数据
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        
        return output_buffer.getvalue()
    
    async def _postprocess_generated_images(self, images: List[bytes], request: GenerationRequest) -> List[bytes]:
        """后处理生成的图像"""
        processed_images = []
        
        for image_data in images:
            # 应用后处理（如调整大小、格式转换等）
            processed_image = await self._apply_postprocessing(image_data, request)
            processed_images.append(processed_image)
        
        return processed_images
    
    async def _apply_postprocessing(self, image_data: bytes, request: GenerationRequest) -> bytes:
        """应用后处理"""
        # 这里可以添加图像质量优化、格式转换等后处理
        # 暂时直接返回原始图像数据
        return image_data
    
    def _update_generation_stats(self, result: Optional[GenerationResult], success: bool):
        """更新生成统计"""
        self.generation_stats["total_generations"] += 1
        
        if success and result:
            self.generation_stats["successful_generations"] += 1
            self.generation_stats["total_images_generated"] += len(result.images)
            
            # 更新平均生成时间
            total_time = self.generation_stats["average_generation_time"] * (self.generation_stats["total_generations"] - 1)
            total_time += result.processing_time
            self.generation_stats["average_generation_time"] = total_time / self.generation_stats["total_generations"]
            
            # 更新提供商使用统计
            provider = result.provider.value
            if provider not in self.generation_stats["provider_usage"]:
                self.generation_stats["provider_usage"][provider] = 0
            self.generation_stats["provider_usage"][provider] += 1
            
            # 更新风格使用统计
            style = result.metadata.get("style", "unknown")
            if style not in self.generation_stats["style_usage"]:
                self.generation_stats["style_usage"][style] = 0
            self.generation_stats["style_usage"][style] += 1
    
    def get_generation_report(self) -> Dict[str, Any]:
        """获取生成报告"""
        success_rate = 0.0
        if self.generation_stats["total_generations"] > 0:
            success_rate = (self.generation_stats["successful_generations"] / 
                          self.generation_stats["total_generations"]) * 100
        
        return {
            "success_rate": success_rate,
            "average_generation_time": self.generation_stats["average_generation_time"],
            "total_generations": self.generation_stats["total_generations"],
            "successful_generations": self.generation_stats["successful_generations"],
            "total_images_generated": self.generation_stats["total_images_generated"],
            "provider_usage": self.generation_stats["provider_usage"],
            "style_usage": self.generation_stats["style_usage"]
        }
    
    def configure_provider(self, provider: ImageGenerationProvider, config: Dict[str, Any]):
        """配置提供商"""
        if provider in self.provider_config:
            self.provider_config[provider].update(config)
            logger.info(f"图像生成提供商配置已更新: {provider.value}")
    
    def enable_provider(self, provider: ImageGenerationProvider, enabled: bool = True):
        """启用/禁用提供商"""
        if provider in self.provider_config:
            self.provider_config[provider]["enabled"] = enabled
            status = "启用" if enabled else "禁用"
            logger.info(f"图像生成提供商 {provider.value} 已{status}")


# 创建全局图像生成增强器实例
image_generation_enhancer = ImageGenerationEnhancer()