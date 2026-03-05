#!/usr/bin/env python3
"""
模型下载脚本
用于下载知识库所需的Embedding模型和重排序模型
并将它们统一管理到应用目录下
"""

import os
import sys
import shutil
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 模型配置
MODELS_CONFIG = {
    "embedding": {
        "name": "BAAI/bge-large-zh-v1.5",
        "local_path": "BAAI/bge-large-zh-v1.5",
        "description": "Embedding模型，用于文档向量化"
    },
    "reranker": {
        "name": "BAAI/bge-reranker-large",
        "local_path": "BAAI/bge-reranker-large",
        "description": "重排序模型，用于搜索结果精排"
    }
}


def get_models_dir():
    """获取应用模型目录"""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(backend_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


def get_hf_cache_dir():
    """获取HuggingFace缓存目录"""
    return os.path.expanduser("~/.cache/huggingface/hub")


def check_model_in_cache(model_name):
    """检查模型是否在HuggingFace缓存中"""
    cache_dir = get_hf_cache_dir()
    model_id = model_name.replace("/", "--")
    model_path = os.path.join(cache_dir, f"models--{model_id}")
    return os.path.exists(model_path)


def copy_model_from_cache(model_name, target_dir):
    """从HuggingFace缓存复制模型到目标目录"""
    cache_dir = get_hf_cache_dir()
    model_id = model_name.replace("/", "--")
    cache_model_dir = os.path.join(cache_dir, f"models--{model_id}")
    
    if not os.path.exists(cache_model_dir):
        return False
    
    # 查找snapshots目录下的模型文件
    snapshots_dir = os.path.join(cache_model_dir, "snapshots")
    if not os.path.exists(snapshots_dir):
        return False
    
    # 获取最新的snapshot
    snapshots = os.listdir(snapshots_dir)
    if not snapshots:
        return False
    
    latest_snapshot = os.path.join(snapshots_dir, snapshots[0])
    
    # 创建目标目录
    os.makedirs(target_dir, exist_ok=True)
    
    # 复制模型文件
    for item in os.listdir(latest_snapshot):
        src = os.path.join(latest_snapshot, item)
        dst = os.path.join(target_dir, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    
    return True


def download_model(model_name, target_dir):
    """下载模型到目标目录"""
    print(f"正在下载模型: {model_name}")
    print(f"目标目录: {target_dir}")
    
    try:
        # 尝试使用huggingface_hub下载
        from huggingface_hub import snapshot_download
        
        os.makedirs(target_dir, exist_ok=True)
        
        snapshot_download(
            repo_id=model_name,
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print(f"✓ 模型下载成功: {model_name}")
        return True
        
    except Exception as e:
        print(f"✗ 模型下载失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("知识库模型下载工具")
    print("=" * 60)
    
    models_dir = get_models_dir()
    print(f"模型存储目录: {models_dir}")
    print()
    
    success_count = 0
    
    for model_type, config in MODELS_CONFIG.items():
        print(f"\n[{model_type.upper()}] {config['description']}")
        print(f"模型名称: {config['name']}")
        
        target_dir = os.path.join(models_dir, config['local_path'])
        
        # 检查是否已存在
        if os.path.exists(target_dir) and os.listdir(target_dir):
            print(f"✓ 模型已存在: {target_dir}")
            success_count += 1
            continue
        
        # 检查是否在HuggingFace缓存中
        if check_model_in_cache(config['name']):
            print(f"发现模型在HuggingFace缓存中，正在复制...")
            if copy_model_from_cache(config['name'], target_dir):
                print(f"✓ 模型复制成功: {target_dir}")
                success_count += 1
                continue
        
        # 尝试下载
        print(f"正在下载模型...")
        if download_model(config['name'], target_dir):
            success_count += 1
        else:
            print(f"✗ 模型下载失败，请手动下载")
    
    print("\n" + "=" * 60)
    print(f"下载完成: {success_count}/{len(MODELS_CONFIG)} 个模型")
    print("=" * 60)
    
    return success_count == len(MODELS_CONFIG)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
