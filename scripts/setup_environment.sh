#!/bin/bash
# 环境准备脚本 - OP-001
# 用于初始化向量化管理模块的生产环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装"
        exit 1
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 创建必要的目录
setup_directories() {
    log_info "创建必要的目录..."
    
    directories=(
        "data/postgres-primary"
        "data/postgres-replica"
        "data/redis-master"
        "data/redis-slave"
        "data/etcd"
        "data/minio"
        "data/milvus"
        "data/prometheus"
        "data/grafana"
        "data/elasticsearch"
        "logs/backend"
        "logs/nginx"
        "ssl"
        "backups"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_success "创建目录: $dir"
    done
}

# 生成SSL证书
generate_ssl_certificates() {
    log_info "生成SSL证书..."
    
    if [ ! -f "ssl/server.crt" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/server.key \
            -out ssl/server.crt \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=Vectorization/CN=localhost"
        log_success "SSL证书生成完成"
    else
        log_warning "SSL证书已存在，跳过生成"
    fi
}

# 设置环境变量
setup_environment_variables() {
    log_info "设置环境变量..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_warning "请编辑 .env 文件，设置实际的环境变量值"
        else
            log_error ".env.example 文件不存在"
            exit 1
        fi
    else
        log_warning ".env 文件已存在"
    fi
}

# 检查系统资源
check_system_resources() {
    log_info "检查系统资源..."
    
    # 检查内存
    total_memory=$(free -m | awk '/^Mem:/{print $2}')
    if [ $total_memory -lt 8192 ]; then
        log_warning "系统内存不足8GB，建议至少8GB内存"
    else
        log_success "系统内存: ${total_memory}MB"
    fi
    
    # 检查磁盘空间
    available_space=$(df -m . | awk 'NR==2 {print $4}')
    if [ $available_space -lt 51200 ]; then
        log_warning "可用磁盘空间不足50GB，建议至少50GB"
    else
        log_success "可用磁盘空间: ${available_space}MB"
    fi
    
    # 检查CPU核心数
    cpu_cores=$(nproc)
    if [ $cpu_cores -lt 4 ]; then
        log_warning "CPU核心数不足4核，建议至少4核"
    else
        log_success "CPU核心数: $cpu_cores"
    fi
}

# 检查必需的端口
check_required_ports() {
    log_info "检查必需的端口..."
    
    ports=(5432 5433 6379 6380 8000 9000 9001 9090 9091 3000 5601 16686 9200)
    
    for port in "${ports[@]}"; do
        if check_port $port; then
            log_success "端口 $port 可用"
        fi
    done
}

# 拉取Docker镜像
pull_docker_images() {
    log_info "拉取Docker镜像..."
    
    docker-compose pull
    log_success "Docker镜像拉取完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    # 启动PostgreSQL
    docker-compose up -d postgres-primary
    
    # 等待PostgreSQL启动
    log_info "等待PostgreSQL启动..."
    sleep 10
    
    # 运行数据库迁移
    docker-compose run --rm backend alembic upgrade head
    
    log_success "数据库初始化完成"
}

# 验证环境
verify_environment() {
    log_info "验证环境..."
    
    # 检查Docker服务
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行"
        exit 1
    fi
    log_success "Docker服务运行正常"
    
    # 检查Docker Compose
    if ! docker-compose version &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    log_success "Docker Compose已安装"
    
    log_success "环境验证通过"
}

# 显示使用说明
show_usage() {
    echo ""
    echo "========================================"
    echo "  向量化管理模块 - 环境准备完成"
    echo "========================================"
    echo ""
    echo "使用方法:"
    echo "  1. 编辑 .env 文件，设置环境变量"
    echo "  2. 启动服务: docker-compose up -d"
    echo "  3. 查看日志: docker-compose logs -f"
    echo ""
    echo "访问地址:"
    echo "  - API服务: http://localhost:8000"
    echo "  - 前端界面: http://localhost"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000"
    echo "  - Kibana: http://localhost:5601"
    echo "  - Jaeger: http://localhost:16686"
    echo ""
    echo "默认账号:"
    echo "  - Grafana: admin/admin"
    echo ""
    echo "========================================"
}

# 主函数
main() {
    echo "========================================"
    echo "  向量化管理模块 - 环境准备脚本"
    echo "========================================"
    echo ""
    
    # 检查必需的命令
    check_command docker
    check_command docker-compose
    
    # 执行设置步骤
    check_system_resources
    check_required_ports
    setup_directories
    generate_ssl_certificates
    setup_environment_variables
    verify_environment
    pull_docker_images
    
    # 询问是否初始化数据库
    read -p "是否初始化数据库? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        init_database
    fi
    
    show_usage
    
    log_success "环境准备完成!"
}

# 运行主函数
main
