"""外部技能仓库同步服务"""
import os
import git
import yaml
import shutil
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.logging_config import logger
from app.models.skill import Skill, SkillRepository, RemoteSkill
from app.services.skill_service import SkillService


class ExternalSkillSyncService:
    """外部技能仓库同步服务"""

    DEFAULT_SKILLS_REPO_URL = "https://github.com/anthropics/skills"

    def __init__(self, db: Session):
        self.db = db
        self.temp_dir = Path(tempfile.gettempdir()) / "py_copilot_skills"

    def clone_repository(self, repo_url: str, branch: str = "main", credentials: Optional[Dict] = None) -> Path:
        """克隆技能仓库到本地临时目录"""
        repo_name = self._get_repo_name(repo_url)
        repo_path = self.temp_dir / repo_name

        if repo_path.exists():
            try:
                shutil.rmtree(repo_path)
            except Exception as e:
                logger.warning(f"无法删除现有目录 {repo_path}: {e}")

        try:
            repo = git.Repo.clone_from(
                repo_url,
                repo_path,
                branch=branch,
                depth=1
            )
            logger.info(f"成功克隆仓库 {repo_url} 到 {repo_path}")
            return repo_path
        except git.GitCommandError as e:
            logger.error(f"克隆仓库失败 {repo_url}: {e}")
            raise Exception(f"克隆仓库失败: {e}")

    def _get_repo_name(self, repo_url: str) -> str:
        """从 URL 提取仓库名称"""
        return repo_url.rstrip('/').split('/')[-1].replace('.git', '')

    def parse_skill_metadata(self, skill_path: Path) -> Optional[Dict[str, Any]]:
        """解析技能的 SKILL.md 文件，提取元数据"""
        skill_file = skill_path / "SKILL.md"

        if not skill_file.exists():
            logger.warning(f"技能目录中缺少 SKILL.md 文件: {skill_path}")
            return None

        try:
            content = skill_file.read_text(encoding='utf-8')

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    yaml_frontmatter = parts[1].strip()
                    metadata = yaml.safe_load(yaml_frontmatter)
                    return metadata

            return None
        except Exception as e:
            logger.error(f"解析技能元数据失败 {skill_path}: {e}")
            return None

    def scan_skills_in_repository(self, repo_path: Path, repository_id: int) -> List[RemoteSkill]:
        """扫描仓库中的所有技能并创建 RemoteSkill 记录"""
        skills = []

        try:
            for item in repo_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    metadata = self.parse_skill_metadata(item)

                    if metadata:
                        skill_id = self._generate_skill_id(item.name, repository_id)

                        remote_skill = self._create_or_update_remote_skill(
                            repository_id=repository_id,
                            skill_id=skill_id,
                            name=item.name,
                            display_name=metadata.get('name', item.name),
                            description=metadata.get('description', ''),
                            version=metadata.get('version', '1.0.0'),
                            license=metadata.get('license'),
                            tags=metadata.get('tags', []),
                            author=metadata.get('author'),
                            documentation_url=metadata.get('documentation_url'),
                            requirements=metadata.get('requirements', []),
                            file_path=str(item.relative_to(repo_path)),
                            local_path=str(item)
                        )
                        skills.append(remote_skill)

            logger.info(f"在仓库中扫描到 {len(skills)} 个技能")
            return skills

        except Exception as e:
            logger.error(f"扫描仓库技能失败 {repo_path}: {e}")
            raise

    def _generate_skill_id(self, skill_name: str, repository_id: int) -> str:
        """生成技能唯一标识符"""
        raw = f"{repository_id}:{skill_name}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def _create_or_update_remote_skill(
        self,
        repository_id: int,
        skill_id: str,
        name: str,
        display_name: str,
        description: str,
        version: str,
        license: Optional[str],
        tags: List[str],
        author: Optional[str],
        documentation_url: Optional[str],
        requirements: List[Dict],
        file_path: str,
        local_path: str
    ) -> RemoteSkill:
        """创建或更新远程技能记录"""
        existing = self.db.query(RemoteSkill).filter(
            and_(
                RemoteSkill.repository_id == repository_id,
                RemoteSkill.name == name
            )
        ).first()

        if existing:
            existing.remote_id = skill_id
            existing.display_name = display_name
            existing.description = description
            existing.version = version
            existing.license = license
            existing.tags = tags
            existing.author = author
            existing.documentation_url = documentation_url
            existing.requirements = requirements
            existing.file_path = file_path
            existing.local_path = local_path
            existing.last_checked_at = datetime.utcnow()
            return existing
        else:
            remote_skill = RemoteSkill(
                repository_id=repository_id,
                remote_id=skill_id,
                name=name,
                display_name=display_name,
                description=description,
                version=version,
                license=license,
                tags=tags,
                author=author,
                documentation_url=documentation_url,
                requirements=requirements,
                file_path=file_path,
                local_path=local_path,
                last_checked_at=datetime.utcnow()
            )
            self.db.add(remote_skill)
            return remote_skill

    def sync_repository(self, repository_id: int) -> Dict[str, Any]:
        """同步指定的技能仓库"""
        repo = self.db.query(SkillRepository).filter(
            SkillRepository.id == repository_id
        ).first()

        if not repo:
            raise ValueError(f"仓库不存在: {repository_id}")

        try:
            self.db.query(RemoteSkill).filter(
                RemoteSkill.repository_id == repository_id
            ).delete()

            repo_path = self.clone_repository(
                repo.url,
                branch=repo.branch,
                credentials=repo.credentials
            )

            self.scan_skills_in_repository(repo_path, repository_id)

            repo.last_sync_at = datetime.utcnow()
            repo.last_sync_status = "success"
            repo.last_sync_error = None

            self.db.commit()

            return {
                "status": "success",
                "repository_id": repository_id,
                "message": "仓库同步成功"
            }

        except Exception as e:
            repo.last_sync_status = "failed"
            repo.last_sync_error = str(e)
            self.db.rollback()
            logger.error(f"仓库同步失败 {repository_id}: {e}")
            raise

    def install_remote_skill(self, remote_skill_id: int, target_dir: Path) -> Skill:
        """安装远程技能到本地"""
        remote_skill = self.db.query(RemoteSkill).filter(
            RemoteSkill.id == remote_skill_id
        ).first()

        if not remote_skill:
            raise ValueError(f"远程技能不存在: {remote_skill_id}")

        skill_service = SkillService(self.db)

        existing_skill = self.db.query(Skill).filter(
            Skill.remote_id == remote_skill.remote_id
        ).first()

        if existing_skill:
            return existing_skill

        target_path = target_dir / remote_skill.name
        source_path = Path(remote_skill.local_path)

        if source_path.exists():
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.copytree(source_path, target_path)

        skill = skill_service.create_skill({
            "name": remote_skill.name,
            "display_name": remote_skill.display_name,
            "description": remote_skill.description,
            "version": remote_skill.version,
            "license": remote_skill.license,
            "tags": remote_skill.tags,
            "author": remote_skill.author,
            "documentation_url": remote_skill.documentation_url,
            "requirements": remote_skill.requirements,
            "source": "external",
            "source_url": remote_skill.repository.url if remote_skill.repository else None,
            "remote_id": remote_skill.remote_id,
            "status": "disabled"
        })

        remote_skill.is_installed = True
        self.db.commit()

        logger.info(f"成功安装技能: {remote_skill.name}")
        return skill

    def uninstall_remote_skill(self, remote_skill_id: int, target_dir: Path) -> bool:
        """卸载已安装的远程技能"""
        remote_skill = self.db.query(RemoteSkill).filter(
            RemoteSkill.id == remote_skill_id
        ).first()

        if not remote_skill:
            raise ValueError(f"远程技能不存在: {remote_skill_id}")

        skill = self.db.query(Skill).filter(
            Skill.remote_id == remote_skill.remote_id
        ).first()

        if skill:
            target_path = target_dir / remote_skill.name
            if target_path.exists():
                shutil.rmtree(target_path)

            self.db.delete(skill)

        remote_skill.is_installed = False
        self.db.commit()

        logger.info(f"成功卸载技能: {remote_skill.name}")
        return True

    def get_remote_skill_content(self, remote_skill_id: int) -> Optional[str]:
        """获取远程技能的内容"""
        remote_skill = self.db.query(RemoteSkill).filter(
            RemoteSkill.id == remote_skill_id
        ).first()

        if not remote_skill:
            return None

        local_path = remote_skill.local_path
        skill_file = Path(local_path) / "SKILL.md"

        if skill_file.exists():
            return skill_file.read_text(encoding='utf-8')

        return None

    def cleanup_temp_dir(self):
        """清理临时目录"""
        if self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"已清理临时目录: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")
