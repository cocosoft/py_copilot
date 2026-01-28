"""
工作流知识库集成

实现工作流系统与知识库的集成，包括知识检索、文档处理、智能决策等功能。
"""
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from sqlalchemy.orm import Session

from app.modules.knowledge.services.knowledge_service import KnowledgeService
from app.services.knowledge.retrieval_service import RetrievalService, AdvancedRetrievalService
from app.agents.knowledge_integration import AgentKnowledgeIntegration

logger = logging.getLogger(__name__)


class KnowledgeWorkflowStep:
    """知识工作流步骤基类"""
    
    def __init__(self, name: str, description: str = ""):
        """初始化工作流步骤
        
        Args:
            name: 步骤名称
            description: 步骤描述
        """
        self.name = name
        self.description = description
        self.input_schema = {}
        self.output_schema = {}
    
    def execute(self, context: Dict[str, Any], db_session: Session) -> Dict[str, Any]:
        """执行步骤
        
        Args:
            context: 工作流上下文
            db_session: 数据库会话
            
        Returns:
            执行结果
        """
        raise NotImplementedError("子类必须实现execute方法")


class KnowledgeSearchStep(KnowledgeWorkflowStep):
    """知识搜索步骤"""
    
    def __init__(self):
        """初始化知识搜索步骤"""
        super().__init__(
            name="knowledge_search",
            description="在知识库中搜索相关信息"
        )
        self.input_schema = {
            "query": {"type": "string", "required": True},
            "knowledge_base_id": {"type": "integer", "required": False},
            "limit": {"type": "integer", "default": 5}
        }
        self.output_schema = {
            "search_results": {"type": "array"},
            "result_count": {"type": "integer"}
        }
    
    def execute(self, context: Dict[str, Any], db_session: Session) -> Dict[str, Any]:
        """执行知识搜索
        
        Args:
            context: 工作流上下文
            db_session: 数据库会话
            
        Returns:
            搜索结果
        """
        try:
            query = context.get("query")
            knowledge_base_id = context.get("knowledge_base_id")
            limit = context.get("limit", 5)
            
            if not query:
                return {"success": False, "error": "缺少搜索查询"}
            
            retrieval_service = RetrievalService()
            
            if knowledge_base_id:
                results = retrieval_service.search_documents(
                    query=query,
                    limit=limit,
                    knowledge_base_id=knowledge_base_id
                )
            else:
                results = retrieval_service.search_documents(
                    query=query,
                    limit=limit
                )
            
            logger.info(f"知识搜索完成，查询: {query}, 结果数: {len(results)}")
            
            return {
                "success": True,
                "search_results": results,
                "result_count": len(results),
                "query": query,
                "knowledge_base_id": knowledge_base_id
            }
            
        except Exception as e:
            logger.error(f"知识搜索失败: {e}")
            return {"success": False, "error": str(e)}


class DocumentAnalysisStep(KnowledgeWorkflowStep):
    """文档分析步骤"""
    
    def __init__(self):
        """初始化文档分析步骤"""
        super().__init__(
            name="document_analysis",
            description="分析文档内容并提取关键信息"
        )
        self.input_schema = {
            "document_content": {"type": "string", "required": True},
            "analysis_type": {"type": "string", "default": "summary"}
        }
        self.output_schema = {
            "analysis_result": {"type": "object"},
            "key_points": {"type": "array"},
            "summary": {"type": "string"}
        }
    
    def execute(self, context: Dict[str, Any], db_session: Session) -> Dict[str, Any]:
        """执行文档分析
        
        Args:
            context: 工作流上下文
            db_session: 数据库会话
            
        Returns:
            分析结果
        """
        try:
            document_content = context.get("document_content")
            analysis_type = context.get("analysis_type", "summary")
            
            if not document_content:
                return {"success": False, "error": "缺少文档内容"}
            
            # 简单的文档分析实现
            analysis_result = self._analyze_document(document_content, analysis_type)
            
            logger.info(f"文档分析完成，类型: {analysis_type}, 内容长度: {len(document_content)}")
            
            return {
                "success": True,
                "analysis_result": analysis_result,
                "key_points": analysis_result.get("key_points", []),
                "summary": analysis_result.get("summary", ""),
                "analysis_type": analysis_type
            }
            
        except Exception as e:
            logger.error(f"文档分析失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_document(self, content: str, analysis_type: str) -> Dict[str, Any]:
        """分析文档内容
        
        Args:
            content: 文档内容
            analysis_type: 分析类型
            
        Returns:
            分析结果
        """
        # 简单的分析实现（实际项目中可以使用NLP库）
        lines = content.split('\n')
        sentences = content.split('.')
        words = content.split()
        
        result = {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "line_count": len(lines),
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0
        }
        
        if analysis_type == "summary":
            # 生成摘要（取前3句话）
            summary_sentences = sentences[:3]
            result["summary"] = ". ".join(summary_sentences) + "."
            
        elif analysis_type == "key_points":
            # 提取关键点（基于关键词）
            key_points = self._extract_key_points(content)
            result["key_points"] = key_points
            
        elif analysis_type == "structure":
            # 分析文档结构
            result["has_headings"] = any(line.strip().endswith(':') for line in lines)
            result["has_lists"] = any(line.strip().startswith('-') or line.strip().startswith('*') for line in lines)
            result["paragraph_count"] = len([line for line in lines if line.strip()])
        
        return result
    
    def _extract_key_points(self, content: str) -> List[str]:
        """提取关键点
        
        Args:
            content: 文档内容
            
        Returns:
            关键点列表
        """
        # 简单的关键点提取（实际项目中可以使用更复杂的算法）
        sentences = content.split('.')
        key_points = []
        
        # 提取包含重要关键词的句子
        important_keywords = ['重要', '关键', '主要', '核心', '重点', '必须', '需要', '应该']
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # 只处理有内容的句子
                # 检查是否包含重要关键词
                if any(keyword in sentence for keyword in important_keywords):
                    key_points.append(sentence)
                
                # 提取较长的句子作为关键点（简化逻辑）
                elif len(sentence) > 50 and len(key_points) < 5:
                    key_points.append(sentence)
        
        return key_points[:5]  # 最多返回5个关键点


class KnowledgeBasedDecisionStep(KnowledgeWorkflowStep):
    """基于知识的决策步骤"""
    
    def __init__(self):
        """初始化决策步骤"""
        super().__init__(
            name="knowledge_decision",
            description="基于知识库信息做出智能决策"
        )
        self.input_schema = {
            "decision_context": {"type": "string", "required": True},
            "options": {"type": "array", "required": True},
            "criteria": {"type": "object", "default": {}}
        }
        self.output_schema = {
            "selected_option": {"type": "string"},
            "decision_reasoning": {"type": "string"},
            "confidence_score": {"type": "number"},
            "supporting_knowledge": {"type": "array"}
        }
    
    def execute(self, context: Dict[str, Any], db_session: Session) -> Dict[str, Any]:
        """执行基于知识的决策
        
        Args:
            context: 工作流上下文
            db_session: 数据库会话
            
        Returns:
            决策结果
        """
        try:
            decision_context = context.get("decision_context")
            options = context.get("options", [])
            criteria = context.get("criteria", {})
            
            if not decision_context:
                return {"success": False, "error": "缺少决策上下文"}
            
            if not options:
                return {"success": False, "error": "缺少决策选项"}
            
            # 搜索相关知识
            retrieval_service = RetrievalService()
            knowledge_results = retrieval_service.search_documents(
                query=decision_context,
                limit=10
            )
            
            # 基于知识做出决策
            decision_result = self._make_decision(
                context=decision_context,
                options=options,
                criteria=criteria,
                knowledge_results=knowledge_results
            )
            
            logger.info(f"知识决策完成，选项数: {len(options)}, 选择: {decision_result.get('selected_option')}")
            
            return {
                "success": True,
                **decision_result
            }
            
        except Exception as e:
            logger.error(f"知识决策失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _make_decision(self, 
                      context: str, 
                      options: List[str], 
                      criteria: Dict[str, Any],
                      knowledge_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基于知识做出决策
        
        Args:
            context: 决策上下文
            options: 选项列表
            criteria: 决策标准
            knowledge_results: 相关知识结果
            
        Returns:
            决策结果
        """
        if not options:
            return {
                "selected_option": "",
                "decision_reasoning": "没有可用选项",
                "confidence_score": 0.0,
                "supporting_knowledge": []
            }
        
        # 简单的决策逻辑（实际项目中可以使用更复杂的算法）
        # 基于知识结果与选项的匹配度
        option_scores = {}
        supporting_knowledge = []
        
        for option in options:
            score = 0.0
            option_knowledge = []
            
            # 计算选项与知识的匹配度
            for knowledge in knowledge_results:
                knowledge_content = knowledge.get('content', '').lower()
                option_lower = option.lower()
                
                # 检查知识内容是否包含选项关键词
                if option_lower in knowledge_content:
                    match_score = len(option_lower) / len(knowledge_content) * 0.5
                    score += match_score
                    
                    # 记录支持知识
                    if len(option_knowledge) < 3:  # 最多记录3个支持知识
                        option_knowledge.append({
                            "content": knowledge_content[:100] + "...",
                            "score": knowledge.get('score', 0.0)
                        })
            
            option_scores[option] = {
                "score": min(1.0, score),
                "supporting_knowledge": option_knowledge
            }
        
        # 选择得分最高的选项
        if option_scores:
            best_option = max(option_scores.keys(), key=lambda x: option_scores[x]["score"])
            best_score = option_scores[best_option]["score"]
            best_knowledge = option_scores[best_option]["supporting_knowledge"]
            
            return {
                "selected_option": best_option,
                "decision_reasoning": f"基于知识库匹配度选择，得分: {best_score:.2f}",
                "confidence_score": best_score,
                "supporting_knowledge": best_knowledge
            }
        else:
            # 如果没有匹配的知识，随机选择一个选项
            import random
            selected_option = random.choice(options)
            
            return {
                "selected_option": selected_option,
                "decision_reasoning": "没有找到相关知识，随机选择",
                "confidence_score": 0.1,
                "supporting_knowledge": []
            }


class KnowledgeWorkflowEngine:
    """知识工作流引擎"""
    
    def __init__(self, db_session: Session):
        """初始化工作流引擎
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self.steps = {}
        self.workflows = {}
        self._register_default_steps()
    
    def _register_default_steps(self):
        """注册默认步骤"""
        self.register_step(KnowledgeSearchStep())
        self.register_step(DocumentAnalysisStep())
        self.register_step(KnowledgeBasedDecisionStep())
    
    def register_step(self, step: KnowledgeWorkflowStep):
        """注册工作流步骤
        
        Args:
            step: 工作流步骤
        """
        self.steps[step.name] = step
        logger.info(f"注册工作流步骤: {step.name}")
    
    def create_workflow(self, name: str, steps_config: List[Dict[str, Any]]) -> str:
        """创建工作流
        
        Args:
            name: 工作流名称
            steps_config: 步骤配置列表
            
        Returns:
            工作流ID
        """
        workflow_id = f"workflow_{name}_{datetime.now().timestamp()}"
        
        workflow = {
            "id": workflow_id,
            "name": name,
            "steps": steps_config,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.workflows[workflow_id] = workflow
        logger.info(f"创建工作流: {name} (ID: {workflow_id})")
        
        return workflow_id
    
    def execute_workflow(self, workflow_id: str, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流
        
        Args:
            workflow_id: 工作流ID
            initial_context: 初始上下文
            
        Returns:
            执行结果
        """
        try:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                return {"success": False, "error": "工作流不存在"}
            
            steps_config = workflow.get("steps", [])
            context = initial_context.copy()
            execution_results = []
            
            logger.info(f"开始执行工作流: {workflow['name']}")
            
            for i, step_config in enumerate(steps_config):
                step_name = step_config.get("name")
                step_params = step_config.get("params", {})
                
                if step_name not in self.steps:
                    return {
                        "success": False, 
                        "error": f"步骤 '{step_name}' 未注册",
                        "executed_steps": execution_results
                    }
                
                # 合并步骤参数到上下文
                step_context = {**context, **step_params}
                
                # 执行步骤
                step = self.steps[step_name]
                step_result = step.execute(step_context, self.db)
                
                execution_result = {
                    "step_name": step_name,
                    "step_index": i,
                    "success": step_result.get("success", False),
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                }
                
                execution_results.append(execution_result)
                
                # 如果步骤失败，停止执行
                if not step_result.get("success", False):
                    logger.error(f"工作流步骤失败: {step_name}")
                    return {
                        "success": False,
                        "error": f"步骤 '{step_name}' 执行失败: {step_result.get('error')}",
                        "executed_steps": execution_results
                    }
                
                # 将步骤结果合并到上下文
                context.update(step_result)
                
                logger.info(f"工作流步骤完成: {step_name}")
            
            logger.info(f"工作流执行完成: {workflow['name']}")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "final_context": context,
                "execution_results": execution_results,
                "total_steps": len(steps_config),
                "completed_steps": len(execution_results)
            }
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_workflow_info(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流信息
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流信息
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"success": False, "error": "工作流不存在"}
        
        return {"success": True, "workflow": workflow}
    
    def list_available_steps(self) -> List[Dict[str, Any]]:
        """列出可用的工作流步骤
        
        Returns:
            步骤列表
        """
        steps_info = []
        
        for step_name, step in self.steps.items():
            steps_info.append({
                "name": step_name,
                "description": step.description,
                "input_schema": step.input_schema,
                "output_schema": step.output_schema
            })
        
        return steps_info