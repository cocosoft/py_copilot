import requests

# 配置API地址
BASE_URL = "http://localhost:8001"
API_ENDPOINT = f"{BASE_URL}/api/model-management/suppliers"

print("正在验证字节跳动供应商是否添加成功...")
print(f"API端点: {API_ENDPOINT}")

# 发送GET请求获取所有供应商
try:
    response = requests.get(API_ENDPOINT)
    response.raise_for_status()  # 检查请求是否成功
    
    # 解析响应
    response_data = response.json()
    print(f"\n响应数据类型: {type(response_data)}")
    print(f"响应数据: {response_data}")
    
    # 根据响应数据类型进行不同处理
    if isinstance(response_data, list):
        suppliers = response_data
        print(f"\n获取到 {len(suppliers)} 个供应商:")
        
        # 查找字节跳动供应商
        bytedance_found = False
        for supplier in suppliers:
            if isinstance(supplier, dict):
                print(f"- {supplier.get('name')} (ID: {supplier.get('id')})")
                if supplier.get('name') == '字节跳动':
                    bytedance_found = True
                    print(f"\n字节跳动供应商存在！详细信息:")
                    print(f"ID: {supplier.get('id')}")
                    print(f"名称: {supplier.get('name')}")
                    print(f"显示名称: {supplier.get('display_name')}")
                    print(f"描述: {supplier.get('description')}")
                    print(f"网站: {supplier.get('website')}")
                    print(f"创建时间: {supplier.get('created_at')}")
                    print(f"是否活跃: {supplier.get('is_active')}")
                    break
            else:
                print(f"- 无效的供应商数据: {supplier}")
        
        if not bytedance_found:
            print("\n未找到字节跳动供应商！")
            valid_suppliers = [s for s in suppliers if isinstance(s, dict)]
            print(f"所有供应商名称: {[s.get('name') for s in valid_suppliers]}")
    
    elif isinstance(response_data, dict):
        # 可能是单个供应商或者包含供应商列表的字典
        if 'suppliers' in response_data:
            suppliers = response_data['suppliers']
            print(f"\n获取到 {len(suppliers)} 个供应商:")
            
            # 查找字节跳动供应商
            bytedance_found = False
            for supplier in suppliers:
                if isinstance(supplier, dict):
                    print(f"- {supplier.get('name')} (ID: {supplier.get('id')})")
                    if supplier.get('name') == '字节跳动':
                        bytedance_found = True
                        print(f"\n字节跳动供应商存在！详细信息:")
                        print(f"ID: {supplier.get('id')}")
                        print(f"名称: {supplier.get('name')}")
                        print(f"显示名称: {supplier.get('display_name')}")
                        print(f"描述: {supplier.get('description')}")
                        print(f"网站: {supplier.get('website')}")
                        print(f"创建时间: {supplier.get('created_at')}")
                        print(f"是否活跃: {supplier.get('is_active')}")
                        break
                else:
                    print(f"- 无效的供应商数据: {supplier}")
            
            if not bytedance_found:
                print("\n未找到字节跳动供应商！")
                valid_suppliers = [s for s in suppliers if isinstance(s, dict)]
                print(f"所有供应商名称: {[s.get('name') for s in valid_suppliers]}")
        else:
            print(f"\n响应是单个对象，不是供应商列表: {response_data}")
    
    else:
        print(f"\n响应数据格式未知: {response_data}")
    
except requests.exceptions.RequestException as e:
    print(f"\n验证失败: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"响应状态码: {e.response.status_code}")
        try:
            error_data = e.response.json()
            print(f"错误信息: {error_data}")
        except:
            print(f"错误响应: {e.response.text}")
