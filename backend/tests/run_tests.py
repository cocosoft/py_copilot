"""知识图谱测试运行器"""
import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_knowledge_graph_tests():
    """运行知识图谱相关测试"""
    # 发现并加载测试
    loader = unittest.TestLoader()
    
    # 加载知识图谱测试
    knowledge_graph_suite = loader.loadTestsFromName('test_knowledge_graph')
    
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTest(knowledge_graph_suite)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result


def run_all_tests():
    """运行所有测试"""
    # 发现并加载所有测试
    loader = unittest.TestLoader()
    
    # 加载测试目录中的所有测试
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 60)
    print("知识图谱测试套件")
    print("=" * 60)
    
    # 运行知识图谱特定测试
    print("\n运行知识图谱端到端测试...")
    kg_result = run_knowledge_graph_tests()
    
    print("\n" + "=" * 60)
    print("测试结果摘要:")
    print(f"运行测试数: {kg_result.testsRun}")
    print(f"失败数: {len(kg_result.failures)}")
    print(f"错误数: {len(kg_result.errors)}")
    print(f"跳过数: {len(kg_result.skipped)}")
    
    if kg_result.wasSuccessful():
        print("✅ 所有测试通过!")
    else:
        print("❌ 存在测试失败或错误")
        
        # 显示失败详情
        if kg_result.failures:
            print("\n失败测试:")
            for test, traceback in kg_result.failures:
                print(f"  - {test}: {traceback.split(chr(10))[0]}")
        
        if kg_result.errors:
            print("\n错误测试:")
            for test, traceback in kg_result.errors:
                print(f"  - {test}: {traceback.split(chr(10))[0]}")
    
    print("=" * 60)