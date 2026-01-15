"""聊天微服务"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.microservices import (
    MicroserviceConfig, get_service_registry, get_message_queue, 
    ServiceRegistry, MessageQueue
)
from app.modules.memory.services.memory_service import MemoryService
from app.models.chat_enhancements import (
    StreamingResponse as StreamingResponseModel,
    Topic, ChainOfThought, UploadedFile, VoiceInput, SearchQuery
)
from app.core.database import get_db


class ChatRequest(BaseModel):
    """聊天请求模型"""
    conversation_id: int
    user_id: int
    message: str
    enable_streaming: bool = True
    enable_chain_of_thought: bool = False
    topic_id: Optional[int] = None
    file_ids: List[int] = []
    voice_input_id: Optional[int] = None
    search_enabled: bool = False
    search_query: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    message_id: int
    content: str
    is_streaming: bool
    chain_of_thought: Optional[str] = None
    topic_id: Optional[int] = None
    search_results: List[Dict[str, Any]] = []


class ChatService:
    """聊天服务管理器"""
    
    def __init__(self):
        self.service_registry: ServiceRegistry = get_service_registry()
        self.message_queue: MessageQueue = get_message_queue()
        self.memory_service = MemoryService()
        self.connected_websockets: Dict[str, WebSocket] = {}
    
    async def process_chat_message(self, chat_request: ChatRequest) -> ChatResponse:
        """处理聊天消息"""
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 1. 检索相关记忆
            relevant_memories = await self.memory_service.retrieve_relevant_memories(
                db=db,
                user_id=chat_request.user_id,
                query=chat_request.message,
                limit=5
            )
            
            # 2. 构建增强的上下文
            enhanced_context = await self._build_enhanced_context(
                chat_request, relevant_memories
            )
            
            # 3. 处理流式响应
            if chat_request.enable_streaming:
                return await self._handle_streaming_response(
                    chat_request, enhanced_context, db
                )
            else:
                return await self._handle_standard_response(
                    chat_request, enhanced_context, db
                )
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")
        finally:
            db.close()
    
    async def _build_enhanced_context(self, chat_request: ChatRequest, 
                                    memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建增强的对话上下文"""
        
        context = {
            "user_message": chat_request.message,
            "memories": memories,
            "topic_id": chat_request.topic_id,
            "file_ids": chat_request.file_ids,
            "voice_input_id": chat_request.voice_input_id,
            "search_enabled": chat_request.search_enabled,
            "search_query": chat_request.search_query
        }
        
        # 如果有话题ID，获取话题信息
        if chat_request.topic_id:
            db = next(get_db())
            try:
                topic = db.query(Topic).filter(Topic.id == chat_request.topic_id).first()
                if topic:
                    context["topic"] = {
                        "name": topic.topic_name,
                        "summary": topic.topic_summary
                    }
            finally:
                db.close()
        
        # 如果有文件，获取文件信息
        if chat_request.file_ids:
            db = next(get_db())
            try:
                files = db.query(UploadedFile).filter(
                    UploadedFile.id.in_(chat_request.file_ids)
                ).all()
                context["files"] = [
                    {
                        "id": file.id,
                        "filename": file.filename,
                        "file_type": file.file_type
                    } for file in files
                ]
            finally:
                db.close()
        
        return context
    
    async def _handle_streaming_response(self, chat_request: ChatRequest, 
                                       context: Dict[str, Any], db) -> ChatResponse:
        """处理流式响应"""
        
        # 创建消息记录
        from app.models.conversation import Message
        message = Message(
            conversation_id=chat_request.conversation_id,
            user_id=chat_request.user_id,
            content=chat_request.message,
            role="user"
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # 创建流式响应记录
        streaming_response = StreamingResponseModel(
            message_id=message.id,
            chunk_index=0,
            content_chunk="",
            is_final_chunk=False
        )
        db.add(streaming_response)
        db.commit()
        
        # 返回初始响应
        return ChatResponse(
            message_id=message.id,
            content="",
            is_streaming=True,
            topic_id=chat_request.topic_id
        )
    
    async def _handle_standard_response(self, chat_request: ChatRequest, 
                                      context: Dict[str, Any], db) -> ChatResponse:
        """处理标准响应"""
        
        # 创建消息记录
        from app.models.conversation import Message
        message = Message(
            conversation_id=chat_request.conversation_id,
            user_id=chat_request.user_id,
            content=chat_request.message,
            role="user"
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # 生成AI响应（这里简化处理，实际应该调用LLM服务）
        ai_response = await self._generate_ai_response(context)
        
        # 创建AI消息记录
        ai_message = Message(
            conversation_id=chat_request.conversation_id,
            user_id=chat_request.user_id,
            content=ai_response,
            role="assistant"
        )
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        
        # 处理思维链
        chain_of_thought = None
        if chat_request.enable_chain_of_thought:
            chain_of_thought = await self._generate_chain_of_thought(context, ai_response)
            
            # 保存思维链记录
            cot_record = ChainOfThought(
                message_id=ai_message.id,
                reasoning_chain=chain_of_thought,
                confidence_score=0.8
            )
            db.add(cot_record)
            db.commit()
        
        # 处理搜索
        search_results = []
        if chat_request.search_enabled and chat_request.search_query:
            search_results = await self._perform_search(chat_request.search_query)
            
            # 保存搜索记录
            search_record = SearchQuery(
                conversation_id=chat_request.conversation_id,
                query_text=chat_request.search_query,
                search_results=search_results
            )
            db.add(search_record)
            db.commit()
        
        return ChatResponse(
            message_id=ai_message.id,
            content=ai_response,
            is_streaming=False,
            chain_of_thought=chain_of_thought,
            topic_id=chat_request.topic_id,
            search_results=search_results
        )
    
    async def _generate_ai_response(self, context: Dict[str, Any]) -> str:
        """生成AI响应（简化版本）"""
        # 这里应该调用实际的LLM服务
        # 现在返回一个模拟响应
        return f"基于您的消息和上下文，我理解您想讨论: {context.get('user_message', '')}"
    
    async def _generate_chain_of_thought(self, context: Dict[str, Any], 
                                       response: str) -> str:
        """生成思维链（简化版本）"""
        # 这里应该调用支持思维链的模型
        return f"思考过程: 分析用户消息 -> 检索相关记忆 -> 生成响应 -> {response}"
    
    async def _perform_search(self, query: str) -> List[Dict[str, Any]]:
        """执行搜索（简化版本）"""
        # 这里应该调用搜索服务
        return [
            {
                "title": "搜索结果1",
                "content": f"与'{query}'相关的信息",
                "source": "知识库"
            }
        ]
    
    async def handle_websocket_connection(self, websocket: WebSocket, client_id: str):
        """处理WebSocket连接"""
        await websocket.accept()
        self.connected_websockets[client_id] = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # 处理不同类型的消息
                await self._handle_websocket_message(client_id, message_data)
                
        except WebSocketDisconnect:
            # 客户端断开连接
            self.connected_websockets.pop(client_id, None)
        except Exception as e:
            print(f"WebSocket错误: {e}")
            self.connected_websockets.pop(client_id, None)
    
    async def _handle_websocket_message(self, client_id: str, message_data: Dict[str, Any]):
        """处理WebSocket消息"""
        message_type = message_data.get("type")
        
        if message_type == "chat_message":
            # 处理聊天消息
            chat_request = ChatRequest(**message_data["data"])
            response = await self.process_chat_message(chat_request)
            
            # 发送响应
            websocket = self.connected_websockets.get(client_id)
            if websocket:
                await websocket.send_text(json.dumps({
                    "type": "chat_response",
                    "data": response.dict()
                }))
        
        elif message_type == "stream_chunk":
            # 处理流式响应块
            await self._handle_stream_chunk(client_id, message_data["data"])
    
    async def _handle_stream_chunk(self, client_id: str, chunk_data: Dict[str, Any]):
        """处理流式响应块"""
        # 这里可以处理流式响应的中间结果
        websocket = self.connected_websockets.get(client_id)
        if websocket:
            await websocket.send_text(json.dumps({
                "type": "stream_update",
                "data": chunk_data
            }))


# 创建聊天服务实例
chat_service = ChatService()


# 创建聊天微服务应用
chat_app = FastAPI(
    title="Py Copilot Chat Service",
    version="1.0.0",
    description="聊天功能微服务"
)


@chat_app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "chat"}


@chat_app.post("/chat")
async def chat_endpoint(chat_request: ChatRequest):
    """聊天接口"""
    response = await chat_service.process_chat_message(chat_request)
    return response


@chat_app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket连接"""
    await chat_service.handle_websocket_connection(websocket, client_id)


@chat_app.on_event("startup")
async def startup_event():
    """服务启动事件"""
    # 注册服务到服务注册中心
    config = MicroserviceConfig(
        name="chat-service",
        host="localhost",
        port=8001,
        description="聊天功能微服务"
    )
    
    # 尝试注册服务，即使失败也继续启动
    try:
        await chat_service.service_registry.register_service(config)
        print("聊天微服务已注册到服务注册中心")
    except Exception as e:
        print(f"服务注册失败，但服务将继续运行: {e}")
    
    print("聊天微服务启动完成")


@chat_app.on_event("shutdown")
async def shutdown_event():
    """服务关闭事件"""
    print("聊天微服务已关闭")