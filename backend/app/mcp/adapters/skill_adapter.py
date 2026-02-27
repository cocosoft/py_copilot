"""技能适配器

将现有技能系统适配到 MCP 协议。
"""

import logging
from typing import Dict, Any, List
import asyncio

from .base import BaseAdapter

logger = logging.getLogger(__name__)


class SkillAdapter(BaseAdapter):
    """技能适配器
    
    将 SkillRegistry 中的技能适配为 MCP 工具。
    
    Attributes:
        skill_registry: 技能注册表实例
    """
    
    def __init__(self, skill_registry=None):
        """初始化技能适配器
        
        Args:
            skill_registry: 技能注册表实例，如果为 None 则延迟加载
        """
        super().__init__("skill_adapter")
        self._skill_registry = skill_registry
        self._skills_cache = None
        
    @property
    def skill_registry(self):
        """获取技能注册表（延迟加载）"""
        if self._skill_registry is None:
            try:
                from app.skills.skill_registry import SkillRegistry
                self._skill_registry = SkillRegistry()
            except Exception as e:
                logger.error(f"加载 SkillRegistry 失败: {e}")
                self._skill_registry = None
        return self._skill_registry
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """获取工具列表（技能作为工具）
        
        从 SkillRegistry 获取所有可用技能。
        
        Returns:
            MCP 格式的工具列表
        """
        tools = []
        
        try:
            if self.skill_registry:
                # 获取所有技能
                all_skills = self.skill_registry.get_all_skills()
                
                for skill_name, skill_info in all_skills.items():
                    # 转换参数格式
                    input_schema = self._convert_skill_to_schema(skill_info)
                    
                    tools.append({
                        'name': f"skill_{skill_name}",
                        'description': skill_info.get('description', f'执行 {skill_name} 技能'),
                        'inputSchema': input_schema
                    })
        except Exception as e:
            logger.error(f"获取技能列表失败: {e}", exc_info=True)
        
        return tools
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """执行工具（执行技能）
        
        调用 SkillRegistry 执行指定技能。
        
        Args:
            tool_name: 工具名称（格式：skill_<name>）
            arguments: 工具参数
            
        Returns:
            技能执行结果
        """
        try:
            if not self.skill_registry:
                raise RuntimeError("SkillRegistry 未初始化")
            
            # 移除 skill_ 前缀获取真实技能名
            skill_name = tool_name
            if skill_name.startswith('skill_'):
                skill_name = skill_name[6:]
            
            # 执行技能
            result = await self.skill_registry.execute_skill(skill_name, arguments)
            
            return result
        except Exception as e:
            logger.error(f"执行技能失败 {tool_name}: {e}", exc_info=True)
            raise
    
    def _convert_skill_to_schema(self, skill_info: Dict[str, Any]) -> Dict[str, Any]:
        """将技能信息转换为 JSON Schema
        
        Args:
            skill_info: 技能信息字典
            
        Returns:
            JSON Schema 格式
        """
        # 获取技能参数定义
        parameters = skill_info.get('parameters', [])
        
        properties = {}
        required = []
        
        for param in parameters:
            param_name = param.get('name')
            if not param_name:
                continue
            
            param_type = param.get('type', 'string')
            param_description = param.get('description', '')
            param_required = param.get('required', False)
            
            # 类型映射
            schema_type = self._map_type_to_json_schema(param_type)
            
            properties[param_name] = {
                'type': schema_type,
                'description': param_description
            }
            
            if param_required:
                required.append(param_name)
        
        # 如果没有定义参数，添加默认的 input 参数
        if not properties:
            properties['input'] = {
                'type': 'string',
                'description': '技能输入内容'
            }
        
        return {
            'type': 'object',
            'properties': properties,
            'required': required
        }
    
    def _map_type_to_json_schema(self, param_type: str) -> str:
        """将参数类型映射为 JSON Schema 类型
        
        Args:
            param_type: 参数类型
            
        Returns:
            JSON Schema 类型
        """
        type_mapping = {
            'string': 'string',
            'str': 'string',
            'integer': 'integer',
            'int': 'integer',
            'number': 'number',
            'float': 'number',
            'boolean': 'boolean',
            'bool': 'boolean',
            'array': 'array',
            'list': 'array',
            'object': 'object',
            'dict': 'object'
        }
        
        return type_mapping.get(param_type.lower(), 'string')
    
    async def get_prompts(self) -> List[Dict[str, Any]]:
        """获取提示模板列表
        
        将技能描述转换为提示模板。
        
        Returns:
            提示模板列表
        """
        prompts = []
        
        try:
            if self.skill_registry:
                all_skills = self.skill_registry.get_all_skills()
                
                for skill_name, skill_info in all_skills.items():
                    prompts.append({
                        'name': f"skill_prompt_{skill_name}",
                        'description': f"使用 {skill_name} 技能的提示模板",
                        'arguments': [
                            {
                                'name': 'context',
                                'description': '执行上下文',
                                'required': False
                            }
                        ]
                    })
        except Exception as e:
            logger.error(f"获取技能提示模板失败: {e}", exc_info=True)
        
        return prompts
    
    async def get_prompt_content(self, name: str, arguments: Dict[str, Any]) -> str:
        """获取提示模板内容
        
        Args:
            name: 模板名称
            arguments: 模板参数
            
        Returns:
            提示模板内容
        """
        # 移除 skill_prompt_ 前缀
        skill_name = name
        if skill_name.startswith('skill_prompt_'):
            skill_name = skill_name[13:]
        
        context = arguments.get('context', '')
        
        return f"""请使用技能 '{skill_name}' 来处理以下任务：

上下文信息：
{context}

请调用相应的技能工具来完成此任务。"""
