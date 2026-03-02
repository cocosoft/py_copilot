"""
技能管理器

管理 ClawHub 技能的注册、安装、执行和监控
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from app.modules.skills.skill_models import (
    SkillMetadata,
    SkillConfig,
    SkillInfo,
    SkillStatus,
    SkillSource,
    SkillExecutionRequest,
    SkillExecutionResult,
    SkillInstallResult,
    SkillSearchResult,
    SkillMarketItem
)
from app.modules.skills.clawhub_adapter import ClawHubSkillAdapter, ClawHubSkillInstaller
from app.modules.function_calling.tool_manager import tool_manager

logger = logging.getLogger(__name__)


class SkillManager:
    """
    技能管理器
    
    管理所有技能的注册、安装、执行和监控
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化技能管理器"""
        if SkillManager._initialized:
            return
        
        # 技能目录
        self.skills_dir = Path(__file__).parent / "installed"
        self.skills_dir.mkdir(exist_ok=True)
        
        # 技能注册表
        self._skills: Dict[str, SkillInfo] = {}
        self._adapters: Dict[str, ClawHubSkillAdapter] = {}
        
        # 安装器
        self._installer = ClawHubSkillInstaller(str(self.skills_dir))
        
        # 执行历史
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
        
        # 加载已安装的技能
        self._load_installed_skills()
        
        SkillManager._initialized = True
        logger.info("技能管理器初始化完成")
    
    def _load_installed_skills(self):
        """加载已安装的技能"""
        try:
            # 扫描技能目录
            for skill_dir in self.skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_name = skill_dir.name
                    self._load_skill(skill_name)
                    
        except Exception as e:
            logger.error(f"加载已安装技能失败: {str(e)}")
    
    def _load_skill(self, skill_name: str) -> bool:
        """
        加载单个技能
        
        Args:
            skill_name: 技能名称
            
        Returns:
            bool: 是否成功
        """
        try:
            skill_path = self.skills_dir / skill_name
            
            if not skill_path.exists():
                return False
            
            # 解析技能配置
            metadata, config = self._installer._parse_skill_config(skill_path, skill_name)
            
            # 创建技能信息
            skill_info = SkillInfo(
                metadata=metadata,
                config=config,
                status=SkillStatus.INSTALLED,
                installed_at=datetime.now()
            )
            
            # 创建适配器
            adapter = ClawHubSkillAdapter(
                skill_path=str(skill_path),
                skill_metadata=metadata,
                skill_config=config
            )
            
            # 注册到管理器
            self._skills[skill_name] = skill_info
            self._adapters[skill_name] = adapter
            
            # 注册到工具管理器
            tool_manager.register_tool(adapter)
            
            logger.info(f"技能已加载: {skill_name}")
            return True
            
        except Exception as e:
            logger.error(f"加载技能失败 {skill_name}: {str(e)}")
            return False
    
    def install_skill(
        self,
        skill_source: str,
        source_type: str = "npm",
        version: Optional[str] = None
    ) -> SkillInstallResult:
        """
        安装技能
        
        Args:
            skill_source: 技能来源（npm包名或git URL）
            source_type: 来源类型（npm/git）
            version: 版本号
            
        Returns:
            SkillInstallResult: 安装结果
        """
        try:
            if source_type == "npm":
                result = self._installer.install_from_npm(skill_source, version)
            elif source_type == "git":
                result = self._installer.install_from_git(skill_source)
            else:
                return SkillInstallResult(
                    success=False,
                    skill_name=skill_source,
                    message=f"不支持的来类型: {source_type}",
                    error="INVALID_SOURCE_TYPE"
                )
            
            if result["success"]:
                skill_name = result["skill_name"]
                
                # 重新加载技能
                self._load_skill(skill_name)
                
                return SkillInstallResult(
                    success=True,
                    skill_name=skill_name,
                    message=f"技能 '{skill_name}' 安装成功",
                    installed_path=result["installed_path"]
                )
            else:
                return SkillInstallResult(
                    success=False,
                    skill_name=skill_source,
                    message="安装失败",
                    error=result.get("error", "Unknown error")
                )
                
        except Exception as e:
            logger.error(f"安装技能失败: {str(e)}")
            return SkillInstallResult(
                success=False,
                skill_name=skill_source,
                message="安装异常",
                error=str(e)
            )
    
    def uninstall_skill(self, skill_name: str) -> bool:
        """
        卸载技能
        
        Args:
            skill_name: 技能名称
            
        Returns:
            bool: 是否成功
        """
        try:
            # 从安装器卸载
            success = self._installer.uninstall(skill_name)
            
            if success:
                # 从注册表移除
                if skill_name in self._skills:
                    del self._skills[skill_name]
                
                if skill_name in self._adapters:
                    del self._adapters[skill_name]
                
                logger.info(f"技能已卸载: {skill_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"卸载技能失败: {str(e)}")
            return False
    
    def get_skill(self, skill_name: str) -> Optional[SkillInfo]:
        """
        获取技能信息
        
        Args:
            skill_name: 技能名称
            
        Returns:
            Optional[SkillInfo]: 技能信息
        """
        return self._skills.get(skill_name)
    
    def get_skill_adapter(self, skill_name: str) -> Optional[ClawHubSkillAdapter]:
        """
        获取技能适配器
        
        Args:
            skill_name: 技能名称
            
        Returns:
            Optional[ClawHubSkillAdapter]: 技能适配器
        """
        return self._adapters.get(skill_name)
    
    def get_all_skills(self) -> List[SkillInfo]:
        """
        获取所有技能
        
        Returns:
            List[SkillInfo]: 技能列表
        """
        return list(self._skills.values())
    
    def get_skills_by_category(self, category: str) -> List[SkillInfo]:
        """
        按类别获取技能
        
        Args:
            category: 技能类别
            
        Returns:
            List[SkillInfo]: 技能列表
        """
        return [
            skill for skill in self._skills.values()
            if skill.metadata.category == category
        ]
    
    def get_active_skills(self) -> List[SkillInfo]:
        """
        获取激活的技能
        
        Returns:
            List[SkillInfo]: 技能列表
        """
        return [
            skill for skill in self._skills.values()
            if skill.status == SkillStatus.ACTIVE
        ]
    
    async def execute_skill(
        self,
        skill_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> SkillExecutionResult:
        """
        执行技能
        
        Args:
            skill_name: 技能名称
            parameters: 执行参数
            timeout: 超时时间
            
        Returns:
            SkillExecutionResult: 执行结果
        """
        import time
        start_time = time.time()
        
        # 检查技能是否存在
        skill = self._skills.get(skill_name)
        if not skill:
            return SkillExecutionResult(
                success=False,
                skill_name=skill_name,
                error=f"技能 '{skill_name}' 不存在",
                error_code="SKILL_NOT_FOUND",
                execution_time=time.time() - start_time
            )
        
        # 检查技能状态
        if skill.status == SkillStatus.ERROR:
            return SkillExecutionResult(
                success=False,
                skill_name=skill_name,
                error=f"技能 '{skill_name}' 处于错误状态",
                error_code="SKILL_ERROR",
                execution_time=time.time() - start_time
            )
        
        # 获取适配器
        adapter = self._adapters.get(skill_name)
        if not adapter:
            return SkillExecutionResult(
                success=False,
                skill_name=skill_name,
                error=f"技能适配器 '{skill_name}' 不存在",
                error_code="ADAPTER_NOT_FOUND",
                execution_time=time.time() - start_time
            )
        
        try:
            # 更新执行时间
            skill.last_executed_at = datetime.now()
            skill.execution_count += 1
            
            # 使用工具管理器执行
            tool_result = await tool_manager.execute_tool(
                f"clawhub_{skill_name}",
                **parameters
            )
            
            execution_time = time.time() - start_time
            
            # 记录执行历史
            self._record_execution(skill_name, parameters, tool_result)
            
            # 更新错误计数
            if not tool_result.success:
                skill.error_count += 1
            
            return SkillExecutionResult(
                success=tool_result.success,
                skill_name=skill_name,
                output=tool_result.result,
                error=tool_result.error,
                error_code=tool_result.error_code,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"执行技能失败 {skill_name}: {str(e)}")
            skill.error_count += 1
            
            return SkillExecutionResult(
                success=False,
                skill_name=skill_name,
                error=f"执行异常: {str(e)}",
                error_code="EXECUTION_EXCEPTION",
                execution_time=time.time() - start_time
            )
    
    def _record_execution(
        self,
        skill_name: str,
        parameters: Dict[str, Any],
        result: Any
    ):
        """
        记录执行历史
        
        Args:
            skill_name: 技能名称
            parameters: 执行参数
            result: 执行结果
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "skill_name": skill_name,
            "parameters": parameters,
            "success": result.success if hasattr(result, 'success') else False,
            "execution_time": result.execution_time if hasattr(result, 'execution_time') else 0
        }
        
        self._execution_history.append(record)
        
        # 限制历史记录大小
        if len(self._execution_history) > self._max_history_size:
            self._execution_history = self._execution_history[-self._max_history_size:]
    
    def enable_skill(self, skill_name: str) -> bool:
        """
        启用技能
        
        Args:
            skill_name: 技能名称
            
        Returns:
            bool: 是否成功
        """
        skill = self._skills.get(skill_name)
        if not skill:
            return False
        
        skill.status = SkillStatus.ACTIVE
        logger.info(f"技能已启用: {skill_name}")
        return True
    
    def disable_skill(self, skill_name: str) -> bool:
        """
        禁用技能
        
        Args:
            skill_name: 技能名称
            
        Returns:
            bool: 是否成功
        """
        skill = self._skills.get(skill_name)
        if not skill:
            return False
        
        skill.status = SkillStatus.INACTIVE
        logger.info(f"技能已禁用: {skill_name}")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total = len(self._skills)
        active = len(self.get_active_skills())
        
        # 按类别统计
        category_counts = {}
        for skill in self._skills.values():
            category = skill.metadata.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 执行统计
        total_executions = sum(s.execution_count for s in self._skills.values())
        total_errors = sum(s.error_count for s in self._skills.values())
        
        return {
            "total_skills": total,
            "active_skills": active,
            "inactive_skills": total - active,
            "category_distribution": category_counts,
            "execution_statistics": {
                "total_executions": total_executions,
                "total_errors": total_errors,
                "success_rate": round((total_executions - total_errors) / total_executions * 100, 2) if total_executions > 0 else 0
            }
        }
    
    def search_skills(self, query: str) -> SkillSearchResult:
        """
        搜索已安装的技能
        
        Args:
            query: 搜索关键词
            
        Returns:
            SkillSearchResult: 搜索结果
        """
        query = query.lower()
        
        matching_skills = []
        for skill in self._skills.values():
            # 搜索名称、描述、标签
            if (query in skill.metadata.name.lower() or
                query in skill.metadata.description.lower() or
                any(query in tag.lower() for tag in skill.metadata.tags)):
                
                matching_skills.append(SkillMarketItem(
                    name=skill.metadata.name,
                    display_name=skill.metadata.display_name,
                    description=skill.metadata.description,
                    version=skill.metadata.version,
                    author=skill.metadata.author,
                    category=skill.metadata.category,
                    tags=skill.metadata.tags,
                    repository_url=skill.metadata.repository_url or "",
                    updated_at=skill.updated_at or datetime.now()
                ))
        
        return SkillSearchResult(
            skills=matching_skills,
            total=len(matching_skills),
            query=query
        )


# 全局技能管理器实例
skill_manager = SkillManager()
