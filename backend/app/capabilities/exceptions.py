"""
能力中心异常定义

本模块定义了能力中心的所有自定义异常
"""


class CapabilityException(Exception):
    """
    能力中心基础异常
    
    所有能力相关异常的基类
    """
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or "CAPABILITY_ERROR"
        self.details = details or {}


class CapabilityNotFoundException(CapabilityException):
    """
    能力未找到异常
    
    当请求的能力不存在时抛出
    """
    
    def __init__(self, capability_name: str, message: str = None):
        msg = message or f"能力 '{capability_name}' 不存在"
        super().__init__(msg, code="CAPABILITY_NOT_FOUND", details={"capability_name": capability_name})
        self.capability_name = capability_name


class CapabilityExecutionException(CapabilityException):
    """
    能力执行异常
    
    当能力执行失败时抛出
    """
    
    def __init__(self, capability_name: str, error: str, message: str = None):
        msg = message or f"能力 '{capability_name}' 执行失败: {error}"
        super().__init__(msg, code="CAPABILITY_EXECUTION_ERROR", details={
            "capability_name": capability_name,
            "error": error
        })
        self.capability_name = capability_name
        self.error = error


class ValidationException(CapabilityException):
    """
    验证异常
    
    当输入数据验证失败时抛出
    """
    
    def __init__(self, errors: list, message: str = None):
        msg = message or f"输入验证失败: {', '.join(errors)}"
        super().__init__(msg, code="VALIDATION_ERROR", details={"errors": errors})
        self.errors = errors


class OrchestrationException(CapabilityException):
    """
    编排异常
    
    当任务编排失败时抛出
    """
    
    def __init__(self, message: str, stage: str = None, details: dict = None):
        super().__init__(message, code="ORCHESTRATION_ERROR", details=details)
        self.stage = stage


class IntentRecognitionException(OrchestrationException):
    """
    意图识别异常
    
    当意图识别失败时抛出
    """
    
    def __init__(self, message: str, input_text: str = None):
        super().__init__(message, stage="intent_recognition", details={"input_text": input_text})
        self.input_text = input_text


class TaskPlanningException(OrchestrationException):
    """
    任务规划异常
    
    当任务规划失败时抛出
    """
    
    def __init__(self, message: str, intent: dict = None):
        super().__init__(message, stage="task_planning", details={"intent": intent})
        self.intent = intent


class ExecutionException(OrchestrationException):
    """
    执行异常
    
    当任务执行失败时抛出
    """
    
    def __init__(self, message: str, step_id: str = None, details: dict = None):
        super().__init__(message, stage="execution", details=details)
        self.step_id = step_id


class TimeoutException(ExecutionException):
    """
    超时异常
    
    当执行超时时抛出
    """
    
    def __init__(self, capability_name: str, timeout_seconds: int):
        msg = f"能力 '{capability_name}' 执行超时（{timeout_seconds}秒）"
        super().__init__(msg, details={
            "capability_name": capability_name,
            "timeout_seconds": timeout_seconds
        })
        self.capability_name = capability_name
        self.timeout_seconds = timeout_seconds


class RetryExhaustedException(ExecutionException):
    """
    重试耗尽异常
    
    当重试次数耗尽仍失败时抛出
    """
    
    def __init__(self, capability_name: str, max_retries: int, last_error: str):
        msg = f"能力 '{capability_name}' 重试{max_retries}次后仍失败: {last_error}"
        super().__init__(msg, details={
            "capability_name": capability_name,
            "max_retries": max_retries,
            "last_error": last_error
        })
        self.capability_name = capability_name
        self.max_retries = max_retries
        self.last_error = last_error


class CircuitBreakerOpenException(ExecutionException):
    """
    熔断器打开异常
    
    当熔断器处于打开状态时抛出
    """
    
    def __init__(self, capability_name: str):
        msg = f"能力 '{capability_name}' 的熔断器已打开，服务暂时不可用"
        super().__init__(msg, details={"capability_name": capability_name})
        self.capability_name = capability_name


class DependencyException(OrchestrationException):
    """
    依赖异常
    
    当依赖的能力执行失败时抛出
    """
    
    def __init__(self, capability_name: str, dependency_name: str, error: str):
        msg = f"能力 '{capability_name}' 的依赖 '{dependency_name}' 执行失败: {error}"
        super().__init__(msg, stage="dependency_resolution", details={
            "capability_name": capability_name,
            "dependency_name": dependency_name,
            "error": error
        })
        self.capability_name = capability_name
        self.dependency_name = dependency_name


class ConfigurationException(CapabilityException):
    """
    配置异常
    
    当配置错误时抛出
    """
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, code="CONFIGURATION_ERROR", details={"config_key": config_key})
        self.config_key = config_key


class InitializationException(CapabilityException):
    """
    初始化异常
    
    当能力中心初始化失败时抛出
    """
    
    def __init__(self, message: str, component: str = None):
        super().__init__(message, code="INITIALIZATION_ERROR", details={"component": component})
        self.component = component
