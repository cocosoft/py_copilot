"""API文档管理路由"""

from app.core.config import Settings
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.api_document_service import ApiDocumentService
from app.api.deps import get_db
from app.models.api_favorite import ApiFavorite
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 延迟导入api_router以避免循环导入
_api_router = None

def get_api_router():
    """获取api_router实例（延迟导入）"""
    global _api_router
    if _api_router is None:
        from app.api import api_router
        _api_router = api_router
    return _api_router

# 创建API文档服务实例（延迟初始化）
api_doc_service = None

def get_api_doc_service():
    """获取API文档服务实例"""
    global api_doc_service
    if api_doc_service is None:
        api_doc_service = ApiDocumentService(api_router=get_api_router())
    return api_doc_service


class FavoriteRequest(BaseModel):
    """收藏请求模型"""
    api_path: str
    api_method: str
    api_summary: Optional[str] = None
    api_module: Optional[str] = None
    user_id: Optional[int] = None


@router.get("/list", response_model=List[Dict[str, Any]])
async def get_api_list(
    module: Optional[str] = None,
    method: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取API列表"""
    try:
        service = get_api_doc_service()
        api_list = service.extract_api_info()
        
        if module:
            api_list = [api for api in api_list if api['module'] == module]
        if method:
            api_list = [api for api in api_list if api['method'] == method]
        
        return api_list
    except Exception as e:
        logger.error(f"获取API列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取API列表失败")


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_api(
    keyword: str,
    db: Session = Depends(get_db)
):
    """搜索API"""
    try:
        service = get_api_doc_service()
        api_list = service.extract_api_info()
        
        results = []
        keyword_lower = keyword.lower()
        for api in api_list:
            if (keyword_lower in api['path'].lower() or
                keyword_lower in api['summary'].lower() or
                keyword_lower in api['description'].lower() or
                any(keyword_lower in tag.lower() for tag in api['tags'])):
                results.append(api)
        
        return results
    except Exception as e:
        logger.error(f"搜索API失败: {e}")
        raise HTTPException(status_code=500, detail="搜索API失败")


@router.get("/stats")
async def get_api_stats(db: Session = Depends(get_db)):
    """获取API统计信息"""
    try:
        service = get_api_doc_service()
        api_list = service.extract_api_info()
        
        module_stats = {}
        for api in api_list:
            module = api['module']
            if module not in module_stats:
                module_stats[module] = 0
            module_stats[module] += 1
        
        method_stats = {}
        for api in api_list:
            method = api['method']
            if method not in method_stats:
                method_stats[method] = 0
            method_stats[method] += 1
        
        return {
            'total': len(api_list),
            'module_stats': module_stats,
            'method_stats': method_stats
        }
    except Exception as e:
        logger.error(f"获取API统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取API统计信息失败")


@router.post("/test")
async def test_api(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """测试API"""
    try:
        api_path = request.get('path', '')
        api_method = request.get('method', 'GET').upper()
        api_data = request.get('data', {})
        
        if not api_path:
            raise HTTPException(status_code=400, detail="API路径不能为空")
        
        # 构建完整的API路径
        if not api_path.startswith('/'):
            api_path = '/' + api_path
        if not api_path.startswith('/api'):
            api_path = '/api' + api_path
        
        # 使用 httpx.AsyncClient 进行真实的API测试
        import httpx
        
        # 获取当前应用的base URL
        base_url = Settings().api_base_url
        full_url = base_url + api_path
        
        # 创建异步HTTP客户端
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 根据HTTP方法执行请求
            if api_method == 'GET':
                response = await client.get(full_url, params=api_data)
            elif api_method == 'POST':
                response = await client.post(full_url, json=api_data)
            elif api_method == 'PUT':
                response = await client.put(full_url, json=api_data)
            elif api_method == 'DELETE':
                response = await client.delete(full_url, params=api_data)
            elif api_method == 'PATCH':
                response = await client.patch(full_url, json=api_data)
            else:
                raise HTTPException(status_code=400, detail=f"不支持的HTTP方法: {api_method}")
            
            # 尝试解析JSON响应
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # 返回真实的测试结果
            return {
                'status': 'success',
                'message': 'API测试完成',
                'result': {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'data': response_data
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"API测试失败: {str(e)}")


@router.post("/favorites")
async def add_favorite(
    request: FavoriteRequest,
    db: Session = Depends(get_db)
):
    """添加API收藏"""
    try:
        existing = db.query(ApiFavorite).filter(
            and_(
                ApiFavorite.api_path == request.api_path,
                ApiFavorite.api_method == request.api_method,
                (ApiFavorite.user_id == request.user_id) if request.user_id else True
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="该API已在收藏列表中")
        
        favorite = ApiFavorite(
            user_id=request.user_id,
            api_path=request.api_path,
            api_method=request.api_method,
            api_summary=request.api_summary,
            api_module=request.api_module
        )
        
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        
        return {
            'status': 'success',
            'message': '收藏成功',
            'data': {
                'id': favorite.id,
                'api_path': favorite.api_path,
                'api_method': favorite.api_method
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加收藏失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="添加收藏失败")


@router.delete("/favorites")
async def remove_favorite(
    api_path: str,
    api_method: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """移除API收藏"""
    try:
        query = db.query(ApiFavorite).filter(
            and_(
                ApiFavorite.api_path == api_path,
                ApiFavorite.api_method == api_method
            )
        )
        
        if user_id:
            query = query.filter(ApiFavorite.user_id == user_id)
        
        favorite = query.first()
        
        if not favorite:
            raise HTTPException(status_code=404, detail="收藏不存在")
        
        db.delete(favorite)
        db.commit()
        
        return {
            'status': 'success',
            'message': '取消收藏成功'
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除收藏失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="移除收藏失败")


@router.get("/favorites")
async def get_favorites(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取收藏列表"""
    try:
        query = db.query(ApiFavorite)
        
        if user_id:
            query = query.filter(ApiFavorite.user_id == user_id)
        
        favorites = query.order_by(ApiFavorite.created_at.desc()).all()
        
        return {
            'status': 'success',
            'data': [
                {
                    'id': fav.id,
                    'api_path': fav.api_path,
                    'api_method': fav.api_method,
                    'api_summary': fav.api_summary,
                    'api_module': fav.api_module,
                    'created_at': fav.created_at.isoformat() if fav.created_at else None
                }
                for fav in favorites
            ]
        }
    except Exception as e:
        logger.error(f"获取收藏列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取收藏列表失败")


@router.get("/favorites/check")
async def check_favorite(
    api_path: str,
    api_method: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """检查API是否已收藏"""
    try:
        query = db.query(ApiFavorite).filter(
            and_(
                ApiFavorite.api_path == api_path,
                ApiFavorite.api_method == api_method
            )
        )
        
        if user_id:
            query = query.filter(ApiFavorite.user_id == user_id)
        
        favorite = query.first()
        
        return {
            'status': 'success',
            'is_favorite': favorite is not None
        }
    except Exception as e:
        logger.error(f"检查收藏状态失败: {e}")
        raise HTTPException(status_code=500, detail="检查收藏状态失败")
