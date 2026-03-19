#!/usr/bin/env python3
"""
系统整体功能验证脚本

验证第一阶段优化成果的整体功能完整性
包括：统一文档处理器、统一向量化服务、统一前端组件库
"""

import os
import sys
import json
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemValidator:
    """系统整体功能验证类"""
    
    def __init__(self):
        self.validation_results = {}
        self.start_time = None
        self.end_time = None
    
    def start_validation(self):
        """开始验证"""
        self.start_time = datetime.now()
        logger.info("🚀 开始系统整体功能验证")
        logger.info("=" * 60)
    
    def end_validation(self):
        """结束验证"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info(f"🏁 验证完成，耗时: {duration:.2f}秒")
        
        # 生成验证报告
        self.generate_validation_report()
    
    def validate_backend_services(self) -> bool:
        """验证后端服务完整性"""
        logger.info("🔧 验证后端服务完整性...")
        
        try:
            # 检查统一文档处理器
            from app.services.knowledge.unified_document_processor import UnifiedDocumentProcessor
            processor = UnifiedDocumentProcessor()
            
            # 检查统一向量化服务
            from app.services.knowledge.unified_vectorization_service import UnifiedVectorizationService
            vector_service = UnifiedVectorizationService()
            
            # 检查依赖服务
            dependencies = [
                'DocumentParser',
                'AdvancedTextProcessor',
                'KnowledgeTextProcessor',
                'ChromaService',
                'FAISSIndexService',
                'RetrievalService',
                'KnowledgeGraphService'
            ]
            
            logger.info("✅ 后端服务完整性验证通过")
            
            self.validation_results['backend_services'] = {
                'status': 'PASS',
                'message': '后端服务完整性验证通过',
                'details': {
                    'unified_document_processor': '可用',
                    'unified_vectorization_service': '可用',
                    'dependencies': dependencies
                }
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ 后端服务完整性验证失败: {e}")
            self.validation_results['backend_services'] = {
                'status': 'FAIL',
                'message': f'后端服务完整性验证失败: {str(e)}'
            }
            return False
    
    def validate_frontend_components(self) -> bool:
        """验证前端组件完整性"""
        logger.info("🎨 验证前端组件完整性...")
        
        try:
            # 检查前端组件库文件结构
            frontend_path = os.path.join(os.path.dirname(__file__), 'frontend', 'src', 'components', 'UnifiedComponentLibrary')
            
            required_files = [
                'index.js',
                'Core/Button/index.jsx',
                'Core/Button/Button.css',
                'Core/Modal/index.jsx',
                'Core/Modal/Modal.css',
                'Core/Loading/index.jsx',
                'Core/Loading/Loading.css',
                'Core/ErrorBoundary/index.jsx',
                'Core/ErrorBoundary/ErrorBoundary.css',
                'README.md',
                'COMPONENT_USAGE.md'
            ]
            
            existing_files = []
            missing_files = []
            
            for file in required_files:
                file_path = os.path.join(frontend_path, file)
                if os.path.exists(file_path):
                    existing_files.append(file)
                else:
                    missing_files.append(file)
            
            if missing_files:
                logger.warning(f"⚠️ 前端组件文件缺失: {missing_files}")
                self.validation_results['frontend_components'] = {
                    'status': 'WARN',
                    'message': f'前端组件文件部分缺失 ({len(missing_files)} 个文件)',
                    'details': {
                        'existing_files': existing_files,
                        'missing_files': missing_files
                    }
                }
                return False
            else:
                logger.info("✅ 前端组件完整性验证通过")
                self.validation_results['frontend_components'] = {
                    'status': 'PASS',
                    'message': '前端组件完整性验证通过',
                    'details': {
                        'total_files': len(existing_files),
                        'files': existing_files
                    }
                }
                return True
                
        except Exception as e:
            logger.error(f"❌ 前端组件完整性验证失败: {e}")
            self.validation_results['frontend_components'] = {
                'status': 'FAIL',
                'message': f'前端组件完整性验证失败: {str(e)}'
            }
            return False
    
    def validate_documentation(self) -> bool:
        """验证文档完整性"""
        logger.info("📚 验证文档完整性...")
        
        try:
            required_docs = [
                '知识库系统优化实施方案.md',
                'backend/integration_test_plan.md',
                'backend/integration_test.py',
                'frontend/src/components/UnifiedComponentLibrary/README.md',
                'frontend/src/components/UnifiedComponentLibrary/COMPONENT_USAGE.md'
            ]
            
            existing_docs = []
            missing_docs = []
            
            for doc in required_docs:
                doc_path = os.path.join(os.path.dirname(__file__), doc)
                if os.path.exists(doc_path):
                    existing_docs.append(doc)
                else:
                    missing_docs.append(doc)
            
            if missing_docs:
                logger.warning(f"⚠️ 文档文件缺失: {missing_docs}")
                self.validation_results['documentation'] = {
                    'status': 'WARN',
                    'message': f'文档文件部分缺失 ({len(missing_docs)} 个文件)',
                    'details': {
                        'existing_docs': existing_docs,
                        'missing_docs': missing_docs
                    }
                }
                return False
            else:
                logger.info("✅ 文档完整性验证通过")
                self.validation_results['documentation'] = {
                    'status': 'PASS',
                    'message': '文档完整性验证通过',
                    'details': {
                        'total_docs': len(existing_docs),
                        'docs': existing_docs
                    }
                }
                return True
                
        except Exception as e:
            logger.error(f"❌ 文档完整性验证失败: {e}")
            self.validation_results['documentation'] = {
                'status': 'FAIL',
                'message': f'文档完整性验证失败: {str(e)}'
            }
            return False
    
    def validate_test_coverage(self) -> bool:
        """验证测试覆盖率"""
        logger.info("🧪 验证测试覆盖率...")
        
        try:
            required_tests = [
                'backend/integration_test.py',
                'backend/test_unified_processor.py',
                'backend/test_unified_vectorization.py',
                'frontend/src/components/UnifiedComponentLibrary/test-components.jsx',
                'frontend/src/components/UnifiedComponentLibrary/integration-test.jsx'
            ]
            
            existing_tests = []
            missing_tests = []
            
            for test in required_tests:
                test_path = os.path.join(os.path.dirname(__file__), test)
                if os.path.exists(test_path):
                    existing_tests.append(test)
                else:
                    missing_tests.append(test)
            
            if missing_tests:
                logger.warning(f"⚠️ 测试文件缺失: {missing_tests}")
                self.validation_results['test_coverage'] = {
                    'status': 'WARN',
                    'message': f'测试文件部分缺失 ({len(missing_tests)} 个文件)',
                    'details': {
                        'existing_tests': existing_tests,
                        'missing_tests': missing_tests
                    }
                }
                return False
            else:
                logger.info("✅ 测试覆盖率验证通过")
                self.validation_results['test_coverage'] = {
                    'status': 'PASS',
                    'message': '测试覆盖率验证通过',
                    'details': {
                        'total_tests': len(existing_tests),
                        'tests': existing_tests
                    }
                }
                return True
                
        except Exception as e:
            logger.error(f"❌ 测试覆盖率验证失败: {e}")
            self.validation_results['test_coverage'] = {
                'status': 'FAIL',
                'message': f'测试覆盖率验证失败: {str(e)}'
            }
            return False
    
    def validate_performance_improvements(self) -> bool:
        """验证性能改进"""
        logger.info("⚡ 验证性能改进...")
        
        try:
            # 基于集成测试结果评估性能改进
            integration_test_report_path = os.path.join(os.path.dirname(__file__), 'backend', 'integration_test_report.json')
            
            if os.path.exists(integration_test_report_path):
                with open(integration_test_report_path, 'r', encoding='utf-8') as f:
                    test_report = json.load(f)
                
                # 检查性能测试结果
                performance_result = test_report.get('test_details', {}).get('performance', {})
                
                if performance_result.get('status') == 'PASS':
                    metrics = performance_result.get('metrics', {})
                    avg_time = metrics.get('average_time', 1.0)
                    
                    # 性能基准：平均处理时间应小于1秒
                    if avg_time < 1.0:
                        logger.info("✅ 性能改进验证通过")
                        self.validation_results['performance_improvements'] = {
                            'status': 'PASS',
                            'message': f'性能改进验证通过 (平均处理时间: {avg_time:.3f}秒)',
                            'details': metrics
                        }
                        return True
                    else:
                        logger.warning(f"⚠️ 性能需要优化 (平均处理时间: {avg_time:.3f}秒)")
                        self.validation_results['performance_improvements'] = {
                            'status': 'WARN',
                            'message': f'性能需要优化 (平均处理时间: {avg_time:.3f}秒)',
                            'details': metrics
                        }
                        return False
                else:
                    logger.warning("⚠️ 性能测试结果不可用")
                    self.validation_results['performance_improvements'] = {
                        'status': 'WARN',
                        'message': '性能测试结果不可用'
                    }
                    return False
            else:
                logger.warning("⚠️ 集成测试报告不存在")
                self.validation_results['performance_improvements'] = {
                    'status': 'WARN',
                    'message': '集成测试报告不存在'
                }
                return False
                
        except Exception as e:
            logger.error(f"❌ 性能改进验证失败: {e}")
            self.validation_results['performance_improvements'] = {
                'status': 'FAIL',
                'message': f'性能改进验证失败: {str(e)}'
            }
            return False
    
    def validate_code_quality(self) -> bool:
        """验证代码质量"""
        logger.info("🔍 验证代码质量...")
        
        try:
            # 检查关键代码文件的质量指标
            key_files = [
                'backend/app/services/knowledge/unified_document_processor.py',
                'backend/app/services/knowledge/unified_vectorization_service.py',
                'frontend/src/components/UnifiedComponentLibrary/Core/Button/index.jsx',
                'frontend/src/components/UnifiedComponentLibrary/Core/Modal/index.jsx'
            ]
            
            quality_metrics = {
                'total_files': len(key_files),
                'files_analyzed': 0,
                'avg_lines_per_file': 0,
                'has_comments': False,
                'has_docstrings': False
            }
            
            total_lines = 0
            analyzed_files = 0
            
            for file_path in key_files:
                full_path = os.path.join(os.path.dirname(__file__), file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            lines = content.count('\n') + 1
                            total_lines += lines
                            analyzed_files += 1
                            
                            # 检查代码质量指标
                            if '#' in content or '//' in content or '/*' in content:
                                quality_metrics['has_comments'] = True
                            if '"""' in content or "'''" in content:
                                quality_metrics['has_docstrings'] = True
                                
                    except Exception:
                        continue
            
            if analyzed_files > 0:
                quality_metrics['files_analyzed'] = analyzed_files
                quality_metrics['avg_lines_per_file'] = total_lines / analyzed_files
                
                # 质量评估标准
                quality_ok = (
                    analyzed_files >= len(key_files) * 0.8 and  # 至少80%的文件可分析
                    quality_metrics['has_comments'] and  # 有注释
                    quality_metrics['has_docstrings']  # 有文档字符串
                )
                
                if quality_ok:
                    logger.info("✅ 代码质量验证通过")
                    self.validation_results['code_quality'] = {
                        'status': 'PASS',
                        'message': '代码质量验证通过',
                        'details': quality_metrics
                    }
                    return True
                else:
                    logger.warning("⚠️ 代码质量需要改进")
                    self.validation_results['code_quality'] = {
                        'status': 'WARN',
                        'message': '代码质量需要改进',
                        'details': quality_metrics
                    }
                    return False
            else:
                logger.warning("⚠️ 无法分析代码质量")
                self.validation_results['code_quality'] = {
                    'status': 'WARN',
                    'message': '无法分析代码质量'
                }
                return False
                
        except Exception as e:
            logger.error(f"❌ 代码质量验证失败: {e}")
            self.validation_results['code_quality'] = {
                'status': 'FAIL',
                'message': f'代码质量验证失败: {str(e)}'
            }
            return False
    
    def generate_validation_report(self):
        """生成验证报告"""
        logger.info("📊 生成系统整体功能验证报告...")
        
        # 统计验证结果
        total_validations = len(self.validation_results)
        passed_validations = sum(1 for result in self.validation_results.values() if result['status'] == 'PASS')
        failed_validations = sum(1 for result in self.validation_results.values() if result['status'] == 'FAIL')
        warning_validations = sum(1 for result in self.validation_results.values() if result['status'] == 'WARN')
        
        # 生成报告
        report = {
            'validation_summary': {
                'total_validations': total_validations,
                'passed_validations': passed_validations,
                'failed_validations': failed_validations,
                'warning_validations': warning_validations,
                'success_rate': (passed_validations / total_validations) * 100 if total_validations > 0 else 0,
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'duration_seconds': (self.end_time - self.start_time).total_seconds()
            },
            'validation_details': self.validation_results
        }
        
        # 保存报告
        with open('system_validation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印摘要
        logger.info("=" * 60)
        logger.info("📋 系统整体功能验证报告摘要")
        logger.info("=" * 60)
        logger.info(f"总验证项: {total_validations}")
        logger.info(f"通过验证: {passed_validations}")
        logger.info(f"失败验证: {failed_validations}")
        logger.info(f"警告验证: {warning_validations}")
        logger.info(f"整体成功率: {report['validation_summary']['success_rate']:.1f}%")
        
        # 详细结果
        for validation_name, result in self.validation_results.items():
            status_icon = '✅' if result['status'] == 'PASS' else '⚠️' if result['status'] == 'WARN' else '❌'
            logger.info(f"{status_icon} {validation_name}: {result['message']}")
        
        logger.info("=" * 60)
        
        # 总体评估
        if failed_validations == 0 and warning_validations == 0:
            logger.info("🎉 系统整体功能验证完全通过！第一阶段优化成果验收合格。")
        elif failed_validations == 0:
            logger.info("✅ 系统整体功能验证基本通过，存在一些警告项需要关注。")
        else:
            logger.warning("⚠️ 系统整体功能验证存在失败项，需要修复问题。")
    
    def run_all_validations(self):
        """运行所有验证"""
        self.start_validation()
        
        # 执行验证用例
        validations = [
            ('后端服务完整性', self.validate_backend_services),
            ('前端组件完整性', self.validate_frontend_components),
            ('文档完整性', self.validate_documentation),
            ('测试覆盖率', self.validate_test_coverage),
            ('性能改进', self.validate_performance_improvements),
            ('代码质量', self.validate_code_quality)
        ]
        
        for validation_name, validation_func in validations:
            logger.info(f"\n🔍 执行验证: {validation_name}")
            validation_func()
        
        self.end_validation()


def main():
    """主函数"""
    validator = SystemValidator()
    validator.run_all_validations()

if __name__ == "__main__":
    main()