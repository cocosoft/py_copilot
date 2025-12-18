"""工作流异常定义"""


class WorkflowException(Exception):
    """工作流异常基类"""
    pass


class TransientError(WorkflowException):
    """临时性错误，可以重试"""
    pass


class PermanentError(WorkflowException):
    """永久性错误，不应重试"""
    pass


class NodeExecutionError(WorkflowException):
    """节点执行错误"""
    def __init__(self, node_id: str, message: str, is_transient: bool = True):
        self.node_id = node_id
        self.message = message
        self.is_transient = is_transient
        super().__init__(f"节点 {node_id} 执行错误: {message}")


class WorkflowValidationError(WorkflowException):
    """工作流验证错误"""
    def __init__(self, message: str):
        super().__init__(f"工作流验证错误: {message}")


class WorkflowExecutionError(WorkflowException):
    """工作流执行错误"""
    def __init__(self, workflow_id: str, message: str):
        self.workflow_id = workflow_id
        super().__init__(f"工作流 {workflow_id} 执行错误: {message}")
