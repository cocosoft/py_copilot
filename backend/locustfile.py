"""参数管理系统性能测试"""
from locust import HttpUser, task, between, tag
import random


class ParameterManagementUser(HttpUser):
    """参数管理系统性能测试用户类"""
    wait_time = between(1, 3)  # 每个用户操作间隔1-3秒
    
    def on_start(self):
        """测试开始前的准备工作"""
        # 这里可以添加登录逻辑或其他初始化操作
        pass
    
    @tag("parameter_templates")
    @task(2)
    def get_parameter_templates(self):
        """测试获取参数模板列表"""
        response = self.client.get("/api/v1/parameter-templates")
        if response.status_code == 200:
            # 保存模板ID用于后续测试
            templates = response.json()
            if 'templates' in templates and templates['templates']:
                self.templates = templates['templates']
        
    @tag("model_management")
    @task(1)
    def get_suppliers(self):
        """测试获取供应商列表"""
        response = self.client.get("/api/v1/model-management/suppliers/all")
        if response.status_code == 200:
            # 保存供应商ID用于后续测试
            suppliers = response.json()
            if suppliers:
                self.suppliers = suppliers
    
    @tag("model_management")
    @task(3)
    def get_models(self):
        """测试获取模型列表"""
        if hasattr(self, 'suppliers') and self.suppliers:
            supplier_id = random.choice(self.suppliers)['id']
            self.client.get(f"/api/v1/model-management/suppliers/{supplier_id}/models")
        else:
            # 如果没有供应商数据，使用默认供应商ID
            self.client.get("/api/v1/model-management/suppliers/1/models")
    
    @tag("model_templates")
    @task(4)
    def sync_model_parameters_with_template(self):
        """测试同步模型参数与模板"""
        if hasattr(self, 'suppliers') and self.suppliers and hasattr(self, 'templates') and self.templates:
            supplier_id = random.choice(self.suppliers)['id']
            template_id = random.choice(self.templates)['id']
            
            # 获取该供应商的模型
            models_response = self.client.get(f"/api/v1/model-management/suppliers/{supplier_id}/models")
            if models_response.status_code == 200:
                models_data = models_response.json()
                if 'models' in models_data and models_data['models']:
                    model_id = random.choice(models_data['models'])['id']
                    
                    # 同步模型参数与模板
                    self.client.post(
                        f"/api/v1/suppliers/{supplier_id}/models/{model_id}/sync-parameters",
                        json={
                            "template_id": template_id
                        }
                    )
        else:
            # 如果没有数据，使用默认ID
            self.client.post(
                "/api/v1/suppliers/1/models/1/sync-parameters",
                json={
                    "template_id": 1
                }
            )
    
    @tag("model_parameters")
    @task(3)
    def get_model_parameters_with_templates(self):
        """测试获取模型参数（带模板）"""
        if hasattr(self, 'suppliers') and self.suppliers:
            supplier_id = random.choice(self.suppliers)['id']
            
            # 获取该供应商的模型
            models_response = self.client.get(f"/api/v1/model-management/suppliers/{supplier_id}/models")
            if models_response.status_code == 200:
                models_data = models_response.json()
                if 'models' in models_data and models_data['models']:
                    model_id = random.choice(models_data['models'])['id']
                    self.client.get(f"/api/v1/model-management/suppliers/{supplier_id}/models/{model_id}/parameters")
        else:
            # 如果没有数据，使用默认ID
            self.client.get("/api/v1/model-management/suppliers/1/models/1/parameters")
    
    @tag("system_parameters")
    @task(1)
    def get_system_parameters(self):
        """测试获取系统参数"""
        self.client.get("/api/v1/system-parameters")


if __name__ == "__main__":
    import os
    import subprocess
    
    # 启动Locust测试
    subprocess.run([
        "locust",
        "-f", os.path.basename(__file__),
        "--host", "http://localhost:8001"
    ])
