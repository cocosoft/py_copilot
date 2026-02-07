"""API文档解析服务"""

from fastapi import APIRouter
from typing import List, Dict, Any, Optional
import inspect


class ApiDocumentService:
    
    def __init__(self, api_router=None):
        """初始化API文档服务"""
        self.api_router = api_router
    
    def extract_api_info(self) -> List[Dict[str, Any]]:
        """提取所有API信息"""
        if not self.api_router:
            return []
        
        api_list = []
        
        for route in self.api_router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                for method in route.methods:
                    if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        api_info = self._parse_route(route, method)
                        if api_info:
                            api_list.append(api_info)
        
        return api_list
    
    def _parse_route(self, route, method: str) -> Optional[Dict[str, Any]]:
        """解析单个路由"""
        try:
            endpoint = route.endpoint
            path = route.path
            
            docstring = inspect.getdoc(endpoint)
            summary, description = self._parse_docstring(docstring)
            
            tags = getattr(route, 'tags', [])
            
            module = self._determine_module(path)
            
            request_params = self._extract_request_params(endpoint)
            
            response_model = self._extract_response_model(endpoint)
            
            return {
                'path': path,
                'method': method,
                'summary': summary,
                'description': description,
                'tags': tags,
                'module': module,
                'request_params': request_params,
                'response_model': response_model
            }
        except Exception as e:
            return None
    
    def _parse_docstring(self, docstring: Optional[str]) -> tuple:
        """解析文档字符串"""
        if not docstring:
            return '', ''
        
        lines = docstring.strip().split('\n')
        summary = lines[0] if lines else ''
        description = '\n'.join(lines[1:]) if len(lines) > 1 else ''
        
        return summary, description
    
    def _determine_module(self, path: str) -> str:
        """根据路径确定模块"""
        parts = path.split('/')
        if len(parts) >= 3:
            return parts[2]
        return 'other'
    
    def _extract_request_params(self, endpoint) -> Dict[str, Any]:
        """提取请求参数"""
        try:
            sig = inspect.signature(endpoint)
            params = {}
            
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'request', 'db', 'current_user']:
                    continue
                
                param_info = {
                    'name': param_name,
                    'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                    'default': str(param.default) if param.default != inspect.Parameter.empty else None,
                    'required': param.default == inspect.Parameter.empty
                }
                params[param_name] = param_info
            
            return params
        except Exception:
            return {}
    
    def _extract_response_model(self, endpoint) -> Dict[str, Any]:
        """提取响应模型"""
        try:
            if hasattr(endpoint, '__annotations__') and 'return' in endpoint.__annotations__:
                return {
                    'type': str(endpoint.__annotations__['return'])
                }
            return {}
        except Exception:
            return {}
