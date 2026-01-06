"""技能管理服务层"""
import re
import os
import yaml
import hashlib
import subprocess
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.logging_config import logger
from app.models.skill import Skill, SkillSession, SkillModelBinding, SkillExecutionLog, SkillRepository, RemoteSkill


class SkillLoader:
    """技能加载器，用于解析技能文件"""
    
    SKILL_FILE_NAME = "SKILL.md"
    FRONTMATTER_PATTERN = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
    
    @classmethod
    def parse_skill_file(cls, file_path: str) -> Optional[Dict[str, Any]]:
        """解析技能文件，提取元数据和内容"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"技能文件不存在: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter_match = cls.FRONTMATTER_PATTERN.match(content)
            if not frontmatter_match:
                logger.warning(f"技能文件缺少frontmatter: {file_path}")
                return None
            
            frontmatter_yaml = frontmatter_match.group(1)
            metadata = yaml.safe_load(frontmatter_yaml)
            if not metadata:
                logger.warning(f"技能文件frontmatter解析失败: {file_path}")
                return None
            
            required_fields = ['name', 'description']
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"技能文件缺少必要字段 '{field}': {file_path}")
                    return None
            
            markdown_content = cls.FRONTMATTER_PATTERN.sub('', content).strip()
            
            return {
                'metadata': metadata,
                'content': markdown_content,
                'file_path': file_path
            }
        except Exception as e:
            logger.error(f"解析技能文件失败 {file_path}: {e}")
            return None
    
    @classmethod
    def load_skill_from_directory(cls, skill_dir: str) -> Optional[Dict[str, Any]]:
        """从目录加载技能"""
        skill_file = os.path.join(skill_dir, cls.SKILL_FILE_NAME)
        if not os.path.exists(skill_file):
            logger.warning(f"技能目录中缺少 {cls.SKILL_FILE_NAME}: {skill_dir}")
            return None
        return cls.parse_skill_file(skill_file)
    
    @classmethod
    def extract_parameters_schema(cls, content: str) -> Optional[Dict[str, Any]]:
        """从技能内容中提取参数模式"""
        param_block_pattern = re.compile(
            r'```(?:yaml|json)?\s*parameters?\s*:?\s*\n(.*?)\n```',
            re.DOTALL
        )
        match = param_block_pattern.search(content)
        if match:
            try:
                return yaml.safe_load(match.group(1))
            except yaml.YAMLError:
                pass
        return None


class SkillService:
    """技能管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
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
                query = query.filter(Skill.tags.contains([tag]))
        
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
    
    def enable_skill(self, skill_id: int) -> Optional[Skill]:
        """启用技能"""
        return self.update_skill(skill_id, {'status': 'enabled'})
    
    def disable_skill(self, skill_id: int) -> Optional[Skill]:
        """禁用技能"""
        return self.update_skill(skill_id, {'status': 'disabled'})
    
    def load_skill_from_file(self, file_path: str) -> Optional[Skill]:
        """从文件加载技能"""
        skill_info = SkillLoader.parse_skill_file(file_path)
        if not skill_info:
            return None
        
        metadata = skill_info['metadata']
        content = skill_info['content']
        parameters_schema = SkillLoader.extract_parameters_schema(content)
        
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
                skill_file = os.path.join(item_path, SkillLoader.SKILL_FILE_NAME)
                if os.path.exists(skill_file):
                    skill = self.load_skill_from_file(skill_file)
                    if skill:
                        skills.append(skill)
        return skills
    
    def match_skills(self, task_description: str, limit: int = 5) -> List[Skill]:
        """根据任务描述匹配相关技能"""
        task_words = set(re.findall(r'\w+', task_description.lower()))
        
        skills = self.db.query(Skill).filter(Skill.status == 'enabled').all()
        
        def calculate_relevance(skill: Skill) -> float:
            score = 0.0
            skill_words = set()
            
            if skill.name:
                skill_words.update(re.findall(r'\w+', skill.name.lower()))
            if skill.display_name:
                skill_words.update(re.findall(r'\w+', skill.display_name.lower()))
            if skill.description:
                skill_words.update(re.findall(r'\w+', skill.description.lower()))
            if skill.tags:
                skill_words.update([t.lower() for t in skill.tags])
            
            for word in task_words:
                if word in skill_words:
                    score += 1.0
            
            if skill.description and task_description.lower() in skill.description.lower():
                score += 0.5
            
            return score
        
        scored_skills = [(skill, calculate_relevance(skill)) for skill in skills]
        scored_skills = [(s, score) for s, score in scored_skills if score > 0]
        scored_skills.sort(key=lambda x: x[1], reverse=True)
        
        return [skill for skill, _ in scored_skills[:limit]]
    
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
        """执行技能内容"""
        if not content:
            return "技能内容为空"
        
        placeholder_pattern = re.compile(r'\{(\w+)\}')
        placeholders = {
            'task': task,
            'params': str(params) if params else '',
        }
        
        result = content
        for match in placeholder_pattern.finditer(content):
            placeholder_name = match.group(1)
            if placeholder_name in placeholders:
                result = result.replace(match.group(0), str(placeholders[placeholder_name]))
        
        return result
    
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


class SkillRepositoryService:
    """技能仓库服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_repositories(self) -> List[SkillRepository]:
        """获取所有仓库"""
        return self.db.query(SkillRepository).all()
    
    def get_repository(self, repository_id: int) -> Optional[SkillRepository]:
        """获取仓库"""
        return self.db.query(SkillRepository).filter(SkillRepository.id == repository_id).first()
    
    def create_repository(self, repo_data: Dict[str, Any]) -> SkillRepository:
        """创建仓库"""
        repo = SkillRepository(**repo_data)
        self.db.add(repo)
        self.db.commit()
        self.db.refresh(repo)
        return repo
    
    def sync_repository(self, repository_id: int) -> Dict[str, Any]:
        """同步仓库"""
        repo = self.get_repository(repository_id)
        if not repo:
            raise ValueError(f"仓库不存在: {repository_id}")
        
        repo.last_sync_at = datetime.utcnow()
        self.db.commit()
        
        return {
            'success': True,
            'repository_id': repository_id,
            'message': '仓库同步完成'
        }
    
    def install_remote_skill(
        self,
        remote_skill_id: int,
        local_path: str
    ) -> Optional[Skill]:
        """安装远程技能"""
        remote_skill = self.db.query(RemoteSkill).filter(RemoteSkill.id == remote_skill_id).first()
        if not remote_skill:
            raise ValueError(f"远程技能不存在: {remote_skill_id}")
        
        os.makedirs(local_path, exist_ok=True)
        
        remote_skill.is_installed = True
        remote_skill.local_path = local_path
        self.db.commit()
        
        return self.db.query(Skill).filter(Skill.remote_id == remote_skill.remote_id).first()
