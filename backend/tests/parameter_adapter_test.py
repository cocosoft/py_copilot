import unittest
from app.services.parameter_management.parameter_normalizer import ParameterNormalizer

class ParameterAdapterTest(unittest.TestCase):
    """
    供应商参数适配器测试框架
    用于测试不同供应商的参数归一化和反归一化功能
    """
    
    def setUp(self):
        """测试前的准备工作"""
        self.test_cases = {
            "anthropic": {
                "supplier_id": 3,
                "name": "Anthropic",
                "raw_params": {
                    "max_tokens_to_sample": 500,
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "stop_sequences": ["\n", "<|endoftext|>"],
                    "stream": True
                },
                "expected_normalized": {
                    "max_tokens": 500,
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "stop": ["\n", "<|endoftext|>"],
                    "stream": True
                }
            },
            "google": {
                "supplier_id": 4,
                "name": "Google",
                "raw_params": {
                    "maxOutputTokens": 500,
                    "temperature": 0.8,
                    "topP": 0.9,
                    "stopSequences": ["\n", "<|endoftext|>"],
                    "stream": True
                },
                "expected_normalized": {
                    "max_tokens": 500,
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "stop": ["\n", "<|endoftext|>"],
                    "stream": True
                }
            },
            "baidu": {
                "supplier_id": 2,
                "name": "百度AI",
                "raw_params": {
                    "max_output_tokens": 500,
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "stop": ["\n", "<|endoftext|>"],
                    "stream": True
                },
                "expected_normalized": {
                    "max_tokens": 500,
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "stop": ["\n", "<|endoftext|>"],
                    "stream": True
                }
            },
            "openai": {
                "supplier_id": 1,
                "name": "OpenAI",
                "raw_params": {
                    "max_tokens": 500,
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "stop": ["\n", "<|endoftext|>"],
                    "stream": True
                },
                "expected_normalized": {
                    "max_tokens": 500,
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "stop": ["\n", "<|endoftext|>"],
                    "stream": True
                }
            }
        }
    
    def test_normalization(self):
        """测试参数归一化功能"""
        print("\n=== 测试参数归一化功能 ===")
        
        for supplier, test_data in self.test_cases.items():
            print(f"\n测试 {test_data['name']} 参数归一化:")
            
            # 执行归一化
            normalized_params = ParameterNormalizer.normalize_parameters(
                test_data['supplier_id'], 
                test_data['raw_params']
            )
            
            # 验证预期参数
            for param_name, expected_value in test_data['expected_normalized'].items():
                self.assertIn(param_name, normalized_params, 
                            f"{test_data['name']}归一化后缺少参数: {param_name}")
                self.assertEqual(normalized_params[param_name], expected_value, 
                               f"{test_data['name']}参数 {param_name} 归一化值错误: 预期 {expected_value}, 实际 {normalized_params[param_name]}")
            
            print(f"  ✓ {test_data['name']} 参数归一化测试通过")
    
    def test_denormalization(self):
        """测试参数反归一化功能"""
        print("\n=== 测试参数反归一化功能 ===")
        
        for supplier, test_data in self.test_cases.items():
            print(f"\n测试 {test_data['name']} 参数反归一化:")
            
            # 先归一化再反归一化
            normalized_params = ParameterNormalizer.normalize_parameters(
                test_data['supplier_id'], 
                test_data['raw_params']
            )
            
            denormalized_params = ParameterNormalizer.denormalize_parameters(
                test_data['supplier_id'], 
                normalized_params
            )
            
            # 验证核心参数是否正确反归一化
            if supplier == "anthropic":
                # Anthropic特殊检查
                self.assertIn("max_tokens_to_sample", denormalized_params)
                self.assertEqual(denormalized_params["max_tokens_to_sample"], 
                               test_data['raw_params']['max_tokens_to_sample'])
            elif supplier == "google":
                # Google特殊检查
                self.assertIn("maxOutputTokens", denormalized_params)
                self.assertEqual(denormalized_params["maxOutputTokens"], 
                               test_data['raw_params']['maxOutputTokens'])
            elif supplier == "baidu":
                # 百度AI特殊检查
                self.assertIn("max_output_tokens", denormalized_params)
                self.assertEqual(denormalized_params["max_output_tokens"], 
                               test_data['raw_params']['max_output_tokens'])
            
            print(f"  ✓ {test_data['name']} 参数反归一化测试通过")
    
    def test_default_parameters(self):
        """测试默认参数功能"""
        print("\n=== 测试默认参数功能 ===")
        
        for supplier, test_data in self.test_cases.items():
            print(f"\n测试 {test_data['name']} 默认参数:")
            
            # 只提供少量参数，测试默认参数是否添加
            minimal_params = {
                "temperature": 0.5
            }
            
            normalized_params = ParameterNormalizer.normalize_parameters(
                test_data['supplier_id'], 
                minimal_params
            )
            
            # 验证核心参数是否有默认值
            self.assertIn("max_tokens", normalized_params, 
                        f"{test_data['name']}缺少max_tokens默认参数")
            self.assertIn("top_p", normalized_params, 
                        f"{test_data['name']}缺少top_p默认参数")
            self.assertIn("stream", normalized_params, 
                        f"{test_data['name']}缺少stream默认参数")
            
            print(f"  ✓ {test_data['name']} 默认参数测试通过")
    
    def test_round_trip_conversion(self):
        """测试参数的完整转换流程：原始→归一化→反归一化"""
        print("\n=== 测试参数完整转换流程 ===")
        
        for supplier, test_data in self.test_cases.items():
            print(f"\n测试 {test_data['name']} 参数完整转换流程:")
            
            # 原始参数
            raw_params = test_data['raw_params']
            
            # 归一化
            normalized_params = ParameterNormalizer.normalize_parameters(
                test_data['supplier_id'], 
                raw_params
            )
            
            # 反归一化
            denormalized_params = ParameterNormalizer.denormalize_parameters(
                test_data['supplier_id'], 
                normalized_params
            )
            
            # 验证核心参数值是否保持一致
            if supplier == "anthropic":
                self.assertEqual(denormalized_params.get("max_tokens_to_sample"), 
                               raw_params.get("max_tokens_to_sample"))
            elif supplier == "google":
                self.assertEqual(denormalized_params.get("maxOutputTokens"), 
                               raw_params.get("maxOutputTokens"))
            elif supplier == "baidu":
                self.assertEqual(denormalized_params.get("max_output_tokens"), 
                               raw_params.get("max_output_tokens"))
            
            # 验证温度参数是否保持一致
            self.assertEqual(denormalized_params.get("temperature"), 
                           raw_params.get("temperature"))
            
            print(f"  ✓ {test_data['name']} 参数完整转换流程测试通过")


if __name__ == "__main__":
    """运行测试"""
    print("============================================")
    print("供应商参数适配器测试框架")
    print("============================================")
    print("测试目标：验证各供应商参数的归一化和反归一化功能")
    print("测试范围：Anthropic, Google, 百度AI, OpenAI")
    print("============================================\n")
    
    unittest.main(verbosity=2)
