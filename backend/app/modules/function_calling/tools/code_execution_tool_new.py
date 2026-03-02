"""
代码执行工具

提供安全的代码执行环境，支持多种编程语言
"""

from typing import Dict, Any, List
import time
import logging
import subprocess
import tempfile
import os

from app.modules.function_calling.base_tool import BaseTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)

logger = logging.getLogger(__name__)


class CodeExecutionTool(BaseTool):
    """
    代码执行工具
    
    提供安全的代码执行环境，支持Python、JavaScript等语言
    """
    
    # 允许的语言和对应的执行命令
    SUPPORTED_LANGUAGES = {
        "python": {
            "extension": ".py",
            "command": ["python"],
            "timeout": 30
        },
        "javascript": {
            "extension": ".js",
            "command": ["node"],
            "timeout": 30
        },
        "bash": {
            "extension": ".sh",
            "command": ["bash"],
            "timeout": 10
        }
    }
    
    # 危险命令黑名单
    DANGEROUS_PATTERNS = [
        "rm -rf /",
        "rm -rf /*",
        ":(){:|:&};:",  # Fork bomb
        "eval(",
        "exec(",
        "__import__('os').system",
        "subprocess.call",
        "os.system",
        "os.popen",
        "import os",
        "import subprocess"
    ]
    
    def __init__(self):
        """初始化代码执行工具"""
        super().__init__()
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="code_execution",
            display_name="代码执行",
            description="在安全环境中执行代码，支持Python、JavaScript等语言",
            category=ToolCategory.CODE.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="💻",
            tags=["代码", "执行", "编程"],
            is_active=True
        )
    
    def _get_parameters(self) -> List[ToolParameter]:
        """
        获取工具参数定义
        
        Returns:
            List[ToolParameter]: 参数定义列表
        """
        return [
            ToolParameter(
                name="code",
                type="string",
                description="要执行的代码",
                required=True
            ),
            ToolParameter(
                name="language",
                type="string",
                description="编程语言",
                required=True,
                enum=["python", "javascript", "bash"]
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="执行超时时间（秒）",
                required=False,
                default=30
            ),
            ToolParameter(
                name="input_data",
                type="string",
                description="标准输入数据",
                required=False
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行代码
        
        Args:
            **kwargs: 执行参数
                - code: 代码内容（必需）
                - language: 编程语言（必需）
                - timeout: 超时时间（可选）
                - input_data: 输入数据（可选）
        
        Returns:
            ToolExecutionResult: 执行结果
        """
        start_time = time.time()
        tool_name = self._metadata.name
        
        try:
            # 验证参数
            validation_result = self.validate_parameters(**kwargs)
            if not validation_result.is_valid:
                errors = [e.message for e in validation_result.errors]
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"参数验证失败: {'; '.join(errors)}",
                    error_code="VALIDATION_ERROR",
                    execution_time=time.time() - start_time
                )
            
            code = kwargs.get("code")
            language = kwargs.get("language")
            timeout = kwargs.get("timeout", 30)
            input_data = kwargs.get("input_data", "")
            
            logger.info(f"执行代码: language={language}, code_length={len(code)}")
            
            # 安全检查
            security_check = self._security_check(code, language)
            if not security_check["safe"]:
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"安全检查失败: {security_check['reason']}",
                    error_code="SECURITY_ERROR",
                    execution_time=time.time() - start_time
                )
            
            # 执行代码
            result = self._execute_code(code, language, timeout, input_data)
            
            return ToolExecutionResult.success_result(
                tool_name=tool_name,
                result=result,
                execution_time=time.time() - start_time,
                metadata={
                    "language": language,
                    "timeout": timeout,
                    "code_length": len(code)
                }
            )
            
        except Exception as e:
            logger.error(f"代码执行失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"执行失败: {str(e)}",
                error_code="EXECUTION_ERROR",
                execution_time=time.time() - start_time
            )
    
    def _security_check(self, code: str, language: str) -> Dict[str, Any]:
        """
        安全检查
        
        Args:
            code: 代码内容
            language: 编程语言
            
        Returns:
            Dict[str, Any]: 检查结果
        """
        # 检查危险模式
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in code.lower():
                return {
                    "safe": False,
                    "reason": f"检测到危险代码模式: {pattern}"
                }
        
        # 检查文件系统操作
        dangerous_file_ops = [
            "open('/",
            'open("/"',
            "with open('/",
            'with open("/"',
        ]
        
        for op in dangerous_file_ops:
            if op in code:
                return {
                    "safe": False,
                    "reason": "检测到危险的文件系统操作"
                }
        
        return {"safe": True}
    
    def _execute_code(self, code: str, language: str, timeout: int, input_data: str) -> Dict[str, Any]:
        """
        执行代码
        
        Args:
            code: 代码内容
            language: 编程语言
            timeout: 超时时间
            input_data: 输入数据
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"不支持的语言: {language}")
        
        lang_config = self.SUPPORTED_LANGUAGES[language]
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=lang_config["extension"],
            delete=False
        ) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            # 执行代码
            command = lang_config["command"] + [temp_file_path]
            
            process = subprocess.run(
                command,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=min(timeout, lang_config["timeout"])
            )
            
            return {
                "success": process.returncode == 0,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "return_code": process.returncode,
                "language": language,
                "execution_time": process.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时（超过{timeout}秒）",
                "return_code": -1,
                "language": language,
                "execution_time": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "language": language,
                "execution_time": 0
            }
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except:
                pass
