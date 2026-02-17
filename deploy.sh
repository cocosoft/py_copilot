#!/bin/bash

# 部署脚本 - Linux/Mac

set -e

echo "========================================"
echo "Py Copilot 部署脚本"
echo "========================================"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "[错误] Docker未安装，请先安装Docker"
    exit 1
fi

echo "[信息] Docker已安装"
echo ""

# 检查Docker Compose是否可用
if ! docker compose version &> /dev/null; then
    echo "[错误] Docker Compose不可用，请确保Docker已正确安装"
    exit 1
fi

echo "[信息] Docker Compose可用"
echo ""

# 停止现有容器
echo "[信息] 停止现有容器..."
docker compose down

# 构建镜像
echo "[信息] 构建Docker镜像..."
docker compose build

if [ $? -ne 0 ]; then
    echo "[错误] 镜像构建失败"
    exit 1
fi

echo "[信息] 镜像构建成功"
echo ""

# 启动容器
echo "[信息] 启动容器..."
docker compose up -d

if [ $? -ne 0 ]; then
    echo "[错误] 容器启动失败"
    exit 1
fi

echo "[信息] 容器启动成功"
echo ""

# 等待服务就绪
echo "[信息] 等待服务就绪..."
sleep 10

# 检查服务状态
echo "[信息] 检查服务状态..."
docker compose ps

echo ""
echo "========================================"
echo "部署完成！"
echo "========================================"
echo ""
echo "前端地址: http://localhost"
echo "后端地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "查看日志: docker compose logs -f"
echo "停止服务: docker compose down"
echo ""
