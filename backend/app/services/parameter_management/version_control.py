"""参数版本控制服务，支持参数变更跟踪和回滚"""
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.supplier_db import ModelDB, ModelParameter, ModelParameterVersion
from app.schemas.parameter_version import (
    ParameterVersionCreate, 
    ParameterVersionResponse,
    ParameterChangeLog
)


class VersionControlService:
    """参数版本控制服务"""
    
    @staticmethod
    def create_version(
        db: Session, 
        model_id: int, 
        version_data: ParameterVersionCreate,
        created_by: Optional[str] = None
    ) -> ModelParameterVersion:
        """
        创建参数版本快照
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            version_data: 版本创建数据
            created_by: 创建人
            
        Returns:
            创建的版本对象
        """
        # 验证模型存在
        model = db.query(ModelDB).filter(ModelDB.id == model_id).first()
        if not model:
            raise ValueError(f"模型ID {model_id} 不存在")
        
        # 获取当前模型的所有参数
        current_params = db.query(ModelParameter).filter(ModelParameter.model_id == model_id).all()
        
        # 序列化参数数据
        parameters_data = []
        for param in current_params:
            parameters_data.append({
                "id": param.id,
                "parameter_name": param.parameter_name,
                "parameter_value": param.parameter_value,
                "parameter_type": param.parameter_type,
                "parameter_source": param.parameter_source,
                "is_override": param.is_override,
                "parameter_level": param.parameter_level,
                "inherit_from": param.inherit_from,
                "parent_parameter_id": param.parent_parameter_id,
                "is_inherited": param.is_inherited,
                "description": param.description,
                "is_default": param.is_default
            })
        
        # 创建版本记录
        version = ModelParameterVersion(
            model_id=model_id,
            version_name=version_data.version_name,
            version_description=version_data.version_description,
            parameters_snapshot=json.dumps(parameters_data, ensure_ascii=False),
            created_by=created_by,
            is_active=True
        )
        
        db.add(version)
        db.commit()
        db.refresh(version)
        
        return version
    
    @staticmethod
    def get_model_versions(
        db: Session, 
        model_id: int, 
        include_inactive: bool = False
    ) -> List[ParameterVersionResponse]:
        """
        获取模型的所有版本
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            include_inactive: 是否包含非活跃版本
            
        Returns:
            版本列表
        """
        query = db.query(ModelParameterVersion).filter(ModelParameterVersion.model_id == model_id)
        
        if not include_inactive:
            query = query.filter(ModelParameterVersion.is_active == True)
        
        versions = query.order_by(desc(ModelParameterVersion.created_at)).all()
        
        return [
            ParameterVersionResponse(
                id=version.id,
                model_id=version.model_id,
                version_name=version.version_name,
                version_description=version.version_description,
                parameters_snapshot=json.loads(version.parameters_snapshot),
                created_by=version.created_by,
                created_at=version.created_at,
                is_active=version.is_active
            )
            for version in versions
        ]
    
    @staticmethod
    def restore_version(db: Session, version_id: int) -> Dict[str, Any]:
        """
        恢复到指定版本
        
        Args:
            db: 数据库会话
            version_id: 版本ID
            
        Returns:
            恢复结果信息
        """
        version = db.query(ModelParameterVersion).filter(ModelParameterVersion.id == version_id).first()
        if not version:
            raise ValueError(f"版本ID {version_id} 不存在")
        
        if not version.is_active:
            raise ValueError(f"版本 {version_id} 不是活跃版本，无法恢复")
        
        # 获取当前参数作为备份
        current_params = db.query(ModelParameter).filter(ModelParameter.model_id == version.model_id).all()
        
        # 删除当前所有参数
        for param in current_params:
            db.delete(param)
        
        # 恢复版本参数
        parameters_data = json.loads(version.parameters_snapshot)
        restored_params = []
        
        for param_data in parameters_data:
            # 创建新的参数记录
            param = ModelParameter(
                model_id=version.model_id,
                parameter_name=param_data["parameter_name"],
                parameter_value=param_data["parameter_value"],
                parameter_type=param_data["parameter_type"],
                parameter_source=param_data["parameter_source"],
                is_override=param_data["is_override"],
                parameter_level=param_data["parameter_level"],
                inherit_from=param_data["inherit_from"],
                parent_parameter_id=param_data["parent_parameter_id"],
                is_inherited=param_data["is_inherited"],
                description=param_data["description"],
                is_default=param_data["is_default"]
            )
            db.add(param)
            restored_params.append(param)
        
        db.commit()
        
        # 创建恢复记录
        restore_version = ModelParameterVersion(
            model_id=version.model_id,
            version_name=f"恢复至 {version.version_name}",
            version_description=f"从版本 {version.version_name} 恢复参数配置",
            parameters_snapshot=json.dumps([
                {
                    "id": p.id,
                    "parameter_name": p.parameter_name,
                    "parameter_value": p.parameter_value,
                    "parameter_type": p.parameter_type,
                    "parameter_source": p.parameter_source,
                    "is_override": p.is_override,
                    "parameter_level": p.parameter_level,
                    "inherit_from": p.inherit_from,
                    "parent_parameter_id": p.parent_parameter_id,
                    "is_inherited": p.is_inherited,
                    "description": p.description,
                    "is_default": p.is_default
                }
                for p in current_params
            ], ensure_ascii=False),
            created_by="system",
            is_active=True
        )
        db.add(restore_version)
        db.commit()
        
        return {
            "version_id": version_id,
            "version_name": version.version_name,
            "model_id": version.model_id,
            "restored_parameters_count": len(restored_params),
            "restore_version_id": restore_version.id
        }
    
    @staticmethod
    def compare_versions(
        db: Session, 
        version1_id: int, 
        version2_id: int
    ) -> Dict[str, Any]:
        """
        比较两个版本的差异
        
        Args:
            db: 数据库会话
            version1_id: 版本1 ID
            version2_id: 版本2 ID
            
        Returns:
            版本差异信息
        """
        version1 = db.query(ModelParameterVersion).filter(ModelParameterVersion.id == version1_id).first()
        version2 = db.query(ModelParameterVersion).filter(ModelParameterVersion.id == version2_id).first()
        
        if not version1:
            raise ValueError(f"版本1 ID {version1_id} 不存在")
        if not version2:
            raise ValueError(f"版本2 ID {version2_id} 不存在")
        
        if version1.model_id != version2.model_id:
            raise ValueError("无法比较不同模型的版本")
        
        # 解析参数快照
        params1 = {p["parameter_name"]: p for p in json.loads(version1.parameters_snapshot)}
        params2 = {p["parameter_name"]: p for p in json.loads(version2.parameters_snapshot)}
        
        # 找出差异
        added = []
        removed = []
        modified = []
        
        # 检查新增的参数
        for param_name in params2.keys() - params1.keys():
            added.append({
                "parameter_name": param_name,
                "version2_value": params2[param_name]["parameter_value"]
            })
        
        # 检查删除的参数
        for param_name in params1.keys() - params2.keys():
            removed.append({
                "parameter_name": param_name,
                "version1_value": params1[param_name]["parameter_value"]
            })
        
        # 检查修改的参数
        for param_name in params1.keys() & params2.keys():
            if params1[param_name]["parameter_value"] != params2[param_name]["parameter_value"]:
                modified.append({
                    "parameter_name": param_name,
                    "version1_value": params1[param_name]["parameter_value"],
                    "version2_value": params2[param_name]["parameter_value"]
                })
        
        return {
            "version1": {
                "id": version1.id,
                "name": version1.version_name,
                "created_at": version1.created_at
            },
            "version2": {
                "id": version2.id,
                "name": version2.version_name,
                "created_at": version2.created_at
            },
            "differences": {
                "added": added,
                "removed": removed,
                "modified": modified
            },
            "summary": {
                "total_added": len(added),
                "total_removed": len(removed),
                "total_modified": len(modified)
            }
        }
    
    @staticmethod
    def get_change_log(
        db: Session, 
        model_id: int, 
        limit: int = 50
    ) -> List[ParameterChangeLog]:
        """
        获取参数变更日志
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            limit: 返回记录数限制
            
        Returns:
            变更日志列表
        """
        versions = db.query(ModelParameterVersion).filter(
            ModelParameterVersion.model_id == model_id
        ).order_by(desc(ModelParameterVersion.created_at)).limit(limit).all()
        
        change_log = []
        
        for i in range(len(versions) - 1):
            current_version = versions[i]
            previous_version = versions[i + 1] if i + 1 < len(versions) else None
            
            if previous_version:
                # 比较两个连续版本的差异
                comparison = VersionControlService.compare_versions(
                    db, previous_version.id, current_version.id
                )
                
                change_log.append(ParameterChangeLog(
                    version_id=current_version.id,
                    version_name=current_version.version_name,
                    created_at=current_version.created_at,
                    created_by=current_version.created_by,
                    changes_summary=comparison["summary"],
                    changes_details=comparison["differences"]
                ))
        
        return change_log
    
    @staticmethod
    def auto_create_version(
        db: Session, 
        model_id: int, 
        change_description: str,
        created_by: Optional[str] = None
    ) -> Optional[ModelParameterVersion]:
        """
        自动创建版本（在参数变更时调用）
        
        Args:
            db: 数据库会话
            model_id: 模型ID
            change_description: 变更描述
            created_by: 创建人
            
        Returns:
            创建的版本对象（如果创建了版本）
        """
        # 检查是否需要自动创建版本
        # 这里可以根据配置决定是否自动创建版本
        auto_version_enabled = True  # 可以从配置中读取
        
        if not auto_version_enabled:
            return None
        
        # 获取最近的版本
        latest_version = db.query(ModelParameterVersion).filter(
            ModelParameterVersion.model_id == model_id
        ).order_by(desc(ModelParameterVersion.created_at)).first()
        
        # 如果距离上次版本创建时间较短，可以跳过自动创建
        if latest_version:
            time_diff = datetime.now() - latest_version.created_at
            if time_diff.total_seconds() < 300:  # 5分钟内不重复创建版本
                return None
        
        # 创建新版本
        version_data = ParameterVersionCreate(
            version_name=f"自动版本_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            version_description=change_description
        )
        
        return VersionControlService.create_version(db, model_id, version_data, created_by)
    
    @staticmethod
    def export_version(db: Session, version_id: int) -> Dict[str, Any]:
        """
        导出版本数据
        
        Args:
            db: 数据库会话
            version_id: 版本ID
            
        Returns:
            导出的版本数据
        """
        version = db.query(ModelParameterVersion).filter(ModelParameterVersion.id == version_id).first()
        if not version:
            raise ValueError(f"版本ID {version_id} 不存在")
        
        model = db.query(ModelDB).filter(ModelDB.id == version.model_id).first()
        
        return {
            "version_id": version.id,
            "version_name": version.version_name,
            "version_description": version.version_description,
            "model_id": version.model_id,
            "model_name": model.model_name if model else "未知模型",
            "created_by": version.created_by,
            "created_at": version.created_at.isoformat(),
            "parameters": json.loads(version.parameters_snapshot),
            "exported_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def import_version(db: Session, version_data: Dict[str, Any]) -> ModelParameterVersion:
        """
        导入版本数据
        
        Args:
            db: 数据库会话
            version_data: 版本数据
            
        Returns:
            导入的版本对象
        """
        # 验证必需字段
        required_fields = ["version_name", "model_id", "parameters"]
        for field in required_fields:
            if field not in version_data:
                raise ValueError(f"导入数据缺少必需字段: {field}")
        
        # 验证模型存在
        model = db.query(ModelDB).filter(ModelDB.id == version_data["model_id"]).first()
        if not model:
            raise ValueError(f"模型ID {version_data['model_id']} 不存在")
        
        # 创建版本记录
        version = ModelParameterVersion(
            model_id=version_data["model_id"],
            version_name=version_data["version_name"],
            version_description=version_data.get("version_description"),
            parameters_snapshot=json.dumps(version_data["parameters"], ensure_ascii=False),
            created_by=version_data.get("created_by", "import"),
            is_active=True
        )
        
        db.add(version)
        db.commit()
        db.refresh(version)
        
        return version