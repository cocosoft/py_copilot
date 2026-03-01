"""
添加任务执行追踪字段

Revision ID: 005_add_task_execution_fields
Revises: 004_add_capability_center_support
Create Date: 2026-03-01 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_add_task_execution_fields'
down_revision = '004_add_capability_center_support'
branch_labels = None
depends_on = None


def upgrade():
    """
    升级数据库，添加执行追踪相关字段
    """
    # tasks 表添加执行追踪ID字段（SQLite兼容版本）
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.add_column(
            sa.Column('execution_trace_id', sa.String(36), nullable=True)
        )
        batch_op.create_index('idx_tasks_trace_id', ['execution_trace_id'])
    
    # task_skills 表添加执行日志关联字段（SQLite兼容版本，无外键约束）
    with op.batch_alter_table('task_skills') as batch_op:
        batch_op.add_column(
            sa.Column('execution_log_id', sa.Integer, nullable=True)
        )
        batch_op.add_column(
            sa.Column('node_status', sa.String(20), default='pending')
        )
        batch_op.add_column(
            sa.Column('started_at', sa.DateTime, nullable=True)
        )
        batch_op.add_column(
            sa.Column('completed_at', sa.DateTime, nullable=True)
        )
        # 创建索引
        batch_op.create_index('idx_task_skills_log', ['execution_log_id'])
        batch_op.create_index('idx_task_skills_node_status', ['node_status'])


def downgrade():
    """
    降级数据库
    """
    with op.batch_alter_table('task_skills') as batch_op:
        batch_op.drop_index('idx_task_skills_node_status')
        batch_op.drop_index('idx_task_skills_log')
        batch_op.drop_column('completed_at')
        batch_op.drop_column('started_at')
        batch_op.drop_column('node_status')
        batch_op.drop_column('execution_log_id')
    
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.drop_index('idx_tasks_trace_id')
        batch_op.drop_column('execution_trace_id')
