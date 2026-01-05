#!/bin/bash

# 后端API部署脚本
# 部署基于FastAPI的Python后端API服务

set -e

# 定义颜色用于输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 定义服务名称和配置
SERVICE_NAME="py-copilot-backend"
IMAGE_NAME="py-copilot-backend"
CONTAINER_NAME="py-copilot-backend-container"
PORT=8000
ENV_FILE=".env.production"
DATA_DIR="./data/backend"
LOG_DIR="./logs/backend"

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

# 构建Docker镜像
build_image() {
    print_info "构建后端Docker镜像..."
    
    # 检查是否存在.env.production文件
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "未找到环境配置文件 $ENV_FILE，使用默认配置"
        ENV_FILE=""
    fi
    
    # 构建镜像
    docker build -f Dockerfile.backend -t "$IMAGE_NAME:latest" . || {
        print_error "构建镜像失败"
        exit 1
    }
    
    print_success "镜像构建完成: $IMAGE_NAME:latest"
}

# 停止现有容器
stop_existing_container() {
    print_info "检查现有容器..."
    
    if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
        print_info "停止现有容器: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME" || true
        docker rm "$CONTAINER_NAME" || true
        print_success "已移除现有容器"
    fi
}

# 启动容器
start_container() {
    print_info "启动后端容器..."
    
    # 设置环境变量
    ENV_PARAMS=""
    if [ -f "$ENV_FILE" ]; then
        ENV_PARAMS="--env-file $ENV_FILE"
    fi
    
    # 启动容器
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "$PORT:8000" \
        $ENV_PARAMS \
        -v "$(pwd)/$DATA_DIR:/app/data" \
        -v "$(pwd)/$LOG_DIR:/app/logs" \
        --restart unless-stopped \
        "$IMAGE_NAME:latest"
    
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
    if ! docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
        print_error "容器未运行"
        return 1
    fi
    
    # 检查健康端点
    print_info "检查健康端点..."
    for i in {1..30}; do
        if curl -f -s http://localhost:$PORT/health > /dev/null; then
            print_success "服务健康检查通过"
            return 0
        fi
        print_info "等待服务响应... (尝试 $i/30)"
        sleep 2
    done
    
    print_error "服务健康检查失败"
    return 1
}

# 显示日志
show_logs() {
    print_info "显示服务日志..."
    docker logs -f "$CONTAINER_NAME"
}

# 主函数
main() {
    print_info "开始部署后端API服务..."
    
    # 检查Docker
    check_docker
    
    # 创建目录
    create_directories
    
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
        echo "  - API地址: http://localhost:$PORT"
        echo "  - API文档: http://localhost:$PORT/docs"
        echo ""
        print_info "常用命令:"
        echo "  - 查看日志: docker logs -f $CONTAINER_NAME"
        echo "  - 重启服务: docker restart $CONTAINER_NAME"
        echo "  - 停止服务: docker stop $CONTAINER_NAME"
        echo ""
        print_info "查看实时日志请运行: $0 --logs"
    else
        print_error "部署失败，请检查日志"
        echo ""
        print_info "查看错误日志请运行: docker logs $CONTAINER_NAME"
        exit 1
    fi
}

# 处理命令行参数
if [[ "$1" == "--logs" ]]; then
    show_logs
else
    main
fi