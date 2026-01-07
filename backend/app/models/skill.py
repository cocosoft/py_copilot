"""技能管理数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Skill(Base):
    """技能数据库模型"""
    __tablename__ = "skills"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    version = Column(String(50), default="1.0.0")
    license = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    source = Column(String(50), default="local")
    source_url = Column(String(500), nullable=True)
    remote_id = Column(String(100), nullable=True)
    content = Column(Text)
    parameters_schema = Column(JSON, nullable=True)
    status = Column(String(20), default="disabled", index=True)
    is_system = Column(Boolean, default=False)
    icon = Column(String(255), nullable=True)
    author = Column(String(200), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    requirements = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    installed_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True, index=True)
    usage_count = Column(Integer, default=0)
    config = Column(JSON, default=dict)

    skill_sessions = relationship("SkillSession", back_populates="skill", cascade="all, delete-orphan")
    skill_model_bindings = relationship("SkillModelBinding", back_populates="skill", cascade="all, delete-orphan")
    versions = relationship("SkillVersion", back_populates="skill", cascade="all, delete-orphan")


class SkillSession(Base):
    """技能会话关联模型"""
    __tablename__ = "skill_sessions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    context = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    activated_at = Column(DateTime(timezone=True), server_default=func.now())
    deactivated_at = Column(DateTime(timezone=True), nullable=True)

    skill = relationship("Skill", back_populates="skill_sessions")
    conversation = relationship("app.models.conversation.Conversation", back_populates="skill_sessions")
    user = relationship("app.models.user.User", back_populates="skill_sessions")


class SkillModelBinding(Base):
    """技能与模型绑定模型"""
    __tablename__ = "skill_model_bindings"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=True)
    model_type_id = Column(Integer, ForeignKey("model_categories.id", ondelete="CASCADE"), nullable=True)
    priority = Column(Integer, default=0)
    config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    skill = relationship("Skill", back_populates="skill_model_bindings")
    model = relationship("app.models.supplier_db.ModelDB")
    model_type = relationship("app.models.model_category.ModelCategory")


class SkillExecutionLog(Base):
    """技能执行日志模型"""
    __tablename__ = "skill_execution_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("skill_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    task_description = Column(Text)
    input_params = Column(JSON, default=dict)
    output_result = Column(Text, nullable=True)
    status = Column(String(20), default="pending", index=True)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True, index=True)
    token_usage = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    skill = relationship("Skill")
    session = relationship("SkillSession")
    conversation = relationship("app.models.conversation.Conversation")
    user = relationship("app.models.user.User")


class SkillRepository(Base):
    """技能仓库配置模型"""
    __tablename__ = "skill_repositories"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    branch = Column(String(100), default="main")
    is_enabled = Column(Boolean, default=True)
    sync_interval_hours = Column(Integer, default=24)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(20), nullable=True)
    last_sync_error = Column(Text, nullable=True)
    credentials = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    remote_skills = relationship("RemoteSkill", back_populates="repository", cascade="all, delete-orphan")


class SkillVersion(Base):
    """技能版本历史模型"""
    __tablename__ = "skill_versions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    content = Column(Text)
    description = Column(Text)
    parameters_schema = Column(JSON, nullable=True)
    requirements = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    change_log = Column(Text, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    skill = relationship("Skill", back_populates="versions")
    author = relationship("app.models.user.User")


class RemoteSkill(Base):
    """远程技能元数据模型"""
    __tablename__ = "remote_skills"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("skill_repositories.id", ondelete="CASCADE"), nullable=False)
    remote_id = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    display_name = Column(String(200), nullable=True)
    description = Column(Text)
    version = Column(String(50))
    license = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    author = Column(String(200), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    icon_url = Column(String(500), nullable=True)
    requirements = Column(JSON, default=list)
    file_path = Column(String(500), nullable=True)
    local_path = Column(String(500), nullable=True)
    is_installed = Column(Boolean, default=False)
    is_update_available = Column(Boolean, default=False)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    skill_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    repository = relationship("SkillRepository", back_populates="remote_skills")
    __table_args__ = (
        None,
        None
    )
