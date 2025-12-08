import requests
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_suppliers():
    """获取所有供应商"""
    # API端点
    base_url = "http://localhost:8001/api"
    suppliers_url = f"{base_url}/model-management/suppliers/all"
    
    try:
        # 发送请求
        response = requests.get(suppliers_url)
        
        logger.info(f"[测试] 响应状态码: {response.status_code}")
        logger.info(f"[测试] 响应内容: {response.json()}")
        
        if response.status_code == 200:
            suppliers = response.json()
            logger.info(f"[测试] 共获取到 {len(suppliers)} 个供应商")
            
            # 打印每个供应商的ID和名称
            for supplier in suppliers:
                logger.info(f"供应商ID: {supplier['id']}, 名称: {supplier['name']}")
        else:
            logger.error(f"❌ 获取供应商失败，状态码: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    get_all_suppliers()
