"""对话管理相关API路由（简化版）"""
from datetime import datetime
from typing import Any, List, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status, Body, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.conversation.schemas.conversation import SendMessageRequest
from app.modules.llm.services.llm_service import llm_service
from app.modules.llm.services.llm_tasks import llm_tasks

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
    # 查询对话
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        # 如果对话不存在，自动创建一个新对话
        conversation = mock_storage.create_conversation(title=f"对话 {conversation_id}")
        print(f"已自动创建对话: {conversation}")
    
    if not conversation.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话已被关闭"
        )
    
    # 创建用户消息
    user_message = mock_storage.create_message(conversation_id, request.content, "user")
    
    # 如果需要使用LLM生成回复
    assistant_message = None
    if request.use_llm:
        try:
            # 获取对话历史
            conversation_history = mock_storage.get_conversation_messages(conversation_id)
            
            # 构建聊天消息列表
            chat_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in conversation_history
            ]
            chat_messages.append({"role": "user", "content": request.content})
            
            # 使用LLM生成回复
            try:
                # 使用请求中的模型名称，如果没有则使用默认值
                model_name = request.model_name or "gpt-3.5-turbo"
                print(f"调用llm_service.chat_completion，模型: {model_name}")
                print(f"聊天消息: {chat_messages}")
                print(f"传递的agent_id参数: {conversation.get('agent_id')}")
                llm_response = llm_service.chat_completion(
                    messages=chat_messages,
                    model_name=model_name,
                    db=db,
                    agent_id=conversation.get("agent_id")
                )
                print(f"LLM响应: {llm_response}")
                ai_content = llm_response.get("generated_text", "抱歉，我无法生成回复。")
                print(f"提取的AI内容: {ai_content}")
            except (AttributeError, TypeError) as e:
                print(f"chat_completion调用失败: {str(e)}")
                # 尝试使用chat方法
                try:
                    llm_response = llm_service.chat(chat_messages, model_name=model_name, db=db, agent_id=conversation.get("agent_id"))
                    ai_content = llm_response.get("content", "抱歉，我无法生成回复。")
                except Exception as e:
                    print(f"LLM chat方法调用失败: {str(e)}")
                    # 使用模拟回复
                    ai_content = f"这是一条模拟回复，基于您的消息：{request.content[:50]}..."
            except Exception as e:
                print(f"chat_completion调用发生其他错误: {str(e)}")
                ai_content = f"这是一条模拟回复，基于您的消息：{request.content[:50]}..."
            
            # 创建助手回复消息
            print(f"创建助手消息，内容: {ai_content}")
            assistant_message = mock_storage.create_message(conversation_id, ai_content, "assistant")
            print(f"助手消息创建结果: {assistant_message}")
            
        except Exception as e:
            print(f"LLM生成回复失败: {str(e)}")
            # 即使发生异常，也要创建一个模拟回复
            ai_content = f"这是一条模拟回复，基于您的消息：{request.content[:50]}..."
            assistant_message = mock_storage.create_message(conversation_id, ai_content, "assistant")
    
    # 构建响应
    response = {
        "conversation_id": conversation_id,
        "user_message": user_message,
        "generated_at": datetime.utcnow()
    }
    
    print(f"构建响应，assistant_message存在: {assistant_message is not None}")
    if assistant_message:
        response["assistant_message"] = assistant_message
        print(f"响应中包含助手消息: {response['assistant_message']}")
    
    print(f"最终响应: {response}")
    return response


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
) -> Dict[str, Any]:
    """
    获取对话的消息历史（分页）
    """
    # 验证对话存在
    conversation = mock_storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 获取消息列表
    messages = mock_storage.get_conversation_messages(conversation_id, skip=offset, limit=page_size)
    total = sum(1 for msg in mock_storage.messages if msg["conversation_id"] == conversation_id and msg["is_visible"])
    
    return {
        "messages": messages,
        "total": total,
        "page": page,
        "page_size": page_size
    }