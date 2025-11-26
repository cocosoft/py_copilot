#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试供应商更新API脚本
用于验证PUT请求是否能正常工作
"""

import requests
import json
import time

# API端点
BASE_URL = "http://localhost:8001/api"
SUPPLIER_ENDPOINT = f"{BASE_URL}/model-management/suppliers"

# 测试的供应商ID
test_supplier_id = 1  # 深度求索的ID

def test_supplier_update():
    """
    测试供应商状态更新API
    """
    try:
        print("==================================")
        print("     供应商更新API测试工具")
        print("==================================")
        
        # 1. 先获取当前供应商信息
        print(f"\n🔍 正在获取供应商信息 (ID: {test_supplier_id})...")
        get_url = f"{SUPPLIER_ENDPOINT}/{test_supplier_id}"
        print(f"   GET URL: {get_url}")
        
        get_response = requests.get(get_url)
        if get_response.status_code != 200:
            print(f"❌ 获取供应商信息失败: HTTP {get_response.status_code}")
            print(f"   响应内容: {get_response.text}")
            return
            
        supplier_data = get_response.json()
        print(f"✅ 成功获取供应商信息: {supplier_data.get('name')}")
        print(f"   当前状态: {'启用' if supplier_data.get('is_active') else '停用'}")
        
        # 2. 准备更新数据 - 切换is_active状态
        current_status = supplier_data.get('is_active', False)
        new_status = not current_status
        update_data = {"is_active": new_status}
        
        print(f"\n🔄 准备更新供应商状态...")
        print(f"   更新数据: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
        
        # 3. 发送PUT请求
        put_url = f"{SUPPLIER_ENDPOINT}/{test_supplier_id}"
        print(f"   PUT URL: {put_url}")
        print("   正在发送请求...")
        
        headers = {"Content-Type": "application/json"}
        put_response = requests.put(
            put_url,
            json=update_data,
            headers=headers
        )
        
        print(f"   请求完成，状态码: {put_response.status_code}")
        print(f"   响应内容: {put_response.text}")
        
        if put_response.status_code == 200:
            print(f"✅ 更新成功！")
            
            # 4. 验证更新是否生效
            print("\n🔍 正在验证更新结果...")
            time.sleep(0.5)  # 等待数据库更新
            
            verify_response = requests.get(get_url)
            if verify_response.status_code == 200:
                updated_data = verify_response.json()
                print(f"   验证状态: {'启用' if updated_data.get('is_active') else '停用'}")
                print(f"   更新结果: {'成功' if updated_data.get('is_active') == new_status else '失败'}")
            else:
                print(f"❌ 验证失败，无法获取更新后的数据")
        else:
            print(f"❌ 更新失败")
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
    finally:
        print("\n==================================")
        print("测试操作已完成!")
        print("==================================")

if __name__ == "__main__":
    test_supplier_update()
