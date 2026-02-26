"""
文件迁移服务

用于将现有文件从旧结构迁移到新结构
支持：
1. 聊天附件迁移
2. 知识库文档迁移
3. Logo文件迁移
4. 数据库记录迁移
"""

import os
import shutil
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.services.storage_path_manager import (
    storage_path_manager,
    FileCategory,
    FilePrefix
)
from app.services.file_storage_service import file_storage_service
from app.models.file_record import FileRecord, FileStatus, StorageType
from app.models.chat_enhancements import UploadedFile, VoiceInput


class FileMigrationService:
    """
    文件迁移服务
    
    将现有文件从分散的旧结构迁移到统一的新结构
    """
    
    def __init__(self, db: Session, base_path: str = "uploads"):
        """
        初始化迁移服务
        
        Args:
            db: 数据库会话
            base_path: 基础存储路径
        """
        self.db = db
        self.base_path = Path(base_path)
        self.migration_log = []
    
    async def migrate_all(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        执行完整迁移
        
        Args:
            dry_run: 是否为试运行（不实际执行）
        
        Returns:
            Dict: 迁移统计信息
        """
        results = {
            'dry_run': dry_run,
            'total_migrated': 0,
            'total_failed': 0,
            'details': {}
        }
        
        # 1. 迁移聊天附件
        chat_result = await self.migrate_chat_attachments(dry_run)
        results['details']['chat_attachments'] = chat_result
        results['total_migrated'] += chat_result['migrated']
        results['total_failed'] += chat_result['failed']
        
        # 2. 迁移知识库文档
        kb_result = await self.migrate_knowledge_documents(dry_run)
        results['details']['knowledge_documents'] = kb_result
        results['total_migrated'] += kb_result['migrated']
        results['total_failed'] += kb_result['failed']
        
        # 3. 迁移Logo文件
        logo_result = await self.migrate_logo_files(dry_run)
        results['details']['logo_files'] = logo_result
        results['total_migrated'] += logo_result['migrated']
        results['total_failed'] += logo_result['failed']
        
        return results
    
    async def migrate_chat_attachments(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        迁移聊天附件
        
        从 backend/uploads/ 迁移到 backend/uploads/users/{user_id}/conversations/{conv_id}/attachments/
        
        Args:
            dry_run: 是否为试运行
        
        Returns:
            Dict: 迁移结果统计
        """
        result = {
            'category': 'chat_attachments',
            'migrated': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # 获取所有上传文件记录
        uploaded_files = self.db.query(UploadedFile).all()
        
        for old_file in uploaded_files:
            try:
                # 检查源文件是否存在
                old_path = Path(old_file.file_path)
                if not old_path.exists():
                    # 尝试在默认uploads目录查找
                    old_path = self.base_path / old_path.name
                    if not old_path.exists():
                        result['skipped'] += 1
                        result['errors'].append(f"文件不存在: {old_file.file_path}")
                        continue
                
                if dry_run:
                    result['migrated'] += 1
                    continue
                
                # 读取文件内容
                with open(old_path, 'rb') as f:
                    content = f.read()
                
                # 确定分类
                category = FileCategory.CONVERSATION_ATTACHMENT
                if old_file.file_type and 'image' in old_file.file_type:
                    # 如果是图片，可能是图像分析
                    pass
                
                # 保存到新位置
                file_info = await file_storage_service.save_file(
                    file_data=content,
                    filename=old_file.file_name,
                    user_id=old_file.user_id,
                    category=category,
                    related_id=old_file.conversation_id,
                    metadata={
                        'old_id': old_file.id,
                        'old_path': str(old_file.file_path),
                        'migrated_at': datetime.now().isoformat(),
                        'file_type': old_file.file_type,
                        'upload_status': old_file.upload_status
                    }
                )
                
                # 创建新的FileRecord记录
                new_record = FileRecord(
                    id=file_info['file_id'],
                    user_id=old_file.user_id,
                    original_name=old_file.file_name,
                    stored_name=file_info['stored_name'],
                    relative_path=file_info['relative_path'],
                    absolute_path=file_info['file_path'],
                    file_size=file_info['file_size'],
                    mime_type=old_file.mime_type or old_file.file_type,
                    extension=Path(old_file.file_name).suffix.lower(),
                    checksum=file_info['checksum'],
                    category=category,
                    storage_type=StorageType.LOCAL,
                    conversation_id=old_file.conversation_id,
                    status=FileStatus.COMPLETED if old_file.upload_status == 'completed' else FileStatus.FAILED,
                    extra_metadata=file_info['metadata'],
                    created_at=old_file.created_at,
                    updated_at=old_file.updated_at
                )
                
                self.db.add(new_record)
                
                # 记录迁移日志
                self.migration_log.append({
                    'old_id': old_file.id,
                    'new_id': file_info['file_id'],
                    'old_path': str(old_file.file_path),
                    'new_path': file_info['file_path'],
                    'status': 'success'
                })
                
                result['migrated'] += 1
                
            except Exception as e:
                result['failed'] += 1
                result['errors'].append(f"迁移失败 {old_file.id}: {str(e)}")
                self.migration_log.append({
                    'old_id': old_file.id,
                    'old_path': str(old_file.file_path),
                    'status': 'failed',
                    'error': str(e)
                })
        
        if not dry_run:
            self.db.commit()
        
        return result
    
    async def migrate_knowledge_documents(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        迁移知识库文档
        
        从 frontend/public/knowledges/ 迁移到 backend/uploads/users/{user_id}/knowledge/{kb_id}/
        
        Args:
            dry_run: 是否为试运行
        
        Returns:
            Dict: 迁移结果统计
        """
        result = {
            'category': 'knowledge_documents',
            'migrated': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # 知识库路径
        kb_base_path = Path("frontend/public/knowledges")
        
        if not kb_base_path.exists():
            result['errors'].append("知识库目录不存在")
            return result
        
        # 遍历所有知识库目录
        for kb_dir in kb_base_path.iterdir():
            if not kb_dir.is_dir():
                continue
            
            # 解析知识库ID
            kb_id_str = kb_dir.name.replace("knowledge_base_", "")
            try:
                knowledge_base_id = int(kb_id_str)
            except ValueError:
                result['errors'].append(f"无法解析知识库ID: {kb_dir.name}")
                continue
            
            # 遍历知识库中的文件
            for file_path in kb_dir.iterdir():
                if not file_path.is_file():
                    continue
                
                try:
                    if dry_run:
                        result['migrated'] += 1
                        continue
                    
                    # 读取文件
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # 注意：这里需要获取知识库所属用户ID
                    # 暂时使用默认用户ID，实际应从知识库记录中获取
                    user_id = 1  # TODO: 从数据库获取知识库所有者
                    
                    # 保存到新位置
                    file_info = await file_storage_service.save_file(
                        file_data=content,
                        filename=file_path.name,
                        user_id=user_id,
                        category=FileCategory.KNOWLEDGE_DOCUMENT,
                        related_id=knowledge_base_id,
                        metadata={
                            'old_path': str(file_path),
                            'migrated_at': datetime.now().isoformat(),
                            'knowledge_base_id': knowledge_base_id
                        }
                    )
                    
                    # 创建记录
                    new_record = FileRecord(
                        id=file_info['file_id'],
                        user_id=user_id,
                        original_name=file_path.name,
                        stored_name=file_info['stored_name'],
                        relative_path=file_info['relative_path'],
                        absolute_path=file_info['file_path'],
                        file_size=file_info['file_size'],
                        extension=Path(file_path.name).suffix.lower(),
                        checksum=file_info['checksum'],
                        category=FileCategory.KNOWLEDGE_DOCUMENT,
                        storage_type=StorageType.LOCAL,
                        knowledge_base_id=knowledge_base_id,
                        status=FileStatus.COMPLETED,
                        extra_metadata=file_info['metadata']
                    )
                    
                    self.db.add(new_record)
                    result['migrated'] += 1
                    
                except Exception as e:
                    result['failed'] += 1
                    result['errors'].append(f"迁移失败 {file_path}: {str(e)}")
        
        if not dry_run:
            self.db.commit()
        
        return result
    
    async def migrate_logo_files(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        迁移Logo文件
        
        从 frontend/public/logos/ 迁移到 backend/uploads/users/{user_id}/profile/ 或保持公开
        
        Args:
            dry_run: 是否为试运行
        
        Returns:
            Dict: 迁移结果统计
        """
        result = {
            'category': 'logo_files',
            'migrated': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Logo基础路径
        logo_base_path = Path("frontend/public/logos")
        
        if not logo_base_path.exists():
            result['errors'].append("Logo目录不存在")
            return result
        
        # 遍历所有Logo目录
        for logo_type_dir in logo_base_path.iterdir():
            if not logo_type_dir.is_dir():
                continue
            
            logo_type = logo_type_dir.name  # models, providers, agents, categories
            
            for file_path in logo_type_dir.iterdir():
                if not file_path.is_file():
                    continue
                
                try:
                    if dry_run:
                        result['migrated'] += 1
                        continue
                    
                    # Logo文件保持公开访问，不迁移到用户目录
                    # 只创建记录
                    
                    # 确定分类
                    if logo_type == 'models':
                        category = FileCategory.MODEL_LOGO
                    elif logo_type == 'providers':
                        category = FileCategory.SUPPLIER_LOGO
                    else:
                        category = FileCategory.USER_AVATAR
                    
                    # 计算文件信息
                    file_size = file_path.stat().st_size
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    checksum = hashlib.md5(content).hexdigest()
                    
                    # 创建记录（保持原位置）
                    new_record = FileRecord(
                        id=str(uuid.uuid4()),
                        user_id=1,  # 系统用户
                        original_name=file_path.name,
                        stored_name=file_path.name,
                        relative_path=str(file_path.relative_to(Path("frontend/public"))),
                        absolute_path=str(file_path.absolute()),
                        file_size=file_size,
                        extension=file_path.suffix.lower(),
                        checksum=checksum,
                        category=category,
                        storage_type=StorageType.PUBLIC,
                        status=FileStatus.COMPLETED,
                        extra_metadata={
                            'logo_type': logo_type,
                            'migrated_at': datetime.now().isoformat(),
                            'is_system_resource': True
                        }
                    )
                    
                    self.db.add(new_record)
                    result['migrated'] += 1
                    
                except Exception as e:
                    result['failed'] += 1
                    result['errors'].append(f"迁移失败 {file_path}: {str(e)}")
        
        if not dry_run:
            self.db.commit()
        
        return result
    
    def generate_migration_report(self) -> str:
        """
        生成迁移报告
        
        Returns:
            str: 报告文本
        """
        report_lines = [
            "=" * 60,
            "文件迁移报告",
            "=" * 60,
            f"生成时间: {datetime.now().isoformat()}",
            "",
            "迁移日志:",
            "-" * 60
        ]
        
        for log in self.migration_log:
            status_icon = "✓" if log['status'] == 'success' else "✗"
            report_lines.append(f"{status_icon} {log.get('old_id', 'N/A')} -> {log.get('new_id', 'N/A')}")
            if 'error' in log:
                report_lines.append(f"  错误: {log['error']}")
        
        report_lines.extend([
            "-" * 60,
            f"总计: {len(self.migration_log)} 个文件",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def save_migration_report(self, output_path: str = "migration_report.txt"):
        """
        保存迁移报告到文件
        
        Args:
            output_path: 输出文件路径
        """
        report = self.generate_migration_report()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)


# 迁移脚本入口
async def run_migration(db: Session, dry_run: bool = True):
    """
    运行迁移脚本
    
    Args:
        db: 数据库会话
        dry_run: 是否为试运行
    
    Returns:
        Dict: 迁移结果
    """
    service = FileMigrationService(db)
    
    print(f"开始文件迁移 (dry_run={dry_run})...")
    
    results = await service.migrate_all(dry_run)
    
    print(f"\n迁移完成!")
    print(f"总计迁移: {results['total_migrated']} 个文件")
    print(f"失败: {results['total_failed']} 个文件")
    
    # 保存报告
    if not dry_run:
        service.save_migration_report("backend/migration_report.txt")
        print("迁移报告已保存到: backend/migration_report.txt")
    
    return results


# 使用示例
if __name__ == "__main__":
    import asyncio
    from app.core.database import SessionLocal
    
    # 先试运行
    db = SessionLocal()
    try:
        print("=== 试运行模式 ===")
        asyncio.run(run_migration(db, dry_run=True))
        
        # 确认后执行实际迁移
        # print("\n=== 实际迁移 ===")
        # asyncio.run(run_migration(db, dry_run=False))
    finally:
        db.close()
