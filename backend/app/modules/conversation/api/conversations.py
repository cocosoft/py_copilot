"""对话管理相关API路由（简化版）"""
import asyncio
import json
from datetime import datetime
from typing import Any, List, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status, Body, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.security_utils import (
    validate_message_content,
    validate_file,
    sanitize_input
)
from app.modules.conversation.schemas.conversation import SendMessageRequest
from app.schemas.conversation import (
    TopicCreate,
    TopicUpdate,
    TopicResponse,
    TopicListResponse,
    SwitchTopicRequest,
    SwitchTopicResponse
)
from app.modules.conversation.services.topic_service import TopicService
from app.modules.conversation.services.topic_title_generator import TopicTitleGenerator
from app.modules.llm.services.llm_service_enhanced import enhanced_llm_service
from app.modules.llm.services.llm_tasks import llm_tasks
from app.models.supplier_db import SupplierDB, ModelDB
from app.models.model_capability import ModelCapability, ModelCapabilityAssociation
from app.models.conversation import Conversation, Message, Topic

# 导入思维链生成函数
def generate_thinking_chain_steps(content: str) -> List[str]:
    """根据消息内容生成思维链步骤"""
    content_lower = content.lower()
    
    if any(word in content_lower for word in ['计算', '数学', '公式', '等于', '加', '减', '乘', '除']):
        return [
            "🧮 识别数学计算问题...",
            "🔢 解析数学表达式...",
            "📊 执行计算步骤...",
            "✅ 验证计算结果..."
        ]
    elif any(word in content_lower for word in ['解释', '什么是', '定义', '概念']):
        return [
            "📚 识别概念解释需求...",
            "🔍 检索相关知识库...",
            "💡 构建解释框架...",
            "📝 组织解释内容..."
        ]
    elif any(word in content_lower for word in ['代码', '编程', '函数', '变量']):
        return [
            "💻 分析编程问题...",
            "🔧 设计解决方案...",
            "📋 编写代码逻辑...",
            "✅ 验证代码正确性..."
        ]
    elif any(word in content_lower for word in ['翻译', '语言', '英文', '中文']):
        return [
            "🌐 识别翻译需求...",
            "📖 分析原文语义...",
            "🔄 构建翻译映射...",
            "✍️ 优化翻译表达..."
        ]
    else:
        return []

router = APIRouter()


# 模拟内存存储
class MockStorage:
    def __init__(self):
        self.conversations = []
        self.messages = []
        self.conversation_id_counter = 1
        self.message_id_counter = 1
    
    def create_conversation(self, title: str = "新对话", description: str = "") -> Dict[str, Any]:
        conversation = {
            "id": self.conversation_id_counter,
            "title": title,
            "description": description,
            "is_active": True,
            "message_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_message_at": None
        }
        self.conversations.append(conversation)
        self.conversation_id_counter += 1
        return conversation
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        for conv in self.conversations:
            if conv["id"] == conversation_id:
                return conv
        return None
    
    def update_conversation(self, conversation_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        conv = self.get_conversation(conversation_id)
        if conv:
            for field, value in update_data.items():
                if field in conv:
                    conv[field] = value
            conv["updated_at"] = datetime.utcnow()
        return conv
    
    def delete_conversation(self, conversation_id: int) -> None:
        self.conversations = [conv for conv in self.conversations if conv["id"] != conversation_id]
        self.messages = [msg for msg in self.messages if msg["conversation_id"] != conversation_id]
    
    def create_message(self, conversation_id: int, content: str, role: str) -> Dict[str, Any]:
        message = {
            "id": self.message_id_counter,
            "conversation_id": conversation_id,
            "content": content,
            "role": role,
            "is_visible": True,
            "created_at": datetime.utcnow()
        }
        self.messages.append(message)
        self.message_id_counter += 1
        
        # 更新对话消息计数和最后消息时间
        conv = self.get_conversation(conversation_id)
        if conv:
            conv["message_count"] = sum(1 for msg in self.messages if msg["conversation_id"] == conversation_id)
            conv["last_message_at"] = datetime.utcnow()
        
        return message
    
    def get_conversation_messages(self, conversation_id: int, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        messages = [msg for msg in self.messages if msg["conversation_id"] == conversation_id and msg["is_visible"]]
        messages.sort(key=lambda x: x["created_at"])
        return messages[skip:skip+limit]
    
    def get_all_conversations(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        conversations = sorted(
            self.conversations,
            key=lambda x: (x["last_message_at"] or datetime.min, x["created_at"]),
            reverse=True
        )
        return conversations[skip:skip+limit]

# 创建模拟存储实例
mock_storage = MockStorage()


@router.post("/")
async def create_conversation(
    title: str = "新对话",
    description: str = "",
    initial_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建新对话
    """
    conversation = mock_storage.create_conversation(title, description)
    
    # 如果提供了初始消息
    if initial_message:
        mock_storage.create_message(conversation["id"], initial_message, "user")
        conversation = mock_storage.get_conversation(conversation["id"])
    
    return conversation


@router.get("/")
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """
    获取对话列表
    """
    offset = (page - 1) * page_size
    conversations = mock_storage.get_all_conversations(skip=offset, limit=page_size)
    total = len(mock_storage.conversations)
    
    return {
        "conversations": conversations,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{conversation_id}")
async def get_conversation_detail(conversation_id: int) -> Dict[str, Any]:
    """
    获取对话详情及消息历史
    """
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取所有消息
    messages = mock_storage.get_conversation_messages(conversation_id, limit=1000)
    
    return {
        **conversation,
        "messages": messages
    }


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Dict[str, Any]:
    """
    更新对话信息
    """
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if is_active is not None:
        update_data["is_active"] = is_active
    
    updated_conversation = mock_storage.update_conversation(conversation_id, update_data)
    return updated_conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: int) -> None:
    """
    删除对话
    """
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    mock_storage.delete_conversation(conversation_id)


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    request: SendMessageRequest = Body(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    在对话中发送消息
    """
    print(f"========== 收到发送消息请求 ==========")
    print(f"conversation_id: {conversation_id}")
    print(f"request.content: {request.content}")
    print(f"request.attached_files: {request.attached_files}")
    print(f"request type: {type(request)}")
    print(f"===============================")
    
    # 查询对话
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    # 如果对话不存在，自动创建一个新对话
    if not conversation:
        conversation = Conversation(
            id=conversation_id,
            user_id=1,  # 默认用户ID，实际应该从认证中获取
            title=f"对话 {conversation_id}",
            description=""
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        print(f"已自动创建对话: {conversation}")
    
    # 验证消息内容
    validation_result = validate_message_content(request.content)
    if not validation_result['is_valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result['message']
        )
    
    # 使用清理后的内容
    sanitized_content = validation_result['sanitized_content']
    
    # 处理附件文件
    file_contents = []
    print(f"========== 处理附件文件 ==========")
    print(f"收到的文件ID列表: {request.attached_files}")
    if request.attached_files and len(request.attached_files) > 0:
        from app.models.chat_enhancements import UploadedFile
        from pathlib import Path
        
        for file_id in request.attached_files:
            try:
                print(f"正在处理文件ID: {file_id}")
                uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
                if uploaded_file:
                    print(f"找到文件记录: {uploaded_file.file_name}, 类型: {uploaded_file.file_type}, 路径: {uploaded_file.file_path}")
                    # 确保文件路径是绝对路径
                    file_path = Path(uploaded_file.file_path)
                    if not file_path.is_absolute():
                        # 如果是相对路径，转换为绝对路径
                        file_path = Path(__file__).parent.parent.parent.parent / uploaded_file.file_path
                        print(f"转换为绝对路径: {file_path}")
                    if file_path.exists():
                        # 使用文件处理器服务处理文件
                        from app.modules.file.services.file_processor import file_processor_service
                        try:
                            file_result = file_processor_service.process_file(
                                file_path=file_path,
                                file_name=uploaded_file.file_name,
                                file_type=uploaded_file.file_type
                            )
                            file_contents.append(file_result)
                            print(f"文件处理结果: {file_result['filename']}, 内容长度: {len(file_result['content'])}")
                        except Exception as e:
                            print(f"文件处理器出错: {str(e)}")
                            file_contents.append({
                                'filename': uploaded_file.file_name,
                                'content': f"[文件内容读取失败: {str(e)}]",
                                'type': uploaded_file.file_type
                            })
                    else:
                        print(f"文件不存在: {file_path}")
                else:
                    print(f"未找到文件ID: {file_id}")
            except Exception as e:
                print(f"处理文件 {file_id} 时出错: {str(e)}")
        
        # 如果有文件内容，将其附加到用户消息中
        if file_contents:
            file_info = "\n\n[附件文件信息]\n"
            for fc in file_contents:
                file_info += f"\n文件名: {fc['filename']}\n"
                file_info += f"类型: {fc['type']}\n"
                if fc['type'] in ['text', 'pdf', 'word', 'excel', 'ppt']:
                    # 限制文件内容长度，避免超出模型上下文限制
                    content = fc['content']
                    if len(content) > 5000:
                        content = content[:5000] + "\n... (内容过长，已截断)"
                    file_info += f"内容:\n{content}\n"
                    print(f"文件 {fc['filename']} 内容长度: {len(fc['content'])}, 截断后长度: {len(content)}")
                else:
                    file_info += f"说明: {fc['content']}\n"
            
            sanitized_content = sanitized_content + file_info
            print(f"已附加 {len(file_contents)} 个文件的内容到消息中")
            print(f"最终消息内容长度: {len(sanitized_content)}")
            print(f"最终消息内容前500字符: {sanitized_content[:500]}")
        else:
            print("没有文件内容被附加")
    else:
        print("没有附件文件")
    print(f"===============================")
    
    # 获取或创建活跃话题
    active_topic = TopicService.get_active_topic(db, conversation_id)
    
    # 如果请求中指定了话题ID，使用指定的话题
    if request.topic_id:
        topic = TopicService.get_topic_by_id(db, request.topic_id)
        if topic:
            active_topic = topic
            # 设置为活跃话题
            TopicService.set_active_topic(db, conversation_id, topic.id)
    
    # 如果没有活跃话题，创建一个新话题
    if not active_topic:
        # 使用默认标题创建话题
        topic_name = "新话题"
        active_topic = TopicService.create_topic(db, conversation_id, topic_name)
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=sanitized_content,
        topic_id=active_topic.id,
        created_at=datetime.utcnow()
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # 如果需要使用LLM生成回复
    assistant_message = None
    
    if request.use_llm:
        try:
            # 只获取当前活跃话题的消息作为上下文，而不是整个对话的消息
            conversation_history = db.query(Message).filter(
                Message.conversation_id == conversation_id,
                Message.topic_id == active_topic.id
            ).order_by(Message.created_at.asc()).all()
            
            # 构建聊天消息列表
            chat_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in conversation_history
            ]
            chat_messages.append({"role": "user", "content": sanitized_content})
            
            # 使用LLM生成回复
            try:
                # 使用请求中的模型名称，如果没有则使用默认值
                model_name = request.model_name or "gpt-3.5-turbo"
                print(f"========== 调用LLM ==========")
                print(f"模型: {model_name}")
                print(f"聊天消息数量: {len(chat_messages)}")
                print(f"传递给LLM的最后一条消息长度: {len(sanitized_content)}")
                print(f"传递给LLM的最后一条消息前500字符: {sanitized_content[:500]}")
                print(f"传递的agent_id参数: {conversation.agent_id}")
                print(f"==============================")
                llm_response = enhanced_llm_service.chat_completion(
                    messages=chat_messages,
                    model_name=model_name,
                    db=db,
                    agent_id=conversation.agent_id
                )
                print(f"LLM响应: {llm_response}")
                
                # 检查LLM调用是否成功
                if llm_response.get("success", True):
                    ai_content = llm_response.get("generated_text", "抱歉，我无法生成回复。")
                    print(f"提取的AI内容: {ai_content}")
                else:
                    # 如果调用失败，使用失败原因作为回复
                    ai_content = llm_response.get("generated_text", "抱歉，我无法生成回复。")
                    print(f"LLM调用失败，返回错误信息: {ai_content}")
                    # 如果有详细的失败分析，也加入到回复中
                    if "failure_analysis" in llm_response:
                        ai_content += f"\n\n详细分析: {llm_response['failure_analysis']}"
            except (AttributeError, TypeError) as e:
                print(f"chat_completion调用失败: {str(e)}")
                # 使用错误信息作为回复
                ai_content = f"抱歉，LLM服务调用失败: {str(e)}"
            except Exception as e:
                print(f"chat_completion调用发生其他错误: {str(e)}")
                # 使用错误信息作为回复
                ai_content = f"抱歉，处理您的请求时发生异常: {str(e)}"
            
            # 创建助手回复消息
            print(f"创建助手消息，内容: {ai_content}")
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_content,
                topic_id=active_topic.id,
                created_at=datetime.utcnow()
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            print(f"助手消息创建结果: {assistant_message}")
            
            # 保存思维链信息（如果有）
            reasoning_content = llm_response.get("reasoning_content", "") if isinstance(llm_response, dict) else ""
            if reasoning_content:
                from app.models.chat_enhancements import ChainOfThought
                
                # 分割思维链内容为步骤
                reasoning_steps = reasoning_content.split('\n')
                reasoning_steps = [step.strip() for step in reasoning_steps if step.strip()]
                
                # 创建思维链记录
                chain_of_thought = ChainOfThought(
                    message_id=assistant_message.id,
                    chain_type="step_by_step",
                    reasoning_steps=reasoning_steps,
                    final_answer=ai_content,
                    is_visible=True
                )
                db.add(chain_of_thought)
                db.commit()
                print(f"已保存思维链信息，共 {len(reasoning_steps)} 个步骤")
            
            # 更新话题的消息计数和结束消息ID
            TopicService.increment_message_count(db, active_topic.id, count=2)
            TopicService.update_end_message(db, active_topic.id, assistant_message.id)
            
            # 如果话题标题是默认的"新话题"，尝试生成更好的标题
            print(f"检查话题标题: active_topic.topic_name={active_topic.topic_name}")
            if active_topic.topic_name == "新话题":
                print("开始调用TopicTitleGenerator生成标题...")
                topic_title = TopicTitleGenerator.generate_title_from_messages(db, conversation_id, active_topic.id)
                print(f"生成的标题: {topic_title}")
                if topic_title != "新对话" and topic_title != "新话题":
                    TopicService.update_topic(db, active_topic.id, topic_name=topic_title)
                    active_topic.topic_name = topic_title
                    print(f"话题标题已更新为: {active_topic.topic_name}")
            
        except Exception as e:
            print(f"LLM生成回复失败: {str(e)}")
            # 即使发生异常，也要创建一个模拟回复
            ai_content = f"这是一条模拟回复，基于您的消息：{request.content[:50]}..."
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_content,
                created_at=datetime.utcnow()
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
    
    # 构建响应
    response = {
        "conversation_id": conversation_id,
        "user_message": {
            "id": user_message.id,
            "content": user_message.content,
            "role": user_message.role,
            "created_at": user_message.created_at.isoformat() if user_message.created_at else None
        },
        "generated_at": datetime.utcnow().isoformat(),
        "status": "success"
    }
    
    print(f"构建响应，assistant_message存在: {assistant_message is not None}")
    if assistant_message:
        response["assistant_message"] = {
            "id": assistant_message.id,
            "content": assistant_message.content,
            "role": assistant_message.role,
            "created_at": assistant_message.created_at.isoformat() if assistant_message.created_at else None
        }
        print(f"响应中包含助手消息: {response['assistant_message']}")
    
    print(f"最终响应: {response}")
    return response


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取对话的消息历史（分页）
    """
    # 验证对话存在
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 构建查询
    query = db.query(Message).filter(Message.conversation_id == conversation_id)
    
    # 计算偏移量和总数
    offset = (page - 1) * page_size
    total = query.count()
    
    # 获取消息列表
    messages = query.order_by(Message.created_at.asc()).offset(offset).limit(page_size).all()
    
    # 构建返回数据
    messages_data = []
    for msg in messages:
        messages_data.append({
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        })
    
    return {
        "status": "success",
        "messages": messages_data,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: int,
    request: SendMessageRequest = Body(...),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    在对话中发送消息（流式响应版本）
    """
    from app.core.streaming_optimizer import (
        StreamingOptimizer,
        StreamingStrategy,
        StreamingConfig
    )
    
    # 查询对话
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    # 如果对话不存在，自动创建一个新对话
    if not conversation:
        conversation = Conversation(
            id=conversation_id,
            user_id=1,
            title=f"对话 {conversation_id}",
            description=""
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        print(f"已自动创建对话: {conversation}")
    
    # 提取参数
    content = request.content
    use_llm = request.use_llm
    model_name = request.model_name
    enable_thinking_chain = request.enable_thinking_chain
    streaming_strategy = "balanced"
    topic_id = request.topic_id
    attached_files = request.attached_files
    
    # 验证消息内容
    validation_result = validate_message_content(content)
    if not validation_result['is_valid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result['message']
        )
    
    # 使用清理后的内容
    sanitized_content = validation_result['sanitized_content']
    
    # 处理附件文件
    file_contents = []
    print(f"========== 处理附件文件 (流式) ==========")
    print(f"收到的文件ID列表: {attached_files}")
    if attached_files and len(attached_files) > 0:
        from app.models.chat_enhancements import UploadedFile
        from pathlib import Path
        
        for file_id in attached_files:
            try:
                print(f"正在处理文件ID: {file_id}")
                uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
                if uploaded_file:
                    print(f"找到文件记录: {uploaded_file.file_name}, 类型: {uploaded_file.file_type}, 路径: {uploaded_file.file_path}")
                    # 确保文件路径是绝对路径
                    file_path = Path(uploaded_file.file_path)
                    if not file_path.is_absolute():
                        # 如果是相对路径，转换为绝对路径
                        file_path = Path(__file__).parent.parent.parent.parent / uploaded_file.file_path
                        print(f"转换为绝对路径: {file_path}")
                    if file_path.exists():
                        # 使用文件处理器服务处理文件
                        from app.modules.file.services.file_processor import file_processor_service
                        try:
                            file_result = file_processor_service.process_file(
                                file_path=file_path,
                                file_name=uploaded_file.file_name,
                                file_type=uploaded_file.file_type
                            )
                            file_contents.append(file_result)
                            print(f"文件处理结果: {file_result['filename']}, 内容长度: {len(file_result['content'])}")
                        except Exception as e:
                            print(f"文件处理器出错: {str(e)}")
                            file_contents.append({
                                'filename': uploaded_file.file_name,
                                'content': f"[文件内容读取失败: {str(e)}]",
                                'type': uploaded_file.file_type
                            })
                    else:
                        print(f"文件不存在: {file_path}")
                else:
                    print(f"未找到文件ID: {file_id}")
            except Exception as e:
                print(f"处理文件 {file_id} 时出错: {str(e)}")
        
        # 如果有文件内容，将其附加到用户消息中
        if file_contents:
            file_info = "\n\n[附件文件信息]\n"
            for fc in file_contents:
                file_info += f"\n文件名: {fc['filename']}\n"
                file_info += f"类型: {fc['type']}\n"
                if fc['type'] in ['text', 'pdf', 'word', 'excel', 'ppt']:
                    # 限制文件内容长度，避免超出模型上下文限制
                    content = fc['content']
                    if len(content) > 5000:
                        content = content[:5000] + "\n... (内容过长，已截断)"
                    file_info += f"内容:\n{content}\n"
                    print(f"文件 {fc['filename']} 内容长度: {len(fc['content'])}, 截断后长度: {len(content)}")
                else:
                    file_info += f"说明: {fc['content']}\n"
            
            sanitized_content = sanitized_content + file_info
            print(f"已附加 {len(file_contents)} 个文件的内容到消息中")
            print(f"最终消息内容长度: {len(sanitized_content)}")
            print(f"最终消息内容前500字符: {sanitized_content[:500]}")
        else:
            print("没有文件内容被附加")
    else:
        print("没有附件文件")
    print(f"===============================")
    
    # 重置活跃话题，确保在新话题状态下能够创建新话题
    active_topic = None
    
    # 如果请求中指定了话题ID，使用指定的话题
    if topic_id:
        topic = TopicService.get_topic_by_id(db, topic_id)
        if topic:
            active_topic = topic
            # 设置为活跃话题
            TopicService.set_active_topic(db, conversation_id, topic.id)
    else:
        # 如果没有指定话题ID，总是创建一个新话题
        # 使用默认标题创建话题
        topic_name = "新话题"
        active_topic = TopicService.create_topic(db, conversation_id, topic_name)
        # 设置新创建的话题为活跃话题
        TopicService.set_active_topic(db, conversation_id, active_topic.id)
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=sanitized_content,
        topic_id=active_topic.id,
        created_at=datetime.utcnow()
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # 构建初始响应
    initial_response = {
        "status": "processing",
        "message_id": user_message.id,
        "conversation_id": conversation_id,
        "topic_id": active_topic.id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # 异步生成响应
    async def generate_response():
        # 发送初始响应
        yield f"data: {json.dumps(initial_response)}\n\n"
        
        if use_llm:
            try:
                # 只获取当前活跃话题的消息作为上下文，而不是整个对话的消息
                conversation_history = db.query(Message).filter(
                    Message.conversation_id == conversation_id,
                    Message.topic_id == active_topic.id
                ).order_by(Message.created_at.asc()).all()
                
                # 构建聊天消息列表
                chat_messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in conversation_history
                ]
                chat_messages.append({"role": "user", "content": sanitized_content})
                
                # 使用LLM生成回复
                try:
                    # 使用请求中的模型名称，如果没有则使用默认值
                    model_name = model_name or "gpt-3.5-turbo"
                    print(f"========== 调用LLM (流式) ==========")
                    print(f"模型: {model_name}")
                    print(f"聊天消息数量: {len(chat_messages)}")
                    print(f"传递给LLM的最后一条消息长度: {len(sanitized_content)}")
                    print(f"传递给LLM的最后一条消息前500字符: {sanitized_content[:500]}")
                    print(f"传递的agent_id参数: {conversation.agent_id}")
                    print(f"==============================")
                    
                    # 调用LLM服务的流式接口
                    async for chunk in enhanced_llm_service.chat_completion_stream(
                        messages=chat_messages,
                        model_name=model_name,
                        db=db,
                        agent_id=conversation.agent_id
                    ):
                        if isinstance(chunk, dict):
                            # 处理完整响应
                            if "success" in chunk:
                                ai_content = chunk.get("generated_text", "抱歉，我无法生成回复。")
                                
                                # 创建助手回复消息
                                assistant_message = Message(
                                    conversation_id=conversation_id,
                                    role="assistant",
                                    content=ai_content,
                                    topic_id=active_topic.id,
                                    created_at=datetime.utcnow()
                                )
                                db.add(assistant_message)
                                db.commit()
                                db.refresh(assistant_message)
                                
                                # 保存思维链信息（如果有）
                                reasoning_content = chunk.get("reasoning_content", "")
                                if reasoning_content:
                                    from app.models.chat_enhancements import ChainOfThought
                                    
                                    # 分割思维链内容为步骤
                                    reasoning_steps = reasoning_content.split('\n')
                                    reasoning_steps = [step.strip() for step in reasoning_steps if step.strip()]
                                    
                                    # 创建思维链记录
                                    chain_of_thought = ChainOfThought(
                                        message_id=assistant_message.id,
                                        chain_type="step_by_step",
                                        reasoning_steps=reasoning_steps,
                                        final_answer=ai_content,
                                        is_visible=True
                                    )
                                    db.add(chain_of_thought)
                                    db.commit()
                                    print(f"已保存思维链信息，共 {len(reasoning_steps)} 个步骤")
                                
                                # 更新话题的消息计数和结束消息ID
                                TopicService.increment_message_count(db, active_topic.id, count=2)
                                TopicService.update_end_message(db, active_topic.id, assistant_message.id)
                                
                                # 如果话题标题是默认的"新话题"，尝试生成更好的标题
                                if active_topic.topic_name == "新话题":
                                    topic_title = TopicTitleGenerator.generate_title_from_messages(db, conversation_id, active_topic.id)
                                    if topic_title != "新对话" and topic_title != "新话题":
                                        TopicService.update_topic(db, active_topic.id, topic_name=topic_title)
                                        active_topic.topic_name = topic_title
                                
                                # 发送最终响应
                                final_response = {
                                    "status": "completed",
                                    "assistant_message": {
                                        "id": assistant_message.id,
                                        "content": assistant_message.content,
                                        "role": "assistant",
                                        "created_at": assistant_message.created_at.isoformat() if assistant_message.created_at else None
                                    },
                                    "topic": {
                                        "id": active_topic.id,
                                        "name": active_topic.topic_name
                                    },
                                    "completed_at": datetime.utcnow().isoformat()
                                }
                                yield f"data: {json.dumps(final_response)}\n\n"
                            else:
                                # 处理错误响应
                                error_response = {
                                    "status": "error",
                                    "error": chunk.get("error", "LLM服务调用失败"),
                                    "completed_at": datetime.utcnow().isoformat()
                                }
                                yield f"data: {json.dumps(error_response)}\n\n"
                        else:
                            # 处理流式文本块
                            chunk_response = {
                                "status": "streaming",
                                "chunk": chunk,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            yield f"data: {json.dumps(chunk_response)}\n\n"
                except (AttributeError, TypeError) as e:
                    print(f"chat_completion_stream调用失败: {str(e)}")
                    # 发送错误响应
                    error_response = {
                        "status": "error",
                        "error": f"LLM服务调用失败: {str(e)}",
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
                except Exception as e:
                    print(f"chat_completion_stream调用发生其他错误: {str(e)}")
                    # 发送错误响应
                    error_response = {
                        "status": "error",
                        "error": f"处理您的请求时发生异常: {str(e)}",
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
            except Exception as e:
                print(f"LLM生成回复失败: {str(e)}")
                # 发送错误响应
                error_response = {
                    "status": "error",
                    "error": f"处理您的请求时发生异常: {str(e)}",
                    "completed_at": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(error_response)}\n\n"
        else:
            # 不使用LLM，直接返回成功响应
            success_response = {
                "status": "completed",
                "message": "消息已发送",
                "completed_at": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(success_response)}\n\n"
        
        # 发送结束标记
        yield "data: [DONE]\n\n"
    
    # 返回流式响应
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
