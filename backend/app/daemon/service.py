"""
守护进程服务

实现7×24运行能力，支持系统服务集成和自动重启机制
"""
import os
import sys
import time
import signal
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DaemonService:
    """守护进程服务"""
    
    def __init__(self, name: str, pid_file: str = None, log_file: str = None):
        """初始化守护进程服务
        
        Args:
            name: 服务名称
            pid_file: PID文件路径
            log_file: 日志文件路径
        """
        self.name = name
        self.pid_file = pid_file or f"/tmp/{name}.pid"
        self.log_file = log_file or f"/tmp/{name}.log"
        self.running = False
        self.exit_code = 0
        logger.info(f"初始化守护进程服务: {name}")
    
    def daemonize(self):
        """守护进程化
        
        实现标准的守护进程化过程
        """
        try:
            # 第一次fork，创建子进程
            pid = os.fork()
            if pid > 0:
                # 父进程退出
                sys.exit(0)
        except OSError as err:
            logger.error(f"第一次fork失败: {err}")
            sys.exit(1)
        
        # 子进程继续运行
        # 修改工作目录
        os.chdir('/')
        # 创建新的会话
        os.setsid()
        # 设置文件权限掩码
        os.umask(0)
        
        try:
            # 第二次fork，防止进程重新获取控制终端
            pid = os.fork()
            if pid > 0:
                # 子进程退出
                sys.exit(0)
        except OSError as err:
            logger.error(f"第二次fork失败: {err}")
            sys.exit(1)
        
        # 重定向标准文件描述符
        sys.stdout.flush()
        sys.stderr.flush()
        
        # 关闭标准输入、输出、错误
        si = open(os.devnull, 'r')
        so = open(self.log_file, 'a+')
        se = open(self.log_file, 'a+')
        
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        
        # 写入PID文件
        pid = str(os.getpid())
        with open(self.pid_file, 'w+') as f:
            f.write(pid + '\n')
        
        logger.info(f"守护进程已启动，PID: {pid}")
    
    def start(self):
        """启动服务
        
        Returns:
            是否成功
        """
        # 检查PID文件是否存在
        if os.path.exists(self.pid_file):
            logger.error(f"服务可能已在运行，PID文件存在: {self.pid_file}")
            return False
        
        try:
            # 守护进程化
            self.daemonize()
            
            # 注册信号处理
            signal.signal(signal.SIGTERM, self._sigterm_handler)
            signal.signal(signal.SIGINT, self._sigint_handler)
            
            # 启动服务
            self.running = True
            logger.info(f"服务已启动: {self.name}")
            
            # 运行主循环
            self._run()
            
        except Exception as e:
            logger.error(f"启动服务失败: {str(e)}")
            logger.error(traceback.format_exc())
            self.exit_code = 1
            return False
        finally:
            # 清理PID文件
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            
            logger.info(f"服务已停止，退出代码: {self.exit_code}")
        
        return True
    
    def stop(self):
        """停止服务
        
        Returns:
            是否成功
        """
        # 检查PID文件
        if not os.path.exists(self.pid_file):
            logger.error(f"服务未运行，PID文件不存在: {self.pid_file}")
            return False
        
        try:
            # 读取PID
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 发送终止信号
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程退出
            timeout = 30
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    os.kill(pid, 0)  # 检查进程是否存在
                    time.sleep(1)
                except OSError:
                    break
            
            # 清理PID文件
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            
            logger.info(f"服务已停止: {self.name}")
            return True
        except Exception as e:
            logger.error(f"停止服务失败: {str(e)}")
            return False
    
    def restart(self):
        """重启服务
        
        Returns:
            是否成功
        """
        logger.info(f"重启服务: {self.name}")
        
        # 停止服务
        if not self.stop():
            return False
        
        # 启动服务
        return self.start()
    
    def status(self):
        """获取服务状态
        
        Returns:
            状态信息
        """
        if not os.path.exists(self.pid_file):
            return {"status": "stopped", "pid": None}
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            os.kill(pid, 0)
            return {"status": "running", "pid": pid}
        except Exception:
            # 进程不存在
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            return {"status": "stopped", "pid": None}
    
    def _run(self):
        """运行服务主循环
        
        子类应该重写此方法实现具体的服务逻辑
        """
        while self.running:
            try:
                # 示例：每10秒执行一次任务
                self._execute_task()
                time.sleep(10)
            except Exception as e:
                logger.error(f"执行任务失败: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续运行
                time.sleep(10)
    
    def _execute_task(self):
        """执行任务
        
        子类应该重写此方法实现具体的任务逻辑
        """
        logger.info(f"执行任务: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _sigterm_handler(self, signum, frame):
        """处理SIGTERM信号
        
        Args:
            signum: 信号编号
            frame: 堆栈帧
        """
        logger.info(f"接收到SIGTERM信号，准备停止服务")
        self.running = False
    
    def _sigint_handler(self, signum, frame):
        """处理SIGINT信号
        
        Args:
            signum: 信号编号
            frame: 堆栈帧
        """
        logger.info(f"接收到SIGINT信号，准备停止服务")
        self.running = False


class PyCopilotDaemon(DaemonService):
    """Py Copilot守护进程"""
    
    def __init__(self, pid_file: str = None, log_file: str = None):
        """初始化Py Copilot守护进程
        
        Args:
            pid_file: PID文件路径
            log_file: 日志文件路径
        """
        # 默认路径
        base_dir = Path(__file__).parent.parent.parent.parent
        default_pid_file = base_dir / "py_copilot.pid"
        default_log_file = base_dir / "logs" / "py_copilot_daemon.log"
        
        # 确保日志目录存在
        default_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(
            name="py_copilot",
            pid_file=pid_file or str(default_pid_file),
            log_file=log_file or str(default_log_file)
        )
        
        # 服务组件
        self.components = {}
    
    def register_component(self, name: str, component):
        """注册服务组件
        
        Args:
            name: 组件名称
            component: 组件实例
        """
        self.components[name] = component
        logger.info(f"组件已注册: {name}")
    
    def _run(self):
        """运行服务主循环"""
        # 初始化组件
        self._initialize_components()
        
        # 主循环
        while self.running:
            try:
                # 执行组件任务
                self._execute_components_tasks()
                
                # 执行定期任务
                self._execute_periodic_tasks()
                
                # 睡眠
                time.sleep(5)
            except Exception as e:
                logger.error(f"执行主循环失败: {str(e)}")
                logger.error(traceback.format_exc())
                # 继续运行
                time.sleep(5)
    
    def _initialize_components(self):
        """初始化组件"""
        logger.info("初始化服务组件")
        
        for name, component in self.components.items():
            try:
                if hasattr(component, "initialize"):
                    component.initialize()
                logger.info(f"组件已初始化: {name}")
            except Exception as e:
                logger.error(f"初始化组件失败: {name}, 错误: {str(e)}")
    
    def _execute_components_tasks(self):
        """执行组件任务"""
        for name, component in self.components.items():
            try:
                if hasattr(component, "execute_task"):
                    component.execute_task()
            except Exception as e:
                logger.error(f"执行组件任务失败: {name}, 错误: {str(e)}")
    
    def _execute_periodic_tasks(self):
        """执行定期任务"""
        current_time = datetime.now()
        
        # 每小时执行一次的任务
        if current_time.minute == 0 and current_time.second < 10:
            self._execute_hourly_tasks()
        
        # 每天执行一次的任务
        if current_time.hour == 0 and current_time.minute == 0 and current_time.second < 10:
            self._execute_daily_tasks()
    
    def _execute_hourly_tasks(self):
        """执行每小时任务"""
        logger.info("执行每小时任务")
        
        # 示例：清理过期的短期记忆
        if "memory_service" in self.components:
            try:
                memory_service = self.components["memory_service"]
                if hasattr(memory_service, "clean_old_short_term_memories"):
                    cleaned_count = memory_service.clean_old_short_term_memories(days=30)
                    logger.info(f"已清理 {cleaned_count} 个旧记忆目录")
            except Exception as e:
                logger.error(f"清理旧记忆失败: {str(e)}")
    
    def _execute_daily_tasks(self):
        """执行每天任务"""
        logger.info("执行每天任务")
        
        # 示例：生成系统报告
        self._generate_system_report()
    
    def _generate_system_report(self):
        """生成系统报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "service_name": self.name,
            "components": {},
            "status": "running"
        }
        
        # 收集组件状态
        for name, component in self.components.items():
            try:
                if hasattr(component, "get_status"):
                    report["components"][name] = component.get_status()
                else:
                    report["components"][name] = "active"
            except Exception as e:
                report["components"][name] = f"error: {str(e)}"
        
        # 保存报告
        report_dir = Path(self.log_file).parent / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"system_report_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            import json
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"系统报告已生成: {report_file}")
        except Exception as e:
            logger.error(f"生成系统报告失败: {str(e)}")


# 服务实例
py_copilot_daemon = PyCopilotDaemon()
