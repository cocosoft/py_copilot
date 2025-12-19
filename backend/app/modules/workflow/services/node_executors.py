from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
import traceback
from app.services.knowledge.knowledge_graph_service import KnowledgeGraphService
from app.services.knowledge.semantic_search_service import SemanticSearchService
from app.services.knowledge.advanced_text_processor import AdvancedTextProcessor

# 导入性能监控装饰器
from app.core.logging_config import log_execution

logger = logging.getLogger(__name__)

class BaseNodeExecutor:
    """节点执行器基类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.node_type = self.__class__.__name__.replace('Executor', '').lower()
    
    @log_execution
    def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点逻辑"""
        logger.info(f"开始执行节点: {self.node_type}")
        
        # 验证输入参数
        if not isinstance(config, dict):
            error_msg = f"配置参数必须是字典类型, 实际类型: {type(config)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "node_type": self.node_type
            }
        
        if not isinstance(context, dict):
            error_msg = f"上下文参数必须是字典类型, 实际类型: {type(context)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "node_type": self.node_type
            }
        
        try:
            result = self._execute_impl(config, context)
            
            # 验证执行结果
            if not isinstance(result, dict):
                error_msg = f"节点执行结果必须是字典类型, 实际类型: {type(result)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "node_type": self.node_type
                }
            
            # 确保结果包含必要的字段
            if "success" not in result:
                result["success"] = True
            
            logger.info(f"节点执行完成: {self.node_type}, 成功={result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"节点执行失败: {self.node_type}, 错误: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "node_type": self.node_type
            }
    
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """子类必须实现此方法"""
        raise NotImplementedError("子类必须实现_execute_impl方法")

class StartNodeExecutor(BaseNodeExecutor):
    """开始节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行开始节点 - 只是传递上下文数据"""
        logger.debug(f"开始节点执行: 配置={config}, 上下文大小={len(context)}")
        
        return {
            "success": True,
            "message": "工作流开始执行",
            "context_data": context
        }

class EndNodeExecutor(BaseNodeExecutor):
    """结束节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行结束节点 - 汇总工作流结果"""
        logger.debug(f"结束节点执行: 配置={config}, 上下文大小={len(context)}")
        
        return {
            "success": True,
            "message": "工作流执行完成",
            "final_result": context
        }

class InputNodeExecutor(BaseNodeExecutor):
    """输入节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行输入节点 - 处理用户输入数据"""
        logger.debug(f"输入节点执行: 配置={config}, 上下文大小={len(context)}")
        
        input_field = config.get("input_field", "input")
        input_value = config.get("default_value", "")
        
        # 验证输入字段
        if not isinstance(input_field, str):
            error_msg = f"输入字段必须是字符串类型, 实际类型: {type(input_field)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 如果上下文中有输入数据，使用它
        if input_field in context:
            input_value = context[input_field]
            logger.debug(f"从上下文中获取输入值: {input_field}={input_value}")
        else:
            logger.debug(f"使用默认输入值: {input_field}={input_value}")
        
        return {
            "success": True,
            "input_value": input_value,
            "input_field": input_field
        }

class OutputNodeExecutor(BaseNodeExecutor):
    """输出节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行输出节点 - 格式化输出结果"""
        logger.debug(f"输出节点执行: 配置={config}, 上下文大小={len(context)}")
        
        output_format = config.get("format", "json")
        output_fields = config.get("fields", [])
        
        # 验证输出格式
        valid_formats = ["json", "xml", "csv", "text"]
        if output_format not in valid_formats:
            logger.warning(f"不支持的输出格式: {output_format}, 使用默认格式: json")
            output_format = "json"
        
        # 验证输出字段
        if not isinstance(output_fields, list):
            logger.warning(f"输出字段必须是列表类型, 实际类型: {type(output_fields)}, 使用空列表")
            output_fields = []
        
        # 根据配置过滤输出字段
        if output_fields:
            filtered_output = {}
            for field in output_fields:
                if not isinstance(field, str):
                    logger.warning(f"跳过非字符串字段: {field}")
                    continue
                if field in context:
                    filtered_output[field] = context[field]
                    logger.debug(f"包含输出字段: {field}")
                else:
                    logger.debug(f"跳过不存在的字段: {field}")
        else:
            filtered_output = context
            logger.debug(f"包含所有上下文字段: 数量={len(context)}")
        
        return {
            "success": True,
            "output_format": output_format,
            "output_data": filtered_output,
            "field_count": len(filtered_output)
        }

class KnowledgeSearchExecutor(BaseNodeExecutor):
    """知识搜索节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行知识搜索节点"""
        logger.debug(f"知识搜索节点执行: 配置={config}")
        
        # 获取搜索查询
        search_query = config.get("search_query")
        if not search_query:
            raise ValueError("搜索查询不能为空")
        
        # 验证搜索查询类型
        if not isinstance(search_query, str):
            raise ValueError(f"搜索查询必须是字符串类型, 实际类型: {type(search_query)}")
        
        # 获取配置参数
        knowledge_base_id = config.get("knowledge_base_id")
        entity_types = config.get("entity_types")
        confidence_threshold = config.get("confidence_threshold", 0.5)
        max_results = config.get("max_results", 10)
        include_relationships = config.get("include_relationships", True)
        
        # 验证参数范围
        if confidence_threshold < 0 or confidence_threshold > 1:
            logger.warning(f"置信度阈值超出范围: {confidence_threshold}, 使用默认值: 0.5")
            confidence_threshold = 0.5
        
        if max_results <= 0 or max_results > 100:
            logger.warning(f"最大结果数超出范围: {max_results}, 使用默认值: 10")
            max_results = 10
        
        # 调用语义搜索服务
        semantic_search_service = SemanticSearchService()
        
        search_params = {
            "query": search_query,
            "knowledge_base_id": knowledge_base_id,
            "entity_types": entity_types,
            "confidence_threshold": confidence_threshold,
            "max_results": max_results,
            "include_relationships": include_relationships
        }
        
        logger.info(f"执行知识搜索: 查询='{search_query}', 最大结果={max_results}")
        
        # 执行搜索（同步调用）
        results = semantic_search_service.semantic_search(
            query=search_query,
            n_results=max_results,
            knowledge_base_id=knowledge_base_id
        )
        
        logger.info(f"知识搜索完成: 找到 {len(results)} 个结果")
        
        return {
            "success": True,
            "results": results,
            "total_count": len(results),
            "search_params": search_params
        }

class EntityExtractionExecutor(BaseNodeExecutor):
    """实体抽取节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行实体抽取节点"""
        logger.debug(f"实体抽取节点执行: 配置={config}")
        
        # 获取输入文本
        text_input = config.get("text_input")
        if not text_input:
            raise ValueError("输入文本不能为空")
        
        # 验证输入文本类型
        if not isinstance(text_input, str):
            raise ValueError(f"输入文本必须是字符串类型, 实际类型: {type(text_input)}")
        
        # 获取配置参数
        entity_types = config.get("entity_types")
        confidence_threshold = config.get("confidence_threshold", 0.5)
        
        # 验证置信度阈值范围
        if confidence_threshold < 0 or confidence_threshold > 1:
            logger.warning(f"置信度阈值超出范围: {confidence_threshold}, 使用默认值: 0.5")
            confidence_threshold = 0.5
        
        # 调用文本处理器进行实体抽取
        text_processor = AdvancedTextProcessor()
        
        logger.info(f"执行实体抽取: 文本长度={len(text_input)}, 实体类型={entity_types}")
        
        # 执行实体抽取（同步调用）
        entities, relationships = text_processor.extract_entities_relationships(text_input)
        
        logger.info(f"实体抽取完成: 找到 {len(entities)} 个实体")
        
        return {
            "success": True,
            "entities": entities,
            "total_count": len(entities),
            "extraction_params": {
                "entity_types": entity_types,
                "confidence_threshold": confidence_threshold
            }
        }

class RelationshipAnalysisExecutor(BaseNodeExecutor):
    """关系分析节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行关系分析节点"""
        logger.debug(f"关系分析节点执行: 配置={config}")
        
        # 获取实体ID列表
        entity_ids = config.get("entity_ids", [])
        if not entity_ids:
            raise ValueError("实体ID列表不能为空")
        
        # 验证实体ID列表类型
        if not isinstance(entity_ids, list):
            raise ValueError(f"实体ID列表必须是列表类型, 实际类型: {type(entity_ids)}")
        
        # 验证实体ID列表内容
        if not all(isinstance(entity_id, str) for entity_id in entity_ids):
            raise ValueError("实体ID列表中的元素必须是字符串类型")
        
        # 获取配置参数
        relationship_types = config.get("relationship_types")
        max_depth = config.get("max_depth", 2)
        
        # 验证最大深度范围
        if max_depth <= 0 or max_depth > 10:
            logger.warning(f"最大深度超出范围: {max_depth}, 使用默认值: 2")
            max_depth = 2
        
        # 调用知识图谱服务进行关系分析
        knowledge_graph_service = KnowledgeGraphService()
        
        logger.info(f"执行关系分析: 实体数量={len(entity_ids)}, 最大深度={max_depth}")
        
        # 执行关系分析（同步调用）
        relationships = knowledge_graph_service.analyze_relationships(
            entity_ids,
            relationship_types=relationship_types,
            max_depth=max_depth
        )
        
        return {
            "success": True,
            "relationships": relationships,
            "total_count": len(relationships),
            "analysis_params": {
                "entity_ids": entity_ids,
                "relationship_types": relationship_types,
                "max_depth": max_depth
            }
        }

class KnowledgeGraphQueryExecutor(BaseNodeExecutor):
    """知识图谱查询节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行知识图谱查询节点"""
        logger.debug(f"知识图谱查询节点执行: 配置={config}")
        
        # 获取查询参数
        query_type = config.get("query_type", "entity")  # entity, relationship, path
        entity_id = config.get("entity_id")
        relationship_type = config.get("relationship_type")
        
        # 验证查询类型
        valid_query_types = ["entity", "relationship", "path"]
        if query_type not in valid_query_types:
            raise ValueError(f"不支持的查询类型: {query_type}, 有效类型: {valid_query_types}")
        
        knowledge_graph_service = KnowledgeGraphService()
        
        logger.info(f"执行知识图谱查询: 类型={query_type}, 实体ID={entity_id}")
        
        if query_type == "entity":
            if not entity_id:
                raise ValueError("实体查询需要提供entity_id")
            if not isinstance(entity_id, str):
                raise ValueError(f"实体ID必须是字符串类型, 实际类型: {type(entity_id)}")
            result = knowledge_graph_service.get_entity(entity_id)
        elif query_type == "relationship":
            if not entity_id:
                raise ValueError("关系查询需要提供entity_id")
            if not isinstance(entity_id, str):
                raise ValueError(f"实体ID必须是字符串类型, 实际类型: {type(entity_id)}")
            result = knowledge_graph_service.get_entity_relationships(entity_id)
        elif query_type == "path":
            source_entity = config.get("source_entity")
            target_entity = config.get("target_entity")
            if not source_entity or not target_entity:
                raise ValueError("路径查询需要提供source_entity和target_entity")
            if not isinstance(source_entity, str) or not isinstance(target_entity, str):
                raise ValueError("源实体和目标实体必须是字符串类型")
            result = knowledge_graph_service.find_path(source_entity, target_entity)
        
        logger.info(f"知识图谱查询完成: 类型={query_type}, 结果类型={type(result)}")
        
        return {
            "success": True,
            "query_type": query_type,
            "result": result
        }

class KnowledgeGraphVisualizationExecutor(BaseNodeExecutor):
    """知识图谱可视化节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行知识图谱可视化节点"""
        logger.debug(f"知识图谱可视化节点执行: 配置={config}")
        
        # 获取可视化参数
        entity_ids = config.get("entity_ids", [])
        visualization_type = config.get("visualization_type", "graph")  # graph, network, tree
        
        # 验证可视化类型
        valid_visualization_types = ["graph", "network", "tree"]
        if visualization_type not in valid_visualization_types:
            logger.warning(f"不支持的的可视化类型: {visualization_type}, 使用默认值: graph")
            visualization_type = "graph"
        
        # 验证实体ID列表类型
        if entity_ids and not isinstance(entity_ids, list):
            raise ValueError(f"实体ID列表必须是列表类型, 实际类型: {type(entity_ids)}")
        
        # 验证实体ID列表内容
        if entity_ids and not all(isinstance(entity_id, str) for entity_id in entity_ids):
            raise ValueError("实体ID列表中的元素必须是字符串类型")
        
        knowledge_graph_service = KnowledgeGraphService(self.db)
        
        logger.info(f"执行知识图谱可视化: 类型={visualization_type}, 实体数量={len(entity_ids)}")
        
        # 生成可视化数据
        if entity_ids:
            # 基于特定实体生成子图
            visualization_data = knowledge_graph_service.generate_subgraph(entity_ids)
        else:
            # 生成整个知识图谱的概览
            visualization_data = knowledge_graph_service.generate_overview()
        
        logger.info(f"知识图谱可视化完成: 实体数量={len(visualization_data.get('entities', []))}, 关系数量={len(visualization_data.get('relationships', []))}")
        
        return {
            "success": True,
            "visualization_type": visualization_type,
            "data": visualization_data,
            "entity_count": len(visualization_data.get("entities", [])),
            "relationship_count": len(visualization_data.get("relationships", []))
        }

class BranchNodeExecutor(BaseNodeExecutor):
    """分支节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行分支节点 - 根据配置将工作流分为多个并行或条件分支"""
        logger.debug(f"分支节点执行: 配置={config}, 上下文大小={len(context)}")
        
        # 获取分支配置
        branch_count = config.get("branchCount", 2)
        branch_type = config.get("branchType", "条件分支")
        
        # 验证分支数量
        if not isinstance(branch_count, int) or branch_count < 2:
            logger.warning(f"分支数量无效: {branch_count}, 使用默认值: 2")
            branch_count = 2
        
        # 验证分支类型
        valid_branch_types = ["条件分支", "并行分支", "循环分支"]
        if branch_type not in valid_branch_types:
            logger.warning(f"分支类型无效: {branch_type}, 使用默认值: 条件分支")
            branch_type = "条件分支"
        
        # 生成分支上下文
        branches = []
        for i in range(branch_count):
            branch_name = f"分支{i+1}"
            branch_data = {
                "branch_id": f"branch_{i+1}",
                "branch_name": branch_name,
                "branch_type": branch_type,
                "context_data": context.copy()  # 复制上下文数据给每个分支
            }
            branches.append(branch_data)
        
        return {
            "success": True,
            "message": f"成功创建{branch_count}个分支",
            "branches": branches,
            "branch_count": branch_count,
            "branch_type": branch_type
        }

class ConditionNodeExecutor(BaseNodeExecutor):
    """条件节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行条件节点 - 根据条件判断决定工作流执行路径"""
        logger.debug(f"条件节点执行: 配置={config}, 上下文大小={len(context)}")
        
        # 获取条件配置
        condition_field = config.get("conditionField")
        operator = config.get("operator", "===")
        condition_value = config.get("value")
        
        # 验证必要参数
        if not condition_field:
            raise ValueError("条件字段不能为空")
        
        # 验证操作符
        valid_operators = ["===", "!==", ">", "<", ">=", "<=", "contains"]
        if operator not in valid_operators:
            logger.warning(f"操作符无效: {operator}, 使用默认值: ===")
            operator = "==="
        
        # 获取上下文中的字段值
        context_value = context.get(condition_field)
        
        # 执行条件判断
        result = False
        try:
            if operator == "===":
                result = context_value == condition_value
            elif operator == "!==":
                result = context_value != condition_value
            elif operator == ">":
                result = float(context_value) > float(condition_value)
            elif operator == "<":
                result = float(context_value) < float(condition_value)
            elif operator == ">=":
                result = float(context_value) >= float(condition_value)
            elif operator == "<=":
                result = float(context_value) <= float(condition_value)
            elif operator == "contains":
                if isinstance(context_value, str) and isinstance(condition_value, str):
                    result = condition_value.lower() in context_value.lower()
                elif isinstance(context_value, list):
                    result = condition_value in context_value
        except Exception as e:
            logger.error(f"条件判断失败: {str(e)}")
            result = False
        
        # 生成条件判断结果
        return {
            "success": True,
            "message": "条件判断完成",
            "condition_result": result,
            "condition_field": condition_field,
            "operator": operator,
            "condition_value": condition_value,
            "context_value": context_value,
            "next_branch": "分支1" if result else "分支2"
        }

class ProcessNodeExecutor(BaseNodeExecutor):
    """处理节点执行器"""
    
    @log_execution
    def _execute_impl(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行处理节点 - 根据配置进行数据处理"""
        logger.debug(f"处理节点执行: 配置={config}, 上下文大小={len(context)}")
        
        # 获取处理配置
        process_type = config.get("processType", "string")
        input_field = config.get("inputField")
        output_field = config.get("outputField", "processed_data")
        process_params = config.get("processParams", {})
        
        # 验证必要参数
        if not input_field:
            raise ValueError("输入字段不能为空")
        
        # 获取输入数据
        input_value = context.get(input_field)
        if input_value is None:
            logger.warning(f"输入字段 '{input_field}' 在上下文中不存在")
            return {
                "success": False,
                "message": f"输入字段 '{input_field}' 在上下文中不存在",
                "input_field": input_field,
                "output_field": output_field
            }
        
        # 执行数据处理
        processed_value = input_value
        try:
            if process_type == "string":
                # 字符串处理
                operation = process_params.get("operation", "uppercase")
                if operation == "uppercase":
                    processed_value = str(input_value).upper()
                elif operation == "lowercase":
                    processed_value = str(input_value).lower()
                elif operation == "trim":
                    processed_value = str(input_value).strip()
                elif operation == "substring":
                    start = process_params.get("start", 0)
                    end = process_params.get("end")
                    processed_value = str(input_value)[start:end]
                elif operation == "replace":
                    old = process_params.get("old", "")
                    new = process_params.get("new", "")
                    processed_value = str(input_value).replace(old, new)
            elif process_type == "number":
                # 数值处理
                operation = process_params.get("operation", "add")
                num = float(process_params.get("number", 0))
                if operation == "add":
                    processed_value = float(input_value) + num
                elif operation == "subtract":
                    processed_value = float(input_value) - num
                elif operation == "multiply":
                    processed_value = float(input_value) * num
                elif operation == "divide":
                    if num == 0:
                        raise ValueError("除数不能为0")
                    processed_value = float(input_value) / num
                elif operation == "round":
                    decimals = int(process_params.get("decimals", 0))
                    processed_value = round(float(input_value), decimals)
            elif process_type == "json":
                # JSON处理
                operation = process_params.get("operation", "parse")
                if operation == "parse":
                    processed_value = json.loads(str(input_value))
                elif operation == "stringify":
                    processed_value = json.dumps(input_value)
            elif process_type == "array":
                # 数组处理
                operation = process_params.get("operation", "join")
                if operation == "join":
                    separator = process_params.get("separator", ",")
                    processed_value = separator.join(map(str, input_value))
                elif operation == "length":
                    processed_value = len(input_value)
                elif operation == "sort":
                    processed_value = sorted(input_value)
        except Exception as e:
            logger.error(f"数据处理失败: {str(e)}")
            return {
                "success": False,
                "message": f"数据处理失败: {str(e)}",
                "input_field": input_field,
                "output_field": output_field
            }
        
        # 返回处理结果
        return {
            "success": True,
            "message": "数据处理完成",
            "input_field": input_field,
            "output_field": output_field,
            "input_value": input_value,
            "processed_value": processed_value,
            "process_type": process_type
        }