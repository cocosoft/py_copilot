"""技能仓库服务"""
import os
import git
import yaml
import tempfile
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.skill import SkillRepository
from app.core.logging_config import logger


class SkillRepositoryService:
    """技能仓库服务，用于管理远程技能仓库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_repositories(self) -> List[SkillRepository]:
        """获取所有技能仓库"""
        return self.db.query(SkillRepository).all()
    
    def get_repository(self, repository_id: int) -> Optional[SkillRepository]:
        """获取单个技能仓库"""
        return self.db.query(SkillRepository).filter(SkillRepository.id == repository_id).first()
    
    def create_repository(self, repo_data: Dict[str, Any]) -> SkillRepository:
        """创建技能仓库"""
        new_repo = SkillRepository(
            name=repo_data['name'],
            url=repo_data['url'],
            description=repo_data.get('description'),
            branch=repo_data.get('branch', 'main'),
            sync_interval_hours=repo_data.get('sync_interval_hours', 24),
            is_enabled=True,
            created_at=datetime.utcnow()
        )
        self.db.add(new_repo)
        self.db.commit()
        self.db.refresh(new_repo)
        return new_repo
    
    def update_repository(self, repository_id: int, repo_data: Dict[str, Any]) -> Optional[SkillRepository]:
        """更新技能仓库"""
        repo = self.get_repository(repository_id)
        if not repo:
            return None
        
        for key, value in repo_data.items():
            if hasattr(repo, key):
                setattr(repo, key, value)
        
        repo.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(repo)
        return repo
    
    def delete_repository(self, repository_id: int) -> bool:
        """删除技能仓库"""
        repo = self.get_repository(repository_id)
        if not repo:
            return False
        
        self.db.delete(repo)
        self.db.commit()
        return True
    
    def sync_repository(self, repository_id: int) -> Dict[str, Any]:
        """同步技能仓库"""
        repo = self.get_repository(repository_id)
        if not repo:
            return {"status": "error", "message": "仓库不存在"}
        
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = os.path.join(temp_dir, "repo")
                
                if os.path.exists(repo_path):
                    # 如果仓库已存在，执行拉取操作
                    git_repo = git.Repo(repo_path)
                    git_repo.git.pull()
                    logger.info(f"拉取仓库更新: {repo.name}")
                else:
                    # 克隆仓库
                    git_repo = git.Repo.clone_from(repo.url, repo_path, branch=repo.branch)
                    logger.info(f"克隆仓库: {repo.name}")
                
                # 扫描仓库中的技能文件
                skill_files = []
                for root, dirs, files in os.walk(repo_path):
                    for file in files:
                        if file == "SKILL.md":
                            skill_files.append(os.path.join(root, file))
                
                # 统计技能数量
                skill_count = len(skill_files)
                logger.info(f"仓库 {repo.name} 包含 {skill_count} 个技能文件")
                
                # 更新仓库同步信息
                repo.last_sync_at = datetime.utcnow()
                repo.last_sync_status = "success"
                repo.updated_at = datetime.utcnow()
                self.db.commit()
                
                return {
                    "status": "success",
                    "message": f"仓库同步成功，发现 {skill_count} 个技能文件",
                    "skill_count": skill_count
                }
                
        except Exception as e:
            logger.error(f"仓库同步失败 {repo.name}: {e}")
            repo.last_sync_status = "failed"
            repo.last_sync_at = datetime.utcnow()
            repo.updated_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "status": "error",
                "message": f"仓库同步失败: {str(e)}"
            }
