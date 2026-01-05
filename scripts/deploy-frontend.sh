#!/bin/bash

# 前端/桌面应用部署脚本
# 部署基于React的前端Web应用和桌面应用

set -e

# 定义颜色用于输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 定义服务名称和配置
FRONTEND_SERVICE_NAME="py-copilot-frontend"
FRONTEND_IMAGE_NAME="py-copilot-frontend"
FRONTEND_CONTAINER_NAME="py-copilot-frontend-container"
FRONTEND_PORT=80
DESKTOP_APP_NAME="py-copilot-desktop"
DESKTOP_APP_PATH="./desktop/build"
DATA_DIR="./data/frontend"
LOG_DIR="./logs/frontend"

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

# 检查Node.js和npm是否安装
check_node() {
    print_info "检查Node.js和npm安装..."
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js未安装，请先安装Node.js"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        print_error "npm未安装，请先安装npm"
        exit 1
    fi
    
    # 检查Node.js版本
    NODE_VERSION=$(node -v)
    print_success "Node.js已安装，版本: $NODE_VERSION"
}

# 检查Docker是否安装
check_docker() {
    print_info "检查Docker安装..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker未运行，请先启动Docker"
        exit 1
    fi
    
    print_success "Docker已安装并运行"
}

# 创建必要的目录
create_directories() {
    print_info "创建必要目录..."
    mkdir -p "$DATA_DIR" "$LOG_DIR"
    
    # 设置目录权限
    chmod -R 755 "$DATA_DIR" "$LOG_DIR"
    
    print_success "目录创建完成"
}

# 安装依赖
install_dependencies() {
    print_info "安装前端依赖..."
    
    # 检查frontend目录是否存在
    if [ ! -d "./frontend" ]; then
        print_error "frontend目录不存在，请确保在项目根目录运行此脚本"
        exit 1
    fi
    
    cd frontend
    
    # 安装依赖
    npm install --production || {
        print_error "依赖安装失败"
        exit 1
    }
    
    cd ..
    
    print_success "依赖安装完成"
}

# 构建前端应用
build_frontend() {
    print_info "构建前端应用..."
    
    cd frontend
    
    # 设置环境变量用于生产构建
    export NODE_ENV=production
    
    # 运行构建命令
    npm run build || {
        print_error "前端构建失败"
        exit 1
    }
    
    # 确认构建目录存在
    if [ ! -d "./dist" ]; then
        print_error "构建目录不存在，构建可能失败"
        exit 1
    fi
    
    cd ..
    
    print_success "前端应用构建完成"
}

# 构建Docker镜像
build_image() {
    print_info "构建前端Docker镜像..."
    
    # 构建镜像
    docker build -f Dockerfile.frontend -t "$FRONTEND_IMAGE_NAME:latest" . || {
        print_error "构建镜像失败"
        exit 1
    }
    
    print_success "镜像构建完成: $FRONTEND_IMAGE_NAME:latest"
}

# 停止现有容器
stop_existing_container() {
    print_info "检查现有容器..."
    
    if docker ps -a --format '{{.Names}}' | grep -q "^$FRONTEND_CONTAINER_NAME$"; then
        print_info "停止现有容器: $FRONTEND_CONTAINER_NAME"
        docker stop "$FRONTEND_CONTAINER_NAME" || true
        docker rm "$FRONTEND_CONTAINER_NAME" || true
        print_success "已移除现有容器"
    fi
}

# 启动容器
start_container() {
    print_info "启动前端容器..."
    
    # 启动容器
    docker run -d \
        --name "$FRONTEND_CONTAINER_NAME" \
        -p "$FRONTEND_PORT:80" \
        -v "$(pwd)/$DATA_DIR:/usr/share/nginx/html/data" \
        -v "$(pwd)/$LOG_DIR:/var/log/nginx" \
        --restart unless-stopped \
        "$FRONTEND_IMAGE_NAME:latest"
    
    if [ $? -eq 0 ]; then
        print_success "容器启动成功"
    else
        print_error "容器启动失败"
        exit 1
    fi
}

# 检查服务健康状态
check_health() {
    print_info "检查服务健康状态..."
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    # 检查容器状态
    if ! docker ps --format '{{.Names}}' | grep -q "^$FRONTEND_CONTAINER_NAME$"; then
        print_error "容器未运行"
        return 1
    fi
    
    # 检查健康端点
    print_info "检查健康端点..."
    for i in {1..30}; do
        if curl -f -s http://localhost:$FRONTEND_PORT/ > /dev/null; then
            print_success "服务健康检查通过"
            return 0
        fi
        print_info "等待服务响应... (尝试 $i/30)"
        sleep 2
    done
    
    print_error "服务健康检查失败"
    return 1
}

# 构建桌面应用
build_desktop() {
    print_info "检查桌面应用构建..."
    
    # 检查是否存在桌面应用构建目录
    if [ ! -d "./electron" ] && [ ! -d "./desktop" ]; then
        print_warning "未找到桌面应用源码，跳过桌面应用构建"
        return 0
    fi
    
    # 如果存在electron目录，使用electron-builder构建
    if [ -d "./electron" ]; then
        print_info "构建Electron桌面应用..."
        
        cd electron
        
        # 安装依赖
        npm install --production || {
            print_error "Electron应用依赖安装失败"
            return 1
        }
        
        # 运行构建
        npm run build || {
            print_error "Electron应用构建失败"
            return 1
        }
        
        cd ..
        
        print_success "Electron应用构建完成"
    fi
    
    # 如果存在desktop目录，尝试构建
    if [ -d "./desktop" ]; then
        print_info "构建桌面应用..."
        
        cd desktop
        
        # 根据具体构建工具执行相应命令
        if [ -f "./package.json" ]; then
            # 安装依赖
            npm install --production || {
                print_error "桌面应用依赖安装失败"
                return 1
            }
            
            # 运行构建
            npm run build || {
                print_error "桌面应用构建失败"
                return 1
            }
        fi
        
        cd ..
        
        print_success "桌面应用构建完成"
    fi
    
    return 0
}

# 显示日志
show_logs() {
    print_info "显示服务日志..."
    docker logs -f "$FRONTEND_CONTAINER_NAME"
}

# 主函数
main() {
    print_info "开始部署前端/桌面应用..."
    
    # 检查Node.js
    check_node
    
    # 检查Docker
    check_docker
    
    # 创建目录
    create_directories
    
    # 安装依赖
    install_dependencies
    
    # 构建前端应用
    build_frontend
    
    # 构建桌面应用（如果存在）
    build_desktop
    
    # 构建镜像
    build_image
    
    # 停止现有容器
    stop_existing_container
    
    # 启动容器
    start_container
    
    # 检查健康状态
    if check_health; then
        print_success "部署完成！"
        echo ""
        print_info "服务访问地址:"
        echo "  - Web应用地址: http://localhost:$FRONTEND_PORT"
        echo ""
        print_info "常用命令:"
        echo "  - 查看日志: docker logs -f $FRONTEND_CONTAINER_NAME"
        echo "  - 重启服务: docker restart $FRONTEND_CONTAINER_NAME"
        echo "  - 停止服务: docker stop $FRONTEND_CONTAINER_NAME"
        echo ""
        print_info "查看实时日志请运行: $0 --logs"
    else
        print_error "部署失败，请检查日志"
        echo ""
        print_info "查看错误日志请运行: docker logs $FRONTEND_CONTAINER_NAME"
        exit 1
    fi
}

# 处理命令行参数
if [[ "$1" == "--logs" ]]; then
    show_logs
else
    main
fi