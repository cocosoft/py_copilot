"""微服务API网关"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import asyncio
from typing import Dict, Any, List
import json

from app.core.microservices import get_service_registry, MicroserviceConfig, CircuitBreaker


class APIGateway:
    """API网关管理器"""
    
    def __init__(self):
        self.service_registry = get_service_registry()
        self.http_client = httpx.AsyncClient()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    async def route_request(self, service_name: str, path: str, method: str, 
                          headers: Dict[str, str], body: Any) -> Dict[str, Any]:
        """路由请求到目标微服务"""
        
        # 发现目标服务
        service_config = await self.service_registry.discover_service(service_name)
        if not service_config:
            raise HTTPException(status_code=503, detail=f"服务 {service_name} 不可用")
        
        # 获取或创建断路器
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        
        circuit_breaker = self.circuit_breakers[service_name]
        
        # 构建目标URL
        target_url = f"http://{service_config.host}:{service_config.port}{service_config.api_prefix}{path}"
        
        async def make_request():
            """执行HTTP请求"""
            try:
                response = await self.http_client.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    json=body if body else None,
                    timeout=30.0
                )
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text,
                    "success": response.status_code < 400
                }
            except httpx.TimeoutException:
                raise HTTPException(status_code=504, detail="服务请求超时")
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"服务调用失败: {str(e)}")
        
        # 使用断路器执行请求
        try:
            result = await circuit_breaker.execute(make_request)
            return result
        except Exception as e:
            raise e
    
    async def health_check(self) -> Dict[str, Any]:
        """网关健康检查"""
        services = await self.service_registry.get_all_services()
        
        health_status = {
            "status": "healthy",
            "services": {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # 检查每个服务的健康状态
        for service_name, config in services.items():
            try:
                health_url = f"http://{config.host}:{config.port}{config.health_check_path}"
                response = await self.http_client.get(health_url, timeout=5.0)
                
                health_status["services"][service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                    "last_check": asyncio.get_event_loop().time()
                }
                
                if response.status_code != 200:
                    health_status["status"] = "degraded"
                    
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "unreachable",
                    "error": str(e),
                    "last_check": asyncio.get_event_loop().time()
                }
                health_status["status"] = "degraded"
        
        return health_status


# 创建网关实例
api_gateway = APIGateway()


# 创建网关应用
gateway_app = FastAPI(
    title="Py Copilot API Gateway",
    version="1.0.0",
    description="微服务API网关"
)

# 添加CORS中间件
gateway_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@gateway_app.get("/health")
async def gateway_health():
    """网关健康检查"""
    health_status = await api_gateway.health_check()
    return health_status


@gateway_app.get("/services")
async def list_services():
    """列出所有可用服务"""
    services = await api_gateway.service_registry.get_all_services()
    return {
        "services": {name: config.dict() for name, config in services.items()}
    }


@gateway_app.api_route("/logos/{path:path}", methods=["GET", "HEAD"])
async def serve_logo(path: str, request: Request):
    """服务静态图片文件"""
    # 构建完整的文件路径
    logo_path = os.path.join(r"E:\PY\CODES\py copilot IV\frontend\public\logos", path)
    
    # 添加日志调试
    print(f"Serving logo request: method={request.method}, path={path}, logo_path={logo_path}")
    
    # 检查文件是否存在
    if not os.path.exists(logo_path):
        print(f"Logo file not found: {logo_path}")
        # 检查是否是agents目录下的请求，如果是，则返回默认图标
        if "agents" in path.split("/"):
            default_agent_logo = os.path.join(r"E:\PY\CODES\py copilot IV\frontend\public\logos\agents", "default.png")
            if os.path.exists(default_agent_logo):
                print(f"Using default agent logo: {default_agent_logo}")
                if request.method == "HEAD":
                    return Response(
                        status_code=200,
                        headers={
                            "Content-Type": "image/png",
                            "Content-Length": str(os.path.getsize(default_agent_logo))
                        }
                    )
                else:
                    return FileResponse(default_agent_logo)
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if request.method == "HEAD":
        # For HEAD requests, just return headers without content
        return Response(
            status_code=200,
            headers={
                "Content-Type": "image/png",
                "Content-Length": str(os.path.getsize(logo_path))
            }
        )
    else:
        # 返回文件
        print(f"Serving logo file: {logo_path}")
        return FileResponse(logo_path)


@gateway_app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_api_v1_request(path: str, request: Request):
    """代理/api/v1 API请求到目标微服务"""
    # 直接调用现有的proxy_v1_request函数处理请求
    return await proxy_v1_request(path, request)

@gateway_app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_v1_request(path: str, request: Request):
    """代理v1 API请求到目标微服务"""
    
    # 根据路径映射到对应的微服务
    service_mapping = {
        "search": "search",
        "files": "file",
        "voice": "voice",
        "image": "image",
        "monitoring": "monitoring",
        "enhanced-chat": "enhanced_chat"
    }
    
    # 确定目标服务
    path_parts = path.split('/')
    
    # 检查是否是供应商、模型、对话、知识、工作流、搜索或主题相关的API请求
    if path_parts and path_parts[0] in ["suppliers", "suppliers-list", "models", "model-capabilities", "capability-types", "capability-dimensions", "model-management", "default-model", "default-models", "parameter-template", "parameter-templates", "parameter-normalization-rules", "parameter-mappings", "system-parameters", "model-categories", "category-templates", "categories", "agents", "agent-categories", "agent-parameters", "search-management", "skills", "external-skills", "conversations", "topics", "knowledge", "knowledge-graph", "workflows", "executions", "search", "memory"]:
        # 这些请求应该由主应用程序处理，直接转发到主应用程序的端口
        try:
            # 获取请求信息
            method = request.method
            headers = dict(request.headers)
            
            # 移除不需要转发的头
            headers_to_remove = ["host", "content-length"]
            for header in headers_to_remove:
                headers.pop(header, None)
            
            # 获取请求体
            body = None
            if method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.json()
                except:
                    body = None
            
            # 直接转发到主应用程序（运行在配置的端口上）
            from app.core.config import Settings
            settings = Settings()
            target_url = f"http://localhost:{settings.gateway_port}/api/v1/{path}"
            
            # 检查是否是流式请求
            if path.endswith("stream"):
                # 使用流式请求
                async def stream_response():
                    try:
                        async with api_gateway.http_client.stream(
                            method=method,
                            url=target_url,
                            headers=headers,
                            json=body if body else None,
                            timeout=60.0  # 增加超时时间以支持思维链模型
                        ) as response:
                            # 确保设置正确的流式响应头
                            response_headers = dict(response.headers)
                            response_headers.setdefault("Content-Type", "text/event-stream")
                            response_headers.setdefault("X-Accel-Buffering", "no")
                            response_headers.setdefault("Cache-Control", "no-cache")
                            response_headers.setdefault("Connection", "keep-alive")
                            
                            # 逐块读取并转发响应数据
                            async for chunk in response.aiter_bytes():
                                if chunk:
                                    yield chunk
                    except Exception as e:
                        # 发送错误信息到客户端，使用json.dumps确保格式正确
                        error_data = {"type": "error", "content": f"网关流式响应失败: {str(e)}"}
                        error_msg = f"data: {json.dumps(error_data)}\n\n"
                        yield error_msg.encode('utf-8')
                
                # 返回流式响应
                return StreamingResponse(
                    stream_response(),
                    media_type="text/event-stream",
                    headers={
                        "Content-Type": "text/event-stream",
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no"
                    }
                )
            else:
                # 普通请求
                response = await api_gateway.http_client.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    json=body if body else None,
                    timeout=30.0
                )
                
                # 返回响应
                return JSONResponse(
                    content=json.loads(response.text) if response.text else {},
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"主应用程序请求失败: {str(e)}")
    # 其他请求路由到相应的微服务
    elif path_parts and path_parts[0] in service_mapping:
        service_name = service_mapping[path_parts[0]]
        # 移除服务标识部分
        remaining_path = '/'.join(path_parts[1:]) if len(path_parts) > 1 else ""
    else:
        raise HTTPException(status_code=404, detail="Not Found")
    
    # 获取请求信息
    method = request.method
    headers = dict(request.headers)
    
    # 移除不需要转发的头
    headers_to_remove = ["host", "content-length"]
    for header in headers_to_remove:
        headers.pop(header, None)
    
    # 获取请求体
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
            body = None
    
    # 路由请求
    try:
        result = await api_gateway.route_request(service_name, f"/{remaining_path}", method, headers, body)
        
        # 返回响应
        return JSONResponse(
            content=json.loads(result["content"]) if result["content"] else {},
            status_code=result["status_code"],
            headers=result["headers"]
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"网关内部错误: {str(e)}")


@gateway_app.api_route("/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(service_name: str, path: str, request: Request):
    """代理请求到目标微服务"""
    
    # 获取请求信息
    method = request.method
    headers = dict(request.headers)
    
    # 移除不需要转发的头
    headers_to_remove = ["host", "content-length"]
    for header in headers_to_remove:
        headers.pop(header, None)
    
    # 获取请求体
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except:
            body = None
    
    # 路由请求
    try:
        result = await api_gateway.route_request(service_name, f"/{path}", method, headers, body)
        
        # 返回响应
        return JSONResponse(
            content=json.loads(result["content"]) if result["content"] else {},
            status_code=result["status_code"],
            headers=result["headers"]
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"网关内部错误: {str(e)}")


@gateway_app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("API网关启动完成")


@gateway_app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    await api_gateway.http_client.aclose()
    print("API网关已关闭")