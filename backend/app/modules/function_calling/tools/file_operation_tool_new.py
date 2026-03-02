"""
文件操作工具

复用服务：FileStorageService
提供文件的读写、列表、信息获取等功能
"""

from typing import Dict, Any, List, Optional
import time
import logging

from app.modules.function_calling.base_tool import ServiceTool
from app.modules.function_calling.tool_schemas import (
    ToolParameter,
    ToolMetadata,
    ToolExecutionResult,
    ToolCategory
)
from app.services.file_storage_service import file_storage_service
from app.services.storage_path_manager import FileCategory

logger = logging.getLogger(__name__)


class FileOperationTool(ServiceTool):
    """
    文件操作工具
    
    复用服务：FileStorageService
    提供文件的读写、列表、信息获取等功能
    """
    
    def __init__(self):
        """初始化文件操作工具"""
        self._file_service = None
        super().__init__()
    
    def _get_service(self):
        """
        获取文件存储服务实例
        
        Returns:
            FileStorageService: 文件存储服务实例
        """
        return file_storage_service
    
    def _get_metadata(self) -> ToolMetadata:
        """
        获取工具元数据
        
        Returns:
            ToolMetadata: 工具元数据
        """
        return ToolMetadata(
            name="file_operation",
            display_name="文件操作",
            description="提供文件读写、列表、信息获取等操作功能",
            category=ToolCategory.FILE.value,
            version="1.0.0",
            author="Py Copilot Team",
            icon="📁",
            tags=["文件", "读写", "存储"],
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
                name="action",
                type="string",
                description="操作类型",
                required=True,
                enum=["read", "write", "list", "info", "delete"]
            ),
            ToolParameter(
                name="file_path",
                type="string",
                description="文件路径",
                required=False
            ),
            ToolParameter(
                name="content",
                type="string",
                description="文件内容（action=write时使用）",
                required=False
            ),
            ToolParameter(
                name="filename",
                type="string",
                description="文件名（action=write时使用）",
                required=False
            ),
            ToolParameter(
                name="user_id",
                type="integer",
                description="用户ID",
                required=True
            ),
            ToolParameter(
                name="category",
                type="string",
                description="文件分类",
                required=False,
                default="document",
                enum=["document", "image", "audio", "video", "temp_file"]
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="文件编码",
                required=False,
                default="utf-8"
            )
        ]
    
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """
        执行文件操作
        
        Args:
            **kwargs: 操作参数
                - action: 操作类型（必需）
                - user_id: 用户ID（必需）
                - 其他参数根据action不同而不同
        
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
            
            action = kwargs.get("action")
            user_id = kwargs.get("user_id")
            
            logger.info(f"执行文件操作: action={action}, user_id={user_id}")
            
            # 根据操作类型执行不同逻辑
            if action == "read":
                return await self._handle_read(kwargs, start_time)
            elif action == "write":
                return await self._handle_write(kwargs, start_time)
            elif action == "list":
                return self._handle_list(kwargs, start_time)
            elif action == "info":
                return self._handle_info(kwargs, start_time)
            elif action == "delete":
                return await self._handle_delete(kwargs, start_time)
            else:
                return ToolExecutionResult.error_result(
                    tool_name=tool_name,
                    error=f"不支持的操作类型: {action}",
                    error_code="INVALID_ACTION",
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"文件操作失败: {str(e)}")
            return ToolExecutionResult.error_result(
                tool_name=tool_name,
                error=f"操作失败: {str(e)}",
                error_code="OPERATION_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def _handle_read(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理读取操作"""
        file_path = kwargs.get("file_path")
        encoding = kwargs.get("encoding", "utf-8")
        
        if not file_path:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error="读取操作需要提供file_path参数",
                error_code="MISSING_PARAMETER",
                execution_time=time.time() - start_time
            )
        
        try:
            service = self.get_service()
            content = await service.read_text_file(file_path, encoding)
            
            return ToolExecutionResult.success_result(
                tool_name=self._metadata.name,
                result={
                    "content": content,
                    "file_path": file_path,
                    "encoding": encoding,
                    "length": len(content)
                },
                execution_time=time.time() - start_time
            )
            
        except FileNotFoundError:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"文件不存在: {file_path}",
                error_code="FILE_NOT_FOUND",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"读取失败: {str(e)}",
                error_code="READ_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def _handle_write(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理写入操作"""
        content = kwargs.get("content")
        filename = kwargs.get("filename")
        user_id = kwargs.get("user_id")
        category_str = kwargs.get("category", "document")
        encoding = kwargs.get("encoding", "utf-8")
        
        if not content or not filename:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error="写入操作需要提供content和filename参数",
                error_code="MISSING_PARAMETER",
                execution_time=time.time() - start_time
            )
        
        try:
            service = self.get_service()
            
            # 转换分类字符串为枚举
            category_map = {
                "document": FileCategory.CONVERSATION_ATTACHMENT,
                "image": FileCategory.CONVERSATION_ATTACHMENT,
                "audio": FileCategory.VOICE_MESSAGE,
                "video": FileCategory.CONVERSATION_ATTACHMENT,
                "temp_file": FileCategory.TEMP_FILE
            }
            category = category_map.get(category_str, FileCategory.CONVERSATION_ATTACHMENT)
            
            file_info = await service.write_text_file(
                content=content,
                filename=filename,
                user_id=user_id,
                category=category,
                encoding=encoding
            )
            
            return ToolExecutionResult.success_result(
                tool_name=self._metadata.name,
                result=file_info,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"写入失败: {str(e)}",
                error_code="WRITE_ERROR",
                execution_time=time.time() - start_time
            )
    
    def _handle_list(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理列表操作"""
        user_id = kwargs.get("user_id")
        category_str = kwargs.get("category")
        
        try:
            service = self.get_service()
            
            # 转换分类字符串为枚举
            category = None
            if category_str:
                category_map = {
                    "document": FileCategory.CONVERSATION_ATTACHMENT,
                    "image": FileCategory.CONVERSATION_ATTACHMENT,
                    "audio": FileCategory.VOICE_MESSAGE,
                    "video": FileCategory.CONVERSATION_ATTACHMENT,
                    "temp_file": FileCategory.TEMP_FILE
                }
                category = category_map.get(category_str)
            
            files = service.list_files(user_id=user_id, category=category)
            
            return ToolExecutionResult.success_result(
                tool_name=self._metadata.name,
                result={
                    "files": files,
                    "total_count": len(files),
                    "user_id": user_id,
                    "category": category_str
                },
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"列表获取失败: {str(e)}",
                error_code="LIST_ERROR",
                execution_time=time.time() - start_time
            )
    
    def _handle_info(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理信息获取操作"""
        file_path = kwargs.get("file_path")
        
        if not file_path:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error="信息获取操作需要提供file_path参数",
                error_code="MISSING_PARAMETER",
                execution_time=time.time() - start_time
            )
        
        try:
            service = self.get_service()
            info = service.get_file_info(file_path)
            
            return ToolExecutionResult.success_result(
                tool_name=self._metadata.name,
                result=info,
                execution_time=time.time() - start_time
            )
            
        except FileNotFoundError:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"文件不存在: {file_path}",
                error_code="FILE_NOT_FOUND",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"信息获取失败: {str(e)}",
                error_code="INFO_ERROR",
                execution_time=time.time() - start_time
            )
    
    async def _handle_delete(self, kwargs: Dict[str, Any], start_time: float) -> ToolExecutionResult:
        """处理删除操作"""
        file_path = kwargs.get("file_path")
        
        if not file_path:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error="删除操作需要提供file_path参数",
                error_code="MISSING_PARAMETER",
                execution_time=time.time() - start_time
            )
        
        try:
            service = self.get_service()
            success = await service.delete_file(file_path)
            
            if success:
                return ToolExecutionResult.success_result(
                    tool_name=self._metadata.name,
                    result={
                        "success": True,
                        "file_path": file_path,
                        "message": "文件删除成功"
                    },
                    execution_time=time.time() - start_time
                )
            else:
                return ToolExecutionResult.error_result(
                    tool_name=self._metadata.name,
                    error=f"文件不存在或删除失败: {file_path}",
                    error_code="DELETE_FAILED",
                    execution_time=time.time() - start_time
                )
            
        except Exception as e:
            return ToolExecutionResult.error_result(
                tool_name=self._metadata.name,
                error=f"删除失败: {str(e)}",
                error_code="DELETE_ERROR",
                execution_time=time.time() - start_time
            )
