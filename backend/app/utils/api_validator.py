"""API验证工具类"""
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status


class APIValidator:
    """API参数验证和错误处理工具类"""
    
    # 支持的维度列表
    VALID_DIMENSIONS = ['tasks', 'languages', 'licenses', 'technologies']
    
    # 支持的关联类型
    VALID_ASSOCIATION_TYPES = ['primary', 'secondary', 'custom']
    
    # 错误码映射
    ERROR_CODES = {
        'invalid_dimension': 'INVALID_DIMENSION',
        'invalid_association_type': 'INVALID_ASSOCIATION_TYPE',
        'model_not_found': 'MODEL_NOT_FOUND',
        'category_not_found': 'CATEGORY_NOT_FOUND',
        'association_exists': 'ASSOCIATION_EXISTS',
        'association_not_found': 'ASSOCIATION_NOT_FOUND',
        'validation_error': 'VALIDATION_ERROR'
    }
    
    @classmethod
    def validate_dimension(cls, dimension: str) -> None:
        """验证维度标识"""
        if dimension not in cls.VALID_DIMENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=cls._build_error_response(
                    'invalid_dimension',
                    f"无效的维度标识: {dimension}",
                    {"valid_dimensions": cls.VALID_DIMENSIONS}
                )
            )
    
    @classmethod
    def validate_association_type(cls, association_type: str) -> None:
        """验证关联类型"""
        if association_type not in cls.VALID_ASSOCIATION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=cls._build_error_response(
                    'invalid_association_type',
                    f"无效的关联类型: {association_type}",
                    {"valid_association_types": cls.VALID_ASSOCIATION_TYPES}
                )
            )
    
    @classmethod
    def validate_id_parameter(cls, param_name: str, param_value: int) -> None:
        """验证ID参数"""
        if param_value <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=cls._build_error_response(
                    'validation_error',
                    f"无效的{param_name}: {param_value}",
                    {"parameter": param_name, "value": param_value}
                )
            )
    
    @classmethod
    def validate_weight(cls, weight: int) -> None:
        """验证权重参数"""
        if weight < 0 or weight > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=cls._build_error_response(
                    'validation_error',
                    f"权重必须在0-100之间: {weight}",
                    {"parameter": "weight", "value": weight, "range": "0-100"}
                )
            )
    
    @classmethod
    def handle_not_found_error(cls, error_type: str, error_message: str, details: Dict[str, Any]) -> None:
        """处理资源未找到错误"""
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=cls._build_error_response(error_type, error_message, details)
        )
    
    @classmethod
    def handle_conflict_error(cls, error_type: str, error_message: str, details: Dict[str, Any]) -> None:
        """处理资源冲突错误"""
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=cls._build_error_response(error_type, error_message, details)
        )
    
    @classmethod
    def handle_validation_error(cls, error_type: str, error_message: str, details: Dict[str, Any]) -> None:
        """处理验证错误"""
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=cls._build_error_response(error_type, error_message, details)
        )
    
    @classmethod
    def handle_internal_error(cls, error_type: str, error_message: str, details: Dict[str, Any]) -> None:
        """处理内部服务器错误"""
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=cls._build_error_response(error_type, error_message, details)
        )
    
    @classmethod
    def _build_error_response(cls, error_type: str, message: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """构建标准错误响应"""
        return {
            "error": cls.ERROR_CODES.get(error_type, 'UNKNOWN_ERROR'),
            "message": message,
            "details": details
        }
    
    @classmethod
    def build_success_response(cls, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """构建标准成功响应"""
        response = {
            "success": True,
            "message": message
        }
        
        if data:
            response["data"] = data
            
        return response
    
    @classmethod
    def validate_dimension_constraints(cls, model_id: int, dimension: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """验证维度约束条件"""
        cls.validate_dimension(dimension)
        cls.validate_id_parameter("model_id", model_id)
        
        # 这里可以添加更复杂的约束验证逻辑
        validation_result = {
            "model_id": model_id,
            "dimension": dimension,
            "constraints_valid": True,
            "violations": []
        }
        
        # 示例约束验证
        if dimension == 'tasks' and constraints.get('max_tokens', 0) > 10000:
            validation_result["constraints_valid"] = False
            validation_result["violations"].append("任务类模型的最大token数不能超过10000")
        
        if dimension == 'languages' and not constraints.get('language_support'):
            validation_result["constraints_valid"] = False
            validation_result["violations"].append("语言类模型必须指定支持的语言")
            
        return validation_result