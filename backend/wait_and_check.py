#!/usr/bin/env python3
"""等待并检查任务状态"""

import requests
import json
import time

base_url = "http://127.0.0.1:8010/api/v1"

# 检查任务状态
task_id = "cd4d600f-48e4-4699-9698-77ae3c26a271"
url = f"{base_url}/knowledge/documents/102/extract-chunk-entities/status/{task_id}"

print(f"等待任务完成: {task_id}")
print("="*60)

max_wait = 300  # 最多等待5分钟
for i in range(max_wait):
    response = requests.get(url, timeout=5)
    result = response.json()
    
    status = result.get('status')
    progress = result.get('progress', 0)
    message = result.get('message', '')
    
    if i % 10 == 0:  # 每20秒打印一次
        print(f"[{i*2}s] 状态: {status}, 进度: {progress}%, {message}")
    
    if status in ['completed', 'failed']:
        print(f"\n任务完成!")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        break
    
    time.sleep(2)
else:
    print(f"\n等待超时")
