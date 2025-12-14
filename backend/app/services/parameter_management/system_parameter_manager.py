"""系统参数管理服务"""
import json
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.parameter_template import ParameterTemplate
from app.schemas.parameter_template import ParameterTemplateCreate, ParameterTemplateUpdate


class SystemParameterManager:
    """系统参数管理器，负责系统级参数的管理和操作"""
    
    @staticmethod
    def get_system_parameter_templates(db: Session, skip: int = 0, limit: int = 100) -> List[ParameterTemplate]:
        """
        获取系统级参数模板列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            系统级参数模板列表
        """
        return db.query(ParameterTemplate).filter(
            ParameterTemplate.level == "system"
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_active_system_parameter_template(db: Session) -> Optional[ParameterTemplate]:
        """
        获取当前激活的系统级参数模板
        
        Args:
            db: 数据库会话
            
        Returns:
            激活的系统级参数模板，或None
        """
        return db.query(ParameterTemplate).filter(
            ParameterTemplate.level == "system",
            ParameterTemplate.is_active == True
        ).first()
    
    @staticmethod
    def create_system_parameter_template(
        db: Session, 
        template_data: ParameterTemplateCreate
    ) -> ParameterTemplate:
        """
        创建系统级参数模板
        
        Args:
            db: 数据库会话
            template_data: 参数模板创建数据
            
        Returns:
            创建的系统级参数模板
            
        Raises:
            ValueError: 当template_data.level不是"system"时
        """
        if template_data.level != "system":
            raise ValueError("系统参数模板的level必须是'system'")
        
        # 验证参数的有效性
        SystemParameterManager.validate_parameters(template_data.parameters)
        
        # 创建新的系统参数模板
        db_template = ParameterTemplate(**template_data.model_dump())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        return db_template
    
    @staticmethod
    def update_system_parameter_template(
        db: Session, 
        template_id: int, 
        template_data: ParameterTemplateUpdate
    ) -> ParameterTemplate:
        """
        更新系统级参数模板
        
        Args:
            db: 数据库会话
            template_id: 参数模板ID
            template_data: 参数模板更新数据
            
        Returns:
            更新后的系统级参数模板
            
        Raises:
            ValueError: 当模板不是系统级模板时
        """
        # 获取模板
        template = db.query(ParameterTemplate).filter(
            ParameterTemplate.id == template_id,
            ParameterTemplate.level == "system"
        ).first()
        
        if not template:
            raise ValueError(f"系统参数模板ID {template_id} 不存在")
        
        # 更新模板字段
        update_data = template_data.model_dump(exclude_unset=True)
        
        # 如果更新了参数列表，需要验证参数的有效性
        if 'parameters' in update_data:
            SystemParameterManager.validate_parameters(update_data['parameters'])
        
        for field, value in update_data.items():
            setattr(template, field, value)
        
        db.commit()
        db.refresh(template)
        
        return template
    
    @staticmethod
    def _convert_parameter_value(value: str, type_name: str) -> Any:
        """
        将字符串类型的参数值转换为指定类型
        
        Args:
            value: 字符串类型的参数值
            type_name: 参数类型名称
            
        Returns:
            转换后的参数值
            
        Raises:
            ValueError: 当参数值无法转换为指定类型时
        """
        try:
            if type_name == "int":
                return int(value)
            elif type_name == "float":
                return float(value)
            elif type_name == "bool":
                return value.lower() in ["true", "1", "yes", "y"]
            elif type_name == "json":
                return json.loads(value)
            elif type_name == "array":
                return json.loads(value)
            elif type_name == "object":
                return json.loads(value)
            elif type_name == "enum":
                # 枚举类型直接返回字符串值，验证在验证规则中进行
                return value
            else:
                return value
        except (ValueError, json.JSONDecodeError):
            raise ValueError(f"参数值 '{value}' 无法转换为类型 '{type_name}'")
    
    @staticmethod
    def validate_parameter(param: Dict[str, Any], param_value: Any = None) -> bool:
        """
        验证单个参数是否符合定义的验证规则
        
        Args:
            param: 参数定义（包含类型、验证规则等）
            param_value: 要验证的参数值，如果为None则使用param['default_value']
            
        Returns:
            True如果验证通过，否则False
            
        Raises:
            ValueError: 当参数验证失败时
        """
        # 如果没有提供值，使用默认值
        if param_value is None:
            if 'default_value' not in param and param.get('required', False):
                raise ValueError(f"参数 '{param['name']}' 是必填的，但没有提供值")
            param_value = param.get('default_value')
            
        # 1. 必填验证
        if param.get('required', False) and param_value is None:
            raise ValueError(f"参数 '{param['name']}' 是必填的")
            
        # 如果值为None且不是必填，则不需要进一步验证
        if param_value is None:
            return True
            
        # 2. 类型验证
        param_type = param.get('type', 'string')
        try:
            converted_value = SystemParameterManager._convert_parameter_value(str(param_value), param_type)
        except ValueError as e:
            raise ValueError(f"参数 '{param['name']}' 类型验证失败: {str(e)}")
            
        # 获取验证规则
        validation_rules = param.get('validation_rules', {})
        
        # 3. 范围验证（针对数值类型）
        if param_type in ['int', 'float']:
            if 'min' in validation_rules and converted_value < validation_rules['min']:
                raise ValueError(f"参数 '{param['name']}' 的值 {converted_value} 小于最小值 {validation_rules['min']}")
                
            if 'max' in validation_rules and converted_value > validation_rules['max']:
                raise ValueError(f"参数 '{param['name']}' 的值 {converted_value} 大于最大值 {validation_rules['max']}")
        
        # 4. 格式验证（针对字符串类型）
        if param_type == 'string' and 'regex' in validation_rules:
            if not re.match(validation_rules['regex'], str(param_value)):
                raise ValueError(f"参数 '{param['name']}' 的值 {param_value} 不符合格式要求")
        
        # 5. 枚举验证
        if param_type == 'enum' and 'enum_values' in validation_rules:
            if param_value not in validation_rules['enum_values']:
                raise ValueError(f"参数 '{param['name']}' 的值 {param_value} 不在枚举列表 {validation_rules['enum_values']} 中")
        
        # 6. 依赖验证
        if 'depends_on' in validation_rules:
            depends_on = validation_rules['depends_on']
            # 注意：依赖验证需要上下文信息，这里简化处理
            # 实际实现可能需要传递所有参数或参数上下文
        
        return True
    
    @staticmethod
    def validate_parameters(params: List[Dict[str, Any]]) -> bool:
        """
        验证参数列表是否符合定义的验证规则
        
        Args:
            params: 参数列表
            
        Returns:
            True如果所有参数验证通过，否则False
            
        Raises:
            ValueError: 当任何参数验证失败时
        """
        for param in params:
            SystemParameterManager.validate_parameter(param)
        return True
    
    @staticmethod
    def activate_system_parameter_template(db: Session, template_id: int) -> ParameterTemplate:
        """
        激活系统级参数模板，同时将其他系统模板设置为非激活状态
        
        Args:
            db: 数据库会话
            template_id: 参数模板ID
            
        Returns:
            激活的系统级参数模板
            
        Raises:
            ValueError: 当模板不是系统级模板时
        """
        # 获取模板
        template = db.query(ParameterTemplate).filter(
            ParameterTemplate.id == template_id,
            ParameterTemplate.level == "system"
        ).first()
        
        if not template:
            raise ValueError(f"系统参数模板ID {template_id} 不存在")
        
        # 将所有系统模板设置为非激活状态
        db.query(ParameterTemplate).filter(
            ParameterTemplate.level == "system"
        ).update({"is_active": False})
        
        # 激活指定的模板
        template.is_active = True
        
        db.commit()
        db.refresh(template)
        
        return template
    
    @staticmethod
    def get_system_parameters(db: Session) -> List[Dict[str, Any]]:
        """
        获取当前激活的系统参数配置
        
        Args:
            db: 数据库会话
            
        Returns:
            系统参数配置列表
        """
        template = SystemParameterManager.get_active_system_parameter_template(db)
        if not template:
            return []
        
        return template.parameters
    
    @staticmethod
    def update_system_parameter(
        db: Session, 
        param_name: str, 
        param_value: Any, 
        param_type: str = "string",
        description: str = ""
    ) -> ParameterTemplate:
        """
        更新单个系统参数
        
        Args:
            db: 数据库会话
            param_name: 参数名称
            param_value: 参数值
            param_type: 参数类型
            description: 参数描述
            
        Returns:
            更新后的系统参数模板
        """
        template = SystemParameterManager.get_active_system_parameter_template(db)
        if not template:
            raise ValueError("没有找到激活的系统参数模板")
        
        # 更新参数
        updated = False
        for param in template.parameters:
            if param["name"] == param_name:
                param["default_value"] = param_value
                param["type"] = param_type
                param["description"] = description
                updated = True
                break
        
        # 如果参数不存在，添加新参数
        if not updated:
            new_param = {
                "name": param_name,
                "type": param_type,
                "default_value": param_value,
                "description": description,
                "required": False,
                "is_standard": True
            }
            template.parameters.append(new_param)
        
        # 验证参数
        SystemParameterManager.validate_parameter(new_param if not updated else param, param_value)
        
        db.commit()
        db.refresh(template)
        
        return template
    
    @staticmethod
    def delete_system_parameter(db: Session, param_name: str) -> ParameterTemplate:
        """
        删除单个系统参数
        
        Args:
            db: 数据库会话
            param_name: 参数名称
            
        Returns:
            更新后的系统参数模板
        """
        template = SystemParameterManager.get_active_system_parameter_template(db)
        if not template:
            raise ValueError("没有找到激活的系统参数模板")
        
        # 删除参数
        template.parameters = [param for param in template.parameters if param["name"] != param_name]
        
        db.commit()
        db.refresh(template)
        
        return template
    
    @staticmethod
    def batch_update_system_parameters(
        db: Session, 
        parameters: Dict[str, Any]
    ) -> ParameterTemplate:
        """
        批量更新系统参数
        
        Args:
            db: 数据库会话
            parameters: 参数字典，键为参数名称，值为包含value、type、description等的字典
            
        Returns:
            更新后的系统参数模板
        """
        template = SystemParameterManager.get_active_system_parameter_template(db)
        if not template:
            raise ValueError("没有找到激活的系统参数模板")
        
        # 将参数列表转换为字典，方便查找
        param_dict = {param["name"]: param for param in template.parameters}
        
        # 更新或添加参数
        for param_name, param_data in parameters.items():
            # 确保param_data是字典格式
            if not isinstance(param_data, dict):
                param_data = {"value": param_data, "type": "string", "description": ""}
            
            param_value = param_data.get("value")
            param_type = param_data.get("type", "string")
            description = param_data.get("description", "")
            
            if param_name in param_dict:
                # 更新现有参数
                param = param_dict[param_name]
                param["default_value"] = param_value
                param["type"] = param_type
                param["description"] = description
            else:
                # 添加新参数
                new_param = {
                    "name": param_name,
                    "type": param_type,
                    "default_value": param_value,
                    "description": description,
                    "required": False,
                    "is_standard": True
                }
                template.parameters.append(new_param)
                param_dict[param_name] = new_param
            
            # 验证参数
            SystemParameterManager.validate_parameter(param_dict[param_name], param_value)
        
        db.commit()
        db.refresh(template)
        
        return template
