"""智能体参数管理服务"""
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.agent_parameter import AgentParameter
from app.models.supplier_db import ModelDB, ModelParameter
from app.models.model_category import ModelCategory
from app.models.parameter_template import ParameterTemplate
from app.services.parameter_management.parameter_manager import ParameterManager


class AgentParameterManager:
    """智能体参数管理器，负责智能体参数的CRUD、校验和继承逻辑"""
    
    @staticmethod
    def create_parameter(
        db: Session,
        agent_id: int,
        parameter_name: str,
        parameter_value: Any,
        parameter_type: str = "string",
        description: str = None,
        parameter_group: str = None,
        source: str = "agent",
        inherited: bool = False,
        inherited_from: str = None
    ) -> AgentParameter:
        """
        创建智能体参数
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            parameter_name: 参数名称
            parameter_value: 参数值
            parameter_type: 参数类型
            description: 参数描述
            parameter_group: 参数分组
            source: 参数来源 (agent, model, system)
            inherited: 是否为继承参数
            inherited_from: 继承来源
            
        Returns:
            创建的智能体参数对象
            
        Raises:
            ValueError: 当参数值与类型不匹配时
        """
        if not AgentParameterManager._validate_parameter_value(parameter_value, parameter_type):
            raise ValueError(f"参数值 '{parameter_value}' 与类型 '{parameter_type}' 不匹配")
        
        existing_param = db.query(AgentParameter).filter(
            AgentParameter.agent_id == agent_id,
            AgentParameter.parameter_name == parameter_name
        ).first()
        
        if existing_param:
            existing_param.parameter_value = str(parameter_value)
            existing_param.parameter_type = parameter_type
            existing_param.description = description
            existing_param.parameter_group = parameter_group
            existing_param.source = source
            existing_param.inherited = inherited
            existing_param.inherited_from = inherited_from
            db.add(existing_param)
            db.commit()
            db.refresh(existing_param)
            return existing_param
        
        agent_param = AgentParameter(
            agent_id=agent_id,
            parameter_name=parameter_name,
            parameter_value=str(parameter_value),
            parameter_type=parameter_type,
            description=description,
            parameter_group=parameter_group,
            source=source,
            inherited=inherited,
            inherited_from=inherited_from
        )
        
        db.add(agent_param)
        db.commit()
        db.refresh(agent_param)
        return agent_param
    
    @staticmethod
    def create_parameters_bulk(
        db: Session,
        agent_id: int,
        parameters: Dict[str, Any],
        parameter_group: str = None
    ) -> List[AgentParameter]:
        """
        批量创建智能体参数
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            parameters: 参数字典 {参数名: {value, type}} 或 {参数名: 值}
            parameter_group: 默认参数分组
            
        Returns:
            创建的参数对象列表
        """
        created_params = []
        
        for param_name, param_data in parameters.items():
            if isinstance(param_data, dict):
                param_value = param_data.get("value")
                param_type = param_data.get("type", AgentParameterManager._infer_parameter_type(param_value))
            else:
                param_value = param_data
                param_type = AgentParameterManager._infer_parameter_type(param_value)
            
            param = AgentParameterManager.create_parameter(
                db=db,
                agent_id=agent_id,
                parameter_name=param_name,
                parameter_value=param_value,
                parameter_type=param_type,
                parameter_group=parameter_group
            )
            created_params.append(param)
        
        return created_params
    
    @staticmethod
    def get_parameter(db: Session, agent_id: int, parameter_name: str) -> Optional[AgentParameter]:
        """
        获取智能体的特定参数
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            parameter_name: 参数名称
            
        Returns:
            找到的参数对象或None
        """
        return db.query(AgentParameter).filter(
            AgentParameter.agent_id == agent_id,
            AgentParameter.parameter_name == parameter_name
        ).first()
    
    @staticmethod
    def get_parameters(db: Session, agent_id: int) -> List[AgentParameter]:
        """
        获取智能体的所有参数
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            
        Returns:
            参数对象列表
        """
        return db.query(AgentParameter).filter(
            AgentParameter.agent_id == agent_id
        ).all()
    
    @staticmethod
    def get_parameters_dict(db: Session, agent_id: int) -> Dict[str, Any]:
        """
        获取智能体参数字典
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            
        Returns:
            参数名字典
        """
        params = AgentParameterManager.get_parameters(db, agent_id)
        return {param.parameter_name: AgentParameterManager._convert_parameter_value(param.parameter_value, param.parameter_type) 
                for param in params}
    
    @staticmethod
    def update_parameter(
        db: Session,
        agent_id: int,
        parameter_name: str,
        parameter_value: Any = None,
        parameter_type: str = None,
        description: str = None,
        parameter_group: str = None
    ) -> Optional[AgentParameter]:
        """
        更新智能体参数
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            parameter_name: 参数名称
            parameter_value: 新参数值
            parameter_type: 新参数类型
            description: 新描述
            parameter_group: 新参数分组
            
        Returns:
            更新后的参数对象或None（当参数不存在时）
        """
        agent_param = AgentParameterManager.get_parameter(db, agent_id, parameter_name)
        if not agent_param:
            return None
        
        if parameter_value is not None:
            if agent_param.parameter_type:
                if not AgentParameterManager._validate_parameter_value(parameter_value, agent_param.parameter_type):
                    raise ValueError(f"参数值 '{parameter_value}' 与类型 '{agent_param.parameter_type}' 不匹配")
            agent_param.parameter_value = str(parameter_value)
        
        if parameter_type is not None:
            if parameter_value is not None:
                if not AgentParameterManager._validate_parameter_value(parameter_value, parameter_type):
                    raise ValueError(f"参数值 '{parameter_value}' 与类型 '{parameter_type}' 不匹配")
            agent_param.parameter_type = parameter_type
        
        if description is not None:
            agent_param.description = description
        
        if parameter_group is not None:
            agent_param.parameter_group = parameter_group
        
        db.add(agent_param)
        db.commit()
        db.refresh(agent_param)
        return agent_param
    
    @staticmethod
    def delete_parameter(db: Session, agent_id: int, parameter_name: str) -> bool:
        """
        删除智能体参数
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            parameter_name: 参数名称
            
        Returns:
            是否成功删除
        """
        agent_param = AgentParameterManager.get_parameter(db, agent_id, parameter_name)
        if not agent_param:
            return False
        
        db.delete(agent_param)
        db.commit()
        return True
    
    @staticmethod
    def delete_all_parameters(db: Session, agent_id: int) -> int:
        """
        删除智能体的所有参数
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            
        Returns:
            删除的参数数量
        """
        params = AgentParameterManager.get_parameters(db, agent_id)
        count = len(params)
        
        for param in params:
            db.delete(param)
        
        db.commit()
        return count
    
    @staticmethod
    def get_effective_parameters(db: Session, agent_id: int, include_inherited: bool = True) -> Dict[str, Any]:
        """获取智能体的有效参数（包含系统、模型、智能体三级参数继承）
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            include_inherited: 是否包含继承参数
            
        Returns:
            合并后的有效参数字典，优先级：智能体参数 > 模型参数 > 系统参数
        """
        from app.services.parameter_management.parameter_manager import ParameterManager
        from app.services.parameter_management.system_parameter_manager import SystemParameterManager
        
        result = {}
        
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return result
        
        # 1. 获取系统默认参数（最低优先级）
        if include_inherited:
            system_params = SystemParameterManager.get_system_parameters(db)
            for param in system_params:
                result[param["parameter_name"]] = param["parameter_value"]
        
        # 2. 获取模型参数（中等优先级）
        model_id = getattr(agent, 'model_id', None)
        if model_id and include_inherited:
            model_params = ParameterManager.get_model_parameters(db, model_id)
            for param in model_params:
                result[param["parameter_name"]] = param["parameter_value"]
        
        # 3. 获取智能体自定义参数（最高优先级）
        agent_params = AgentParameterManager.get_parameters_dict(db, agent_id)
        result.update(agent_params)
        
        return result
    
    @staticmethod
    def get_effective_parameters_with_source(db: Session, agent_id: int) -> List[Dict[str, Any]]:
        """
        获取智能体的有效参数（包含来源信息）
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            
        Returns:
            包含来源信息的参数列表
        """
        result = []
        seen_params = set()
        
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return []
        
        model_id = getattr(agent, 'model_id', None)
        model_params = []
        if model_id:
            model_params = ParameterManager.get_model_parameters(db, model_id)
        
        for param in model_params:
            if param["parameter_name"] not in seen_params:
                param_copy = param.copy()
                param_copy["source"] = "model"
                param_copy["is_effective"] = False
                result.append(param_copy)
                seen_params.add(param["parameter_name"])
        
        agent_params = db.query(AgentParameter).filter(
            AgentParameter.agent_id == agent_id
        ).all()
        
        for param in agent_params:
            if param.parameter_name in seen_params:
                for item in result:
                    if item["parameter_name"] == param.parameter_name:
                        item["parameter_value"] = param.parameter_value
                        item["is_effective"] = True
                        break
            else:
                result.append({
                    "id": param.id,
                    "parameter_name": param.parameter_name,
                    "parameter_value": param.parameter_value,
                    "parameter_type": param.parameter_type,
                    "description": param.description,
                    "source": "agent",
                    "is_effective": True,
                    "inherited": False
                })
                seen_params.add(param.parameter_name)
        
        return result
    
    @staticmethod
    def _validate_parameter_value(value: Any, parameter_type: str) -> bool:
        """
        验证参数值与类型是否匹配
        
        Args:
            value: 参数值
            parameter_type: 参数类型
            
        Returns:
            是否匹配
        """
        try:
            if parameter_type == "number":
                float(value)
            elif parameter_type == "integer":
                if isinstance(value, bool):
                    return False
                int(value)
            elif parameter_type == "boolean":
                return isinstance(value, bool) or str(value).lower() in ("true", "false", "1", "0")
            elif parameter_type == "string":
                str(value)
            elif parameter_type == "json":
                if isinstance(value, str):
                    json.loads(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def _convert_parameter_value(value: str, parameter_type: str) -> Any:
        """
        将参数值字符串转换为指定类型
        
        Args:
            value: 参数值字符串
            parameter_type: 参数类型
            
        Returns:
            转换后的值
        """
        if parameter_type == "number":
            return float(value)
        elif parameter_type == "integer":
            return int(value)
        elif parameter_type == "boolean":
            return str(value).lower() in ("true", "1")
        elif parameter_type == "json":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        else:
            return value
    
    @staticmethod
    def _infer_parameter_type(value: Any) -> str:
        """
        推断参数值的类型
        
        Args:
            value: 参数值
            
        Returns:
            参数类型字符串
        """
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, dict) or isinstance(value, list):
            return "json"
        else:
            return "string"
    
    @staticmethod
    def validate_parameters(db: Session, agent_id: int, parameters: Dict[str, Any] = None) -> List[str]:
        """
        验证参数的有效性
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            parameters: 要验证的参数（默认验证所有参数）
            
        Returns:
            错误列表
        """
        errors = []
        
        if parameters is None:
            params = AgentParameterManager.get_parameters(db, agent_id)
            for param in params:
                if not AgentParameterManager._validate_parameter_value(param.parameter_value, param.parameter_type):
                    errors.append(f"参数 '{param.parameter_name}' 的值 '{param.parameter_value}' 与类型 '{param.parameter_type}' 不匹配")
        else:
            for param_name, param_value in parameters.items():
                agent_param = AgentParameterManager.get_parameter(db, agent_id, param_name)
                if agent_param:
                    if not AgentParameterManager._validate_parameter_value(param_value, agent_param.parameter_type):
                        errors.append(f"参数 '{param_name}' 的值 '{param_value}' 与类型 '{agent_param.parameter_type}' 不匹配")
        
        return errors
