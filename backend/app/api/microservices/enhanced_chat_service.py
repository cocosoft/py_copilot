"""记忆增强流式响应API"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import BaseModel
from datetime import datetime

from app.core.microservices import (
    MicroserviceConfig, get_service_registry, get_message_queue, 
    ServiceRegistry, MessageQueue
)
from app.modules.memory.services.memory_service import MemoryService
from app.models.chat_enhancements import (
    StreamingResponse as StreamingResponseModel,
    ChainOfThought, UploadedFile, VoiceInput, SearchQuery
)
from app.core.database import get_db


class EnhancedChatRequest(BaseModel):
    """增强聊天请求模型"""
    conversation_id: int
    user_id: int
    message: str
    enable_streaming: bool = True
    enable_chain_of_thought: bool = False
    enable_memory_enhancement: bool = True
    memory_retrieval_limit: int = 5
    file_ids: List[int] = []
    voice_input_id: Optional[int] = None
    search_enabled: bool = False
    search_query: Optional[str] = None


class StreamChunk(BaseModel):
    """流式响应块模型"""
    chunk_id: int
    content: str
    is_final: bool = False
    memory_references: Optional[List[Dict[str, Any]]] = None
    reasoning_step: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EnhancedChatService:
    """增强聊天服务管理器"""
    
    def __init__(self):
        self.service_registry: ServiceRegistry = get_service_registry()
        self.message_queue: MessageQueue = get_message_queue()
        self.memory_service = MemoryService()
        self.connected_websockets: Dict[str, WebSocket] = {}
    
    async def process_enhanced_chat(self, chat_request: EnhancedChatRequest) -> StreamingResponse:
        """处理记忆增强的流式聊天"""
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 1. 检索相关记忆（如果启用记忆增强）
            relevant_memories = []
            if chat_request.enable_memory_enhancement:
                relevant_memories = await self._retrieve_relevant_memories(
                    chat_request.user_id, 
                    chat_request.message, 
                    chat_request.memory_retrieval_limit
                )
            
            # 2. 构建增强的上下文
            enhanced_context = await self._build_enhanced_context(
                chat_request, relevant_memories
            )
            
            # 3. 创建消息记录
            from app.models.conversation import Message, Topic
            # 获取活跃话题
            active_topic = db.query(Topic).filter(
                Topic.conversation_id == chat_request.conversation_id,
                Topic.is_active == True
            ).first()
            
            # 如果没有活跃话题，创建一个新话题
            if not active_topic:
                active_topic = Topic(
                    conversation_id=chat_request.conversation_id,
                    topic_name="新话题",
                    is_active=True
                )
                db.add(active_topic)
                db.commit()
                db.refresh(active_topic)
            
            message = Message(
                conversation_id=chat_request.conversation_id,
                user_id=chat_request.user_id,
                content=chat_request.message,
                role="user",
                topic_id=active_topic.id
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            # 4. 返回流式响应
            return StreamingResponse(
                self._generate_streaming_response(
                    message.id, enhanced_context, chat_request, db
                ),
                media_type="text/plain"
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")
        finally:
            db.close()
    
    async def _retrieve_relevant_memories(self, user_id: int, query: str, limit: int) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        try:
            db = next(get_db())
            memories = await self.memory_service.retrieve_relevant_memories(
                db=db,
                user_id=user_id,
                query=query,
                limit=limit
            )
            db.close()
            return memories
        except Exception as e:
            print(f"记忆检索失败: {e}")
            return []
    
    async def _build_enhanced_context(self, chat_request: EnhancedChatRequest, 
                                    memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建增强的对话上下文"""
        
        context = {
            "user_message": chat_request.message,
            "memories": memories,
            "enable_memory_enhancement": chat_request.enable_memory_enhancement,
            "memory_count": len(memories),

            "file_ids": chat_request.file_ids,
            "voice_input_id": chat_request.voice_input_id,
            "search_enabled": chat_request.search_enabled,
            "search_query": chat_request.search_query,
            "enable_chain_of_thought": chat_request.enable_chain_of_thought
        }
        

        
        # 处理文件信息
        if chat_request.file_ids:
            db = next(get_db())
            try:
                from pathlib import Path
                
                files = db.query(UploadedFile).filter(
                    UploadedFile.id.in_(chat_request.file_ids)
                ).all()
                
                file_contents = []
                for file in files:
                    file_info = {
                        "id": file.id,
                        "filename": file.filename,
                        "file_type": file.file_type
                    }
                    
                    # 尝试读取文件内容
                    try:
                        file_path = Path(file.file_path)
                        if file_path.exists():
                            if file.file_type in ['text', 'pdf', 'word', 'excel']:
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                        file_info['content'] = content
                                        print(f"成功读取文件 {file.filename} 内容 (UTF-8), 长度: {len(content)}")
                                except UnicodeDecodeError:
                                    try:
                                        with open(file_path, 'r', encoding='gbk') as f:
                                            content = f.read()
                                            file_info['content'] = content
                                            print(f"成功读取文件 {file.filename} 内容 (GBK), 长度: {len(content)}")
                                    except Exception as e:
                                        print(f"无法读取文件 {file.filename}: {str(e)}")
                                except Exception as e:
                                    print(f"读取文件 {file.filename} 时出错: {str(e)}")
                            else:
                                # 对于非文本文件，只添加文件信息
                                file_info['content'] = f"[文件类型: {file.file_type}, 大小: {file.file_size} 字节]"
                                print(f"非文本文件 {file.filename}, 只添加文件信息")
                        else:
                            print(f"文件不存在: {file_path}")
                    except Exception as e:
                        print(f"处理文件 {file.filename} 时出错: {str(e)}")
                    
                    file_contents.append(file_info)
                
                context["files"] = file_contents
                
                # 如果有文件内容，将其附加到用户消息中
                if file_contents:
                    file_info_text = "\n\n[附件文件信息]\n"
                    for fc in file_contents:
                        file_info_text += f"\n文件名: {fc['filename']}\n"
                        file_info_text += f"类型: {fc['type']}\n"
                        if 'content' in fc and fc['type'] in ['text', 'pdf', 'word', 'excel']:
                            # 限制文件内容长度，避免超出模型上下文限制
                            content = fc['content']
                            if len(content) > 5000:
                                content = content[:5000] + "\n... (内容过长，已截断)"
                            file_info_text += f"内容:\n{content}\n"
                            print(f"文件 {fc['filename']} 内容长度: {len(fc['content'])}, 截断后长度: {len(content)}")
                        else:
                            file_info_text += f"说明: {fc.get('content', 'N/A')}\n"
                    
                    context["user_message"] = context["user_message"] + file_info_text
                    print(f"已附加 {len(file_contents)} 个文件的内容到消息中")
                    print(f"最终消息内容长度: {len(context['user_message'])}")
                    print(f"最终消息内容前500字符: {context['user_message'][:500]}")
            finally:
                db.close()
        
        return context
    
    async def _generate_streaming_response(self, user_message_id: int, context: Dict[str, Any], 
                                         chat_request: EnhancedChatRequest, db) -> AsyncGenerator[str, None]:
        """生成流式响应
        
        Args:
            user_message_id: 用户消息ID（用于关联AI回复）
            context: 增强的对话上下文
            chat_request: 聊天请求
            db: 数据库会话
            
        Yields:
            流式响应块
        """
        
        chunk_id = 0
        full_response = ""
        reasoning_steps = []
        
        try:
            # 1. 生成初始响应（包含记忆引用）
            if context["enable_memory_enhancement"] and context["memory_count"] > 0:
                memory_intro = await self._generate_memory_introduction(context["memories"])
                yield self._format_chunk(chunk_id, memory_intro, False, {
                    "memory_references": context["memories"][:3],
                    "reasoning_step": "记忆检索完成",
                    "user_message_id": user_message_id
                })
                full_response += memory_intro
                chunk_id += 1
                
                # 添加思考延迟，模拟真实思考过程
                await asyncio.sleep(0.5)
            
            # 2. 生成主要响应内容（分块）
            main_response = await self._generate_main_response(context)
            response_chunks = self._split_into_chunks(main_response, chunk_size=50)
            
            for i, chunk in enumerate(response_chunks):
                is_final = (i == len(response_chunks) - 1)
                
                # 如果是思维链模式，添加推理步骤
                reasoning_step = None
                if chat_request.enable_chain_of_thought:
                    reasoning_step = await self._generate_reasoning_step(chunk, context, i, len(response_chunks))
                    reasoning_steps.append(reasoning_step)
                
                yield self._format_chunk(chunk_id, chunk, is_final, {
                    "reasoning_step": reasoning_step,
                    "chunk_index": i,
                    "total_chunks": len(response_chunks),
                    "user_message_id": user_message_id
                })
                
                full_response += chunk
                chunk_id += 1
                
                # 添加流式延迟，模拟真实响应速度
                await asyncio.sleep(0.1)
            
            # 3. 生成总结和后续建议
            if context["enable_memory_enhancement"]:
                summary = await self._generate_response_summary(full_response, context)
                yield self._format_chunk(chunk_id, summary, True, {
                    "reasoning_step": "响应总结完成",
                    "total_response_length": len(full_response),
                    "user_message_id": user_message_id
                })
                full_response += summary
                chunk_id += 1
            
            # 4. 保存完整的AI响应（关联用户消息ID）
            from app.models.conversation import Message, Topic
            # 获取活跃话题
            active_topic = db.query(Topic).filter(
                Topic.conversation_id == chat_request.conversation_id,
                Topic.is_active == True
            ).first()
            
            ai_message = Message(
                conversation_id=chat_request.conversation_id,
                user_id=chat_request.user_id,
                content=full_response,
                role="assistant",
                parent_message_id=user_message_id,  # 关联用户消息
                topic_id=active_topic.id if active_topic else None
            )
            db.add(ai_message)
            db.commit()
            db.refresh(ai_message)
            
            # 5. 保存思维链记录（如果启用）
            if chat_request.enable_chain_of_thought and reasoning_steps:
                chain_of_thought = "\n".join(reasoning_steps)
                cot_record = ChainOfThought(
                    message_id=ai_message.id,
                    reasoning_chain=chain_of_thought,
                    confidence_score=0.8
                )
                db.add(cot_record)
                db.commit()
            
            # 6. 更新记忆访问记录
            if context["enable_memory_enhancement"] and context["memories"]:
                await self._update_memory_access(context["memories"], chat_request.user_id)
            
            # 7. 发送完成信号，包含AI消息ID
            yield self._format_chunk(chunk_id, "", True, {
                "ai_message_id": ai_message.id,
                "user_message_id": user_message_id,
                "status": "completed"
            })
        
        except Exception as e:
            print(f"流式响应生成错误: {e}")
            yield self._format_chunk(chunk_id, f"抱歉，响应生成过程中出现错误: {str(e)}", True, {
                "error": True,
                "error_message": str(e),
                "user_message_id": user_message_id
            })
    
    def _format_chunk(self, chunk_id: int, content: str, is_final: bool, 
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """格式化响应块"""
        chunk_data = {
            "chunk_id": chunk_id,
            "content": content,
            "is_final": is_final,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            chunk_data["metadata"] = metadata
        
        return json.dumps(chunk_data, ensure_ascii=False)
    
    async def _generate_memory_introduction(self, memories: List[Dict[str, Any]]) -> str:
        """生成记忆引用介绍"""
        if not memories:
            return ""
        
        memory_titles = [mem.get("title", "相关记忆") for mem in memories[:3]]
        return f"基于您之前的对话记忆（{', '.join(memory_titles)}），"
    
    async def _generate_main_response(self, context: Dict[str, Any]) -> str:
        """生成主要响应内容"""
        # 这里应该调用实际的LLM服务
        # 现在返回一个模拟响应，包含记忆增强
        
        base_response = f"我理解您想讨论: {context.get('user_message', '')}"
        
        if context["enable_memory_enhancement"] and context["memory_count"] > 0:
            memory_summary = "，并参考了您之前的对话内容。"
            base_response += memory_summary
        
        return base_response + " 有什么我可以帮助您的吗？"
    
    async def _generate_reasoning_step(self, chunk: str, context: Dict[str, Any], 
                                     chunk_index: int, total_chunks: int) -> str:
        """生成推理步骤"""
        steps = [
            "分析用户意图",
            "检索相关记忆",
            "构建响应框架",
            "生成响应内容",
            "优化表达方式"
        ]
        
        step_index = min(chunk_index, len(steps) - 1)
        return f"推理步骤 {chunk_index + 1}/{total_chunks}: {steps[step_index]}"
    
    async def _generate_response_summary(self, response: str, context: Dict[str, Any]) -> str:
        """生成响应总结"""
        return f"\n\n（本次响应参考了 {context['memory_count']} 条相关记忆）"
    
    def _split_into_chunks(self, text: str, chunk_size: int = 50) -> List[str]:
        """将文本分割成块"""
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        return chunks
    
    async def _update_memory_access(self, memories: List[Dict[str, Any]], user_id: int):
        """更新记忆访问记录"""
        try:
            db = next(get_db())
            for memory in memories:
                memory_id = memory.get("id")
                if memory_id:
                    # 更新记忆的访问计数
                    MemoryService.update_preferences_based_on_access(
                        db, memory_id, user_id, "READ"
                    )
            db.commit()
            db.close()
        except Exception as e:
            print(f"记忆访问更新失败: {e}")
    
    async def handle_enhanced_websocket(self, websocket: WebSocket, client_id: str):
        """处理增强的WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            client_id: 客户端ID
        """
        await websocket.accept()
        self.connected_websockets[client_id] = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data.get("type") == "enhanced_chat":
                    chat_request = EnhancedChatRequest(**message_data["data"])
                    
                    # 创建数据库会话
                    db = next(get_db())
                    try:
                        # 创建用户消息记录
                        from app.models.conversation import Message, Topic
                        # 获取活跃话题
                        active_topic = db.query(Topic).filter(
                            Topic.conversation_id == chat_request.conversation_id,
                            Topic.is_active == True
                        ).first()
                        
                        # 如果没有活跃话题，创建一个新话题
                        if not active_topic:
                            active_topic = Topic(
                                conversation_id=chat_request.conversation_id,
                                topic_name="新话题",
                                is_active=True
                            )
                            db.add(active_topic)
                            db.commit()
                            db.refresh(active_topic)
                        
                        user_message = Message(
                            conversation_id=chat_request.conversation_id,
                            user_id=chat_request.user_id,
                            content=chat_request.message,
                            role="user",
                            topic_id=active_topic.id
                        )
                        db.add(user_message)
                        db.commit()
                        db.refresh(user_message)
                        
                        # 构建增强上下文
                        enhanced_context = await self._build_enhanced_context(chat_request, [])
                        
                        # 生成流式响应，传递用户消息ID
                        async for chunk in self._generate_streaming_response(
                            user_message.id, enhanced_context, chat_request, db
                        ):
                            await websocket.send_text(chunk)
                            
                            # 解析chunk检查是否结束
                            chunk_data = json.loads(chunk)
                            if chunk_data.get("is_final", False):
                                break
                    except Exception as e:
                        print(f"处理WebSocket聊天消息失败: {e}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "error": str(e)
                        }))
                    finally:
                        db.close()
                        
        except WebSocketDisconnect:
            self.connected_websockets.pop(client_id, None)
            print(f"客户端 {client_id} 断开WebSocket连接")
        except Exception as e:
            print(f"增强WebSocket错误: {e}")
            self.connected_websockets.pop(client_id, None)


# 创建增强聊天服务实例
enhanced_chat_service = EnhancedChatService()

# 创建增强聊天微服务应用
enhanced_chat_app = FastAPI(
    title="Py Copilot Enhanced Chat Service",
    version="1.0.0",
    description="记忆增强流式响应聊天服务"
)

@enhanced_chat_app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "enhanced_chat"}

@enhanced_chat_app.post("/chat/stream")
async def enhanced_chat_stream(chat_request: EnhancedChatRequest):
    """记忆增强流式聊天接口"""
    return await enhanced_chat_service.process_enhanced_chat(chat_request)

@enhanced_chat_app.websocket("/ws/enhanced/{client_id}")
async def enhanced_websocket_endpoint(websocket: WebSocket, client_id: str):
    """增强WebSocket连接"""
    await enhanced_chat_service.handle_enhanced_websocket(websocket, client_id)

@enhanced_chat_app.on_event("startup")
async def startup_event():
    """服务启动事件"""
    config = MicroserviceConfig(
        name="enhanced-chat-service",
        host="localhost",
        port=8006,
        description="记忆增强流式响应聊天服务"
    )
    
    await enhanced_chat_service.service_registry.register_service(config)
    print("记忆增强聊天微服务启动完成")

@enhanced_chat_app.on_event("shutdown")
async def shutdown_event():
    """服务关闭事件"""
    print("记忆增强聊天微服务已关闭")