"""
话题标题生成API路由
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.dependencies import get_db
from app.services.topic_title_service import TopicTitleService
from app.schemas.response import SuccessData

router = APIRouter()


class GenerateTitleRequest(BaseModel):
    conversation_id: int = Field(..., description="对话ID")
    content: str = Field(..., min_length=10, max_length=5000, description="对话内容")
    max_length: int = Field(20, ge=5, le=50, description="标题最大长度")
    style: str = Field("concise", description="标题风格: concise, descriptive, creative")


class GenerateTitleResponse(BaseModel):
    title: str
    model_id: int
    model_name: str
    generation_time: float
    quality_score: float


@router.post("/topic-title/generate", response_model=SuccessData[GenerateTitleResponse])
async def generate_topic_title(
    request: GenerateTitleRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    生成话题标题
    
    Args:
        request: 标题生成请求
        db: 数据库会话
    
    Returns:
        生成的标题及相关信息
    """
    try:
        service = TopicTitleService()
        result = service.generate_title(
            conversation_content=request.content,
            db=db,
            style=request.style,
            max_length=request.max_length
        )
        
        return SuccessData(
            data=result,
            message="标题生成成功"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标题生成失败: {str(e)}"
        )
