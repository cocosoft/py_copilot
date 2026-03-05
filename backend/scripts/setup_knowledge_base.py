#!/usr/bin/env python3
"""
知识库优化部署脚本
用于安装依赖、下载模型、验证环境
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_python_version():
    """检查Python版本"""
    logger.info("检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error(f"Python版本过低: {version.major}.{version.minor}，需要>=3.8")
        return False
    logger.info(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True


def check_hardware():
    """检查硬件资源"""
    logger.info("检查硬件资源...")
    
    try:
        import psutil
        
        # CPU
        cpu_count = psutil.cpu_count()
        logger.info(f"  CPU核心数: {cpu_count}")
        
        # 内存
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        logger.info(f"  内存总量: {memory_gb:.1f} GB")
        
        # 磁盘
        disk = psutil.disk_usage("/")
        disk_gb = disk.free / (1024**3)
        logger.info(f"  磁盘剩余: {disk_gb:.1f} GB")
        
        # 检查是否满足最低要求
        if memory_gb < 8:
            logger.warning("⚠ 内存不足8GB，可能影响模型加载性能")
        if disk_gb < 10:
            logger.warning("⚠ 磁盘剩余空间不足10GB，可能无法下载模型")
        
        logger.info("✓ 硬件资源检查完成")
        return True
        
    except ImportError:
        logger.warning("未安装psutil，跳过硬件检查")
        return True


def install_dependencies():
    """安装依赖"""
    logger.info("安装依赖...")
    
    dependencies = [
        "sentence-transformers==2.2.2",
        "chromadb==0.4.15",
        "spacy==3.7.2",
        "torch>=2.0.0"
    ]
    
    for dep in dependencies:
        logger.info(f"  安装 {dep}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                check=True,
                capture_output=True
            )
            logger.info(f"  ✓ {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ {dep} 安装失败: {e}")
            return False
    
    logger.info("✓ 依赖安装完成")
    return True


def download_models():
    """下载模型"""
    logger.info("下载模型...")
    
    models_to_download = [
        {
            "name": "BAAI/bge-large-zh-v1.5",
            "type": "embedding",
            "description": "Embedding模型"
        },
        {
            "name": "BAAI/bge-reranker-large",
            "type": "rerank",
            "description": "重排序模型"
        }
    ]
    
    for model in models_to_download:
        logger.info(f"  下载 {model['description']}: {model['name']}...")
        try:
            if model['type'] == 'embedding':
                from sentence_transformers import SentenceTransformer
                SentenceTransformer(model['name'])
            elif model['type'] == 'rerank':
                from sentence_transformers import CrossEncoder
                CrossEncoder(model['name'])
            logger.info(f"  ✓ {model['name']} 下载成功")
        except Exception as e:
            logger.error(f"  ✗ {model['name']} 下载失败: {e}")
            logger.info(f"    请手动下载: {model['name']}")
    
    # 下载spaCy模型
    logger.info("  下载spaCy中文模型...")
    try:
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", "zh_core_web_sm"],
            check=True,
            capture_output=True
        )
        logger.info("  ✓ spaCy中文模型下载成功")
    except subprocess.CalledProcessError as e:
        logger.error(f"  ✗ spaCy中文模型下载失败: {e}")
        logger.info("    请手动运行: python -m spacy download zh_core_web_sm")
    
    logger.info("✓ 模型下载完成")
    return True


def verify_installation():
    """验证安装"""
    logger.info("验证安装...")
    
    checks = []
    
    # 检查sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer, CrossEncoder
        logger.info("  ✓ sentence-transformers 可用")
        checks.append(True)
    except ImportError:
        logger.error("  ✗ sentence-transformers 未安装")
        checks.append(False)
    
    # 检查chromadb
    try:
        import chromadb
        logger.info("  ✓ chromadb 可用")
        checks.append(True)
    except ImportError:
        logger.error("  ✗ chromadb 未安装")
        checks.append(False)
    
    # 检查spacy
    try:
        import spacy
        logger.info("  ✓ spacy 可用")
        checks.append(True)
    except ImportError:
        logger.error("  ✗ spacy 未安装")
        checks.append(False)
    
    # 检查torch
    try:
        import torch
        logger.info(f"  ✓ torch 可用 (版本: {torch.__version__})")
        if torch.cuda.is_available():
            logger.info(f"    CUDA可用: {torch.cuda.get_device_name(0)}")
        else:
            logger.info("    使用CPU模式")
        checks.append(True)
    except ImportError:
        logger.error("  ✗ torch 未安装")
        checks.append(False)
    
    if all(checks):
        logger.info("✓ 所有依赖验证通过")
        return True
    else:
        logger.warning("⚠ 部分依赖未安装，请检查上述错误")
        return False


def run_tests():
    """运行测试"""
    logger.info("运行测试...")
    
    test_files = [
        "tests/test_knowledge_optimization.py",
        "tests/test_end_to_end.py"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            logger.info(f"  运行 {test_file}...")
            try:
                subprocess.run(
                    [sys.executable, test_file],
                    check=True,
                    capture_output=True
                )
                logger.info(f"  ✓ {test_file} 测试通过")
            except subprocess.CalledProcessError as e:
                logger.error(f"  ✗ {test_file} 测试失败")
        else:
            logger.warning(f"  ⚠ {test_file} 不存在")
    
    logger.info("✓ 测试完成")


def backup_existing_data():
    """备份现有数据"""
    logger.info("备份现有数据...")
    
    import shutil
    from datetime import datetime
    
    backup_dir = f"backups/knowledge_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 备份向量数据库
    chroma_db_path = "frontend/public/knowledges/chromadb"
    if os.path.exists(chroma_db_path):
        shutil.copytree(chroma_db_path, f"{backup_dir}/chromadb")
        logger.info(f"  ✓ 向量数据库已备份到 {backup_dir}/chromadb")
    
    logger.info("✓ 数据备份完成")
    return True


def main():
    """主函数"""
    logger.info("="*60)
    logger.info("知识库优化部署脚本")
    logger.info("="*60)
    
    # 1. 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 2. 检查硬件资源
    check_hardware()
    
    # 3. 备份现有数据
    backup_existing_data()
    
    # 4. 安装依赖
    if not install_dependencies():
        logger.warning("部分依赖安装失败，继续执行...")
    
    # 5. 下载模型
    download_models()
    
    # 6. 验证安装
    verify_installation()
    
    # 7. 运行测试
    run_tests()
    
    logger.info("="*60)
    logger.info("部署脚本执行完成")
    logger.info("="*60)
    logger.info("\n后续步骤:")
    logger.info("1. 如果模型下载失败，请手动下载:")
    logger.info("   - BAAI/bge-large-zh-v1.5 (Embedding模型)")
    logger.info("   - BAAI/bge-reranker-large (重排序模型)")
    logger.info("   - zh_core_web_sm (spaCy中文模型)")
    logger.info("2. 重启服务以应用更改")
    logger.info("3. 测试文档上传和搜索功能")


if __name__ == "__main__":
    main()
