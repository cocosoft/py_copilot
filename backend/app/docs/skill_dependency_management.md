# Py Copilot 技能依赖管理规范

## 📋 文档概述

本文档定义了Py Copilot项目的技能依赖管理规范，包括依赖声明、安装、冲突解决、版本管理等机制。旨在确保技能依赖管理的标准化和自动化。

## 🎯 设计目标

### 1. 自动化管理
- **自动依赖解析**：自动识别和安装所需依赖
- **冲突检测**：自动检测和解决依赖冲突
- **版本管理**：支持灵活的版本控制策略

### 2. 安全性保障
- **依赖验证**：验证依赖来源和完整性
- **安全扫描**：自动扫描依赖安全漏洞
- **权限控制**：控制依赖安装权限

### 3. 用户体验
- **简化安装**：一键安装，自动处理依赖
- **透明管理**：清晰的依赖状态和变更信息
- **问题诊断**：详细的依赖问题诊断信息

## 🏗️ 依赖管理架构

### 1. 依赖声明格式

#### 基础依赖声明
```json
{
  "dependencies": [
    {
      "package_name": "p5.js",
      "version": "^1.7.0",
      "required": true,
      "description": "JavaScript图形库，用于算法艺术生成",
      "source": "npm",
      "checksum": "sha256-abc123..."
    },
    {
      "package_name": "canvas",
      "version": "^2.11.0",
      "required": true,
      "description": "Node.js画布库",
      "source": "npm"
    }
  ]
}
```

#### 完整依赖规范
```python
class SkillDependency(BaseModel):
    """技能依赖定义"""
    package_name: str = Field(..., description="依赖包名称")
    version: str = Field(..., description="版本要求，支持语义化版本")
    required: bool = Field(True, description="是否必需依赖")
    description: Optional[str] = Field(None, description="依赖描述")
    source: str = Field("pypi", description="依赖来源：pypi, npm, git, local")
    checksum: Optional[str] = Field(None, description="完整性校验和")
    environment: Optional[str] = Field(None, description="运行环境要求")
    
    # 高级配置
    pre_install_script: Optional[str] = Field(None, description="安装前脚本")
    post_install_script: Optional[str] = Field(None, description="安装后脚本")
    conflict_resolution: Optional[str] = Field(None, description="冲突解决策略")
```

### 2. 依赖来源支持

#### 支持的依赖来源
- **PyPI**：Python包管理（主要）
- **NPM**：Node.js包管理
- **Git**：Git仓库直接安装
- **Local**：本地文件或目录
- **Custom**：自定义包源

#### 来源配置示例
```python
# PyPI依赖
{
    "package_name": "requests",
    "version": "^2.28.0",
    "source": "pypi"
}

# NPM依赖（前端技能）
{
    "package_name": "p5",
    "version": "^1.7.0", 
    "source": "npm"
}

# Git依赖
{
    "package_name": "custom-library",
    "version": "main",
    "source": "git",
    "repository": "https://github.com/user/repo.git"
}
```

## 🔧 依赖管理流程

### 1. 依赖安装流程

```python
class DependencyManager:
    def install_dependencies(self, skill_id: str, dependencies: List[SkillDependency]):
        """安装技能依赖"""
        
        # 1. 依赖解析
        resolved_deps = self.resolve_dependencies(dependencies)
        
        # 2. 冲突检测
        conflicts = self.detect_conflicts(resolved_deps)
        if conflicts:
            return self.handle_conflicts(conflicts)
        
        # 3. 安装前检查
        if not self.pre_install_check(resolved_deps):
            raise DependencyError("安装前检查失败")
        
        # 4. 执行安装
        installation_results = []
        for dep in resolved_deps:
            try:
                result = self.install_single_dependency(dep)
                installation_results.append(result)
            except Exception as e:
                # 记录失败，继续安装其他依赖
                installation_results.append({
                    "package": dep.package_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        # 5. 安装后验证
        self.post_install_verification(installation_results)
        
        return installation_results
```

### 2. 冲突解决策略

#### 冲突类型
1. **版本冲突**：同一包不同版本要求
2. **依赖循环**：循环依赖关系
3. **环境冲突**：运行环境不兼容

#### 解决策略
```python
class ConflictResolver:
    def resolve_version_conflict(self, package: str, versions: List[str]) -> str:
        """解决版本冲突"""
        # 策略1：选择最高兼容版本
        compatible_versions = self.find_compatible_versions(versions)
        if compatible_versions:
            return max(compatible_versions)
        
        # 策略2：询问用户选择
        return self.prompt_user_selection(package, versions)
    
    def resolve_dependency_cycle(self, cycle: List[str]) -> List[str]:
        """解决依赖循环"""
        # 策略：打破循环，选择关键依赖
        critical_dep = self.identify_critical_dependency(cycle)
        return self.break_cycle(cycle, critical_dep)
```

## 🛡️ 安全机制

### 1. 依赖验证

#### 完整性校验
```python
def verify_dependency_integrity(self, dep: SkillDependency, file_path: str) -> bool:
    """验证依赖完整性"""
    if dep.checksum:
        actual_checksum = self.calculate_checksum(file_path)
        return actual_checksum == dep.checksum
    return True  # 没有校验和时跳过验证
```

#### 来源验证
```python
def verify_dependency_source(self, dep: SkillDependency) -> bool:
    """验证依赖来源"""
    trusted_sources = ["pypi.org", "npmjs.com", "github.com"]
    
    if dep.source == "git":
        return any(trusted in dep.repository for trusted in trusted_sources)
    
    return dep.source in ["pypi", "npm"]  # 默认信任官方源
```

### 2. 安全扫描

```python
class SecurityScanner:
    def scan_dependencies(self, dependencies: List[SkillDependency]) -> SecurityReport:
        """扫描依赖安全漏洞"""
        report = SecurityReport()
        
        for dep in dependencies:
            vulnerabilities = self.check_vulnerability_db(dep)
            if vulnerabilities:
                report.add_vulnerabilities(dep, vulnerabilities)
        
        return report
```

## 📊 依赖状态管理

### 1. 依赖状态跟踪

```python
class DependencyState:
    def __init__(self):
        self.installed_deps = {}  # 已安装依赖
        self.dep_graph = {}       # 依赖关系图
        self.conflict_log = []    # 冲突记录
        
    def track_installation(self, skill_id: str, dependencies: List[SkillDependency]):
        """跟踪依赖安装状态"""
        for dep in dependencies:
            self.installed_deps[dep.package_name] = {
                "skill_id": skill_id,
                "version": dep.version,
                "installed_at": datetime.now(),
                "status": "installed"
            }
```

### 2. 依赖使用统计

```python
class DependencyUsageTracker:
    def record_usage(self, package_name: str, skill_id: str):
        """记录依赖使用情况"""
        # 更新使用统计
        self.usage_stats[package_name] = self.usage_stats.get(package_name, 0) + 1
        
        # 记录技能-依赖关联
        self.skill_dep_usage[skill_id].add(package_name)
```

## 🔄 维护和优化

### 1. 依赖清理机制

```python
def cleanup_unused_dependencies(self):
    """清理未使用的依赖"""
    used_deps = set()
    
    # 收集正在使用的依赖
    for skill_id in self.active_skills:
        skill_deps = self.get_skill_dependencies(skill_id)
        used_deps.update(dep.package_name for dep in skill_deps)
    
    # 清理未使用的依赖
    for package_name in list(self.installed_deps.keys()):
        if package_name not in used_deps:
            self.uninstall_dependency(package_name)
```

### 2. 依赖更新策略

```python
def update_dependencies(self, strategy: str = "conservative"):
    """更新依赖策略"""
    if strategy == "conservative":
        # 保守策略：只更新补丁版本
        return self.update_patch_versions()
    elif strategy == "balanced":
        # 平衡策略：更新小版本
        return self.update_minor_versions()
    elif strategy == "aggressive":
        # 激进策略：更新大版本
        return self.update_major_versions()
```

## 🚀 实施指南

### 1. 技能开发者指南

#### 依赖声明最佳实践
```json
{
  "dependencies": [
    {
      "package_name": "numpy",
      "version": "^1.24.0",
      "required": true,
      "description": "数值计算库",
      "source": "pypi"
    }
  ],
  "dev_dependencies": [
    {
      "package_name": "pytest",
      "version": "^7.0.0",
      "required": false,
      "description": "测试框架",
      "source": "pypi"
    }
  ]
}
```

### 2. 系统管理员指南

#### 配置依赖管理
```yaml
# config/dependencies.yaml
dependency_management:
  sources:
    pypi: "https://pypi.org/simple"
    npm: "https://registry.npmjs.org"
    
  security:
    enable_scanning: true
    vulnerability_db: "https://vulndb.example.com"
    
  cleanup:
    auto_cleanup: true
    cleanup_interval: "7d"
    
  updates:
    strategy: "balanced"
    auto_update: false
```

## 📝 总结

### 规范特点
- **全面性**：覆盖依赖管理的全生命周期
- **安全性**：内置安全验证和扫描机制
- **灵活性**：支持多种依赖来源和版本策略
- **自动化**：提供自动化的依赖管理流程

### 实施价值
- **提升可靠性**：确保依赖安装的稳定性和一致性
- **增强安全性**：防范依赖相关的安全风险
- **简化运维**：降低依赖管理的复杂度和工作量
- **促进生态**：为技能生态系统提供坚实的基础设施

本规范将随着项目发展不断完善，为Py Copilot的技能依赖管理提供标准化指导。

---

**文档版本**：v1.0  
**创建日期**：2026-01-26  
**维护团队**：Py Copilot开发团队