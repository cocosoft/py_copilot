"""LLM相关API路由"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas import llm as llm_schemas
from app.services.llm_service import llm_service
from app.services.llm_tasks import llm_tasks

router = APIRouter()


@router.post("/completions/text", response_model=llm_schemas.LLMTextCompletionResponse)
async def text_completion(
    request: llm_schemas.LLMTextCompletionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    文本补全API
    
    Args:
        request: 文本补全请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        文本补全结果
    """
    try:
        # 调用LLM服务进行文本补全
        result = llm_service.text_completion(
            prompt=request.prompt,
            model_name=request.model_name,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            n=request.n,
            stop=request.stop,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result["model"],
            prompt=request.prompt,
            response=result["generated_text"],
            tokens_used=result["tokens_used"],
            task_type="text_completion"
        )
        
        # 构建响应
        return llm_schemas.LLMTextCompletionResponse(
            model=result["model"],
            generated_text=result["generated_text"],
            tokens_used=result["tokens_used"],
            execution_time_ms=result["execution_time_ms"],
            original_prompt=request.prompt
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文本生成失败: {str(e)}"
        )


@router.post("/completions/chat", response_model=llm_schemas.LLMChatCompletionResponse)
async def chat_completion(
    request: llm_schemas.LLMChatCompletionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    聊天补全API
    
    Args:
        request: 聊天补全请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        聊天补全结果
    """
    try:
        # 转换消息格式
        messages = [msg.model_dump() for msg in request.messages]
        
        # 调用LLM服务进行聊天补全
        result = llm_service.chat_completion(
            messages=messages,
            model_name=request.model_name,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            n=request.n,
            stop=request.stop,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            db=db
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result["model"],
            prompt=str(messages),
            response=result["generated_text"],
            tokens_used=result["tokens_used"],
            task_type="chat_completion"
        )
        
        # 构建响应
        return llm_schemas.LLMChatCompletionResponse(
            model=result["model"],
            generated_text=result["generated_text"],
            tokens_used=result["tokens_used"],
            execution_time_ms=result["execution_time_ms"],
            conversation_history=request.messages
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聊天生成失败: {str(e)}"
        )


@router.post("/tasks/process", response_model=llm_schemas.TaskResponse)
async def process_task(
    request: llm_schemas.TaskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    通用任务处理API
    
    Args:
        request: 任务处理请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        任务处理结果
    """
    try:
        # 根据任务类型调用相应的处理函数
        task_type = request.task_type
        options = request.options or {}
        
        # 处理不同类型的任务
        if task_type == "summarize":
            result = llm_tasks.summarize_text(request.text, **options)
        elif task_type == "generate_code":
            result = llm_tasks.generate_code(request.text, **options)
        elif task_type == "translate":
            result = llm_tasks.translate_text(request.text, **options)
        elif task_type == "sentiment":
            result = llm_tasks.analyze_sentiment(request.text, **options)
        elif task_type == "qa":
            result = llm_tasks.answer_question(request.text, **options)
        elif task_type == "extract_info":
            result = llm_tasks.extract_information(request.text, **options)
        elif task_type == "expand":
            result = llm_tasks.expand_text(request.text, **options)
        elif task_type == "paraphrase":
            result = llm_tasks.paraphrase_text(request.text, **options)
        elif task_type == "classify":
            result = llm_tasks.classify_text(request.text, **options)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的任务类型: {task_type}"
            )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result.get("model", "unknown"),
            prompt=request.text,
            response=str(result["result"]),
            tokens_used=result.get("tokens_used", 0),
            task_type=task_type
        )
        
        # 构建响应
        return llm_schemas.TaskResponse(
            task_type=task_type,
            result=result["result"],
            execution_time_ms=result.get("execution_time_ms", 0),
            tokens_used=result.get("tokens_used", 0)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务处理失败: {str(e)}"
        )


@router.get("/models", response_model=llm_schemas.AvailableModelsResponse)
async def get_available_models(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取可用的LLM模型列表
    
    Args:
        current_user: 当前活跃用户
    
    Returns:
        可用模型列表
    """
    try:
        # 获取可用模型列表
        models = llm_service.get_available_models()
        
        # 构建响应
        model_responses = []
        for model in models:
            model_responses.append(llm_schemas.ModelInfoResponse(
                name=model["name"],
                provider=model["provider"],
                type=model["type"],
                max_tokens=model["max_tokens"],
                description=model.get("description"),
                is_default=model["is_default"]
            ))
        
        return llm_schemas.AvailableModelsResponse(
            models=model_responses,
            total=len(model_responses)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型列表失败: {str(e)}"
        )


@router.post("/embeddings", response_model=dict)
async def generate_embeddings(
    text: str,
    model_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    生成文本嵌入向量
    
    Args:
        text: 要生成嵌入向量的文本
        model_id: 要使用的模型ID
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        嵌入向量和模型信息
    """
    try:
        # 生成嵌入向量
        result = llm_service.generate_embeddings(
            text=text,
            model_name=model_id
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result["model"],
            prompt=text,
            response="[embeddings]",
            tokens_used=result.get("tokens_used", 0),
            task_type="embeddings"
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成嵌入向量失败: {str(e)}"
        )


# 健康检查
@router.get("/health", response_model=Dict[str, Any])
async def health_check(
    current_user: User = Depends(get_current_active_user)
):
    """LLM服务健康检查"""
    return {
        "status": "healthy",
        "service": "llm_api",
        "version": "1.0.0"
    }


# 公开的健康检查（不需要认证）
@router.get("/public/health", response_model=Dict[str, Any])
async def public_health_check():
    """公开的LLM服务健康检查（无需认证）"""
    return {
        "status": "healthy",
        "service": "llm_api",
        "version": "1.0.0"
    }


# 创意生成
@router.post("/tasks/generate-ideas", response_model=llm_schemas.TaskResponse)
async def generate_ideas(
    request: llm_schemas.IdeasRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    创意生成API
    
    Args:
        request: 创意生成请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        创意生成结果
    """
    try:
        # 调用创意生成服务
        result = llm_tasks.generate_ideas(
            topic=request.topic,
            **(request.options or {})
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result.get("model", "unknown"),
            prompt=request.topic,
            response=str(result["result"]),
            tokens_used=result.get("tokens_used", 0),
            task_type="generate_ideas"
        )
        
        return llm_schemas.TaskResponse(
            task_type="generate_ideas",
            result=result["result"],
            execution_time_ms=result.get("execution_time_ms", 0),
            tokens_used=result.get("tokens_used", 0)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创意生成失败: {str(e)}"
        )


# 内容生成
@router.post("/tasks/generate-content", response_model=llm_schemas.TaskResponse)
async def generate_content(
    request: llm_schemas.ContentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    内容生成API
    
    Args:
        request: 内容生成请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        内容生成结果
    """
    try:
        # 调用内容生成服务
        result = llm_tasks.generate_content(
            topic=request.topic,
            **(request.options or {})
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result.get("model", "unknown"),
            prompt=request.topic,
            response=str(result["result"]),
            tokens_used=result.get("tokens_used", 0),
            task_type="generate_content"
        )
        
        return llm_schemas.TaskResponse(
            task_type="generate_content",
            result=result["result"],
            execution_time_ms=result.get("execution_time_ms", 0),
            tokens_used=result.get("tokens_used", 0)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"内容生成失败: {str(e)}"
        )


# 语法纠正
@router.post("/tasks/correct-grammar", response_model=llm_schemas.TaskResponse)
async def correct_grammar(
    request: llm_schemas.GrammarRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    语法纠正API
    
    Args:
        request: 语法纠正请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        语法纠正结果
    """
    try:
        # 调用语法纠正服务
        result = llm_tasks.correct_grammar(
            text=request.text,
            **(request.options or {})
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result.get("model", "unknown"),
            prompt=request.text,
            response=str(result["result"]),
            tokens_used=result.get("tokens_used", 0),
            task_type="correct_grammar"
        )
        
        return llm_schemas.TaskResponse(
            task_type="correct_grammar",
            result=result["result"],
            execution_time_ms=result.get("execution_time_ms", 0),
            tokens_used=result.get("tokens_used", 0)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语法纠正失败: {str(e)}"
        )


# 创建对话
@router.post("/conversation/create", response_model=llm_schemas.ConversationCreateResponse)
async def create_conversation(
    request: llm_schemas.ConversationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    创建对话API
    
    Args:
        request: 创建对话请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        创建的对话信息
    """
    try:
        # 调用创建对话服务
        result = llm_tasks.create_conversation(
            **(request.options or {})
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result.get("model", "unknown"),
            prompt="create_conversation",
            response=str(result),
            tokens_used=result.get("tokens_used", 0),
            task_type="create_conversation"
        )
        
        return llm_schemas.ConversationCreateResponse(
            conversation_id=result.get("conversation_id"),
            system_role=result.get("system_role"),
            model=result.get("model"),
            created_at=result.get("created_at")
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建对话失败: {str(e)}"
        )


# 处理对话
@router.post("/conversation/process", response_model=llm_schemas.ConversationProcessResponse)
async def process_conversation(
    request: llm_schemas.ConversationProcessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    处理对话API
    
    Args:
        request: 处理对话请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        对话处理结果
    """
    try:
        # 转换消息格式
        messages = [msg.model_dump() for msg in request.messages]
        
        # 调用处理对话服务
        result = llm_tasks.process_conversation(
            messages=messages,
            **(request.options or {})
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result.get("model", "unknown"),
            prompt=str(messages),
            response=str(result["result"]),
            tokens_used=result.get("tokens_used", 0),
            task_type="process_conversation"
        )
        
        # 构建响应消息
        response_message = llm_schemas.MessageResponse(
            role="assistant",
            content=result["result"]
        )
        
        return llm_schemas.ConversationProcessResponse(
            response=response_message,
            execution_time_ms=result.get("execution_time_ms", 0),
            tokens_used=result.get("tokens_used", 0),
            model=result.get("model")
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理对话失败: {str(e)}"
        )


# 文本改写
@router.post("/tasks/paraphrase", response_model=llm_schemas.TaskResponse)
async def paraphrase_text(
    request: llm_schemas.ParaphraseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    文本改写API
    
    Args:
        request: 文本改写请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        文本改写结果
    """
    try:
        # 调用文本改写服务
        result = llm_tasks.paraphrase_text(
            text=request.text,
            **(request.options or {})
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result.get("model", "unknown"),
            prompt=request.text,
            response=str(result["result"]),
            tokens_used=result.get("tokens_used", 0),
            task_type="paraphrase"
        )
        
        return llm_schemas.TaskResponse(
            task_type="paraphrase",
            result=result["result"],
            execution_time_ms=result.get("execution_time_ms", 0),
            tokens_used=result.get("tokens_used", 0)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文本改写失败: {str(e)}"
        )


# 文本分类
@router.post("/tasks/classify", response_model=llm_schemas.TaskResponse)
async def classify_text(
    request: llm_schemas.ClassifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    文本分类API
    
    Args:
        request: 文本分类请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        文本分类结果
    """
    try:
        # 调用文本分类服务
        result = llm_tasks.classify_text(
            text=request.text,
            **(request.options or {})
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result.get("model", "unknown"),
            prompt=request.text,
            response=str(result["result"]),
            tokens_used=result.get("tokens_used", 0),
            task_type="classify"
        )
        
        return llm_schemas.TaskResponse(
            task_type="classify",
            result=result["result"],
            execution_time_ms=result.get("execution_time_ms", 0),
            tokens_used=result.get("tokens_used", 0)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文本分类失败: {str(e)}"
        )


# 信息提取
@router.post("/tasks/extract-info", response_model=llm_schemas.TaskResponse)
async def extract_info(
    request: llm_schemas.ExtractInfoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    信息提取API
    
    Args:
        request: 信息提取请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        信息提取结果
    """
    try:
        # 调用信息提取服务
        result = llm_tasks.extract_information(
            text=request.text,
            **(request.options or {})
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result.get("model", "unknown"),
            prompt=request.text,
            response=str(result["result"]),
            tokens_used=result.get("tokens_used", 0),
            task_type="extract_info"
        )
        
        return llm_schemas.TaskResponse(
            task_type="extract_info",
            result=result["result"],
            execution_time_ms=result.get("execution_time_ms", 0),
            tokens_used=result.get("tokens_used", 0)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"信息提取失败: {str(e)}"
        )


# 文本扩写
@router.post("/tasks/expand", response_model=llm_schemas.TaskResponse)
async def expand_text(
    request: llm_schemas.ExpandTextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    文本扩写API
    
    Args:
        request: 文本扩写请求参数
        db: 数据库会话
        current_user: 当前活跃用户
    
    Returns:
        文本扩写结果
    """
    try:
        # 调用文本扩写服务
        result = llm_tasks.expand_text(
            text=request.text,
            **(request.options or {})
        )
        
        # 记录请求历史
        llm_service.log_request(
            user_id=current_user.id,
            model_name=result.get("model", "unknown"),
            prompt=request.text,
            response=str(result["result"]),
            tokens_used=result.get("tokens_used", 0),
            task_type="expand"
        )
        
        return llm_schemas.TaskResponse(
            task_type="expand",
            result=result["result"],
            execution_time_ms=result.get("execution_time_ms", 0),
            tokens_used=result.get("tokens_used", 0)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文本扩写失败: {str(e)}"
        )