"""
层次化管理API

提供层次化实体管理的配置和管理接口

任务编号: Phase3-Week10
阶段: 第三阶段 - 功能不完善问题优化
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.services.knowledge.hierarchy_manager import (
    HierarchyManager,
    HierarchyNode,
    HierarchyLevel,
    PermissionType,
    get_hierarchy_manager
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hierarchy", tags=["层次化管理"])


class CreateNodeRequest(BaseModel):
    """创建节点请求"""
    node_id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    level: str = Field(..., description="层次级别: global, knowledge_base, document, entity")
    parent_id: Optional[str] = Field(default=None, description="父节点ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class UpdateNodeRequest(BaseModel):
    """更新节点请求"""
    name: Optional[str] = Field(default=None, description="节点名称")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class PermissionRequest(BaseModel):
    """权限请求"""
    user_id: str = Field(..., description="用户ID")
    permission_type: str = Field(..., description="权限类型: read, write, delete, admin")


class NodeResponse(BaseModel):
    """节点响应"""
    id: str
    name: str
    level: str
    parent_id: Optional[str]
    children: List[str]
    metadata: Dict[str, Any]
    permissions: Dict[str, List[str]]
    created_at: str
    updated_at: str


class PermissionResponse(BaseModel):
    """权限响应"""
    user_id: str
    permissions: List[str]
    inherited: bool


class DataIsolationResponse(BaseModel):
    """数据隔离响应"""
    accessible: bool
    scope: List[str]
    node_level: Optional[str] = None
    permissions: List[str] = []
    reason: Optional[str] = None


class HierarchyTreeResponse(BaseModel):
    """层次树响应"""
    id: str
    name: str
    level: str
    children: List['HierarchyTreeResponse']


def get_manager() -> HierarchyManager:
    """获取层次化管理器依赖"""
    return get_hierarchy_manager()


@router.post("/nodes", response_model=NodeResponse)
async def create_node(
    request: CreateNodeRequest,
    manager: HierarchyManager = Depends(get_manager)
):
    """
    创建层次节点
    
    创建新的层次节点，自动继承父节点权限
    """
    try:
        level_map = {
            "global": HierarchyLevel.GLOBAL,
            "knowledge_base": HierarchyLevel.KNOWLEDGE_BASE,
            "document": HierarchyLevel.DOCUMENT,
            "entity": HierarchyLevel.ENTITY
        }
        
        level = level_map.get(request.level.lower())
        if not level:
            raise HTTPException(status_code=400, detail=f"无效的层次级别: {request.level}")
        
        node = manager.create_node(
            node_id=request.node_id,
            name=request.name,
            level=level,
            parent_id=request.parent_id,
            metadata=request.metadata
        )
        
        return NodeResponse(**node.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建节点失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建节点失败: {str(e)}")


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    manager: HierarchyManager = Depends(get_manager)
):
    """
    获取节点信息
    
    返回指定节点的详细信息
    """
    node = manager.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
    
    return NodeResponse(**node.to_dict())


@router.put("/nodes/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: str,
    request: UpdateNodeRequest,
    manager: HierarchyManager = Depends(get_manager)
):
    """
    更新节点信息
    
    更新节点的名称和元数据
    """
    node = manager.update_node(node_id, name=request.name, metadata=request.metadata)
    if not node:
        raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
    
    return NodeResponse(**node.to_dict())


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: str,
    cascade: bool = Query(default=False, description="是否级联删除子节点"),
    manager: HierarchyManager = Depends(get_manager)
):
    """
    删除节点
    
    删除指定节点，可选择级联删除子节点
    """
    try:
        success = manager.delete_node(node_id, cascade=cascade)
        if not success:
            raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
        
        return {"success": True, "message": f"节点 {node_id} 已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除节点失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除节点失败: {str(e)}")


@router.get("/nodes/{node_id}/children", response_model=List[NodeResponse])
async def get_children(
    node_id: str,
    recursive: bool = Query(default=False, description="是否递归获取所有子节点"),
    manager: HierarchyManager = Depends(get_manager)
):
    """
    获取子节点
    
    返回指定节点的子节点列表
    """
    children = manager.get_children(node_id, recursive=recursive)
    return [NodeResponse(**child.to_dict()) for child in children]


@router.get("/nodes/{node_id}/ancestors", response_model=List[NodeResponse])
async def get_ancestors(
    node_id: str,
    manager: HierarchyManager = Depends(get_manager)
):
    """
    获取祖先节点
    
    返回从父节点到根节点的所有祖先节点
    """
    ancestors = manager.get_ancestors(node_id)
    return [NodeResponse(**ancestor.to_dict()) for ancestor in ancestors]


@router.get("/nodes/{node_id}/path", response_model=List[NodeResponse])
async def get_path(
    node_id: str,
    manager: HierarchyManager = Depends(get_manager)
):
    """
    获取节点路径
    
    返回从根节点到当前节点的完整路径
    """
    path = manager.get_path(node_id)
    return [NodeResponse(**node.to_dict()) for node in path]


@router.post("/nodes/{node_id}/permissions", response_model=PermissionResponse)
async def grant_permission(
    node_id: str,
    request: PermissionRequest,
    manager: HierarchyManager = Depends(get_manager)
):
    """
    授予权限
    
    为用户授予节点权限，权限会自动传播到子节点
    """
    try:
        perm_map = {
            "read": PermissionType.READ,
            "write": PermissionType.WRITE,
            "delete": PermissionType.DELETE,
            "admin": PermissionType.ADMIN
        }
        
        perm_type = perm_map.get(request.permission_type.lower())
        if not perm_type:
            raise HTTPException(status_code=400, detail=f"无效的权限类型: {request.permission_type}")
        
        success = manager.grant_permission(node_id, request.user_id, perm_type)
        if not success:
            raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
        
        permissions = [p.value for p in manager.get_permissions(node_id, request.user_id)]
        
        return PermissionResponse(
            user_id=request.user_id,
            permissions=permissions,
            inherited=False
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"授予权限失败: {e}")
        raise HTTPException(status_code=500, detail=f"授予权限失败: {str(e)}")


@router.delete("/nodes/{node_id}/permissions", response_model=PermissionResponse)
async def revoke_permission(
    node_id: str,
    request: PermissionRequest,
    manager: HierarchyManager = Depends(get_manager)
):
    """
    撤销权限
    
    撤销用户的节点权限，权限会从子节点同步撤销
    """
    try:
        perm_map = {
            "read": PermissionType.READ,
            "write": PermissionType.WRITE,
            "delete": PermissionType.DELETE,
            "admin": PermissionType.ADMIN
        }
        
        perm_type = perm_map.get(request.permission_type.lower())
        if not perm_type:
            raise HTTPException(status_code=400, detail=f"无效的权限类型: {request.permission_type}")
        
        success = manager.revoke_permission(node_id, request.user_id, perm_type)
        if not success:
            raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
        
        permissions = [p.value for p in manager.get_permissions(node_id, request.user_id)]
        
        return PermissionResponse(
            user_id=request.user_id,
            permissions=permissions,
            inherited=False
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"撤销权限失败: {e}")
        raise HTTPException(status_code=500, detail=f"撤销权限失败: {str(e)}")


@router.get("/nodes/{node_id}/permissions/check")
async def check_permission(
    node_id: str,
    user_id: str = Query(..., description="用户ID"),
    permission_type: str = Query(..., description="权限类型"),
    manager: HierarchyManager = Depends(get_manager)
):
    """
    检查权限
    
    检查用户是否拥有指定节点的权限
    """
    try:
        perm_map = {
            "read": PermissionType.READ,
            "write": PermissionType.WRITE,
            "delete": PermissionType.DELETE,
            "admin": PermissionType.ADMIN
        }
        
        perm_type = perm_map.get(permission_type.lower())
        if not perm_type:
            raise HTTPException(status_code=400, detail=f"无效的权限类型: {permission_type}")
        
        has_permission = manager.check_permission(node_id, user_id, perm_type)
        
        return {
            "node_id": node_id,
            "user_id": user_id,
            "permission_type": permission_type,
            "has_permission": has_permission
        }
    except Exception as e:
        logger.error(f"检查权限失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查权限失败: {str(e)}")


@router.get("/nodes/{node_id}/isolation", response_model=DataIsolationResponse)
async def get_data_isolation(
    node_id: str,
    user_id: str = Query(..., description="用户ID"),
    manager: HierarchyManager = Depends(get_manager)
):
    """
    获取数据隔离范围
    
    返回用户在指定节点下的数据访问范围
    """
    scope = manager.get_data_isolation_scope(node_id, user_id)
    return DataIsolationResponse(**scope)


@router.get("/search/level", response_model=List[NodeResponse])
async def search_by_level(
    level: str = Query(..., description="层次级别"),
    user_id: Optional[str] = Query(default=None, description="用户ID（用于权限过滤）"),
    manager: HierarchyManager = Depends(get_manager)
):
    """
    按层次级别搜索
    
    返回指定层次级别的所有节点
    """
    level_map = {
        "global": HierarchyLevel.GLOBAL,
        "knowledge_base": HierarchyLevel.KNOWLEDGE_BASE,
        "document": HierarchyLevel.DOCUMENT,
        "entity": HierarchyLevel.ENTITY
    }
    
    hierarchy_level = level_map.get(level.lower())
    if not hierarchy_level:
        raise HTTPException(status_code=400, detail=f"无效的层次级别: {level}")
    
    results = manager.search_by_level(hierarchy_level, user_id)
    return [NodeResponse(**node.to_dict()) for node in results]


@router.get("/search/parent", response_model=List[NodeResponse])
async def search_by_parent(
    parent_id: str = Query(..., description="父节点ID"),
    user_id: Optional[str] = Query(default=None, description="用户ID（用于权限过滤）"),
    manager: HierarchyManager = Depends(get_manager)
):
    """
    按父节点搜索
    
    返回指定父节点下的所有子节点
    """
    results = manager.search_by_parent(parent_id, user_id)
    return [NodeResponse(**node.to_dict()) for node in results]


@router.get("/tree", response_model=HierarchyTreeResponse)
async def get_hierarchy_tree(
    root_id: str = Query(default="global", description="根节点ID"),
    manager: HierarchyManager = Depends(get_manager)
):
    """
    获取层次树
    
    返回从指定根节点开始的层次树结构
    """
    def build_tree(node_id: str) -> HierarchyTreeResponse:
        node = manager.get_node(node_id)
        if not node:
            return None
        
        children = []
        for child_id in node.children:
            child_tree = build_tree(child_id)
            if child_tree:
                children.append(child_tree)
        
        return HierarchyTreeResponse(
            id=node.id,
            name=node.name,
            level=node.level.value,
            children=children
        )
    
    tree = build_tree(root_id)
    if not tree:
        raise HTTPException(status_code=404, detail=f"根节点 {root_id} 不存在")
    
    return tree


@router.post("/export")
async def export_hierarchy(
    manager: HierarchyManager = Depends(get_manager)
):
    """
    导出层次结构
    
    导出完整的层次结构数据
    """
    try:
        data = manager.export_hierarchy()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"导出层次结构失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/import")
async def import_hierarchy(
    data: Dict[str, Any],
    manager: HierarchyManager = Depends(get_manager)
):
    """
    导入层次结构
    
    导入层次结构数据
    """
    try:
        success = manager.import_hierarchy(data)
        if not success:
            raise HTTPException(status_code=400, detail="导入数据格式无效")
        
        return {"success": True, "message": "层次结构导入成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入层次结构失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
