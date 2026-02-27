"""知识库适配器

将现有知识库系统适配到 MCP 协议。
"""

import logging
from typing import Dict, Any, List
import asyncio

from .base import BaseAdapter

logger = logging.getLogger(__name__)


class KnowledgeAdapter(BaseAdapter):
    """知识库适配器
    
    将知识库系统适配为 MCP 资源和工具。
    
    Attributes:
        knowledge_service: 知识库服务实例
    """
    
    def __init__(self, knowledge_service=None):
        """初始化知识库适配器
        
        Args:
            knowledge_service: 知识库服务实例，如果为 None 则延迟加载
        """
        super().__init__("knowledge_adapter")
        self._knowledge_service = knowledge_service
        
    @property
    def knowledge_service(self):
        """获取知识库服务（延迟加载）"""
        if self._knowledge_service is None:
            try:
                # 尝试导入知识库服务
                # 注意：这里需要根据实际的知识库模块进行调整
                from app.modules.knowledge.services.knowledge_service import KnowledgeService
                self._knowledge_service = KnowledgeService()
            except Exception as e:
                logger.warning(f"加载 KnowledgeService 失败: {e}")
                self._knowledge_service = None
        return self._knowledge_service
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """获取知识库相关工具
        
        Returns:
            MCP 格式的工具列表
        """
        tools = [
            {
                'name': 'knowledge_search',
                'description': '在知识库中搜索相关内容',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'query': {
                            'type': 'string',
                            'description': '搜索查询'
                        },
                        'knowledge_base_id': {
                            'type': 'string',
                            'description': '知识库ID（可选）'
                        },
                        'limit': {
                            'type': 'integer',
                            'description': '返回结果数量限制',
                            'default': 5
                        }
                    },
                    'required': ['query']
                }
            },
            {
                'name': 'knowledge_query',
                'description': '查询知识库中的特定信息',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'question': {
                            'type': 'string',
                            'description': '问题'
                        },
                        'context': {
                            'type': 'string',
                            'description': '额外上下文'
                        }
                    },
                    'required': ['question']
                }
            }
        ]
        
        return tools
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """执行知识库工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            if tool_name == 'knowledge_search':
                return await self._execute_search(arguments)
            elif tool_name == 'knowledge_query':
                return await self._execute_query(arguments)
            else:
                raise ValueError(f"未知工具: {tool_name}")
        except Exception as e:
            logger.error(f"执行知识库工具失败 {tool_name}: {e}", exc_info=True)
            raise
    
    async def _execute_search(self, arguments: Dict[str, Any]) -> str:
        """执行知识库搜索
        
        Args:
            arguments: 搜索参数
            
        Returns:
            搜索结果
        """
        query = arguments.get('query', '')
        knowledge_base_id = arguments.get('knowledge_base_id')
        limit = arguments.get('limit', 5)
        
        try:
            if self.knowledge_service:
                # 调用知识库服务进行搜索
                results = await self.knowledge_service.search(
                    query=query,
                    knowledge_base_id=knowledge_base_id,
                    limit=limit
                )
                
                # 格式化结果
                formatted_results = []
                for i, result in enumerate(results, 1):
                    formatted_results.append(
                        f"[{i}] {result.get('title', '无标题')}\n"
                        f"    {result.get('content', '')[:200]}...\n"
                        f"    相关度: {result.get('score', 0):.2f}"
                    )
                
                return "\n\n".join(formatted_results) if formatted_results else "未找到相关结果"
            else:
                # 模拟搜索结果
                return f"搜索 '{query}' 的结果（知识库服务未连接）:\n\n暂无搜索结果。"
        except Exception as e:
            logger.error(f"知识库搜索失败: {e}")
            return f"搜索失败: {str(e)}"
    
    async def _execute_query(self, arguments: Dict[str, Any]) -> str:
        """执行知识库查询
        
        Args:
            arguments: 查询参数
            
        Returns:
            查询结果
        """
        question = arguments.get('question', '')
        context = arguments.get('context', '')
        
        try:
            if self.knowledge_service:
                # 调用知识库服务进行查询
                result = await self.knowledge_service.query(
                    question=question,
                    context=context
                )
                
                return result.get('answer', '无法找到答案')
            else:
                return f"查询 '{question}' 的结果（知识库服务未连接）:\n\n暂无法回答此问题。"
        except Exception as e:
            logger.error(f"知识库查询失败: {e}")
            return f"查询失败: {str(e)}"
    
    async def get_resources(self) -> List[Dict[str, Any]]:
        """获取知识库资源列表
        
        Returns:
            资源列表
        """
        resources = []
        
        try:
            if self.knowledge_service:
                # 获取知识库列表
                knowledge_bases = await self.knowledge_service.get_knowledge_bases()
                
                for kb in knowledge_bases:
                    kb_id = kb.get('id')
                    kb_name = kb.get('name', '未命名知识库')
                    
                    resources.append({
                        'uri': f'knowledge://{kb_id}',
                        'name': kb_name,
                        'description': kb.get('description', f'知识库: {kb_name}'),
                        'mimeType': 'application/json'
                    })
        except Exception as e:
            logger.error(f"获取知识库资源失败: {e}", exc_info=True)
        
        return resources
    
    async def read_resource(self, uri: str) -> str:
        """读取知识库资源
        
        Args:
            uri: 资源 URI
            
        Returns:
            资源内容
        """
        try:
            if not uri.startswith('knowledge://'):
                raise ValueError(f"无效的知识库 URI: {uri}")
            
            kb_id = uri[12:]  # 移除 'knowledge://' 前缀
            
            if self.knowledge_service:
                kb_info = await self.knowledge_service.get_knowledge_base(kb_id)
                
                if kb_info:
                    return f"""知识库: {kb_info.get('name', '未命名')}
描述: {kb_info.get('description', '无描述')}
文档数量: {kb_info.get('document_count', 0)}
创建时间: {kb_info.get('created_at', '未知')}
"""
                else:
                    return f"知识库不存在: {kb_id}"
            else:
                return f"知识库信息（服务未连接）:\nID: {kb_id}"
        except Exception as e:
            logger.error(f"读取知识库资源失败 {uri}: {e}")
            raise
    
    async def get_prompts(self) -> List[Dict[str, Any]]:
        """获取知识库相关提示模板
        
        Returns:
            提示模板列表
        """
        prompts = [
            {
                'name': 'knowledge_search_prompt',
                'description': '使用知识库搜索的提示模板',
                'arguments': [
                    {
                        'name': 'topic',
                        'description': '搜索主题',
                        'required': True
                    }
                ]
            },
            {
                'name': 'knowledge_qa_prompt',
                'description': '基于知识库回答问题的提示模板',
                'arguments': [
                    {
                        'name': 'question',
                        'description': '问题',
                        'required': True
                    }
                ]
            }
        ]
        
        return prompts
    
    async def get_prompt_content(self, name: str, arguments: Dict[str, Any]) -> str:
        """获取提示模板内容
        
        Args:
            name: 模板名称
            arguments: 模板参数
            
        Returns:
            提示模板内容
        """
        if name == 'knowledge_search_prompt':
            topic = arguments.get('topic', '')
            return f"""请在知识库中搜索关于 "{topic}" 的相关信息。

请使用 knowledge_search 工具来查找相关内容，并总结关键信息。"""
        
        elif name == 'knowledge_qa_prompt':
            question = arguments.get('question', '')
            return f"""请基于知识库回答以下问题：

问题：{question}

请先使用 knowledge_search 工具搜索相关信息，然后基于搜索结果给出准确回答。
如果知识库中没有相关信息，请明确说明。"""
        
        else:
            return f"未知提示模板: {name}"
