"""
后端服务启动脚本
在启动Python进程之前设置所有必要的环境变量
"""
import os
import sys
import subprocess

# 设置环境变量（在启动新进程之前）
env = os.environ.copy()
env['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
env['OMP_NUM_THREADS'] = '1'
env['MKL_NUM_THREADS'] = '1'
env['OPENBLAS_NUM_THREADS'] = '1'
env['VECLIB_MAXIMUM_THREADS'] = '1'
env['NUMEXPR_NUM_THREADS'] = '1'
env['TORCH_NUM_THREADS'] = '1'
env['CUDA_VISIBLE_DEVICES'] = ''
env['HF_HUB_OFFLINE'] = '1'
env['TRANSFORMERS_OFFLINE'] = '1'

# 启动主服务
subprocess.run([sys.executable, 'main.py'], env=env)
