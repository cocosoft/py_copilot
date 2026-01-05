#!/bin/bash

# 测试脚本 - 验证部署脚本语法和基本功能

set -e

# 定义颜色用于输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 测试脚本语法
test_script_syntax() {
    local script_path="$1"
    local script_name=$(basename "$script_path")
    
    print_info "测试脚本语法: $script_name"
    
    # 检查脚本是否存在
    if [ ! -f "$script_path" ]; then
        print_error "脚本文件不存在: $script_path"
        return 1
    fi
    
    # 检查文件权限
    if [ ! -x "$script_path" ]; then
        print_warning "脚本文件没有执行权限: $script_path"
    fi
    
    # 使用shellcheck检查语法（如果可用）
    if command -v shellcheck &> /dev/null; then
        print_info "使用shellcheck检查脚本语法..."
        if ! shellcheck "$script_path"; then
            print_error "脚本语法检查失败: $script_name"
            return 1
        fi
    else
        print_warning "shellcheck未安装，跳过详细语法检查"
    fi
    
    # 检查脚本是否包含基本函数
    if ! grep -q "main()" "$script_path"; then
        print_error "脚本中未找到main()函数: $script_name"
        return 1
    fi
    
    print_success "脚本语法检查通过: $script_name"
    return 0
}

# 测试脚本模拟执行（不实际执行部署）
test_script_simulation() {
    local script_path="$1"
    local script_name=$(basename "$script_path")
    
    print_info "模拟执行脚本: $script_name"
    
    # 提取关键函数和逻辑，不实际执行
    local temp_script=$(mktemp)
    
    # 创建模拟脚本，只包含函数定义和基本逻辑，不包含实际执行
    grep -v "^[[:space:]]*# 启动容器" "$script_path" > "$temp_script"
    grep -v "^[[:space:]]*docker run" "$temp_script" > "$temp_script"
    grep -v "^[[:space:]]*docker build" "$temp_script" > "$temp_script"
    grep -v "^[[:space:]]*docker stop" "$temp_script" > "$temp_script"
    grep -v "^[[:space:]]*curl" "$temp_script" > "$temp_script"
    
    # 检查模拟脚本语法
    if bash -n "$temp_script" 2>/dev/null; then
        print_success "模拟执行检查通过: $script_name"
        rm "$temp_script"
        return 0
    else
        print_error "模拟执行检查失败: $script_name"
        rm "$temp_script"
        return 1
    fi
}

# 测试环境变量和路径
test_environment() {
    print_info "检查部署环境..."
    
    # 检查Docker是否可用
    if command -v docker &> /dev/null; then
        print_success "Docker已安装"
    else
        print_warning "Docker未安装或不在PATH中"
    fi
    
    # 检查Node.js是否可用
    if command -v node &> /dev/null; then
        print_success "Node.js已安装"
    else
        print_warning "Node.js未安装或不在PATH中"
    fi
    
    # 检查项目结构
    if [ -d "./frontend" ]; then
        print_success "前端代码目录存在"
    else
        print_warning "前端代码目录不存在"
    fi
    
    if [ -d "./backend" ]; then
        print_success "后端代码目录存在"
    else
        print_warning "后端代码目录不存在"
    fi
    
    # 检查Dockerfile
    if [ -f "./Dockerfile.backend" ]; then
        print_success "后端Dockerfile存在"
    else
        print_warning "后端Dockerfile不存在"
    fi
    
    if [ -f "./Dockerfile.frontend" ]; then
        print_success "前端Dockerfile存在"
    else
        print_warning "前端Dockerfile不存在"
    fi
    
    return 0
}

# 主函数
main() {
    print_info "开始测试部署脚本..."
    
    # 测试环境
    test_environment
    
    # 测试后端部署脚本
    if [ -f "./scripts/deploy-backend.sh" ]; then
        test_script_syntax "./scripts/deploy-backend.sh"
        test_script_simulation "./scripts/deploy-backend.sh"
    else
        print_error "后端部署脚本不存在: ./scripts/deploy-backend.sh"
    fi
    
    # 测试前端部署脚本
    if [ -f "./scripts/deploy-frontend.sh" ]; then
        test_script_syntax "./scripts/deploy-frontend.sh"
        test_script_simulation "./scripts/deploy-frontend.sh"
    else
        print_error "前端部署脚本不存在: ./scripts/deploy-frontend.sh"
    fi
    
    print_success "部署脚本测试完成"
}

# 执行主函数
main