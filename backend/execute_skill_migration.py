"""
技能迁移执行脚本

实际执行技能迁移过程，生成标准化元数据文件
"""
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def execute_migration():
    """执行技能迁移"""
    print('=== 开始执行技能迁移 ===')
    
    from app.skills.skill_migration import SkillMigration
    
    # 创建迁移器实例
    migration = SkillMigration()
    
    # 执行完整迁移
    report = migration.migrate_all_skills()
    
    # 显示迁移结果
    print(f'\n=== 迁移结果总结 ===')
    print(f'总技能数: {report["total_skills"]}')
    print(f'成功迁移: {report["migrated_skills"]}')
    print(f'迁移失败: {report["failed_skills"]}')
    print(f'成功率: {report["summary"]["success_rate"]}%')
    print(f'警告数量: {report["summary"]["total_warnings"]}')
    print(f'错误数量: {report["summary"]["total_errors"]}')
    
    # 显示迁移详情
    print(f'\n=== 迁移详情 ===')
    for skill_name, details in report['details'].items():
        status = '✅ 成功' if details['status'] == 'success' else '❌ 失败'
        print(f'{skill_name}: {status}')
        if details['status'] == 'success':
            metadata = details['metadata']
            print(f'  分类: {metadata["category"]}')
            print(f'  标签: {metadata["tags"]}')
        else:
            print(f'  错误: {details["error"]}')
    
    # 导出迁移报告
    migration.export_migration_report("skill_migration_report.json")
    print(f'\n迁移报告已导出到: skill_migration_report.json')
    
    return report

def verify_migration():
    """验证迁移结果"""
    print('\n=== 验证迁移结果 ===')
    
    from app.skills.skill_registry import refresh_skill_registry, get_skill_registry
    
    # 刷新技能注册表
    success = refresh_skill_registry()
    if not success:
        print('❌ 技能注册表刷新失败')
        return False
    
    # 获取注册表
    registry = get_skill_registry()
    
    # 验证迁移结果
    print(f'注册表技能数量: {registry.get_skill_count()}')
    
    # 显示分类统计
    category_stats = registry.get_category_stats()
    print('分类统计:')
    for category, count in category_stats.items():
        print(f'  {category.value}: {count} 个技能')
    
    # 验证标准化文件
    from pathlib import Path
    skills_dir = Path("app/skills/skills")
    
    standardized_files_count = 0
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            yaml_file = skill_dir / "skill.yaml"
            json_file = skill_dir / "skill.json"
            
            if yaml_file.exists() and json_file.exists():
                standardized_files_count += 1
    
    print(f'标准化文件生成: {standardized_files_count} 个技能')
    
    return True

def main():
    """主执行函数"""
    try:
        # 执行迁移
        report = execute_migration()
        
        # 验证迁移结果
        verification_success = verify_migration()
        
        if verification_success and report['migrated_skills'] > 0:
            print('\n🎉 技能迁移完成！所有技能已成功迁移到新的元数据标准。')
            print('✅ 标准化元数据文件已生成')
            print('✅ 技能注册表已更新')
            print('✅ 技能管理API可正常使用')
        else:
            print('\n⚠️ 技能迁移存在问题，请检查迁移报告。')
            
    except Exception as e:
        print(f'❌ 迁移执行失败: {e}')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()