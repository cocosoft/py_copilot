"""系统命令执行服务"""
import subprocess
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CommandExecutionService:
    """系统命令执行服务"""
    
    def __init__(self):
        """初始化系统命令执行服务"""
        pass
    
    async def execute_command(
        self,
        command: str,
        working_directory: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        执行系统命令
        
        Args:
            command: 要执行的命令
            working_directory: 工作目录（可选）
            timeout: 超时时间（秒），默认300秒
            
        Returns:
            执行结果字典，包含：
            - success: 是否成功
            - stdout: 标准输出
            - stderr: 标准错误
            - return_code: 返回码
            - execution_time_ms: 执行时间（毫秒）
        """
        start_time = datetime.now()
        
        try:
            # 准备执行环境
            env = os.environ.copy()
            
            # 设置工作目录
            cwd = working_directory if working_directory else None
            
            # 执行命令
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                env=env
            )
            
            # 等待命令完成，带超时
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return_code = -1
                stderr = f"命令执行超时（{timeout}秒）\n{stderr}"
            
            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            execution_time_ms = int(execution_time * 1000)
            
            # 判断是否成功
            success = return_code == 0
            
            # 记录日志
            if success:
                logger.info(f"命令执行成功: {command}")
            else:
                logger.warning(f"命令执行失败: {command}, 返回码: {return_code}")
            
            return {
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": return_code,
                "execution_time_ms": execution_time_ms
            }
            
        except Exception as e:
            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            execution_time_ms = int(execution_time * 1000)
            
            logger.error(f"命令执行异常: {command}, 错误: {e}")
            
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "execution_time_ms": execution_time_ms
            }
    
    async def execute_commands(
        self,
        commands: list,
        working_directory: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        执行多个系统命令
        
        Args:
            commands: 要执行的命令列表
            working_directory: 工作目录（可选）
            timeout: 超时时间（秒），默认300秒
            
        Returns:
            执行结果字典，包含：
            - success: 是否全部成功
            - results: 每个命令的执行结果列表
            - total_execution_time_ms: 总执行时间（毫秒）
        """
        start_time = datetime.now()
        results = []
        all_success = True
        
        for command in commands:
            result = await self.execute_command(
                command=command,
                working_directory=working_directory,
                timeout=timeout
            )
            results.append(result)
            
            if not result["success"]:
                all_success = False
                # 如果某个命令失败，可以选择停止执行后续命令
                # break
        
        # 计算总执行时间
        total_execution_time = (datetime.now() - start_time).total_seconds()
        total_execution_time_ms = int(total_execution_time * 1000)
        
        return {
            "success": all_success,
            "results": results,
            "total_execution_time_ms": total_execution_time_ms
        }
    
    def validate_command(self, command: str) -> bool:
        """
        验证命令是否安全
        
        Args:
            command: 要验证的命令
            
        Returns:
            是否安全
        """
        # 危险命令列表
        dangerous_commands = [
            "del", "rm", "rmdir", "format",
            "shutdown", "reboot",
            "sudo", "su",
            "chmod", "chown"
        ]
        
        # 检查命令中是否包含危险命令
        command_lower = command.lower()
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                logger.warning(f"检测到危险命令: {command}")
                return False
        
        return True
    
    def parse_command_output(self, output: str) -> Dict[str, Any]:
        """
        解析命令输出
        
        Args:
            output: 命令输出
            
        Returns:
            解析后的数据
        """
        # 这里可以根据不同的命令类型进行不同的解析
        # 例如，如果是dir命令，可以解析文件列表
        # 如果是git命令，可以解析提交信息等
        
        return {
            "raw_output": output,
            "lines": output.split('\n'),
            "line_count": len(output.split('\n'))
        }
