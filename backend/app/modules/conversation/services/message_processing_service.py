"""消息处理服务，负责处理消息发送和文件上传等逻辑"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, Message, Topic
from app.modules.conversation.schemas.conversation import SendMessageRequest
from app.modules.conversation.services.conversation_service import ConversationService
from app.modules.conversation.services.topic_service import TopicService
from app.modules.llm.services.llm_service_enhanced import enhanced_llm_service
from app.core.security_utils import validate_message_content
from datetime import datetime
import json


class MessageProcessingService:
    """消息处理服务类"""
    
    @staticmethod
    def process_attached_files(db: Session, request: SendMessageRequest) -> str:
        """处理附件文件"""
        file_contents = []
        
        if request.attached_files and len(request.attached_files) > 0:
            from app.models.chat_enhancements import UploadedFile
            from pathlib import Path
            
            for file_id in request.attached_files:
                try:
                    uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
                    if uploaded_file:
                        # 确保文件路径是绝对路径
                        file_path = Path(uploaded_file.file_path)
                        if not file_path.is_absolute():
                            # 如果是相对路径，转换为绝对路径
                            file_path = Path(__file__).parent.parent.parent.parent / uploaded_file.file_path
                        
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
                            except Exception as e:
                                file_contents.append({
                                    'filename': uploaded_file.file_name,
                                    'content': f"[文件内容读取失败: {str(e)}]",
                                    'type': uploaded_file.file_type
                                })
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
                else:
                    file_info += f"说明: {fc['content']}\n"
            
            return file_info
        return ""
    
    @staticmethod
    def process_message_with_llm(db: Session, conversation: Conversation, user_message: Message, 
                                 active_topic: Topic, request: SendMessageRequest) -> Optional[Message]:
        """使用LLM处理消息"""
        # 获取当前活跃话题的消息作为上下文
        conversation_history = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.topic_id == active_topic.id
        ).order_by(Message.created_at.asc()).all()
        
        chat_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_history
        ]

        try:
            # 使用请求中的模型名称，如果没有则使用默认值
            model_name = request.model_name or "gpt-3.5-turbo"
            
            # 调用增强的LLM服务
            llm_response = enhanced_llm_service.chat_completion(
                messages=chat_messages,
                model_name=model_name,
                db=db,
                agent_id=getattr(conversation, 'agent_id', None)
            )
            
            # 检查是否是流式响应（生成器）
            if hasattr(llm_response, '__iter__') and not isinstance(llm_response, (list, dict)):
                # 处理流式响应，收集所有内容
                ai_content = ""
                try:
                    for chunk in llm_response:
                        if isinstance(chunk, dict):
                            if chunk.get("success", False):
                                ai_content += chunk.get("generated_text", "")
                            elif "content" in chunk:
                                ai_content += chunk.get("content", "")
                        elif isinstance(chunk, str):
                            ai_content += chunk
                    
                    if not ai_content:
                        ai_content = "抱歉，流式响应未返回有效内容。"
                except Exception as stream_error:
                    ai_content = f"抱歉，处理流式响应时出错: {str(stream_error)}"
            # 检查LLM调用是否成功
            elif isinstance(llm_response, dict) and llm_response.get("success", True):
                ai_content = llm_response.get("generated_text", "抱歉，我无法生成回复。")
            else:
                # 如果调用失败，使用失败原因作为回复
                if isinstance(llm_response, dict):
                    ai_content = llm_response.get("generated_text", "抱歉，我无法生成回复。")
                    # 如果有详细的失败分析，也加入到回复中
                    if "failure_analysis" in llm_response:
                        ai_content += f"\n\n详细分析: {llm_response['failure_analysis']}"
                else:
                    ai_content = "抱歉，LLM服务返回了意外的响应格式。"
        except (AttributeError, TypeError) as e:
            # 使用错误信息作为回复
            ai_content = f"抱歉，LLM服务调用失败: {str(e)}"
        except Exception as e:
            # 使用错误信息作为回复
            ai_content = f"抱歉，处理您的请求时发生异常: {str(e)}"
        
        # 创建助手回复消息
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_content,
            topic_id=active_topic.id,
            created_at=datetime.utcnow()
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
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
        
        # 更新话题的消息计数和结束消息ID
        TopicService.increment_message_count(db, active_topic.id, count=2)
        
        return assistant_message