"""验证硅基流动供应商是否成功添加"""
import requests
import sys
import os

# 配置API地址
BASE_URL = "http://localhost:8001"
API_ENDPOINT = f"{BASE_URL}/api/model-management/suppliers"

def verify_silicon_flow_supplier():
    """验证硅基流动供应商是否成功添加"""
    print("正在验证硅基流动供应商是否添加成功...")
    print(f"API端点: {API_ENDPOINT}")
    
    # 发送GET请求获取所有供应商
    try:
        response = requests.get(API_ENDPOINT)
        response.raise_for_status()  # 检查请求是否成功
        
        # 解析响应
        response_data = response.json()
        print(f"\n响应数据类型: {type(response_data)}")
        
        # 根据响应数据类型进行不同处理
        if isinstance(response_data, list):
            suppliers = response_data
            print(f"获取到 {len(suppliers)} 个供应商:")
            
            # 查找硅基流动供应商
            silicon_flow_found = False
            for supplier in suppliers:
                if isinstance(supplier, dict):
                    print(f"- {supplier.get('name')} (ID: {supplier.get('id')}) - 显示名称: {supplier.get('display_name')}")
                    if supplier.get('name') == 'silicon_flow' or supplier.get('display_name') == '硅基流动':
                        silicon_flow_found = True
                        print(f"\n✅ 硅基流动供应商存在！详细信息:")
                        print(f"   ID: {supplier.get('id')}")
                        print(f"   名称: {supplier.get('name')}")
                        print(f"   显示名称: {supplier.get('display_name')}")
                        print(f"   描述: {supplier.get('description')}")
                        print(f"   网站: {supplier.get('website')}")
                        print(f"   创建时间: {supplier.get('created_at')}")
                        print(f"   是否活跃: {supplier.get('is_active')}")
                        break
                else:
                    print(f"- 无效的供应商数据: {supplier}")
            
            if not silicon_flow_found:
                print("\n❌ 未找到硅基流动供应商！")
                valid_suppliers = [s for s in suppliers if isinstance(s, dict)]
                print(f"所有供应商名称: {[s.get('name') for s in valid_suppliers]}")
        else:
            print(f"响应数据格式异常: {response_data}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        print("请确保后端服务器正在运行 (http://localhost:8001)")
    except Exception as e:
        print(f"验证过程中出错: {e}")

def get_supplier_by_id(supplier_id):
    """通过ID获取特定供应商信息"""
    url = f"{API_ENDPOINT}/{supplier_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            supplier = response.json()
            print(f"\n通过ID {supplier_id} 获取的供应商信息:")
            print(f"名称: {supplier.get('name')}")
            print(f"显示名称: {supplier.get('display_name')}")
            print(f"描述: {supplier.get('description')}")
            return supplier
        else:
            print(f"获取供应商 {supplier_id} 失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"获取供应商信息失败: {e}")
        return None

if __name__ == "__main__":
    # 验证硅基流动供应商
    verify_silicon_flow_supplier()
    
    # 通过ID获取硅基流动供应商（ID为45）
    print("\n" + "="*50)
    get_supplier_by_id(45)