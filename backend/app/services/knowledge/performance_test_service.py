"""
性能测试服务

验证优化效果和系统性能

@task DB-001
@phase 系统集成和测试
"""

from typing import List, Dict, Any, Optional
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed


class PerformanceTestRunner:
    """
    性能测试运行器
    """
    
    def __init__(self, concurrency_level: int = 10):
        """
        初始化性能测试运行器
        
        Args:
            concurrency_level: 并发级别
        """
        self.concurrency_level = concurrency_level
    
    def run_load_test(self, test_function: callable, test_data: List[Any]) -> Dict[str, Any]:
        """
        运行负载测试
        
        Args:
            test_function: 测试函数
            test_data: 测试数据
            
        Returns:
            测试结果
        """
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.concurrency_level) as executor:
            future_to_data = {executor.submit(test_function, data): data for data in test_data}
            
            for future in as_completed(future_to_data):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Error in load test: {e}")
        
        total_time = time.time() - start_time
        
        return {
            'total_requests': len(test_data),
            'successful_requests': len(results),
            'total_time': total_time,
            'requests_per_second': len(results) / total_time if total_time > 0 else 0,
            'average_response_time': statistics.mean([r.get('response_time', 0) for r in results]) if results else 0
        }
    
    def run_stress_test(self, test_function: callable, test_data: List[Any], 
                      max_concurrency: int = 50) -> Dict[str, Any]:
        """
        运行压力测试
        
        Args:
            test_function: 测试函数
            test_data: 测试数据
            max_concurrency: 最大并发数
            
        Returns:
            测试结果
        """
        results = []
        concurrency_levels = [1, 5, 10, 20, 30, 40, 50]
        concurrency_results = []
        
        for concurrency in concurrency_levels:
            if concurrency > max_concurrency:
                break
            
            print(f"Running stress test with concurrency: {concurrency}")
            
            current_results = []
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                future_to_data = {executor.submit(test_function, data): data for data in test_data[:100]}
                
                for future in as_completed(future_to_data):
                    try:
                        result = future.result()
                        current_results.append(result)
                    except Exception as e:
                        print(f"Error in stress test: {e}")
            
            total_time = time.time() - start_time
            
            concurrency_results.append({
                'concurrency': concurrency,
                'total_requests': len(test_data[:100]),
                'successful_requests': len(current_results),
                'total_time': total_time,
                'requests_per_second': len(current_results) / total_time if total_time > 0 else 0,
                'average_response_time': statistics.mean([r.get('response_time', 0) for r in current_results]) if current_results else 0
            })
            
            results.extend(current_results)
        
        return {
            'concurrency_results': concurrency_results,
            'overall_results': {
                'total_requests': sum([r['total_requests'] for r in concurrency_results]),
                'successful_requests': sum([r['successful_requests'] for r in concurrency_results]),
                'total_time': sum([r['total_time'] for r in concurrency_results]),
                'requests_per_second': sum([r['requests_per_second'] for r in concurrency_results]) / len(concurrency_results) if concurrency_results else 0,
                'average_response_time': statistics.mean([r['average_response_time'] for r in concurrency_results]) if concurrency_results else 0
            }
        }


class EntityPerformanceTest:
    """
    实体性能测试
    """
    
    def __init__(self, db):
        """
        初始化实体性能测试
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def test_entity_extraction(self, text: str) -> Dict[str, Any]:
        """
        测试实体提取性能
        
        Args:
            text: 测试文本
            
        Returns:
            测试结果
        """
        start_time = time.time()
        
        # 模拟实体提取
        # 实际应用中应该调用真实的实体提取服务
        entities = [
            {'text': 'Entity 1', 'type': 'PERSON', 'confidence': 0.9},
            {'text': 'Entity 2', 'type': 'ORG', 'confidence': 0.85},
            {'text': 'Entity 3', 'type': 'LOC', 'confidence': 0.8}
        ]
        
        response_time = time.time() - start_time
        
        return {
            'text_length': len(text),
            'entity_count': len(entities),
            'response_time': response_time
        }
    
    def test_entity_hierarchy(self, entity_id: int) -> Dict[str, Any]:
        """
        测试实体层级查询性能
        
        Args:
            entity_id: 实体ID
            
        Returns:
            测试结果
        """
        start_time = time.time()
        
        # 模拟实体层级查询
        # 实际应用中应该调用真实的实体层级查询服务
        hierarchy = {
            'document_entity': {'id': entity_id, 'text': 'Document Entity'},
            'kb_entity': {'id': 1, 'name': 'KB Entity'},
            'global_entity': {'id': 1, 'name': 'Global Entity'}
        }
        
        response_time = time.time() - start_time
        
        return {
            'entity_id': entity_id,
            'hierarchy_depth': 3,
            'response_time': response_time
        }


class SearchPerformanceTest:
    """
    搜索性能测试
    """
    
    def __init__(self, db):
        """
        初始化搜索性能测试
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def test_search_performance(self, query: str) -> Dict[str, Any]:
        """
        测试搜索性能
        
        Args:
            query: 搜索查询
            
        Returns:
            测试结果
        """
        start_time = time.time()
        
        # 模拟搜索
        # 实际应用中应该调用真实的搜索服务
        results = [
            {'id': 1, 'title': 'Document 1', 'score': 0.9},
            {'id': 2, 'title': 'Document 2', 'score': 0.85},
            {'id': 3, 'title': 'Document 3', 'score': 0.8}
        ]
        
        response_time = time.time() - start_time
        
        return {
            'query': query,
            'result_count': len(results),
            'response_time': response_time
        }
    
    def test_reranking_performance(self, query: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        测试重排序性能
        
        Args:
            query: 搜索查询
            documents: 文档列表
            
        Returns:
            测试结果
        """
        start_time = time.time()
        
        # 模拟重排序
        # 实际应用中应该调用真实的重排序服务
        reranked_documents = sorted(documents, key=lambda x: x.get('score', 0), reverse=True)
        
        response_time = time.time() - start_time
        
        return {
            'query': query,
            'document_count': len(documents),
            'response_time': response_time
        }


class KnowledgeGraphPerformanceTest:
    """
    知识图谱性能测试
    """
    
    def __init__(self, db):
        """
        初始化知识图谱性能测试
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def test_graph_building(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        测试图谱构建性能
        
        Args:
            knowledge_base_id: 知识库ID
            
        Returns:
            测试结果
        """
        start_time = time.time()
        
        # 模拟图谱构建
        # 实际应用中应该调用真实的图谱构建服务
        graph = {
            'entities': 100,
            'relationships': 50
        }
        
        response_time = time.time() - start_time
        
        return {
            'knowledge_base_id': knowledge_base_id,
            'entity_count': graph['entities'],
            'relationship_count': graph['relationships'],
            'response_time': response_time
        }
    
    def test_graph_query(self, entity_id: int) -> Dict[str, Any]:
        """
        测试图谱查询性能
        
        Args:
            entity_id: 实体ID
            
        Returns:
            测试结果
        """
        start_time = time.time()
        
        # 模拟图谱查询
        # 实际应用中应该调用真实的图谱查询服务
        related_entities = [
            {'id': 1, 'name': 'Related Entity 1'},
            {'id': 2, 'name': 'Related Entity 2'},
            {'id': 3, 'name': 'Related Entity 3'}
        ]
        
        response_time = time.time() - start_time
        
        return {
            'entity_id': entity_id,
            'related_entity_count': len(related_entities),
            'response_time': response_time
        }


class PerformanceTestService:
    """
    性能测试服务
    """
    
    def __init__(self, db):
        """
        初始化性能测试服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.test_runner = PerformanceTestRunner()
        self.entity_test = EntityPerformanceTest(db)
        self.search_test = SearchPerformanceTest(db)
        self.graph_test = KnowledgeGraphPerformanceTest(db)
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """
        运行性能测试
        
        Returns:
            测试结果
        """
        # 1. 实体性能测试
        entity_test_results = self._run_entity_tests()
        
        # 2. 搜索性能测试
        search_test_results = self._run_search_tests()
        
        # 3. 知识图谱性能测试
        graph_test_results = self._run_graph_tests()
        
        # 4. 系统整体性能测试
        system_test_results = self._run_system_tests()
        
        # 5. 生成性能报告
        report = self._generate_performance_report(
            entity_test_results,
            search_test_results,
            graph_test_results,
            system_test_results
        )
        
        return report
    
    def _run_entity_tests(self) -> Dict[str, Any]:
        """
        运行实体性能测试
        """
        # 测试实体提取
        test_data = ["This is a test text about John Doe and Microsoft in New York."] * 100
        entity_extraction_results = self.test_runner.run_load_test(
            self.entity_test.test_entity_extraction, test_data
        )
        
        # 测试实体层级查询
        test_data = [i for i in range(1, 101)]
        entity_hierarchy_results = self.test_runner.run_load_test(
            self.entity_test.test_entity_hierarchy, test_data
        )
        
        return {
            'entity_extraction': entity_extraction_results,
            'entity_hierarchy': entity_hierarchy_results
        }
    
    def _run_search_tests(self) -> Dict[str, Any]:
        """
        运行搜索性能测试
        """
        # 测试搜索性能
        test_data = ["test query", "entity extraction", "knowledge graph", "reranking"] * 25
        search_results = self.test_runner.run_load_test(
            self.search_test.test_search_performance, test_data
        )
        
        # 测试重排序性能
        test_documents = [
            {'id': 1, 'title': 'Document 1', 'score': 0.7},
            {'id': 2, 'title': 'Document 2', 'score': 0.8},
            {'id': 3, 'title': 'Document 3', 'score': 0.9},
            {'id': 4, 'title': 'Document 4', 'score': 0.6},
            {'id': 5, 'title': 'Document 5', 'score': 0.85}
        ]
        reranking_test_data = [("test query", test_documents) for _ in range(100)]
        
        def test_reranking(data):
            query, docs = data
            return self.search_test.test_reranking_performance(query, docs)
        
        reranking_results = self.test_runner.run_load_test(test_reranking, reranking_test_data)
        
        return {
            'search': search_results,
            'reranking': reranking_results
        }
    
    def _run_graph_tests(self) -> Dict[str, Any]:
        """
        运行知识图谱性能测试
        """
        # 测试图谱构建
        test_data = [1] * 10
        graph_building_results = self.test_runner.run_load_test(
            self.graph_test.test_graph_building, test_data
        )
        
        # 测试图谱查询
        test_data = [i for i in range(1, 101)]
        graph_query_results = self.test_runner.run_load_test(
            self.graph_test.test_graph_query, test_data
        )
        
        return {
            'graph_building': graph_building_results,
            'graph_query': graph_query_results
        }
    
    def _run_system_tests(self) -> Dict[str, Any]:
        """
        运行系统整体性能测试
        """
        # 测试系统并发性能
        def test_system_performance(data):
            # 模拟系统操作
            start_time = time.time()
            time.sleep(0.01)  # 模拟处理时间
            response_time = time.time() - start_time
            return {'response_time': response_time}
        
        test_data = [i for i in range(1000)]
        system_results = self.test_runner.run_stress_test(test_system_performance, test_data)
        
        return {
            'system_stress': system_results
        }
    
    def _generate_performance_report(self, entity_results, search_results, 
                                  graph_results, system_results) -> Dict[str, Any]:
        """
        生成性能报告
        """
        report = {
            'title': 'Knowledge Base System Performance Test Report',
            'date': '2026-03-19',
            'summary': {
                'entity_extraction': {
                    'requests_per_second': entity_results['entity_extraction']['requests_per_second'],
                    'average_response_time': entity_results['entity_extraction']['average_response_time']
                },
                'search': {
                    'requests_per_second': search_results['search']['requests_per_second'],
                    'average_response_time': search_results['search']['average_response_time']
                },
                'knowledge_graph': {
                    'graph_building': {
                        'requests_per_second': graph_results['graph_building']['requests_per_second'],
                        'average_response_time': graph_results['graph_building']['average_response_time']
                    },
                    'graph_query': {
                        'requests_per_second': graph_results['graph_query']['requests_per_second'],
                        'average_response_time': graph_results['graph_query']['average_response_time']
                    }
                },
                'system': {
                    'max_concurrency': system_results['system_stress']['concurrency_results'][-1]['concurrency'],
                    'max_requests_per_second': max([r['requests_per_second'] for r in system_results['system_stress']['concurrency_results']])
                }
            },
            'details': {
                'entity_tests': entity_results,
                'search_tests': search_results,
                'graph_tests': graph_results,
                'system_tests': system_results
            },
            'recommendations': self._generate_performance_recommendations(
                entity_results, search_results, graph_results, system_results
            )
        }
        
        return report
    
    def _generate_performance_recommendations(self, entity_results, search_results, 
                                           graph_results, system_results) -> List[Dict[str, Any]]:
        """
        生成性能优化建议
        """
        recommendations = []
        
        # 基于测试结果生成建议
        if entity_results['entity_extraction']['average_response_time'] > 0.1:
            recommendations.append({
                'area': 'Entity Extraction',
                'issue': 'High average response time',
                'recommendation': 'Consider optimizing entity extraction algorithm or adding caching'
            })
        
        if search_results['search']['requests_per_second'] < 50:
            recommendations.append({
                'area': 'Search',
                'issue': 'Low requests per second',
                'recommendation': 'Optimize search index or consider using a more powerful search engine'
            })
        
        if graph_results['graph_building']['average_response_time'] > 0.5:
            recommendations.append({
                'area': 'Knowledge Graph Building',
                'issue': 'High graph building time',
                'recommendation': 'Optimize graph building algorithm or consider incremental updates'
            })
        
        return recommendations
    
    def compare_performance(self, baseline_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        比较性能结果
        
        Args:
            baseline_results: 基准性能结果
            
        Returns:
            比较结果
        """
        current_results = self.run_performance_tests()
        
        # 比较关键指标
        comparison = {
            'entity_extraction': {
                'baseline': baseline_results['summary']['entity_extraction'],
                'current': current_results['summary']['entity_extraction'],
                'improvement': {
                    'requests_per_second': (current_results['summary']['entity_extraction']['requests_per_second'] - 
                                          baseline_results['summary']['entity_extraction']['requests_per_second']) / 
                                         baseline_results['summary']['entity_extraction']['requests_per_second'] * 100,
                    'average_response_time': (baseline_results['summary']['entity_extraction']['average_response_time'] - 
                                           current_results['summary']['entity_extraction']['average_response_time']) / 
                                          baseline_results['summary']['entity_extraction']['average_response_time'] * 100
                }
            },
            'search': {
                'baseline': baseline_results['summary']['search'],
                'current': current_results['summary']['search'],
                'improvement': {
                    'requests_per_second': (current_results['summary']['search']['requests_per_second'] - 
                                          baseline_results['summary']['search']['requests_per_second']) / 
                                         baseline_results['summary']['search']['requests_per_second'] * 100,
                    'average_response_time': (baseline_results['summary']['search']['average_response_time'] - 
                                           current_results['summary']['search']['average_response_time']) / 
                                          baseline_results['summary']['search']['average_response_time'] * 100
                }
            }
        }
        
        return {
            'baseline': baseline_results,
            'current': current_results,
            'comparison': comparison
        }