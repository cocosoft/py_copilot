"""
日志查询API模块

提供日志数据的查询、过滤、统计和导出功能。
"""
import json
import gzip
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .structured_logger import log_manager
from .log_rotation import log_rotation_manager

router = APIRouter(prefix="/api/logs", tags=["日志管理"])


class LogQueryRequest(BaseModel):
    """日志查询请求模型"""
    logger_name: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    message_pattern: Optional[str] = None
    limit: int = 100
    offset: int = 0


class LogEntryResponse(BaseModel):
    """日志条目响应模型"""
    timestamp: str
    level: str
    logger: str
    message: str
    module: Optional[str]
    function: Optional[str]
    line: Optional[int]
    context: Optional[Dict[str, Any]]
    extra_fields: Optional[Dict[str, Any]]


class LogStatsResponse(BaseModel):
    """日志统计响应模型"""
    total_entries: int
    level_stats: Dict[str, int]
    logger_stats: Dict[str, int]
    time_range_hours: int
    hourly_stats: Dict[str, int]


class LogFileInfo(BaseModel):
    """日志文件信息模型"""
    name: str
    size: int
    size_mb: float
    modified: str
    is_archive_candidate: bool
    is_cleanup_candidate: bool


class LogRotationStatsResponse(BaseModel):
    """日志轮转统计响应模型"""
    log_dir: str
    total_size: int
    total_size_mb: float
    file_count: int
    active_logs: List[LogFileInfo]
    archived_logs: List[LogFileInfo]
    rotation_settings: Dict[str, Any]


class LogExportRequest(BaseModel):
    """日志导出请求模型"""
    logger_name: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    format: str = "json"  # json, csv, text


class LogSearchResponse(BaseModel):
    """日志搜索响应模型"""
    entries: List[LogEntryResponse]
    total_count: int
    has_more: bool
    search_time_ms: float


class LogQueryEngine:
    """日志查询引擎"""
    
    def __init__(self, log_dir: str = "logs"):
        """初始化日志查询引擎
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        
    def search_logs(self, request: LogQueryRequest) -> Tuple[List[Dict[str, Any]], int]:
        """搜索日志
        
        Args:
            request: 查询请求
            
        Returns:
            (日志条目列表, 总数量)
        """
        try:
            # 获取日志文件列表
            log_files = self._get_log_files(request.logger_name)
            
            # 解析时间范围
            start_time, end_time = self._parse_time_range(request.start_time, request.end_time)
            
            # 搜索日志
            entries = []
            total_count = 0
            
            for log_file in log_files:
                file_entries, file_count = self._search_single_file(
                    log_file, request, start_time, end_time
                )
                entries.extend(file_entries)
                total_count += file_count
                
            # 排序和分页
            entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # 应用分页
            start_idx = request.offset
            end_idx = request.offset + request.limit
            paginated_entries = entries[start_idx:end_idx]
            
            return paginated_entries, total_count
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"搜索日志失败: {str(e)}")
            
    def _get_log_files(self, logger_name: Optional[str] = None) -> List[Path]:
        """获取日志文件列表
        
        Args:
            logger_name: 日志记录器名称
            
        Returns:
            日志文件路径列表
        """
        files = []
        
        # 活动日志文件
        if logger_name:
            pattern = f"{logger_name}.log*"
        else:
            pattern = "*.log*"
            
        for log_file in self.log_dir.glob(pattern):
            if log_file.is_file() and not log_file.name.endswith(".gz"):
                files.append(log_file)
                
        # 归档日志文件
        archive_dir = self.log_dir / "archived"
        if archive_dir.exists():
            if logger_name:
                pattern = f"{logger_name}_*.gz"
            else:
                pattern = "*.gz"
                
            for archive_file in archive_dir.glob(pattern):
                files.append(archive_file)
                
        return files
        
    def _parse_time_range(self, start_time: Optional[str], end_time: Optional[str]) -> Tuple[Optional[datetime], Optional[datetime]]:
        """解析时间范围
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            (开始时间, 结束时间)
        """
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="开始时间格式错误")
                
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="结束时间格式错误")
                
        return start_dt, end_dt
        
    def _search_single_file(self, log_file: Path, request: LogQueryRequest,
                           start_time: Optional[datetime], end_time: Optional[datetime]) -> Tuple[List[Dict[str, Any]], int]:
        """搜索单个日志文件
        
        Args:
            log_file: 日志文件路径
            request: 查询请求
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            (日志条目列表, 数量)
        """
        entries = []
        count = 0
        
        try:
            # 打开文件
            if log_file.name.endswith(".gz"):
                with gzip.open(log_file, 'rt', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
            # 解析每一行
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    log_entry = json.loads(line)
                    
                    # 应用过滤器
                    if self._filter_log_entry(log_entry, request, start_time, end_time):
                        entries.append(log_entry)
                        count += 1
                        
                except json.JSONDecodeError:
                    # 跳过非JSON格式的行
                    continue
                    
        except Exception as e:
            # 记录错误但继续处理其他文件
            print(f"处理日志文件失败 {log_file}: {e}")
            
        return entries, count
        
    def _filter_log_entry(self, log_entry: Dict[str, Any], request: LogQueryRequest,
                         start_time: Optional[datetime], end_time: Optional[datetime]) -> bool:
        """过滤日志条目
        
        Args:
            log_entry: 日志条目
            request: 查询请求
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            是否匹配
        """
        # 时间过滤
        if "timestamp" in log_entry:
            try:
                log_time = datetime.fromisoformat(log_entry["timestamp"].replace('Z', '+00:00'))
                
                if start_time and log_time < start_time:
                    return False
                    
                if end_time and log_time > end_time:
                    return False
                    
            except ValueError:
                # 时间格式错误，跳过此条目
                return False
                
        # 级别过滤
        if request.level and "level" in log_entry:
            if log_entry["level"].upper() != request.level.upper():
                return False
                
        # 日志记录器过滤
        if request.logger_name and "logger" in log_entry:
            if log_entry["logger"] != request.logger_name:
                return False
                
        # 消息模式过滤
        if request.message_pattern and "message" in log_entry:
            try:
                pattern = re.compile(request.message_pattern, re.IGNORECASE)
                if not pattern.search(log_entry["message"]):
                    return False
            except re.error:
                # 正则表达式错误，使用简单包含匹配
                if request.message_pattern.lower() not in log_entry["message"].lower():
                    return False
                    
        return True
        
    def get_log_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取日志统计信息
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            统计信息
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # 获取所有日志文件
            log_files = self._get_log_files()
            
            stats = {
                "total_entries": 0,
                "level_stats": {},
                "logger_stats": {},
                "hourly_stats": {},
                "time_range_hours": hours
            }
            
            # 初始化小时统计
            for i in range(hours):
                hour_key = (start_time + timedelta(hours=i)).strftime("%Y-%m-%d %H:00")
                stats["hourly_stats"][hour_key] = 0
                
            # 统计日志
            for log_file in log_files:
                self._stats_single_file(log_file, stats, start_time, end_time)
                
            return stats
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取日志统计失败: {str(e)}")
            
    def _stats_single_file(self, log_file: Path, stats: Dict[str, Any],
                          start_time: datetime, end_time: datetime):
        """统计单个日志文件
        
        Args:
            log_file: 日志文件路径
            stats: 统计字典
            start_time: 开始时间
            end_time: 结束时间
        """
        try:
            # 打开文件
            if log_file.name.endswith(".gz"):
                with gzip.open(log_file, 'rt', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
            # 统计每一行
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    log_entry = json.loads(line)
                    
                    # 检查时间范围
                    if "timestamp" in log_entry:
                        try:
                            log_time = datetime.fromisoformat(log_entry["timestamp"].replace('Z', '+00:00'))
                            
                            if log_time < start_time or log_time > end_time:
                                continue
                                
                            # 更新统计
                            stats["total_entries"] += 1
                            
                            # 级别统计
                            level = log_entry.get("level", "UNKNOWN")
                            stats["level_stats"][level] = stats["level_stats"].get(level, 0) + 1
                            
                            # 日志记录器统计
                            logger = log_entry.get("logger", "UNKNOWN")
                            stats["logger_stats"][logger] = stats["logger_stats"].get(logger, 0) + 1
                            
                            # 小时统计
                            hour_key = log_time.strftime("%Y-%m-%d %H:00")
                            if hour_key in stats["hourly_stats"]:
                                stats["hourly_stats"][hour_key] += 1
                                
                        except ValueError:
                            # 时间格式错误，跳过
                            continue
                            
                except json.JSONDecodeError:
                    # 跳过非JSON格式的行
                    continue
                    
        except Exception as e:
            # 记录错误但继续处理其他文件
            print(f"统计日志文件失败 {log_file}: {e}")


# 创建日志查询引擎实例
log_query_engine = LogQueryEngine()


@router.post("/search", response_model=LogSearchResponse)
async def search_logs(request: LogQueryRequest):
    """搜索日志
    
    Args:
        request: 查询请求
        
    Returns:
        搜索结果
    """
    import time
    start_time = time.time()
    
    entries, total_count = log_query_engine.search_logs(request)
    
    # 转换为响应模型
    log_entries = []
    for entry in entries:
        log_entries.append(LogEntryResponse(
            timestamp=entry.get("timestamp", ""),
            level=entry.get("level", "UNKNOWN"),
            logger=entry.get("logger", ""),
            message=entry.get("message", ""),
            module=entry.get("module"),
            function=entry.get("function"),
            line=entry.get("line"),
            context=entry.get("context"),
            extra_fields=entry.get("extra_fields")
        ))
        
    search_time = (time.time() - start_time) * 1000  # 转换为毫秒
    
    return LogSearchResponse(
        entries=log_entries,
        total_count=total_count,
        has_more=request.offset + len(log_entries) < total_count,
        search_time_ms=round(search_time, 2)
    )


@router.get("/stats", response_model=LogStatsResponse)
async def get_log_stats(hours: int = Query(24, ge=1, le=168)):
    """获取日志统计信息
    
    Args:
        hours: 时间范围（小时）
        
    Returns:
        统计信息
    """
    stats = log_query_engine.get_log_stats(hours)
    
    return LogStatsResponse(**stats)


@router.get("/files")
async def get_log_files():
    """获取日志文件列表
    
    Returns:
        日志文件信息
    """
    try:
        stats = log_rotation_manager.get_log_stats()
        
        # 转换为响应模型
        active_logs = []
        for log_info in stats.get("active_logs", []):
            active_logs.append(LogFileInfo(**log_info))
            
        archived_logs = []
        for log_info in stats.get("archived_logs", []):
            archived_logs.append(LogFileInfo(**log_info))
            
        return LogRotationStatsResponse(
            log_dir=stats["log_dir"],
            total_size=stats["total_size"],
            total_size_mb=stats["total_size_mb"],
            file_count=stats["file_count"],
            active_logs=active_logs,
            archived_logs=archived_logs,
            rotation_settings=stats["rotation_settings"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志文件列表失败: {str(e)}")


@router.post("/export")
async def export_logs(request: LogExportRequest):
    """导出日志
    
    Args:
        request: 导出请求
        
    Returns:
        导出结果
    """
    try:
        # 构建查询请求
        query_request = LogQueryRequest(
            logger_name=request.logger_name,
            level=request.level,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=10000,  # 导出限制
            offset=0
        )
        
        entries, total_count = log_query_engine.search_logs(query_request)
        
        # 根据格式导出
        if request.format == "json":
            content = json.dumps(entries, ensure_ascii=False, indent=2)
            content_type = "application/json"
            filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        elif request.format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            if entries:
                headers = list(entries[0].keys())
                writer.writerow(headers)
                
                # 写入数据
                for entry in entries:
                    row = [str(entry.get(header, "")) for header in headers]
                    writer.writerow(row)
                    
            content = output.getvalue()
            content_type = "text/csv"
            filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
        else:  # text格式
            content_lines = []
            for entry in entries:
                timestamp = entry.get("timestamp", "")
                level = entry.get("level", "")
                logger = entry.get("logger", "")
                message = entry.get("message", "")
                
                content_lines.append(f"{timestamp} [{level}] {logger}: {message}")
                
            content = "\n".join(content_lines)
            content_type = "text/plain"
            filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
        return {
            "filename": filename,
            "content_type": content_type,
            "content": content,
            "entry_count": len(entries),
            "export_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出日志失败: {str(e)}")


@router.post("/rotation/manual-rotate")
async def manual_rotate_logs(logger_name: str = Query(None)):
    """手动轮转日志
    
    Args:
        logger_name: 日志记录器名称
        
    Returns:
        轮转结果
    """
    try:
        if logger_name:
            success = log_rotation_manager.manual_rotate(logger_name)
            if success:
                return {
                    "status": "success",
                    "message": f"日志 {logger_name} 轮转完成",
                    "logger_name": logger_name,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(status_code=400, detail=f"轮转日志失败: {logger_name}")
        else:
            # 轮转所有日志
            results = {}
            for logger in ["app", "api", "database", "websocket", "monitoring"]:
                results[logger] = log_rotation_manager.manual_rotate(logger)
                
            return {
                "status": "success",
                "message": "所有日志轮转完成",
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"手动轮转日志失败: {str(e)}")


@router.post("/rotation/manual-archive")
async def manual_archive_logs():
    """手动归档日志
    
    Returns:
        归档结果
    """
    try:
        result = log_rotation_manager.manual_archive()
        
        return {
            "status": "success",
            "message": "手动归档完成",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"手动归档日志失败: {str(e)}")


@router.post("/rotation/manual-cleanup")
async def manual_cleanup_logs():
    """手动清理过期日志
    
    Returns:
        清理结果
    """
    try:
        result = log_rotation_manager.manual_cleanup()
        
        return {
            "status": "success",
            "message": "手动清理完成",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"手动清理日志失败: {str(e)}")


@router.get("/rotation/config")
async def get_rotation_config():
    """获取轮转配置
    
    Returns:
        轮转配置
    """
    try:
        from .log_rotation import log_rotation_config
        
        config = log_rotation_config.get_config()
        
        return {
            "status": "success",
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取轮转配置失败: {str(e)}")


@router.put("/rotation/config")
async def update_rotation_config(config: Dict[str, Any]):
    """更新轮转配置
    
    Args:
        config: 配置参数
        
    Returns:
        更新结果
    """
    try:
        from .log_rotation import log_rotation_config
        
        log_rotation_config.update_config(**config)
        
        # 重新初始化轮转服务
        from .log_rotation import initialize_log_rotation
        initialize_log_rotation()
        
        return {
            "status": "success",
            "message": "轮转配置已更新",
            "config": log_rotation_config.get_config(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新轮转配置失败: {str(e)}")


@router.get("/loggers")
async def get_available_loggers():
    """获取可用的日志记录器列表
    
    Returns:
        日志记录器列表
    """
    try:
        loggers = ["app", "api", "database", "websocket", "monitoring"]
        
        return {
            "status": "success",
            "loggers": loggers,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志记录器列表失败: {str(e)}")


@router.get("/levels")
async def get_available_levels():
    """获取可用的日志级别列表
    
    Returns:
        日志级别列表
    """
    try:
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        return {
            "status": "success",
            "levels": levels,
            "descriptions": {
                "DEBUG": "调试信息",
                "INFO": "一般信息",
                "WARNING": "警告信息",
                "ERROR": "错误信息",
                "CRITICAL": "严重错误"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志级别列表失败: {str(e)}")