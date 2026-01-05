"""
默认模型缓存服务
用于缓存默认模型管理系统的关键数据，提高系统性能
"""
from typing import Any, Dict, List, Optional, Union
import json
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.core.redis import redis_client
from app.models.default_model import DefaultModel, ModelFeedback, ModelPerformance
from app.models.parameter_template import ParameterTemplate, ParameterTemplateVersion


class DefaultModelCacheService:
    """默认模型缓存服务"""
    
    # 缓存键前缀
    DEFAULT_MODEL_PREFIX = "default_model"
    SCENE_DEFAULT_MODEL_PREFIX = "scene_default_model"
    MODEL_SELECTION_PREFIX = "model_selection"
    PARAMETER_TEMPLATE_PREFIX = "parameter_template"
    PARAMETER_TEMPLATE_VERSION_PREFIX = "parameter_template_version"
    
    # 默认缓存过期时间（秒）
    DEFAULT_CACHE_TTL = 3600  # 1小时
    MODEL_SELECTION_CACHE_TTL = 600  # 10分钟
    PARAMETER_TEMPLATE_CACHE_TTL = 7200  # 2小时
    
    @staticmethod
    def _get_cache_key(*parts: str) -> str:
        """生成缓存键"""
        return ":".join(parts)
    
    @staticmethod
    def _serialize_data(data: Any) -> str:
        """序列化数据为JSON字符串"""
        if data is None:
            return None
        
        # 处理datetime对象
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            # 对于无法序列化的对象，返回None
            return None
        
        try:
            return json.dumps(data, default=json_serializer)
        except (TypeError, ValueError):
            return None
    
    @staticmethod
    def _deserialize_data(data: str) -> Any:
        """反序列化JSON字符串为数据"""
        if data is None:
            return None
        
        def json_deserializer(obj):
            # 将字符串转换为datetime对象
            if isinstance(obj, str) and (obj.endswith("Z") or "T" in obj):
                try:
                    return datetime.fromisoformat(obj.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            return obj
        
        try:
            return json.loads(data, object_hook=json_deserializer)
        except (json.JSONDecodeError, TypeError):
            return data
    
    # 缓存过期时间计算
    @staticmethod
    def _get_ttl(seconds: int = None) -> int:
        """获取缓存过期时间"""
        return seconds if seconds is not None else DefaultModelCacheService.DEFAULT_CACHE_TTL
    
    # 默认模型缓存
    @staticmethod
    def cache_global_default_models(models: List[DefaultModel], ttl: int = None) -> bool:
        """缓存全局默认模型"""
        if not redis_client:
            return False
        
        try:
            # 序列化模型数据
            cache_data = DefaultModelCacheService._serialize_data([model.__dict__ for model in models])
            
            # 设置缓存
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.DEFAULT_MODEL_PREFIX, "global"
            )
            
            # 如果传入的ttl为空，使用默认TTL
            ttl = DefaultModelCacheService._get_ttl(ttl)
            
            # 设置缓存，带过期时间
            result = redis_client.setex(
                cache_key, 
                ttl, 
                cache_data
            )
            
            return result
        except Exception as e:
            print(f"缓存全局默认模型失败: {e}")
            return False
    
    @staticmethod
    def get_cached_global_default_models() -> Optional[List[DefaultModel]]:
        """获取缓存的全局默认模型"""
        if not redis_client:
            return None
        
        try:
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.DEFAULT_MODEL_PREFIX, "global"
            )
            
            # 获取缓存
            cache_data = redis_client.get(cache_key)
            
            if not cache_data:
                return None
            
            # 反序列化数据
            data = DefaultModelCacheService._deserialize_data(cache_data)
            
            # 转换为DefaultModel对象列表
            # 注意：在实际应用中，可能需要更复杂的反序列化过程
            # 这里简化处理，只返回字典列表
            return data
        except Exception as e:
            print(f"获取缓存的全局默认模型失败: {e}")
            return None
    
    @staticmethod
    def cache_scene_default_models(scene: str, models: List[DefaultModel], ttl: int = None) -> bool:
        """缓存场景默认模型"""
        if not redis_client:
            return False
        
        try:
            # 序列化模型数据
            cache_data = DefaultModelCacheService._serialize_data([model.__dict__ for model in models])
            
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.SCENE_DEFAULT_MODEL_PREFIX, scene
            )
            
            # 如果传入的ttl为空，使用默认TTL
            ttl = DefaultModelCacheService._get_ttl(ttl)
            
            # 设置缓存
            result = redis_client.setex(
                cache_key, 
                ttl, 
                cache_data
            )
            
            return result
        except Exception as e:
            print(f"缓存场景默认模型失败: {e}")
            return False
    
    @staticmethod
    def get_cached_scene_default_models(scene: str) -> Optional[List[DefaultModel]]:
        """获取缓存的场景默认模型"""
        if not redis_client:
            return None
        
        try:
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.SCENE_DEFAULT_MODEL_PREFIX, scene
            )
            
            # 获取缓存
            cache_data = redis_client.get(cache_key)
            
            if not cache_data:
                return None
            
            # 反序列化数据
            data = DefaultModelCacheService._deserialize_data(cache_data)
            
            # 转换为对象列表
            return data
        except Exception as e:
            print(f"获取缓存的场景默认模型失败: {e}")
            return None
    
    # 智能模型选择缓存
    @staticmethod
    def cache_model_selection_result(scene: str, requirements: Dict[str, Any], 
                                    model_id: int, ttl: int = None) -> bool:
        """缓存智能模型选择结果"""
        if not redis_client:
            return False
        
        try:
            # 序列化和简化需求信息，只保留关键信息用于缓存键
            # 对复杂的requirements进行哈希
            requirements_key = json.dumps(requirements, sort_keys=True)
            
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.MODEL_SELECTION_PREFIX,
                scene,
                requirements_key
            )
            
            # 如果传入的ttl为空，使用默认TTL
            ttl = DefaultModelCacheService._get_ttl(ttl) if ttl is None else ttl
            if ttl is None:
                ttl = DefaultModelCacheService.MODEL_SELECTION_CACHE_TTL
            
            # 缓存模型ID和选择时间
            cache_data = DefaultModelCacheService._serialize_data({
                "model_id": model_id,
                "selected_at": datetime.now().isoformat()
            })
            
            # 设置缓存
            result = redis_client.setex(
                cache_key, 
                ttl, 
                cache_data
            )
            
            return result
        except Exception as e:
            print(f"缓存模型选择结果失败: {e}")
            return False
    
    @staticmethod
    def get_cached_model_selection_result(scene: str, requirements: Dict[str, Any]) -> Optional[int]:
        """获取缓存的智能模型选择结果"""
        if not redis_client:
            return None
        
        try:
            # 序列化和简化需求信息，只保留关键信息用于缓存键
            requirements_key = json.dumps(requirements, sort_keys=True)
            
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.MODEL_SELECTION_PREFIX,
                scene,
                requirements_key
            )
            
            # 获取缓存
            cache_data = redis_client.get(cache_key)
            
            if not cache_data:
                return None
            
            # 反序列化数据
            data = DefaultModelCacheService._deserialize_data(cache_data)
            
            # 返回模型ID
            return data.get("model_id")
        except Exception as e:
            print(f"获取缓存的模型选择结果失败: {e}")
            return None
    
    # 参数模板缓存
    @staticmethod
    def cache_parameter_template(template: ParameterTemplate, ttl: int = None) -> bool:
        """缓存参数模板"""
        if not redis_client:
            return False
        
        try:
            # 序列化模板数据
            cache_data = DefaultModelCacheService._serialize_data(template.__dict__)
            
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                str(template.id)
            )
            
            # 如果传入的ttl为空，使用默认TTL
            ttl = DefaultModelCacheService._get_ttl(ttl)
            
            # 设置缓存
            result = redis_client.setex(
                cache_key, 
                ttl, 
                cache_data
            )
            
            return result
        except Exception as e:
            print(f"缓存参数模板失败: {e}")
            return False
    
    @staticmethod
    def get_cached_parameter_template(template_id: int) -> Optional[ParameterTemplate]:
        """获取缓存的参数模板"""
        if not redis_client:
            return None
        
        try:
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                str(template_id)
            )
            
            # 获取缓存
            cache_data = redis_client.get(cache_key)
            
            if not cache_data:
                return None
            
            # 反序列化数据
            data = DefaultModelCacheService._deserialize_data(cache_data)
            
            # 转换为对象
            return data
        except Exception as e:
            print(f"获取缓存的参数模板失败: {e}")
            return None
    
    @staticmethod
    def cache_parameter_templates_list(templates_list: Any, cache_key_suffix: str, ttl: int = None) -> bool:
        """缓存参数模板列表"""
        if not redis_client:
            return False
        
        try:
            # 序列化列表数据
            cache_data = DefaultModelCacheService._serialize_data(templates_list.__dict__)
            
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                "list",
                cache_key_suffix
            )
            
            # 如果传入的ttl为空，使用默认TTL
            ttl = DefaultModelCacheService._get_ttl(ttl)
            
            # 设置缓存
            result = redis_client.setex(
                cache_key, 
                ttl, 
                cache_data
            )
            
            return result
        except Exception as e:
            print(f"缓存参数模板列表失败: {e}")
            return False
    
    @staticmethod
    def get_cached_parameter_templates_list(cache_key_suffix: str) -> Optional[Any]:
        """获取缓存的参数模板列表"""
        if not redis_client:
            return None
        
        try:
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                "list",
                cache_key_suffix
            )
            
            # 获取缓存
            cache_data = redis_client.get(cache_key)
            
            if not cache_data:
                return None
            
            # 反序列化数据
            data = DefaultModelCacheService._deserialize_data(cache_data)
            
            # 转换为对象
            return data
        except Exception as e:
            print(f"获取缓存的参数模板列表失败: {e}")
            return None
    
    @staticmethod
    def cache_parameter_template(template: ParameterTemplate, ttl: int = None) -> bool:
        """缓存参数模板"""
        if not redis_client:
            return False
        
        try:
            # 序列化模板数据
            cache_data = DefaultModelCacheService._serialize_data(template.__dict__)
            
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                str(template.id)
            )
            
            # 如果传入的ttl为空，使用默认TTL
            ttl = DefaultModelCacheService._get_ttl(ttl)
            
            # 设置缓存
            result = redis_client.setex(
                cache_key, 
                ttl, 
                cache_data
            )
            
            return result
        except Exception as e:
            print(f"缓存参数模板失败: {e}")
            return False
    
    @staticmethod
    def get_cached_parameter_template(template_id: int) -> Optional[ParameterTemplate]:
        """获取缓存的参数模板"""
        if not redis_client:
            return None
        
        try:
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                str(template_id)
            )
            
            # 获取缓存
            cache_data = redis_client.get(cache_key)
            
            if not cache_data:
                return None
            
            # 反序列化数据
            data = DefaultModelCacheService._deserialize_data(cache_data)
            
            # 转换为对象
            return data
        except Exception as e:
            print(f"获取缓存的参数模板失败: {e}")
            return None
    
    @staticmethod
    def cache_parameter_template_versions_list(versions_list: Any, cache_key_suffix: str, ttl: int = None) -> bool:
        """缓存参数模板版本列表"""
        if not redis_client:
            return False
        
        try:
            # 序列化列表数据
            cache_data = DefaultModelCacheService._serialize_data(versions_list.__dict__)
            
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_VERSION_PREFIX,
                "list",
                cache_key_suffix
            )
            
            # 如果传入的ttl为空，使用默认TTL
            ttl = DefaultModelCacheService._get_ttl(ttl)
            
            # 设置缓存
            result = redis_client.setex(
                cache_key, 
                ttl, 
                cache_data
            )
            
            return result
        except Exception as e:
            print(f"缓存参数模板版本列表失败: {e}")
            return False
    
    @staticmethod
    def get_cached_parameter_template_versions_list(cache_key_suffix: str) -> Optional[Any]:
        """获取缓存的参数模板版本列表"""
        if not redis_client:
            return None
        
        try:
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_VERSION_PREFIX,
                "list",
                cache_key_suffix
            )
            
            # 获取缓存
            cache_data = redis_client.get(cache_key)
            
            if not cache_data:
                return None
            
            # 反序列化数据
            data = DefaultModelCacheService._deserialize_data(cache_data)
            
            # 转换为对象
            return data
        except Exception as e:
            print(f"获取缓存的参数模板版本列表失败: {e}")
            return None
    
    @staticmethod
    def cache_parameter_template_scenes(scenes: List[str], ttl: int = None) -> bool:
        """缓存参数模板场景列表"""
        if not redis_client:
            return False
        
        try:
            # 序列化场景数据
            cache_data = DefaultModelCacheService._serialize_data(scenes)
            
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                "scenes"
            )
            
            # 如果传入的ttl为空，使用默认TTL
            ttl = DefaultModelCacheService._get_ttl(ttl)
            
            # 设置缓存
            result = redis_client.setex(
                cache_key, 
                ttl, 
                cache_data
            )
            
            return result
        except Exception as e:
            print(f"缓存参数模板场景列表失败: {e}")
            return False
    
    @staticmethod
    def get_cached_parameter_template_scenes() -> Optional[List[str]]:
        """获取缓存的参数模板场景列表"""
        if not redis_client:
            return None
        
        try:
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                "scenes"
            )
            
            # 获取缓存
            cache_data = redis_client.get(cache_key)
            
            if not cache_data:
                return None
            
            # 反序列化数据
            data = DefaultModelCacheService._deserialize_data(cache_data)
            
            return data
        except Exception as e:
            print(f"获取缓存的参数模板场景列表失败: {e}")
            return None
    
    @staticmethod
    def invalidate_parameter_template_cache(template_id: int = None, cache_type: str = None) -> bool:
        """使参数模板缓存失效"""
        if not redis_client:
            return False
        
        try:
            if cache_type == "list":
                # 失效所有参数模板列表缓存
                pattern = DefaultModelCacheService._get_cache_key(
                    DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                    "list",
                    "*"
                )
                # 使用SCAN命令查找匹配的键
                cursor = 0
                keys_to_delete = []
                while True:
                    cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
                    keys_to_delete.extend(keys)
                    if cursor == 0:
                        break
                
                if keys_to_delete:
                    return redis_client.delete(*keys_to_delete) > 0
                return True
                
            elif cache_type == "versions":
                # 失效所有参数模板版本列表缓存
                pattern = DefaultModelCacheService._get_cache_key(
                    DefaultModelCacheService.PARAMETER_TEMPLATE_VERSION_PREFIX,
                    "list",
                    "*"
                )
                # 使用SCAN命令查找匹配的键
                cursor = 0
                keys_to_delete = []
                while True:
                    cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
                    keys_to_delete.extend(keys)
                    if cursor == 0:
                        break
                
                if keys_to_delete:
                    return redis_client.delete(*keys_to_delete) > 0
                return True
                
            elif template_id is not None:
                # 失效特定参数模板缓存
                cache_key = DefaultModelCacheService._get_cache_key(
                    DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                    str(template_id)
                )
                return redis_client.delete(cache_key) > 0
            
            # 默认失效所有参数模板相关缓存
            patterns = [
                DefaultModelCacheService._get_cache_key(
                    DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                    "*"
                ),
                DefaultModelCacheService._get_cache_key(
                    DefaultModelCacheService.PARAMETER_TEMPLATE_VERSION_PREFIX,
                    "*"
                )
            ]
            
            for pattern in patterns:
                cursor = 0
                keys_to_delete = []
                while True:
                    cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
                    keys_to_delete.extend(keys)
                    if cursor == 0:
                        break
                
                if keys_to_delete:
                    redis_client.delete(*keys_to_delete)
            
            return True
        except Exception as e:
            print(f"使参数模板缓存失效失败: {e}")
            return False
    
    @staticmethod
    def invalidate_parameter_templates_cache(cache_type: str) -> bool:
        """使参数模板列表缓存失效"""
        if not redis_client:
            return False
        
        try:
            if cache_type == "list":
                # 失效所有参数模板列表缓存
                pattern = DefaultModelCacheService._get_cache_key(
                    DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                    "list",
                    "*"
                )
                # 使用SCAN命令查找匹配的键
                cursor = 0
                keys_to_delete = []
                while True:
                    cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
                    keys_to_delete.extend(keys)
                    if cursor == 0:
                        break
                
                if keys_to_delete:
                    return redis_client.delete(*keys_to_delete) > 0
                return True
                
            elif cache_type == "scenes":
                # 失效参数模板场景列表缓存
                cache_key = DefaultModelCacheService._get_cache_key(
                    DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                    "scenes"
                )
                return redis_client.delete(cache_key) > 0
                
            elif cache_type == "versions":
                # 失效所有参数模板版本列表缓存
                pattern = DefaultModelCacheService._get_cache_key(
                    DefaultModelCacheService.PARAMETER_TEMPLATE_VERSION_PREFIX,
                    "list",
                    "*"
                )
                # 使用SCAN命令查找匹配的键
                cursor = 0
                keys_to_delete = []
                while True:
                    cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
                    keys_to_delete.extend(keys)
                    if cursor == 0:
                        break
                
                if keys_to_delete:
                    return redis_client.delete(*keys_to_delete) > 0
                return True
            
            return False
        except Exception as e:
            print(f"使参数模板列表缓存失效失败: {e}")
            return False
    
    @staticmethod
    def cache_parameter_template_versions(template_id: int, versions: List[ParameterTemplateVersion], ttl: int = None) -> bool:
        """缓存参数模板版本列表"""
        if not redis_client:
            return False
        
        try:
            # 序列化版本数据
            cache_data = DefaultModelCacheService._serialize_data([version.__dict__ for version in versions])
            
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_VERSION_PREFIX,
                str(template_id)
            )
            
            # 如果传入的ttl为空，使用默认TTL
            ttl = DefaultModelCacheService._get_ttl(ttl)
            
            # 设置缓存
            result = redis_client.setex(
                cache_key, 
                ttl, 
                cache_data
            )
            
            return result
        except Exception as e:
            print(f"缓存参数模板版本列表失败: {e}")
            return False
    
    @staticmethod
    def get_cached_parameter_template_versions(template_id: int) -> Optional[List[ParameterTemplateVersion]]:
        """获取缓存的参数模板版本列表"""
        if not redis_client:
            return None
        
        try:
            # 设置缓存键
            cache_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_VERSION_PREFIX,
                str(template_id)
            )
            
            # 获取缓存
            cache_data = redis_client.get(cache_key)
            
            if not cache_data:
                return None
            
            # 反序列化数据
            data = DefaultModelCacheService._deserialize_data(cache_data)
            
            # 转换为对象列表
            return data
        except Exception as e:
            print(f"获取缓存的参数模板版本列表失败: {e}")
            return None
    
    # 缓存管理
    @staticmethod
    def invalidate_default_model_cache(scope: str, scene: str = None) -> bool:
        """使默认模型缓存失效"""
        if not redis_client:
            return False
        
        try:
            if scope == "global":
                # 失效全局默认模型缓存
                cache_key = DefaultModelCacheService._get_cache_key(
                    DefaultModelCacheService.DEFAULT_MODEL_PREFIX, "global"
                )
                return redis_client.delete(cache_key) > 0
            elif scope == "scene" and scene:
                # 失效场景默认模型缓存
                cache_key = DefaultModelCacheService._get_cache_key(
                    DefaultModelCacheService.SCENE_DEFAULT_MODEL_PREFIX, scene
                )
                return redis_client.delete(cache_key) > 0
            return False
        except Exception as e:
            print(f"使默认模型缓存失效失败: {e}")
            return False
    
    @staticmethod
    def invalidate_parameter_template_cache(template_id: int) -> bool:
        """使参数模板缓存失效"""
        if not redis_client:
            return False
        
        try:
            # 失效模板缓存
            template_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_PREFIX,
                str(template_id)
            )
            
            # 失效模板版本缓存
            versions_key = DefaultModelCacheService._get_cache_key(
                DefaultModelCacheService.PARAMETER_TEMPLATE_VERSION_PREFIX,
                str(template_id)
            )
            
            # 删除两个缓存
            return redis_client.delete(template_key, versions_key) > 0
        except Exception as e:
            print(f"使参数模板缓存失效失败: {e}")
            return False