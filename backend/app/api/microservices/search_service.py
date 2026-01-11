"""搜索微服务"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio

from app.core.microservices import MicroserviceConfig, get_service_registry
from app.services.knowledge.semantic_search_service import SemanticSearchService
from app.services.web_search_service import WebSearchService


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str
    search_type: str = "semantic"  # semantic, web, hybrid
    knowledge_base_ids: List[int] = []
    limit: int = 10
    similarity_threshold: float = 0.7
    include_metadata: bool = True


class SearchResult(BaseModel):
    """搜索结果模型"""
    id: str
    title: str
    content: str
    source: str  # knowledge_base, web, etc.
    similarity_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    url: Optional[str] = None


class SearchResponse(BaseModel):
    """搜索响应模型"""
    query: str
    search_type: str
    total_results: int
    results: List[SearchResult]
    processing_time: float


class SearchService:
    """搜索服务管理器"""
    
    def __init__(self):
        self.service_registry = get_service_registry()
        self.semantic_search_service = SemanticSearchService()
        self.web_search_service = WebSearchService()
    
    async def perform_search(self, search_request: SearchRequest) -> SearchResponse:
        """执行搜索"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if search_request.search_type == "semantic":
                results = await self._semantic_search(search_request)
            elif search_request.search_type == "web":
                results = await self._web_search(search_request)
            elif search_request.search_type == "hybrid":
                results = await self._hybrid_search(search_request)
            else:
                raise HTTPException(status_code=400, detail="不支持的搜索类型")
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return SearchResponse(
                query=search_request.query,
                search_type=search_request.search_type,
                total_results=len(results),
                results=results,
                processing_time=processing_time
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
    
    async def _semantic_search(self, search_request: SearchRequest) -> List[SearchResult]:
        """语义搜索"""
        try:
            # 调用语义搜索服务
            search_results = await self.semantic_search_service.search(
                query=search_request.query,
                knowledge_base_ids=search_request.knowledge_base_ids,
                limit=search_request.limit,
                similarity_threshold=search_request.similarity_threshold
            )
            
            # 转换为标准格式
            results = []
            for result in search_results:
                search_result = SearchResult(
                    id=f"semantic_{result.get('id', '')}",
                    title=result.get('title', ''),
                    content=result.get('content', ''),
                    source="knowledge_base",
                    similarity_score=result.get('similarity_score'),
                    metadata=result.get('metadata') if search_request.include_metadata else None
                )
                results.append(search_result)
            
            return results
            
        except Exception as e:
            print(f"语义搜索错误: {e}")
            return []
    
    async def _web_search(self, search_request: SearchRequest) -> List[SearchResult]:
        """网络搜索"""
        try:
            # 调用网络搜索服务
            web_results = await self.web_search_service.search(
                query=search_request.query,
                limit=search_request.limit
            )
            
            # 转换为标准格式
            results = []
            for result in web_results:
                search_result = SearchResult(
                    id=f"web_{result.get('id', '')}",
                    title=result.get('title', ''),
                    content=result.get('snippet', ''),
                    source="web",
                    url=result.get('url'),
                    metadata=result if search_request.include_metadata else None
                )
                results.append(search_result)
            
            return results
            
        except Exception as e:
            print(f"网络搜索错误: {e}")
            return []
    
    async def _hybrid_search(self, search_request: SearchRequest) -> List[SearchResult]:
        """混合搜索"""
        # 并行执行语义搜索和网络搜索
        semantic_task = asyncio.create_task(self._semantic_search(search_request))
        web_task = asyncio.create_task(self._web_search(search_request))
        
        semantic_results, web_results = await asyncio.gather(semantic_task, web_task)
        
        # 合并和去重结果
        all_results = semantic_results + web_results
        
        # 根据相关性分数排序
        all_results.sort(key=lambda x: x.similarity_score or 0, reverse=True)
        
        # 去重（基于内容相似性）
        unique_results = self._deduplicate_results(all_results)
        
        return unique_results[:search_request.limit]
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重搜索结果"""
        seen_content = set()
        unique_results = []
        
        for result in results:
            # 基于内容前100个字符进行去重
            content_preview = result.content[:100]
            if content_preview not in seen_content:
                seen_content.add(content_preview)
                unique_results.append(result)
        
        return unique_results
    
    async def index_document(self, document_data: Dict[str, Any]) -> bool:
        """索引文档"""
        try:
            # 调用语义搜索服务索引文档
            await self.semantic_search_service.index_document(document_data)
            return True
        except Exception as e:
            print(f"文档索引失败: {e}")
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            await self.semantic_search_service.delete_document(document_id)
            return True
        except Exception as e:
            print(f"文档删除失败: {e}")
            return False


# 创建搜索服务实例
search_service = SearchService()


# 创建搜索微服务应用
search_app = FastAPI(
    title="Py Copilot Search Service",
    version="1.0.0",
    description="搜索功能微服务"
)


@search_app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "search"}


@search_app.post("/search")
async def search_endpoint(search_request: SearchRequest):
    """搜索接口"""
    response = await search_service.perform_search(search_request)
    return response


@search_app.post("/index")
async def index_document(document_data: Dict[str, Any]):
    """索引文档接口"""
    success = await search_service.index_document(document_data)
    return {"success": success}


@search_app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """删除文档接口"""
    success = await search_service.delete_document(document_id)
    return {"success": success}


@search_app.get("/statistics")
async def get_statistics():
    """获取搜索统计信息"""
    # 这里可以返回搜索服务的统计信息
    return {
        "total_searches": 0,
        "average_response_time": 0,
        "indexed_documents": 0
    }


@search_app.on_event("startup")
async def startup_event():
    """服务启动事件"""
    # 注册服务到服务注册中心
    config = MicroserviceConfig(
        name="search-service",
        host="localhost",
        port=8002,
        description="搜索功能微服务"
    )
    
    await search_service.service_registry.register_service(config)
    print("搜索微服务启动完成")


@search_app.on_event("shutdown")
async def shutdown_event():
    """服务关闭事件"""
    print("搜索微服务已关闭")