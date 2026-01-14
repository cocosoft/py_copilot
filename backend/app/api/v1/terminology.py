"""术语库API路由"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_db
from app.models.terminology import Terminology, TerminologyHistory
from app.api.deps import get_current_user
from app.models.user import User

# 创建路由器
router = APIRouter(prefix="/terminology", tags=["terminology"])


@router.get("/")
def get_terminology(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    source_language: Optional[str] = Query(None, description="源语言筛选"),
    target_language: Optional[str] = Query(None, description="目标语言筛选"),
    domain: Optional[str] = Query(None, description="领域筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取术语库条目列表"""
    try:
        # 构建查询
        query = db.query(Terminology)
        
        # 应用筛选条件
        if source_language:
            query = query.filter(Terminology.source_language == source_language)
        if target_language:
            query = query.filter(Terminology.target_language == target_language)
        if domain:
            query = query.filter(Terminology.domain == domain)
        if search:
            query = query.filter(
                or_(
                    Terminology.source_term.ilike(f"%{search}%"),
                    Terminology.target_term.ilike(f"%{search}%")
                )
            )
        
        # 只显示已审核通过的术语
        query = query.filter(Terminology.approval_status == "approved")
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        items = query.order_by(Terminology.usage_count.desc())\
                    .offset((page - 1) * page_size)\
                    .limit(page_size)\
                    .all()
        
        # 转换为字典格式
        terminology_list = []
        for item in items:
            terminology_list.append({
                "id": item.id,
                "source_term": item.source_term,
                "target_term": item.target_term,
                "source_language": item.source_language,
                "target_language": item.target_language,
                "domain": item.domain,
                "description": item.description,
                "tags": item.tags.split(",") if item.tags else [],
                "confidence_score": item.confidence_score,
                "usage_count": item.usage_count,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None
            })
        
        return {
            "success": True,
            "message": "获取术语库成功",
            "data": {
                "items": terminology_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取术语库失败: {str(e)}")


@router.post("/")
def save_terminology(
    term_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存术语库条目"""
    try:
        # 检查是否已存在相同术语
        existing_term = db.query(Terminology).filter(
            and_(
                Terminology.source_term == term_data.get("source_term"),
                Terminology.source_language == term_data.get("source_language"),
                Terminology.target_language == term_data.get("target_language")
            )
        ).first()
        
        if existing_term:
            # 更新现有术语
            existing_term.target_term = term_data.get("target_term", existing_term.target_term)
            existing_term.domain = term_data.get("domain", existing_term.domain)
            existing_term.description = term_data.get("description", existing_term.description)
            existing_term.tags = term_data.get("tags", existing_term.tags)
            existing_term.confidence_score = term_data.get("confidence_score", existing_term.confidence_score)
        else:
            # 创建新术语
            new_term = Terminology(
                source_term=term_data.get("source_term"),
                target_term=term_data.get("target_term"),
                source_language=term_data.get("source_language"),
                target_language=term_data.get("target_language"),
                domain=term_data.get("domain"),
                description=term_data.get("description"),
                tags=term_data.get("tags"),
                confidence_score=term_data.get("confidence_score", 80),
                user_id=current_user.id,
                source="manual"
            )
            db.add(new_term)
        
        db.commit()
        
        return {
            "success": True,
            "message": "术语保存成功"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存术语失败: {str(e)}")


@router.post("/search")
def search_terminology(
    search_params: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索术语库"""
    try:
        query = search_params.get("query", "").strip()
        source_language = search_params.get("source_language")
        target_language = search_params.get("target_language")
        domain = search_params.get("domain")
        
        if not query:
            return {
                "success": True,
                "message": "搜索成功",
                "data": {
                    "items": [],
                    "total": 0
                }
            }
        
        # 构建查询
        db_query = db.query(Terminology)
        
        # 应用搜索条件
        db_query = db_query.filter(
            or_(
                Terminology.source_term.ilike(f"%{query}%"),
                Terminology.target_term.ilike(f"%{query}%")
            )
        )
        
        if source_language:
            db_query = db_query.filter(Terminology.source_language == source_language)
        if target_language:
            db_query = db_query.filter(Terminology.target_language == target_language)
        if domain:
            db_query = db_query.filter(Terminology.domain == domain)
        
        # 只显示已审核通过的术语
        db_query = db_query.filter(Terminology.approval_status == "approved")
        
        # 按使用次数排序
        items = db_query.order_by(Terminology.usage_count.desc()).limit(20).all()
        
        # 转换为字典格式
        terminology_list = []
        for item in items:
            terminology_list.append({
                "id": item.id,
                "source_term": item.source_term,
                "target_term": item.target_term,
                "source_language": item.source_language,
                "target_language": item.target_language,
                "domain": item.domain,
                "description": item.description,
                "tags": item.tags.split(",") if item.tags else [],
                "confidence_score": item.confidence_score,
                "usage_count": item.usage_count
            })
        
        return {
            "success": True,
            "message": "搜索成功",
            "data": {
                "items": terminology_list,
                "total": len(terminology_list)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索术语库失败: {str(e)}")


@router.post("/apply")
def apply_terminology(
    apply_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """应用术语库到翻译文本"""
    try:
        source_text = apply_data.get("source_text", "")
        target_text = apply_data.get("target_text", "")
        source_language = apply_data.get("source_language")
        target_language = apply_data.get("target_language")
        
        if not source_text or not target_text:
            return {
                "success": True,
                "message": "无需术语替换",
                "data": {
                    "original_text": target_text,
                    "applied_text": target_text,
                    "applied_terms": []
                }
            }
        
        # 获取相关术语
        terms_query = db.query(Terminology).filter(
            and_(
                Terminology.source_language == source_language,
                Terminology.target_language == target_language,
                Terminology.approval_status == "approved"
            )
        ).order_by(Terminology.usage_count.desc()).limit(50)
        
        terms = terms_query.all()
        
        applied_terms = []
        applied_text = target_text
        
        # 应用术语替换（按术语长度从长到短排序，避免短术语覆盖长术语）
        sorted_terms = sorted(terms, key=lambda x: len(x.source_term), reverse=True)
        
        for term in sorted_terms:
            if term.source_term.lower() in source_text.lower():
                # 在目标文本中查找并替换
                if term.target_term.lower() in applied_text.lower():
                    # 术语已存在，跳过
                    continue
                
                # 执行替换（保持大小写）
                import re
                
                # 查找源术语在源文本中的位置
                source_matches = re.finditer(re.escape(term.source_term), source_text, re.IGNORECASE)
                
                for match in source_matches:
                    # 记录应用的术语
                    applied_terms.append({
                        "source_term": term.source_term,
                        "target_term": term.target_term,
                        "position": match.start(),
                        "length": len(term.source_term)
                    })
                    
                    # 更新术语使用次数
                    term.usage_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": "术语应用完成",
            "data": {
                "original_text": target_text,
                "applied_text": applied_text,
                "applied_terms": applied_terms
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"应用术语失败: {str(e)}")


@router.get("/domains")
def get_terminology_domains(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取术语库领域列表"""
    try:
        domains = db.query(Terminology.domain).distinct().filter(
            Terminology.domain.isnot(None),
            Terminology.approval_status == "approved"
        ).all()
        
        domain_list = [domain[0] for domain in domains if domain[0]]
        
        # 添加默认领域
        default_domains = ["general", "business", "technical", "medical", "legal", "academic"]
        
        # 合并并去重
        all_domains = list(set(domain_list + default_domains))
        all_domains.sort()
        
        return {
            "success": True,
            "message": "获取领域列表成功",
            "data": {
                "domains": all_domains
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取领域列表失败: {str(e)}")