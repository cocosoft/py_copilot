"""
层次化管理服务

实现层次化实体管理、权限继承、层次化搜索和数据隔离

任务编号: Phase3-Week10
阶段: 第三阶段 - 功能不完善问题优化
"""

import logging
import json
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class HierarchyLevel(Enum):
    """层次级别"""
    GLOBAL = "global"
    KNOWLEDGE_BASE = "knowledge_base"
    DOCUMENT = "document"
    ENTITY = "entity"


class PermissionType(Enum):
    """权限类型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


@dataclass
class HierarchyNode:
    """层次节点"""
    id: str
    name: str
    level: HierarchyLevel
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level.value,
            "parent_id": self.parent_id,
            "children": self.children,
            "metadata": self.metadata,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class Permission:
    """权限定义"""
    user_id: str
    permission_type: PermissionType
    resource_id: str
    inherited: bool = False
    source_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "permission_type": self.permission_type.value,
            "resource_id": self.resource_id,
            "inherited": self.inherited,
            "source_id": self.source_id
        }


class HierarchyManager:
    """层次化管理器"""
    
    def __init__(self):
        self.nodes: Dict[str, HierarchyNode] = {}
        self.permission_cache: Dict[str, Dict[str, Set[PermissionType]]] = defaultdict(lambda: defaultdict(set))
        self._initialize_default_hierarchy()
    
    def _initialize_default_hierarchy(self):
        """初始化默认层次结构"""
        global_node = HierarchyNode(
            id="global",
            name="全局",
            level=HierarchyLevel.GLOBAL,
            permissions={
                "admin": ["read", "write", "delete", "admin"],
                "user": ["read"]
            }
        )
        self.nodes["global"] = global_node
        logger.info("初始化默认层次结构完成")
    
    def create_node(self, node_id: str, name: str, level: HierarchyLevel,
                   parent_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> HierarchyNode:
        """创建层次节点"""
        if node_id in self.nodes:
            raise ValueError(f"节点 {node_id} 已存在")
        
        if parent_id and parent_id not in self.nodes:
            raise ValueError(f"父节点 {parent_id} 不存在")
        
        node = HierarchyNode(
            id=node_id,
            name=name,
            level=level,
            parent_id=parent_id,
            metadata=metadata or {}
        )
        
        self.nodes[node_id] = node
        
        if parent_id:
            self.nodes[parent_id].children.append(node_id)
        
        self._inherit_permissions(node_id)
        
        logger.info(f"创建层次节点: {node_id}, 级别: {level.value}, 父节点: {parent_id}")
        return node
    
    def get_node(self, node_id: str) -> Optional[HierarchyNode]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def update_node(self, node_id: str, name: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[HierarchyNode]:
        """更新节点"""
        node = self.nodes.get(node_id)
        if not node:
            return None
        
        if name:
            node.name = name
        if metadata:
            node.metadata.update(metadata)
        
        node.updated_at = datetime.now()
        
        logger.info(f"更新层次节点: {node_id}")
        return node
    
    def delete_node(self, node_id: str, cascade: bool = False) -> bool:
        """删除节点"""
        if node_id == "global":
            raise ValueError("不能删除全局节点")
        
        node = self.nodes.get(node_id)
        if not node:
            return False
        
        if node.children:
            if cascade:
                for child_id in node.children[:]:
                    self.delete_node(child_id, cascade=True)
            else:
                raise ValueError(f"节点 {node_id} 有子节点，无法删除")
        
        if node.parent_id:
            parent = self.nodes.get(node.parent_id)
            if parent and node_id in parent.children:
                parent.children.remove(node_id)
        
        del self.nodes[node_id]
        
        if node_id in self.permission_cache:
            del self.permission_cache[node_id]
        
        logger.info(f"删除层次节点: {node_id}")
        return True
    
    def get_children(self, node_id: str, recursive: bool = False) -> List[HierarchyNode]:
        """获取子节点"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        
        children = [self.nodes[cid] for cid in node.children if cid in self.nodes]
        
        if recursive:
            all_children = children[:]
            for child in children:
                all_children.extend(self.get_children(child.id, recursive=True))
            return all_children
        
        return children
    
    def get_ancestors(self, node_id: str) -> List[HierarchyNode]:
        """获取祖先节点"""
        ancestors = []
        node = self.nodes.get(node_id)
        
        while node and node.parent_id:
            parent = self.nodes.get(node.parent_id)
            if parent:
                ancestors.append(parent)
                node = parent
            else:
                break
        
        return ancestors
    
    def get_path(self, node_id: str) -> List[HierarchyNode]:
        """获取从根到当前节点的路径"""
        path = []
        node = self.nodes.get(node_id)
        
        if not node:
            return path
        
        ancestors = self.get_ancestors(node_id)
        ancestors.reverse()
        path.extend(ancestors)
        path.append(node)
        
        return path
    
    def grant_permission(self, node_id: str, user_id: str, 
                        permission_type: PermissionType) -> bool:
        """授予权限"""
        node = self.nodes.get(node_id)
        if not node:
            return False
        
        if user_id not in node.permissions:
            node.permissions[user_id] = []
        
        perm_str = permission_type.value
        if perm_str not in node.permissions[user_id]:
            node.permissions[user_id].append(perm_str)
        
        self.permission_cache[node_id][user_id].add(permission_type)
        
        self._propagate_permission_to_children(node_id, user_id, permission_type)
        
        logger.info(f"授予权限: 节点={node_id}, 用户={user_id}, 权限={permission_type.value}")
        return True
    
    def revoke_permission(self, node_id: str, user_id: str,
                         permission_type: PermissionType) -> bool:
        """撤销权限"""
        node = self.nodes.get(node_id)
        if not node:
            return False
        
        if user_id in node.permissions:
            perm_str = permission_type.value
            if perm_str in node.permissions[user_id]:
                node.permissions[user_id].remove(perm_str)
        
        if node_id in self.permission_cache and user_id in self.permission_cache[node_id]:
            self.permission_cache[node_id][user_id].discard(permission_type)
        
        self._revoke_permission_from_children(node_id, user_id, permission_type)
        
        logger.info(f"撤销权限: 节点={node_id}, 用户={user_id}, 权限={permission_type.value}")
        return True
    
    def check_permission(self, node_id: str, user_id: str,
                        permission_type: PermissionType) -> bool:
        """检查权限"""
        if node_id not in self.permission_cache:
            self._build_permission_cache(node_id)
        
        return permission_type in self.permission_cache[node_id].get(user_id, set())
    
    def get_permissions(self, node_id: str, user_id: str) -> Set[PermissionType]:
        """获取用户在节点上的所有权限"""
        if node_id not in self.permission_cache:
            self._build_permission_cache(node_id)
        
        return self.permission_cache[node_id].get(user_id, set())
    
    def _inherit_permissions(self, node_id: str):
        """继承父节点权限"""
        node = self.nodes.get(node_id)
        if not node or not node.parent_id:
            return
        
        parent = self.nodes.get(node.parent_id)
        if not parent:
            return
        
        for user_id, perms in parent.permissions.items():
            for perm_str in perms:
                try:
                    perm_type = PermissionType(perm_str)
                    if user_id not in node.permissions:
                        node.permissions[user_id] = []
                    if perm_str not in node.permissions[user_id]:
                        node.permissions[user_id].append(perm_str)
                    self.permission_cache[node_id][user_id].add(perm_type)
                except ValueError:
                    pass
    
    def _propagate_permission_to_children(self, node_id: str, user_id: str,
                                          permission_type: PermissionType):
        """向子节点传播权限"""
        children = self.get_children(node_id)
        for child in children:
            if user_id not in child.permissions:
                child.permissions[user_id] = []
            
            perm_str = permission_type.value
            if perm_str not in child.permissions[user_id]:
                child.permissions[user_id].append(perm_str)
            
            self.permission_cache[child.id][user_id].add(permission_type)
            
            self._propagate_permission_to_children(child.id, user_id, permission_type)
    
    def _revoke_permission_from_children(self, node_id: str, user_id: str,
                                         permission_type: PermissionType):
        """从子节点撤销权限"""
        children = self.get_children(node_id)
        for child in children:
            if user_id in child.permissions:
                perm_str = permission_type.value
                if perm_str in child.permissions[user_id]:
                    child.permissions[user_id].remove(perm_str)
            
            if child.id in self.permission_cache and user_id in self.permission_cache[child.id]:
                self.permission_cache[child.id][user_id].discard(permission_type)
            
            self._revoke_permission_from_children(child.id, user_id, permission_type)
    
    def _build_permission_cache(self, node_id: str):
        """构建权限缓存"""
        node = self.nodes.get(node_id)
        if not node:
            return
        
        ancestors = self.get_ancestors(node_id)
        
        for user_id in set(list(node.permissions.keys()) + 
                          [uid for a in ancestors for uid in a.permissions.keys()]):
            perms = set()
            
            for ancestor in ancestors:
                if user_id in ancestor.permissions:
                    for perm_str in ancestor.permissions[user_id]:
                        try:
                            perms.add(PermissionType(perm_str))
                        except ValueError:
                            pass
            
            if user_id in node.permissions:
                for perm_str in node.permissions[user_id]:
                    try:
                        perms.add(PermissionType(perm_str))
                    except ValueError:
                        pass
            
            self.permission_cache[node_id][user_id] = perms
    
    def search_by_level(self, level: HierarchyLevel, 
                       user_id: Optional[str] = None,
                       permission_type: PermissionType = PermissionType.READ) -> List[HierarchyNode]:
        """按层次级别搜索"""
        results = []
        
        for node in self.nodes.values():
            if node.level == level:
                if user_id is None or self.check_permission(node.id, user_id, permission_type):
                    results.append(node)
        
        return results
    
    def search_by_parent(self, parent_id: str,
                        user_id: Optional[str] = None,
                        permission_type: PermissionType = PermissionType.READ) -> List[HierarchyNode]:
        """按父节点搜索"""
        parent = self.nodes.get(parent_id)
        if not parent:
            return []
        
        results = []
        for child_id in parent.children:
            if child_id in self.nodes:
                child = self.nodes[child_id]
                if user_id is None or self.check_permission(child.id, user_id, permission_type):
                    results.append(child)
        
        return results
    
    def search_by_metadata(self, key: str, value: Any,
                          user_id: Optional[str] = None,
                          permission_type: PermissionType = PermissionType.READ) -> List[HierarchyNode]:
        """按元数据搜索"""
        results = []
        
        for node in self.nodes.values():
            if node.metadata.get(key) == value:
                if user_id is None or self.check_permission(node.id, user_id, permission_type):
                    results.append(node)
        
        return results
    
    def get_data_isolation_scope(self, node_id: str, user_id: str) -> Dict[str, Any]:
        """获取数据隔离范围"""
        node = self.nodes.get(node_id)
        if not node:
            return {"accessible": False, "scope": [], "reason": "节点不存在"}
        
        if not self.check_permission(node_id, user_id, PermissionType.READ):
            return {"accessible": False, "scope": [], "reason": "无访问权限"}
        
        accessible_nodes = [node_id]
        accessible_nodes.extend([c.id for c in self.get_children(node_id, recursive=True)])
        
        return {
            "accessible": True,
            "scope": accessible_nodes,
            "node_level": node.level.value,
            "permissions": [p.value for p in self.get_permissions(node_id, user_id)]
        }
    
    def export_hierarchy(self) -> Dict[str, Any]:
        """导出层次结构"""
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "exported_at": datetime.now().isoformat()
        }
    
    def import_hierarchy(self, data: Dict[str, Any]) -> bool:
        """导入层次结构"""
        try:
            nodes_data = data.get("nodes", {})
            
            self.nodes.clear()
            self.permission_cache.clear()
            
            for nid, ndata in nodes_data.items():
                level = HierarchyLevel(ndata["level"])
                node = HierarchyNode(
                    id=nid,
                    name=ndata["name"],
                    level=level,
                    parent_id=ndata.get("parent_id"),
                    children=ndata.get("children", []),
                    metadata=ndata.get("metadata", {}),
                    permissions=ndata.get("permissions", {}),
                    created_at=datetime.fromisoformat(ndata["created_at"]) if ndata.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(ndata["updated_at"]) if ndata.get("updated_at") else datetime.now()
                )
                self.nodes[nid] = node
            
            for node in self.nodes.values():
                self._build_permission_cache(node.id)
            
            logger.info(f"导入层次结构完成，共 {len(self.nodes)} 个节点")
            return True
        except Exception as e:
            logger.error(f"导入层次结构失败: {e}")
            return False


_hierarchy_manager: Optional[HierarchyManager] = None


def get_hierarchy_manager() -> HierarchyManager:
    """获取层次化管理器实例"""
    global _hierarchy_manager
    if _hierarchy_manager is None:
        _hierarchy_manager = HierarchyManager()
    return _hierarchy_manager
