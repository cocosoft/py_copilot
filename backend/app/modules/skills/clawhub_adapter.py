"""
ClawHub 技能适配器

将 ClawHub 技能适配到 Py Copilot 工具系统
"""

import os
import json
import subprocess
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import shutil

from app.modules.function_calling.base_tool import BaseTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)
from app.modules.skills.skill_models import (
    SkillMetadata,
    SkillConfig,
    SkillExecutionResult,
    SkillStatus
)

logger = logging.getLogger(__name__)


class ClawHubSkillAdapter(BaseTool):
    """
    ClawHub 技能适配器
    
    将 ClawHub 技能包装为 Py Copilot 工具
    通过调用 Node.js 进程执行技能
    """
    
    def __init__(self, skill_path: str, skill_metadata: SkillMetadata, skill_config: SkillConfig):
        """
        初始化适配器
        
        Args:
            skill_path: 技能安装路径
            skill_metadata: 技能元数据
            skill_config: 技能配置
        """
        self.skill_path = skill_path
        self.skill_metadata = skill_metadata
        self.skill_config = skill_config
        self._parameters: List[ToolParameter] = []
        super().__init__()
        
        # 加载参数定义
        self._load_parameters()
    
    def _load_parameters(self):
        """从技能配置加载参数定义"""
        try:
            # 尝试读取技能的 package.json 或 skill.json
            config_files = ['skill.json', 'package.json', 'config.json']
            
            for config_file in config_files:
                config_path = os.path.join(self.skill_path, config_file)
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        
                        # 提取参数定义
                        if 'parameters' in config:
                            for param in config['parameters']:
                                self._parameters.append(ToolParameter(
                                    name=param.get('name', ''),
                                    type=param.get('type', 'string'),
                                    description=param.get('description', ''),
                                    required=param.get('required', False),
                                    default=param.get('default'),
                                    enum=param.get('enum')
                                ))
                        break
                        
        except Exception as e:
            logger.warning(f"加载技能参数失败: {str(e)}")
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        # 映射技能类别到工具类别
        category_map = {
            'ai': ToolCategory.UTILITY.value,
            'coding': ToolCategory.CODE.value,
            'search': ToolCategory.SEARCH.value,
            'productivity': ToolCategory.UTILITY.value,
            'browser': ToolCategory.UTILITY.value,
            'data': ToolCategory.DATA.value,
            'automation': ToolCategory.UTILITY.value,
            'communication': ToolCategory.UTILITY.value,
            'media': ToolCategory.IMAGE.value,
            'security': ToolCategory.UTILITY.value
        }
        
        return ToolMetadata(
            name=f"clawhub_{self.skill_metadata.name}",
            display_name=self.skill_metadata.display_name,
            description=self.skill_metadata.description,
            category=category_map.get(self.skill_metadata.category, ToolCategory.UTILITY.value),
            version=self.skill_metadata.version,
            author=self.skill_metadata.author,
            icon=self.skill_metadata.icon,
            tags=self.skill_metadata.tags + ['clawhub', 'skill'],
            is_active=True
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        """
        获取工具参数定义
        
        Returns:
            List[ToolParameter]: 参数定义列表
        """
        # 如果没有加载到参数，提供通用参数
        if not self._parameters:
            return [
                ToolParameter(
                    name="input",
                    type="string",
                    description="技能输入",
                    required=False
                ),
                ToolParameter(
                    name="options",
                    type="object",
                    description="技能选项",
                    required=False
                )
            ]
        
        return self._parameters
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行技能
        
        Args:
            **kwargs: 执行参数
            
        Returns:
            ToolExecutionResult: 执行结果
        """
        import time
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
            
            # 构建执行命令
            command = self._build_command(kwargs)
            
            # 设置环境变量
            env = os.environ.copy()
            env.update(self.skill_config.environment_variables)
            
            # 执行技能
            logger.info(f"执行 ClawHub 技能: {self.skill_metadata.name}")
            
            process = subprocess.run(
                command,
                cwd=self.skill_path,
                capture_output=True,
                text=True,
                timeout=self.skill_config.timeout,
                env=env
            )
            
            execution_time = time.time() - start_time
            
            # 解析输出
            if process.returncode == 0:
                try:
                    # 尝试解析 JSON 输出
                    output = json.loads(process.stdout)
                except json.JSONDecodeError:
                    output = process.stdout
                
                return ToolExecutionResult.success_result(
                    tool_name=tool_name,
                    result={
                        "output": output,
                        "stdout": process.stdout,
                        "stderr": process.stderr
                    },
                    execution_time=execution_time
                )
            else:
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"技能执行失败: {process.stderr}",
                    error_code="SKILL_EXECUTION_ERROR",
                    execution_time=execution_time
                )
                
        except subprocess.TimeoutExpired:
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"技能执行超时（超过{self.skill_config.timeout}秒）",
                error_code="TIMEOUT_ERROR",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"技能执行异常: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"执行异常: {str(e)}",
                error_code="EXECUTION_EXCEPTION",
                execution_time=time.time() - start_time
            )
    
    def _build_command(self, parameters: Dict[str, Any]) -> List[str]:
        """
        构建执行命令
        
        Args:
            parameters: 执行参数
            
        Returns:
            List[str]: 命令列表
        """
        runtime = self.skill_config.runtime
        entry_point = self.skill_config.entry_point
        
        command = [runtime, entry_point]
        
        # 添加参数
        if parameters:
            # 将参数转换为 JSON 字符串
            param_json = json.dumps(parameters, ensure_ascii=False)
            command.extend(['--params', param_json])
        
        return command
    
    def get_skill_info(self) -> Dict[str, Any]:
        """
        获取技能信息
        
        Returns:
            Dict[str, Any]: 技能信息
        """
        return {
            "metadata": self.skill_metadata.dict(),
            "config": self.skill_config.dict(),
            "path": self.skill_path,
            "tool_metadata": self._metadata.dict(),
            "parameters": [p.dict() for p in self._parameters]
        }


class ClawHubSkillInstaller:
    """
    ClawHub 技能安装器
    
    负责从 ClawHub 安装技能
    """
    
    def __init__(self, skills_dir: str):
        """
        初始化安装器
        
        Args:
            skills_dir: 技能安装目录
        """
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(parents=True, exist_ok=True)
    
    def install_from_npm(self, skill_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        从 npm 安装技能
        
        Args:
            skill_name: 技能名称
            version: 版本号
            
        Returns:
            Dict[str, Any]: 安装结果
        """
        try:
            # 构建安装路径
            install_path = self.skills_dir / skill_name
            
            # 如果已存在，先删除
            if install_path.exists():
                shutil.rmtree(install_path)
            
            # 使用 npm 安装
            package_spec = f"{skill_name}@{version}" if version else skill_name
            
            logger.info(f"安装技能: {package_spec}")
            
            process = subprocess.run(
                ['npm', 'install', package_spec, '--prefix', str(install_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"npm 安装失败: {process.stderr}"
                }
            
            # 解析技能配置
            metadata, config = self._parse_skill_config(install_path, skill_name)
            
            return {
                "success": True,
                "skill_name": skill_name,
                "installed_path": str(install_path),
                "metadata": metadata.dict(),
                "config": config.dict()
            }
            
        except Exception as e:
            logger.error(f"安装技能失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def install_from_git(self, git_url: str, skill_name: Optional[str] = None) -> Dict[str, Any]:
        """
        从 Git 仓库安装技能
        
        Args:
            git_url: Git 仓库地址
            skill_name: 技能名称（可选）
            
        Returns:
            Dict[str, Any]: 安装结果
        """
        try:
            # 从 URL 提取技能名称
            if not skill_name:
                skill_name = git_url.split('/')[-1].replace('.git', '')
            
            install_path = self.skills_dir / skill_name
            
            # 如果已存在，先删除
            if install_path.exists():
                shutil.rmtree(install_path)
            
            # 克隆仓库
            logger.info(f"克隆技能仓库: {git_url}")
            
            process = subprocess.run(
                ['git', 'clone', git_url, str(install_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Git 克隆失败: {process.stderr}"
                }
            
            # 安装依赖
            if (install_path / 'package.json').exists():
                subprocess.run(
                    ['npm', 'install'],
                    cwd=str(install_path),
                    capture_output=True,
                    timeout=120
                )
            
            # 解析技能配置
            metadata, config = self._parse_skill_config(install_path, skill_name)
            
            return {
                "success": True,
                "skill_name": skill_name,
                "installed_path": str(install_path),
                "metadata": metadata.dict(),
                "config": config.dict()
            }
            
        except Exception as e:
            logger.error(f"安装技能失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_skill_config(self, skill_path: Path, skill_name: str) -> tuple:
        """
        解析技能配置
        
        Args:
            skill_path: 技能路径
            skill_name: 技能名称
            
        Returns:
            tuple: (SkillMetadata, SkillConfig)
        """
        # 默认配置
        metadata = SkillMetadata(
            name=skill_name,
            display_name=skill_name,
            description=f"ClawHub 技能: {skill_name}",
            category="utility"
        )
        
        config = SkillConfig(
            entry_point="index.js",
            runtime="node"
        )
        
        # 尝试读取 package.json
        package_json_path = skill_path / 'package.json'
        if package_json_path.exists():
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
                
                metadata.display_name = package_data.get('name', skill_name)
                metadata.description = package_data.get('description', '')
                metadata.version = package_data.get('version', '1.0.0')
                metadata.author = package_data.get('author', '')
                
                # 提取入口点
                if 'main' in package_data:
                    config.entry_point = package_data['main']
                
                # 提取依赖
                if 'dependencies' in package_data:
                    config.dependencies = list(package_data['dependencies'].keys())
        
        # 尝试读取 skill.json
        skill_json_path = skill_path / 'skill.json'
        if skill_json_path.exists():
            with open(skill_json_path, 'r', encoding='utf-8') as f:
                skill_data = json.load(f)
                
                if 'metadata' in skill_data:
                    metadata_dict = skill_data['metadata']
                    metadata.display_name = metadata_dict.get('displayName', metadata.display_name)
                    metadata.description = metadata_dict.get('description', metadata.description)
                    metadata.category = metadata_dict.get('category', metadata.category)
                    metadata.tags = metadata_dict.get('tags', [])
                    metadata.icon = metadata_dict.get('icon', '🔧')
                
                if 'config' in skill_data:
                    config_dict = skill_data['config']
                    config.entry_point = config_dict.get('entryPoint', config.entry_point)
                    config.runtime = config_dict.get('runtime', config.runtime)
                    config.timeout = config_dict.get('timeout', 30)
                    config.permissions = config_dict.get('permissions', [])
        
        return metadata, config
    
    def uninstall(self, skill_name: str) -> bool:
        """
        卸载技能
        
        Args:
            skill_name: 技能名称
            
        Returns:
            bool: 是否成功
        """
        try:
            skill_path = self.skills_dir / skill_name
            
            if skill_path.exists():
                shutil.rmtree(skill_path)
                logger.info(f"技能已卸载: {skill_name}")
                return True
            else:
                logger.warning(f"技能不存在: {skill_name}")
                return False
                
        except Exception as e:
            logger.error(f"卸载技能失败: {str(e)}")
            return False
