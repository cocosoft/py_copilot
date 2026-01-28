"""
技能注册表
管理已安装的技能，提供技能发现和执行功能
"""

import json
import os
import importlib.util
import inspect
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import logging

from app.schemas.skill_metadata import SkillMetadata

logger = logging.getLogger(__name__)


class SkillRegistry:
    """技能注册表类"""
    
    def __init__(self, skills_dir: str = None):
        """初始化技能注册表
        
        Args:
            skills_dir: 技能目录路径
        """
        self.skills_dir = Path(skills_dir) if skills_dir else Path(__file__).parent.parent / "skills"
        self.skills: Dict[str, Dict[str, Any]] = {}
        self.skill_modules: Dict[str, Any] = {}
        
        # 确保目录存在
        self.skills_dir.mkdir(parents=True, exist_ok=True)
    
    async def reload_skills(self) -> None:
        """重新加载所有技能"""
        logger.info("开始重新加载技能")
        
        self.skills.clear()
        self.skill_modules.clear()
        
        # 扫描技能目录
        await self._scan_skills_directory()
        
        logger.info(f"技能重新加载完成，共发现 {len(self.skills)} 个技能")
    
    async def _scan_skills_directory(self) -> None:
        """扫描技能目录，发现技能"""
        if not self.skills_dir.exists():
            logger.warning(f"技能目录不存在: {self.skills_dir}")
            return
        
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                await self._load_skill_from_directory(skill_dir)
    
    async def _load_skill_from_directory(self, skill_dir: Path) -> None:
        """从目录加载技能"""
        skill_id = skill_dir.name
        
        try:
            # 查找skill.json文件
            skill_json_path = skill_dir / "skill.json"
            if not skill_json_path.exists():
                logger.warning(f"技能目录 {skill_dir} 中未找到skill.json文件")
                return
            
            # 加载技能元数据
            with open(skill_json_path, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            
            metadata = SkillMetadata(**metadata_dict)
            
            # 验证技能ID
            if metadata.id != skill_id:
                logger.warning(f"技能ID不匹配: 目录名为 {skill_id}, 元数据中为 {metadata.id}")
                return
            
            # 加载技能模块
            skill_module = await self._load_skill_module(skill_dir, metadata)
            
            # 注册技能
            self.skills[skill_id] = {
                "metadata": metadata.dict(),
                "module": skill_module,
                "directory": str(skill_dir),
                "loaded": skill_module is not None
            }
            
            if skill_module:
                self.skill_modules[skill_id] = skill_module
            
            logger.info(f"技能加载成功: {skill_id}")
            
        except Exception as e:
            logger.error(f"加载技能失败: {skill_id}, 错误: {e}")
    
    async def _load_skill_module(self, skill_dir: Path, metadata: SkillMetadata) -> Optional[Any]:
        """加载技能模块"""
        try:
            # 确定主文件路径
            main_file = metadata.main_file or "main.py"
            main_file_path = skill_dir / main_file
            
            if not main_file_path.exists():
                logger.warning(f"技能主文件不存在: {main_file_path}")
                return None
            
            # 创建模块规范
            module_name = f"app.skills.{metadata.id}"
            spec = importlib.util.spec_from_file_location(module_name, main_file_path)
            
            if spec is None:
                logger.error(f"无法创建模块规范: {module_name}")
                return None
            
            # 创建和加载模块
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 验证模块是否包含必要的函数
            if not self._validate_skill_module(module, metadata):
                logger.warning(f"技能模块验证失败: {metadata.id}")
                return None
            
            return module
            
        except Exception as e:
            logger.error(f"加载技能模块失败: {metadata.id}, 错误: {e}")
            return None
    
    def _validate_skill_module(self, module: Any, metadata: SkillMetadata) -> bool:
        """验证技能模块"""
        # 检查是否有execute函数
        if not hasattr(module, 'execute'):
            logger.warning(f"技能模块缺少execute函数: {metadata.id}")
            return False
        
        # 检查execute函数是否为可调用函数
        if not callable(module.execute):
            logger.warning(f"技能模块的execute不是可调用函数: {metadata.id}")
            return False
        
        # 检查是否有必要的描述信息
        if not hasattr(module, '__doc__') or not module.__doc__:
            logger.warning(f"技能模块缺少文档字符串: {metadata.id}")
        
        return True
    
    async def get_all_skills(self) -> List[Dict[str, Any]]:
        """获取所有技能信息"""
        skills_list = []
        
        for skill_id, skill_info in self.skills.items():
            skill_data = skill_info["metadata"].copy()
            skill_data["loaded"] = skill_info["loaded"]
            skill_data["directory"] = skill_info["directory"]
            skills_list.append(skill_data)
        
        return skills_list
    
    async def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取指定技能信息"""
        if skill_id not in self.skills:
            return None
        
        skill_info = self.skills[skill_id].copy()
        skill_info["metadata"]["loaded"] = skill_info["loaded"]
        return skill_info["metadata"]
    
    async def execute_skill(self, skill_id: str, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行技能
        
        Args:
            skill_id: 技能ID
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        if skill_id not in self.skills:
            return {
                "success": False,
                "error": f"技能未找到: {skill_id}"
            }
        
        if not self.skills[skill_id]["loaded"]:
            return {
                "success": False,
                "error": f"技能未加载: {skill_id}"
            }
        
        try:
            module = self.skill_modules[skill_id]
            
            # 准备输入数据
            input_data = input_data or {}
            
            # 执行技能
            result = await self._safe_execute(module.execute, input_data)
            
            return {
                "success": True,
                "skill_id": skill_id,
                "result": result,
                "message": "技能执行成功"
            }
            
        except Exception as e:
            logger.error(f"执行技能失败: {skill_id}, 错误: {e}")
            return {
                "success": False,
                "skill_id": skill_id,
                "error": f"执行失败: {str(e)}"
            }
    
    async def _safe_execute(self, execute_func: Callable, input_data: Dict[str, Any]) -> Any:
        """安全执行技能函数"""
        # 检查函数是否为异步函数
        if inspect.iscoroutinefunction(execute_func):
            return await execute_func(input_data)
        else:
            # 同步函数在异步环境中执行
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, execute_func, input_data)
    
    def is_skill_loaded(self, skill_id: str) -> bool:
        """检查技能是否已加载"""
        return skill_id in self.skills and self.skills[skill_id]["loaded"]
    
    def get_loaded_skills(self) -> List[str]:
        """获取已加载的技能ID列表"""
        return [skill_id for skill_id, skill_info in self.skills.items() if skill_info["loaded"]]
    
    async def unload_skill(self, skill_id: str) -> bool:
        """卸载技能"""
        if skill_id not in self.skills:
            return False
        
        try:
            # 从模块字典中移除
            if skill_id in self.skill_modules:
                del self.skill_modules[skill_id]
            
            # 更新技能状态
            self.skills[skill_id]["loaded"] = False
            self.skills[skill_id]["module"] = None
            
            logger.info(f"技能卸载成功: {skill_id}")
            return True
            
        except Exception as e:
            logger.error(f"卸载技能失败: {skill_id}, 错误: {e}")
            return False
    
    async def get_skill_functions(self, skill_id: str) -> List[Dict[str, Any]]:
        """获取技能提供的函数列表"""
        if skill_id not in self.skill_modules:
            return []
        
        module = self.skill_modules[skill_id]
        functions = []
        
        # 查找所有公共函数（不以_开头）
        for name in dir(module):
            if name.startswith('_'):
                continue
            
            obj = getattr(module, name)
            if callable(obj):
                # 获取函数信息
                func_info = {
                    "name": name,
                    "doc": obj.__doc__ or "",
                    "signature": str(inspect.signature(obj))
                }
                functions.append(func_info)
        
        return functions
    
    async def call_skill_function(self, skill_id: str, function_name: str, 
                                args: List[Any] = None, kwargs: Dict[str, Any] = None) -> Any:
        """调用技能中的特定函数"""
        if skill_id not in self.skill_modules:
            raise ValueError(f"技能未加载: {skill_id}")
        
        module = self.skill_modules[skill_id]
        
        if not hasattr(module, function_name):
            raise ValueError(f"函数不存在: {function_name}")
        
        func = getattr(module, function_name)
        
        if not callable(func):
            raise ValueError(f"不是可调用函数: {function_name}")
        
        args = args or []
        kwargs = kwargs or {}
        
        # 安全调用函数
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)


# 创建全局技能注册表实例
skill_registry = SkillRegistry()