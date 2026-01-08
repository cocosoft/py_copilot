"""技能管理服务层"""
import re
import os
import yaml
import hashlib
import subprocess
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, text

from app.core.logging_config import logger
from app.models.skill import Skill, SkillSession, SkillModelBinding, SkillExecutionLog, SkillRepository, RemoteSkill, SkillVersion
from app.services.skill_loader import SkillLoader
from app.services.skill_matching_service import SkillMatchingService
from app.services.skill_repository_service import SkillRepositoryService




class SkillService:
    """技能管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.skill_loader = SkillLoader()
        self.skill_matching_service = SkillMatchingService(db)
        self.skill_repository_service = SkillRepositoryService(db)
    
    def get_skills(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Skill], int]:
        """获取技能列表"""
        query = self.db.query(Skill)
        
        if status:
            query = query.filter(Skill.status == status)
        
        if tags:
            for tag in tags:
                # 对于SQLite，使用字符串匹配方式检查JSON数组是否包含特定元素
                # SQLite将JSON数组存储为字符串，例如 ["tag1", "tag2"]
                # 我们需要精确匹配标签，考虑三种情况：开头、中间、结尾
                query = query.filter(
                    or_(
                        Skill.tags.like(f"%[\"{tag}\"]%"),    # 匹配只有一个标签的情况
                        Skill.tags.like(f"%[\"{tag}\",%"),   # 匹配开头的标签
                        Skill.tags.like(f"%,\"{tag}\"]%"),   # 匹配结尾的标签
                        Skill.tags.like(f"%,\"{tag}\",%")    # 匹配中间的标签
                    )
                )
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Skill.name.ilike(search_term),
                    Skill.display_name.ilike(search_term),
                    Skill.description.ilike(search_term)
                )
            )
        
        total = query.count()
        skills = query.offset(skip).limit(limit).all()
        return skills, total
    
    def get_skill(self, skill_id: int) -> Optional[Skill]:
        """根据ID获取技能"""
        return self.db.query(Skill).filter(Skill.id == skill_id).first()
    
    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """根据名称获取技能"""
        return self.db.query(Skill).filter(Skill.name == name).first()
    
    def create_skill(self, skill_data: Dict[str, Any]) -> Skill:
        """创建技能"""
        skill = Skill(
            name=skill_data['name'],
            display_name=skill_data.get('display_name'),
            description=skill_data.get('description'),
            version=skill_data.get('version', '1.0.0'),
            license=skill_data.get('license'),
            tags=skill_data.get('tags', []),
            source=skill_data.get('source', 'local'),
            source_url=skill_data.get('source_url'),
            remote_id=skill_data.get('remote_id'),
            content=skill_data.get('content'),
            parameters_schema=skill_data.get('parameters_schema'),
            status=skill_data.get('status', 'disabled'),
            icon=skill_data.get('icon'),
            author=skill_data.get('author'),
            documentation_url=skill_data.get('documentation_url'),
            requirements=skill_data.get('requirements', []),
            config=skill_data.get('config', {})
        )
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill
    
    def update_skill(self, skill_id: int, skill_data: Dict[str, Any]) -> Optional[Skill]:
        """更新技能"""
        skill = self.get_skill(skill_id)
        if not skill:
            return None
        
        for key, value in skill_data.items():
            if hasattr(skill, key) and value is not None:
                setattr(skill, key, value)
        
        self.db.commit()
        self.db.refresh(skill)
        return skill
    
    def delete_skill(self, skill_id: int) -> bool:
        """删除技能"""
        skill = self.get_skill(skill_id)
        if not skill:
            return False
        
        self.db.delete(skill)
        self.db.commit()
        return True
    
    def create_skill_version(self, skill_id: int, version_data: Dict[str, Any]) -> Optional[SkillVersion]:
        """创建技能版本"""
        skill = self.get_skill(skill_id)
        if not skill:
            return None
        
        # 标记当前版本为非当前版本
        self.db.query(SkillVersion).filter(
            SkillVersion.skill_id == skill_id, 
            SkillVersion.is_current == True
        ).update({'is_current': False})
        
        # 创建新版本
        version = SkillVersion(
            skill_id=skill_id,
            version=version_data.get('version', skill.version),
            content=version_data.get('content', skill.content),
            description=version_data.get('description', skill.description),
            parameters_schema=version_data.get('parameters_schema', skill.parameters_schema),
            requirements=version_data.get('requirements', skill.requirements),
            tags=version_data.get('tags', skill.tags),
            change_log=version_data.get('change_log'),
            author_id=version_data.get('author_id'),
            is_current=True
        )
        
        self.db.add(version)
        
        # 更新技能的当前版本
        skill.version = version.version
        self.db.commit()
        
        self.db.refresh(version)
        return version
    
    def update_skill(self, skill_id: int, skill_data: Dict[str, Any]) -> Optional[Skill]:
        """更新技能，并自动创建新版本"""
        skill = self.get_skill(skill_id)
        if not skill:
            return None
        
        # 创建版本历史
        self.create_skill_version(skill_id, {
            'version': skill.version,
            'content': skill.content,
            'description': skill.description,
            'parameters_schema': skill.parameters_schema,
            'requirements': skill.requirements,
            'tags': skill.tags,
            'change_log': skill_data.get('change_log', '自动创建的版本历史记录')
        })
        
        # 更新技能
        for key, value in skill_data.items():
            if hasattr(skill, key) and value is not None and key != 'change_log':
                setattr(skill, key, value)
        
        self.db.commit()
        self.db.refresh(skill)
        return skill
    
    def get_skill_versions(self, skill_id: int) -> List[SkillVersion]:
        """获取技能的所有版本"""
        return self.db.query(SkillVersion).filter(
            SkillVersion.skill_id == skill_id
        ).order_by(SkillVersion.created_at.desc()).all()
    
    def get_skill_version(self, version_id: int) -> Optional[SkillVersion]:
        """根据版本ID获取版本"""
        return self.db.query(SkillVersion).filter(
            SkillVersion.id == version_id
        ).first()
    
    def get_current_skill_version(self, skill_id: int) -> Optional[SkillVersion]:
        """获取技能的当前版本"""
        return self.db.query(SkillVersion).filter(
            SkillVersion.skill_id == skill_id,
            SkillVersion.is_current == True
        ).first()
    
    def rollback_skill_version(self, skill_id: int, version_id: int) -> Optional[Skill]:
        """回滚技能到指定版本"""
        version = self.get_skill_version(version_id)
        if not version or version.skill_id != skill_id:
            return None
        
        skill = self.get_skill(skill_id)
        if not skill:
            return None
        
        # 标记当前版本为非当前版本
        self.db.query(SkillVersion).filter(
            SkillVersion.skill_id == skill_id,
            SkillVersion.is_current == True
        ).update({'is_current': False})
        
        # 创建回滚前的版本记录
        self.create_skill_version(skill_id, {
            'version': skill.version,
            'content': skill.content,
            'description': skill.description,
            'parameters_schema': skill.parameters_schema,
            'requirements': skill.requirements,
            'tags': skill.tags,
            'change_log': f'回滚到版本 {version.version} 前的版本'
        })
        
        # 标记目标版本为当前版本
        version.is_current = True
        
        # 更新技能为目标版本的内容
        skill.version = version.version
        skill.content = version.content
        skill.description = version.description
        skill.parameters_schema = version.parameters_schema
        skill.requirements = version.requirements
        skill.tags = version.tags
        
        self.db.commit()
        self.db.refresh(skill)
        return skill
    
    def compare_skill_versions(self, version_id_1: int, version_id_2: int) -> Dict[str, Any]:
        """比较两个技能版本的差异"""
        version1 = self.get_skill_version(version_id_1)
        version2 = self.get_skill_version(version_id_2)
        
        if not version1 or not version2:
            raise ValueError("无效的版本ID")
        
        if version1.skill_id != version2.skill_id:
            raise ValueError("不能比较不同技能的版本")
        
        # 比较各个字段
        diffs = {}
        fields_to_compare = ['version', 'description', 'content', 'parameters_schema', 'requirements', 'tags']
        
        for field in fields_to_compare:
            value1 = getattr(version1, field)
            value2 = getattr(version2, field)
            if value1 != value2:
                diffs[field] = {
                    'version1': value1,
                    'version2': value2
                }
        
        return {
            'version1': version1.version,
            'version2': version2.version,
            'diffs': diffs
        }
    
    def enable_skill(self, skill_id: int) -> Optional[Skill]:
        """启用技能"""
        return self.update_skill(skill_id, {'status': 'enabled'})
    
    def disable_skill(self, skill_id: int) -> Optional[Skill]:
        """禁用技能"""
        return self.update_skill(skill_id, {'status': 'disabled'})
    
    def load_skill_from_file(self, file_path: str) -> Optional[Skill]:
        """从文件加载技能"""
        skill_info = self.skill_loader.parse_skill_file(file_path)
        if not skill_info:
            return None
        
        metadata = skill_info['metadata']
        content = skill_info['content']
        parameters_schema = self.skill_loader.extract_parameters_schema(content)
        
        existing_skill = self.get_skill_by_name(metadata['name'])
        if existing_skill:
            logger.info(f"技能已存在，更新: {metadata['name']}")
            return self.update_skill(existing_skill.id, {
                'display_name': metadata.get('display_name'),
                'description': metadata.get('description'),
                'version': metadata.get('version', '1.0.0'),
                'license': metadata.get('license'),
                'tags': metadata.get('tags', []),
                'author': metadata.get('author'),
                'documentation_url': metadata.get('documentation_url'),
                'requirements': metadata.get('requirements', []),
                'content': content,
                'parameters_schema': parameters_schema,
                'source': 'local',
                'installed_at': datetime.utcnow()
            })
        
        return self.create_skill({
            'name': metadata['name'],
            'display_name': metadata.get('display_name'),
            'description': metadata.get('description'),
            'version': metadata.get('version', '1.0.0'),
            'license': metadata.get('license'),
            'tags': metadata.get('tags', []),
            'author': metadata.get('author'),
            'documentation_url': metadata.get('documentation_url'),
            'requirements': metadata.get('requirements', []),
            'content': content,
            'parameters_schema': parameters_schema,
            'source': 'local',
            'installed_at': datetime.utcnow()
        })
    
    def load_skills_from_directory(self, directory: str) -> List[Skill]:
        """从目录加载所有技能"""
        skills = []
        if not os.path.exists(directory):
            logger.warning(f"技能目录不存在: {directory}")
            return skills
        
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                skill_file = os.path.join(item_path, self.skill_loader.SKILL_FILE_NAME)
                if os.path.exists(skill_file):
                    skill = self.load_skill_from_file(skill_file)
                    if skill:
                        skills.append(skill)
        return skills
    
    def match_skills(self, task_description: str, limit: int = 5) -> List[Skill]:
        """根据任务描述匹配相关技能，使用TF-IDF和余弦相似度优化"""
        return self.skill_matching_service.match_skills(task_description, limit)
    
    def record_usage(self, skill_id: int) -> None:
        """记录技能使用"""
        skill = self.get_skill(skill_id)
        if skill:
            skill.usage_count += 1
            skill.last_used_at = datetime.utcnow()
            self.db.commit()


class SkillSessionService:
    """技能会话服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def activate_skills(
        self,
        conversation_id: int,
        skill_ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> List[SkillSession]:
        """激活技能"""
        sessions = []
        for skill_id in skill_ids:
            existing = self.db.query(SkillSession).filter(
                and_(
                    SkillSession.skill_id == skill_id,
                    SkillSession.conversation_id == conversation_id,
                    SkillSession.is_active == True
                )
            ).first()
            
            if existing:
                continue
            
            session = SkillSession(
                skill_id=skill_id,
                conversation_id=conversation_id,
                context=context or {}
            )
            self.db.add(session)
            sessions.append(session)
        
        self.db.commit()
        for session in sessions:
            self.db.refresh(session)
        
        return sessions
    
    def deactivate_skills(
        self,
        conversation_id: int,
        skill_ids: Optional[List[int]] = None
    ) -> int:
        """停用技能"""
        query = self.db.query(SkillSession).filter(
            and_(
                SkillSession.conversation_id == conversation_id,
                SkillSession.is_active == True
            )
        )
        
        if skill_ids:
            query = query.filter(SkillSession.skill_id.in_(skill_ids))
        
        sessions = query.all()
        for session in sessions:
            session.is_active = False
            session.deactivated_at = datetime.utcnow()
        
        self.db.commit()
        return len(sessions)
    
    def get_active_skills(self, conversation_id: int) -> List[SkillSession]:
        """获取会话中激活的技能"""
        return self.db.query(SkillSession).filter(
            and_(
                SkillSession.conversation_id == conversation_id,
                SkillSession.is_active == True
            )
        ).all()
    
    def update_session_context(
        self,
        session_id: int,
        context: Dict[str, Any]
    ) -> Optional[SkillSession]:
        """更新会话上下文"""
        session = self.db.query(SkillSession).filter(SkillSession.id == session_id).first()
        if session:
            session.context = context
            self.db.commit()
            self.db.refresh(session)
        return session


class SkillExecutionService:
    """技能执行服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def execute_skill(
        self,
        skill_id: int,
        task: str,
        params: Optional[Dict[str, Any]] = None,
        session_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """执行技能"""
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise ValueError(f"技能不存在: {skill_id}")
        
        if skill.status != 'enabled':
            raise ValueError(f"技能未启用: {skill.name}")
        
        import time
        start_time = time.time()
        
        execution_log = SkillExecutionLog(
            skill_id=skill_id,
            session_id=session_id,
            conversation_id=conversation_id,
            user_id=user_id,
            task_description=task,
            input_params=params or {},
            status='running'
        )
        self.db.add(execution_log)
        self.db.commit()
        self.db.refresh(execution_log)
        
        try:
            result = self._execute_skill_content(skill.content, task, params)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            execution_log.status = 'success'
            execution_log.output_result = result
            execution_log.execution_time_ms = execution_time_ms
            self.db.commit()
            
            skill.usage_count += 1
            skill.last_used_at = datetime.utcnow()
            self.db.commit()
            
            return {
                'success': True,
                'result': result,
                'execution_time_ms': execution_time_ms
            }
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            execution_log.status = 'failed'
            execution_log.error_message = str(e)
            execution_log.execution_time_ms = execution_time_ms
            self.db.commit()
            
            return {
                'success': False,
                'error': str(e),
                'execution_time_ms': execution_time_ms
            }
    
    def _execute_skill_content(
        self,
        content: str,
        task: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行技能内容（增强版安全沙箱）"""
        if not content:
            return "技能内容为空"
        
        # 安全沙箱配置
        MAX_EXECUTION_TIME = 1.0  # 最大执行时间（秒）
        
        def _clean_content(content_str: str) -> str:
            """清理技能内容，移除潜在危险代码"""
            # 移除危险字符序列
            dangerous_patterns = [
                r'\b(eval|exec|compile|globals|locals|__import__)\b',
                r'\b(os|sys|subprocess|shutil|threading|multiprocessing)\b',
                r'\b(open|file|read|write|delete|remove)\b',
                r'\b(import|from|as|global|nonlocal)\b',
                r'\b(while|for)\s*\(\s*True\s*\)',  # 无限循环
            ]
            
            cleaned = content_str
            for pattern in dangerous_patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            
            # 移除特殊字符
            cleaned = re.sub(r'[\\`$<>|;]', '', cleaned)
            return cleaned
        
        def _validate_task(task_str: str) -> str:
            """验证并清理任务描述"""
            if not isinstance(task_str, str):
                raise ValueError("任务描述必须是字符串类型")
            
            # 限制任务描述长度
            if len(task_str) > 1000:
                return task_str[:1000] + "..."  # 截断过长的任务描述
            
            return task_str
        
        def _validate_params(params_dict: Optional[Dict[str, Any]]) -> Dict[str, Any]:
            """验证并清理参数"""
            if not params_dict:
                return {}
            
            validated_params = {}
            for key, value in params_dict.items():
                # 仅允许基本类型参数
                if isinstance(value, (str, int, float, bool)):
                    validated_params[key] = value
                else:
                    validated_params[key] = str(value)  # 转换为字符串
            
            return validated_params
        
        def _safe_execute():
            """安全执行函数"""
            placeholder_pattern = re.compile(r'\{(\w+)\}')
            
            # 清理和验证输入
            cleaned_content = _clean_content(content)
            validated_task = _validate_task(task)
            validated_params = _validate_params(params)
            
            placeholders = {
                'task': validated_task,
                'params': str(validated_params),
            }
            
            result = cleaned_content
            for match in placeholder_pattern.finditer(cleaned_content):
                placeholder_name = match.group(1)
                if placeholder_name in placeholders:
                    result = result.replace(match.group(0), str(placeholders[placeholder_name]))
            
            return result
        
        try:
            # 使用超时限制执行
            import threading
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = _safe_execute()
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(MAX_EXECUTION_TIME)
            
            if thread.is_alive():
                raise TimeoutError("技能执行超时")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        except TimeoutError:
            return "技能执行超时，已被安全终止"
        except Exception as e:
            return f"技能执行出错: {str(e)}"
    
    def get_execution_logs(
        self,
        skill_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        limit: int = 100
    ) -> List[SkillExecutionLog]:
        """获取执行日志"""
        query = self.db.query(SkillExecutionLog)
        
        if skill_id:
            query = query.filter(SkillExecutionLog.skill_id == skill_id)
        if conversation_id:
            query = query.filter(SkillExecutionLog.conversation_id == conversation_id)
        
        return query.order_by(SkillExecutionLog.created_at.desc()).limit(limit).all()



