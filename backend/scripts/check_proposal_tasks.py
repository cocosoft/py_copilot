"""
检查 SETTINGS_MERGE_PROPOSAL_V8.md 中的任务完成情况

对比实施文档 SETTINGS_MERGE_IMPLEMENTATION_V8.md 和实际代码
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def check_data_model_extensions():
    """检查数据模型扩展"""
    print("=" * 60)
    print("1. 数据模型扩展检查")
    print("=" * 60)

    engine = create_engine(settings.database_url)
    results = {}

    with engine.connect() as conn:
        # 检查 Tool 模型扩展
        result = conn.execute(text("PRAGMA table_info(tools)"))
        tool_columns = [row[1] for row in result.fetchall()]
        official_fields = ['source', 'is_official', 'is_builtin', 'official_badge',
                          'is_system', 'is_protected', 'allow_disable', 'allow_edit',
                          'min_app_version', 'update_mode']
        results['tool_official'] = all(f in tool_columns for f in official_fields)
        print(f"  [{'✅' if results['tool_official'] else '❌'}] Tool模型官方能力字段")

        # 检查 Skill 模型扩展
        result = conn.execute(text("PRAGMA table_info(skills)"))
        skill_columns = [row[1] for row in result.fetchall()]
        results['skill_official'] = all(f in skill_columns for f in official_fields)
        print(f"  [{'✅' if results['skill_official'] else '❌'}] Skill模型官方能力字段")

        # 检查 Agent 模型扩展
        result = conn.execute(text("PRAGMA table_info(agents)"))
        agent_columns = [row[1] for row in result.fetchall()]
        agent_fields = ['agent_type', 'primary_capability_id', 'primary_capability_type',
                       'capability_orchestration', 'is_official', 'is_template', 'template_category']
        results['agent_type'] = all(f in agent_columns for f in agent_fields)
        print(f"  [{'✅' if results['agent_type'] else '❌'}] Agent模型类型字段")

        # 检查关联表
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_tool_associations'"
        ))
        results['assoc_table'] = result.fetchone() is not None
        print(f"  [{'✅' if results['assoc_table'] else '❌'}] 关联表创建")

    return all(results.values())


def check_official_capability_system():
    """检查官方能力体系"""
    print("\n" + "=" * 60)
    print("2. 官方能力体系检查")
    print("=" * 60)

    engine = create_engine(settings.database_url)
    results = {}

    with engine.connect() as conn:
        # 检查官方工具
        result = conn.execute(text("SELECT COUNT(*) FROM tools WHERE is_official = 1"))
        official_tools = result.fetchone()[0]
        results['official_tools'] = official_tools >= 5  # 至少5个官方工具
        print(f"  [{'✅' if results['official_tools'] else '❌'}] 官方工具 ({official_tools}个)")

        # 检查官方技能
        result = conn.execute(text("SELECT COUNT(*) FROM skills WHERE is_official = 1"))
        official_skills = result.fetchone()[0]
        results['official_skills'] = official_skills >= 4  # 至少4个官方技能
        print(f"  [{'✅' if results['official_skills'] else '❌'}] 官方技能 ({official_skills}个)")

        # 检查保护机制字段
        result = conn.execute(text("PRAGMA table_info(tools)"))
        columns = [row[1] for row in result.fetchall()]
        protection_fields = ['is_system', 'is_protected', 'allow_disable', 'allow_edit']
        results['protection'] = all(f in columns for f in protection_fields)
        print(f"  [{'✅' if results['protection'] else '❌'}] 保护机制字段")

    return all(results.values())


def check_capability_center():
    """检查能力中心"""
    print("\n" + "=" * 60)
    print("3. 能力中心检查")
    print("=" * 60)

    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    frontend_root = os.path.join(project_root, 'frontend')

    results = {}

    # 检查能力中心页面
    page_path = os.path.join(frontend_root, "src", "pages", "CapabilityCenter.jsx")
    results['page'] = os.path.exists(page_path)
    print(f"  [{'✅' if results['page'] else '❌'}] 能力中心页面")

    # 检查能力卡片组件
    card_path = os.path.join(frontend_root, "src", "components", "CapabilityCenter", "CapabilityCard.jsx")
    results['card'] = os.path.exists(card_path)
    print(f"  [{'✅' if results['card'] else '❌'}] 能力卡片组件")

    # 检查官方徽章展示
    if os.path.exists(card_path):
        with open(card_path, 'r', encoding='utf-8') as f:
            content = f.read()
            results['badge'] = 'official' in content.lower() or '官方' in content
    else:
        results['badge'] = False
    print(f"  [{'✅' if results['badge'] else '❌'}] 官方徽章展示")

    # 检查后端API
    try:
        from app.api.main import app
        capability_routes = [r for r in app.routes if hasattr(r, 'path') and 'capability-center' in r.path]
        results['api'] = len(capability_routes) > 0
        print(f"  [{'✅' if results['api'] else '❌'}] 能力中心API ({len(capability_routes)}个路由)")
    except Exception as e:
        print(f"  [❌] 能力中心API检查失败: {e}")
        results['api'] = False

    return all(results.values())


def check_agent_classification():
    """检查智能体分类"""
    print("\n" + "=" * 60)
    print("4. 智能体分类检查")
    print("=" * 60)

    engine = create_engine(settings.database_url)
    results = {}

    with engine.connect() as conn:
        # 检查agent_type字段
        result = conn.execute(text("PRAGMA table_info(agents)"))
        columns = [row[1] for row in result.fetchall()]
        results['agent_type'] = 'agent_type' in columns
        print(f"  [{'✅' if results['agent_type'] else '❌'}] agent_type字段")

        # 检查主能力字段
        results['primary_cap'] = 'primary_capability_id' in columns and 'primary_capability_type' in columns
        print(f"  [{'✅' if results['primary_cap'] else '❌'}] 主能力字段")

        # 检查能力编排字段
        results['orchestration'] = 'capability_orchestration' in columns
        print(f"  [{'✅' if results['orchestration'] else '❌'}] 能力编排字段")

        # 检查官方智能体标识
        results['official_agent'] = 'is_official' in columns and 'is_template' in columns
        print(f"  [{'✅' if results['official_agent'] else '❌'}] 官方智能体标识")

    return all(results.values())


def check_deprecated_features():
    """检查废弃功能处理"""
    print("\n" + "=" * 60)
    print("5. 废弃功能处理检查")
    print("=" * 60)

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    results = {}

    # 检查搜索管理废弃API
    deprecated_api_path = os.path.join(project_root, "backend", "app", "api", "v1", "search_management_deprecated.py")
    results['deprecated_api'] = os.path.exists(deprecated_api_path)
    print(f"  [{'✅' if results['deprecated_api'] else '❌'}] 废弃API标记")

    # 检查前端路由重定向
    routes_path = os.path.join(project_root, "frontend", "src", "routes", "index.jsx")
    if os.path.exists(routes_path):
        with open(routes_path, 'r', encoding='utf-8') as f:
            content = f.read()
            results['redirect'] = 'RedirectToCapabilityCenter' in content
    else:
        results['redirect'] = False
    print(f"  [{'✅' if results['redirect'] else '❌'}] 前端路由重定向")

    # 检查侧边栏导航更新
    navbar_path = os.path.join(project_root, "frontend", "src", "components", "Navbar.jsx")
    if os.path.exists(navbar_path):
        with open(navbar_path, 'r', encoding='utf-8') as f:
            content = f.read()
            results['navbar'] = 'capability-center' in content or 'capabilityCenter' in content
    else:
        results['navbar'] = False
    print(f"  [{'✅' if results['navbar'] else '❌'}] 侧边栏导航更新")

    return all(results.values())


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(" SETTINGS_MERGE_PROPOSAL_V8 任务完成检查 ")
    print("=" * 60)

    all_passed = True

    # 执行所有检查
    all_passed &= check_data_model_extensions()
    all_passed &= check_official_capability_system()
    all_passed &= check_capability_center()
    all_passed &= check_agent_classification()
    all_passed &= check_deprecated_features()

    # 汇总结果
    print("\n" + "=" * 60)
    print(" 检查完成 ")
    print("=" * 60)

    if all_passed:
        print("\n✅ 所有任务已完成！")
        print("\n实施状态：")
        print("  - 数据模型扩展: ✅ 完成")
        print("  - 官方能力体系: ✅ 完成")
        print("  - 能力中心: ✅ 完成")
        print("  - 智能体分类: ✅ 完成")
        print("  - 废弃功能处理: ✅ 完成")
        return 0
    else:
        print("\n❌ 部分任务未完成，请查看详情。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
