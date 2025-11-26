"""应用中间件配置"""
from fastapi import Request
from fastapi.responses import JSONResponse
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next):
    """日志中间件，记录请求信息"""
    start_time = time.time()
    
    # 记录请求信息
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # 处理请求
    try:
        response = await call_next(request)
    except Exception as e:
        # 记录异常
        logger.error(f"Error processing request: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 在响应头中添加处理时间
    response.headers["X-Process-Time"] = str(process_time)
    
    # 记录响应信息
    logger.info(f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    
    return response


async def cors_middleware(request: Request, call_next):
    """跨域资源共享中间件（这是一个示例，实际项目中FastAPI有内置的CORSMiddleware）"""
    if request.method == "OPTIONS":
        return JSONResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        )
    
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response