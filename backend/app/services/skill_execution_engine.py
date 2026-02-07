"""技能执行引擎核心组件"""
import json
import os
import tempfile
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.skill import Skill, SkillExecutionLog, SkillArtifact, SkillDependency
from app.core.database import get_db
from app.core.config import settings

# 导入本地技能匹配服务
from app.services.local_llm.skill_matching import LocalSkillMatchingService


class ParameterValidator:
    """参数验证器"""
    
    @staticmethod
    def validate_parameters(skill: Skill, input_params: Dict[str, Any]) -> Dict[str, Any]:
        """验证输入参数是否符合技能定义的参数模式"""
        if not skill.parameters_schema:
            return input_params
            
        schema = skill.parameters_schema
        validated_params = {}
        
        # 遍历参数schema定义
        for param_name, param_def in schema.items():
            # 检查必填参数
            if param_def.get("required", False) and param_name not in input_params:
                raise ValueError(f"参数 {param_name} 是必填项")
                
            # 获取参数值，使用默认值如果不存在
            param_value = input_params.get(param_name, param_def.get("default"))
            
            # 检查参数类型
            if param_value is not None:
                param_value = ParameterValidator._validate_parameter_type(param_name, param_value, param_def)
                
                # 检查枚举值
                if "enum" in param_def and param_value not in param_def["enum"]:
                    raise ValueError(f"参数 {param_name} 必须是以下值之一: {', '.join(param_def['enum'])}")
                
                # 检查最小/最大值
                if "minimum" in param_def and isinstance(param_value, (int, float)):
                    if param_value < param_def["minimum"]:
                        raise ValueError(f"参数 {param_name} 不能小于 {param_def['minimum']}")
                if "maximum" in param_def and isinstance(param_value, (int, float)):
                    if param_value > param_def["maximum"]:
                        raise ValueError(f"参数 {param_name} 不能大于 {param_def['maximum']}")
                
                # 检查最小/最大长度
                if "minLength" in param_def and isinstance(param_value, str):
                    if len(param_value) < param_def["minLength"]:
                        raise ValueError(f"参数 {param_name} 长度不能小于 {param_def['minLength']}")
                if "maxLength" in param_def and isinstance(param_value, str):
                    if len(param_value) > param_def["maxLength"]:
                        raise ValueError(f"参数 {param_name} 长度不能大于 {param_def['maxLength']}")
                
                # 检查正则表达式模式
                if "pattern" in param_def and isinstance(param_value, str):
                    import re
                    if not re.match(param_def["pattern"], param_value):
                        raise ValueError(f"参数 {param_name} 不符合模式要求: {param_def['pattern']}")
            
            validated_params[param_name] = param_value
            
        return validated_params
    
    @staticmethod
    def _validate_parameter_type(param_name: str, param_value: Any, param_def: Dict[str, Any]) -> Any:
        """验证参数类型"""
        expected_type = param_def.get("type")
        if not expected_type:
            return param_value
            
        try:
            if expected_type == "string":
                return ParameterValidator._validate_string(param_name, param_value, param_def)
            elif expected_type == "integer":
                return ParameterValidator._validate_integer(param_name, param_value, param_def)
            elif expected_type == "number":
                return ParameterValidator._validate_number(param_name, param_value, param_def)
            elif expected_type == "boolean":
                return ParameterValidator._validate_boolean(param_name, param_value, param_def)
            elif expected_type == "array":
                return ParameterValidator._validate_array(param_name, param_value, param_def)
            elif expected_type == "object":
                return ParameterValidator._validate_object(param_name, param_value, param_def)
            else:
                return param_value
                
        except (ValueError, TypeError) as e:
            raise ValueError(f"参数 {param_name} 类型错误: {str(e)}")
    
    @staticmethod
    def _validate_string(param_name: str, param_value: Any, param_def: Dict[str, Any]) -> str:
        """验证字符串类型"""
        if isinstance(param_value, str):
            return param_value
        return str(param_value)
    
    @staticmethod
    def _validate_integer(param_name: str, param_value: Any, param_def: Dict[str, Any]) -> int:
        """验证整数类型"""
        if isinstance(param_value, int):
            return param_value
        return int(param_value)
    
    @staticmethod
    def _validate_number(param_name: str, param_value: Any, param_def: Dict[str, Any]) -> float:
        """验证数字类型"""
        if isinstance(param_value, (int, float)):
            return float(param_value)
        return float(param_value)
    
    @staticmethod
    def _validate_boolean(param_name: str, param_value: Any, param_def: Dict[str, Any]) -> bool:
        """验证布尔类型"""
        if isinstance(param_value, bool):
            return param_value
        if isinstance(param_value, str):
            if param_value.lower() in ("true", "1", "yes"):
                return True
            elif param_value.lower() in ("false", "0", "no"):
                return False
        return bool(param_value)
    
    @staticmethod
    def _validate_array(param_name: str, param_value: Any, param_def: Dict[str, Any]) -> List[Any]:
        """验证数组类型"""
        if isinstance(param_value, list):
            return param_value
        
        # 尝试解析JSON字符串
        if isinstance(param_value, str):
            try:
                parsed = json.loads(param_value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        
        # 如果是逗号分隔的字符串，转换为数组
        if isinstance(param_value, str):
            return [item.strip() for item in param_value.split(",") if item.strip()]
        
        # 其他情况转换为单元素数组
        return [param_value]
    
    @staticmethod
    def _validate_object(param_name: str, param_value: Any, param_def: Dict[str, Any]) -> Dict[str, Any]:
        """验证对象类型"""
        if isinstance(param_value, dict):
            return param_value
        
        # 尝试解析JSON字符串
        if isinstance(param_value, str):
            try:
                parsed = json.loads(param_value)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"参数 {param_name} 必须是有效的对象或JSON字符串")


class ArtifactManager:
    """Artifact管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.artifacts_dir = os.path.join(settings.upload_folder, "skill_artifacts")
        os.makedirs(self.artifacts_dir, exist_ok=True)
    
    def create_artifact(self, execution_id: int, name: str, artifact_type: str, content: str) -> SkillArtifact:
        """创建新的Artifact"""
        # 创建文件路径
        file_path = None
        if len(content) > 10000:  # 如果内容较大，保存到文件
            file_name = f"{uuid.uuid4()}.{artifact_type}"
            file_path = os.path.join(self.artifacts_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            artifact = SkillArtifact(
                skill_execution_id=execution_id,
                name=name,
                type=artifact_type,
                file_path=file_path,
                created_at=datetime.now()
            )
        else:
            artifact = SkillArtifact(
                skill_execution_id=execution_id,
                name=name,
                type=artifact_type,
                content=content,
                created_at=datetime.now()
            )
        
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        
        return artifact
    
    def get_artifacts(self, execution_id: int) -> List[SkillArtifact]:
        """获取指定执行的所有Artifacts"""
        return self.db.query(SkillArtifact).filter(SkillArtifact.skill_execution_id == execution_id).all()
    
    def get_artifact_content(self, artifact: SkillArtifact) -> str:
        """获取Artifact的内容"""
        if artifact.file_path and os.path.exists(artifact.file_path):
            with open(artifact.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return artifact.content or ""


class ExecutionEnvironment:
    """执行环境管理器"""
    
    def __init__(self, skill: Skill):
        self.skill = skill
        self.temp_dir = None
    
    def __enter__(self):
        """创建临时执行环境"""
        self.temp_dir = tempfile.mkdtemp(prefix=f"skill_{self.skill.name}_")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """清理临时执行环境"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def prepare_environment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """准备执行环境"""
        # 创建工作目录结构
        work_dir = os.path.join(self.temp_dir, "work")
        resources_dir = os.path.join(self.temp_dir, "resources")
        
        os.makedirs(work_dir, exist_ok=True)
        os.makedirs(resources_dir, exist_ok=True)
        
        # 返回环境信息
        return {
            "work_dir": work_dir,
            "resources_dir": resources_dir,
            "skill_name": self.skill.name,
            "skill_version": self.skill.version,
            "params": params
        }


class SkillExecutionEngine:
    """技能执行引擎核心类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.parameter_validator = ParameterValidator()
        self.artifact_manager = ArtifactManager(db)
        self.local_skill_matching_service = LocalSkillMatchingService()
    
    async def execute(self, skill_id: int, task: Optional[str] = None, params: Optional[Dict[str, Any]] = None, 
                session_id: Optional[int] = None, conversation_id: Optional[int] = None, user_id: Optional[int] = None, 
                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行技能（API兼容方法）"""
        # 调用核心执行方法
        execution_log = await self.execute_skill(skill_id=skill_id, user_id=user_id, params=params, context=context)
        
        # 获取artifacts
        artifacts = self.artifact_manager.get_artifacts(execution_log.id)
        artifact_list = []
        for artifact in artifacts:
            artifact_list.append({
                "id": artifact.id,
                "name": artifact.name,
                "type": artifact.type,
                "created_at": artifact.created_at
            })
        
        # 返回API兼容的结果格式
        return {
            "success": execution_log.status == "completed",
            "result": execution_log.output_result,
            "error": execution_log.error_message,
            "execution_time_ms": execution_log.execution_time_ms,
            "execution_id": execution_log.id,
            "artifacts": artifact_list
        }
    
    async def execute_skill(self, skill_id: int, user_id: Optional[int] = None, params: Optional[Dict[str, Any]] = None, 
                      context: Optional[Dict[str, Any]] = None) -> SkillExecutionLog:
        """执行技能"""
        # 获取技能
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise ValueError(f"技能ID {skill_id} 不存在")
            
        if skill.status != "enabled":
            raise ValueError(f"技能 {skill.name} 未启用")
        
        # 使用本地技能匹配服务进行技能意图识别和参数提取
        try:
            intent_result = await self.local_skill_matching_service.identify_skill_intent(
                skill_name=skill.name,
                user_input=context.get('user_input') if context else None,
                db=self.db
            )
            if intent_result.get('parameters'):
                # 合并提取的参数
                for key, value in intent_result['parameters'].items():
                    if key not in params:
                        params[key] = value
        except Exception as e:
            print(f"本地技能意图识别失败: {str(e)}")
        
        # 验证参数
        validated_params = self.parameter_validator.validate_parameters(skill, params or {})
        
        # 检查依赖
        self._check_dependencies(skill)
        
        # 创建执行日志
        execution_log = SkillExecutionLog(
            skill_id=skill.id,
            user_id=user_id,
            input_params=validated_params,
            status="running",
            execution_steps=[],
            created_at=datetime.now(),
            conversation_id=context.get('conversation_id') if context else None,
            session_id=context.get('session_id') if context else None
        )
        self.db.add(execution_log)
        self.db.commit()
        self.db.refresh(execution_log)
        
        start_time = datetime.now()
        
        try:
            # 准备执行环境
            with ExecutionEnvironment(skill) as env:
                # 合并上下文信息到环境中
                env_info = env.prepare_environment(validated_params)
                if context:
                    env_info["context"] = context
                
                # 更新执行步骤，包含上下文信息
                step_data = {
                    "message": "执行环境准备完成",
                    "environment_info": env_info
                }
                if context:
                    step_data["context"] = context
                self._update_execution_step(execution_log, "environment_prepared", step_data)
                
                # 执行技能逻辑，传递上下文
                result, artifacts = self._execute_skill_logic(skill, validated_params, env_info, execution_log, context)
                
                # 更新执行步骤
                self._update_execution_step(execution_log, "skill_executed", {
                    "message": "技能逻辑执行完成",
                    "result": result
                })
                
                # 更新执行日志
                execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                execution_log.status = "completed"
                execution_log.output_result = result
                execution_log.execution_time_ms = execution_time_ms
                
                # 使用本地技能匹配服务进行执行结果分析
                try:
                    analysis_result = await self.local_skill_matching_service.analyze_execution_result(
                        skill_name=skill.name,
                        execution_result=result,
                        execution_time_ms=execution_time_ms,
                        db=self.db
                    )
                    # 更新执行日志，添加分析结果
                    if analysis_result.get('enhanced_result'):
                        execution_log.output_result = analysis_result['enhanced_result']
                except Exception as e:
                    print(f"本地执行结果分析失败: {str(e)}")
                
                # 更新技能使用统计
                skill.last_used_at = datetime.now()
                skill.usage_count = (skill.usage_count or 0) + 1
                
        except Exception as e:
            # 记录错误
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            execution_log.status = "failed"
            execution_log.error_message = str(e)
            execution_log.execution_time_ms = execution_time_ms
            
            # 更新执行步骤
            self._update_execution_step(execution_log, "execution_failed", {
                "message": "技能执行失败",
                "error": str(e)
            })
        
        self.db.commit()
        return execution_log
    
    def _check_dependencies(self, skill: Skill) -> None:
        """检查技能依赖"""
        dependencies = self.db.query(SkillDependency).filter(SkillDependency.skill_id == skill.id).all()
        
        for dep in dependencies:
            dep_skill = self.db.query(Skill).filter(Skill.id == dep.dependency_skill_id).first()
            if not dep_skill:
                raise ValueError(f"技能 {skill.name} 依赖的技能 {dep.dependency_skill_id} 不存在")
                
            if dep_skill.status != "enabled":
                raise ValueError(f"技能 {skill.name} 依赖的技能 {dep_skill.name} 未启用")
                
            # 检查版本要求
            if dep.version_requirement:
                if not self._check_version_compatibility(dep_skill.version, dep.version_requirement):
                    raise ValueError(f"技能 {skill.name} 依赖的技能 {dep_skill.name} 版本不兼容。要求: {dep.version_requirement}, 当前: {dep_skill.version}")
    
    def _check_version_compatibility(self, current_version: str, requirement: str) -> bool:
        """检查版本兼容性"""
        try:
            # 解析语义化版本号
            current_parts = self._parse_semver(current_version)
            if not current_parts:
                return False
                
            # 解析版本要求
            if requirement.startswith(">=") or requirement.startswith("<=") or requirement.startswith(">") or requirement.startswith("<") or requirement.startswith("=="):
                return self._check_comparison_requirement(current_parts, requirement)
            elif requirement.startswith("^") or requirement.startswith("~"):
                return self._check_caret_tilde_requirement(current_parts, requirement)
            else:
                # 默认使用精确匹配
                return current_version == requirement
                
        except Exception:
            return False
    
    def _parse_semver(self, version: str) -> Optional[Dict[str, Any]]:
        """解析语义化版本号"""
        import re
        
        # 语义化版本号正则表达式
        semver_pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        
        match = re.match(semver_pattern, version)
        if not match:
            return None
            
        return {
            "major": int(match.group(1)),
            "minor": int(match.group(2)),
            "patch": int(match.group(3)),
            "prerelease": match.group(4),
            "build": match.group(5)
        }
    
    def _check_comparison_requirement(self, current_parts: Dict[str, Any], requirement: str) -> bool:
        """检查比较操作符版本要求"""
        # 解析要求中的版本号
        if requirement.startswith(">=") or requirement.startswith("<=") or requirement.startswith("=="):
            req_version = requirement[2:]  # 去掉双字符操作符
        elif requirement.startswith(">") or requirement.startswith("<"):
            req_version = requirement[1:]  # 去掉单字符操作符
        else:
            return False
            
        req_parts = self._parse_semver(req_version)
        if not req_parts:
            return False
            
        # 比较版本
        comparison = self._compare_versions(current_parts, req_parts)
        
        if requirement.startswith(">="):
            return comparison >= 0
        elif requirement.startswith("<="):
            return comparison <= 0
        elif requirement.startswith(">"):
            return comparison > 0
        elif requirement.startswith("<"):
            return comparison < 0
        elif requirement.startswith("=="):
            return comparison == 0
            
        return False
    
    def _check_caret_tilde_requirement(self, current_parts: Dict[str, Any], requirement: str) -> bool:
        """检查^和~版本要求"""
        # 解析要求中的版本号
        req_version = requirement[1:]  # 去掉^或~
        req_parts = self._parse_semver(req_version)
        if not req_parts:
            return False
            
        comparison = self._compare_versions(current_parts, req_parts)
        
        if requirement.startswith("^"):
            # ^1.2.3 允许 >=1.2.3 且 <2.0.0
            return comparison >= 0 and current_parts["major"] == req_parts["major"]
        elif requirement.startswith("~"):
            # ~1.2.3 允许 >=1.2.3 且 <1.3.0
            return (comparison >= 0 and 
                   current_parts["major"] == req_parts["major"] and 
                   current_parts["minor"] == req_parts["minor"])
            
        return False
    
    def _compare_versions(self, v1: Dict[str, Any], v2: Dict[str, Any]) -> int:
        """比较两个版本号"""
        # 比较主版本号
        if v1["major"] != v2["major"]:
            return v1["major"] - v2["major"]
            
        # 比较次版本号
        if v1["minor"] != v2["minor"]:
            return v1["minor"] - v2["minor"]
            
        # 比较修订号
        if v1["patch"] != v2["patch"]:
            return v1["patch"] - v2["patch"]
            
        # 比较预发布版本
        if v1["prerelease"] != v2["prerelease"]:
            if v1["prerelease"] is None:
                return 1  # 正式版本 > 预发布版本
            elif v2["prerelease"] is None:
                return -1  # 预发布版本 < 正式版本
            else:
                # 比较预发布版本字符串
                return (v1["prerelease"] > v2["prerelease"]) - (v1["prerelease"] < v2["prerelease"])
                
        return 0
    
    def _execute_skill_logic(self, skill: Skill, params: Dict[str, Any], env_info: Dict[str, Any], execution_log: SkillExecutionLog, 
                            context: Optional[Dict[str, Any]] = None) -> tuple:
        """执行技能逻辑"""
        # 检查是否有执行流程定义
        if skill.execution_flow and isinstance(skill.execution_flow, list) and len(skill.execution_flow) > 0:
            # 执行多步骤流程
            return self._execute_flow_logic(skill, params, env_info, execution_log, context)
        else:
            # 执行单步骤逻辑
            return self._execute_single_step_logic(skill, params, env_info, execution_log, context)
    
    def _execute_flow_logic(self, skill: Skill, params: Dict[str, Any], env_info: Dict[str, Any], execution_log: SkillExecutionLog, 
                            context: Optional[Dict[str, Any]] = None) -> tuple:
        """执行多步骤流程逻辑"""
        results = []
        artifacts = []
        
        for step_index, step_config in enumerate(skill.execution_flow):
            step_name = step_config.get("name", f"step_{step_index + 1}")
            step_type = step_config.get("type", "script")
            
            # 更新执行步骤，包含上下文信息
            step_data = {
                "message": f"开始执行步骤: {step_name}",
                "step_type": step_type,
                "step_config": step_config
            }
            if context:
                step_data["context"] = context
            self._update_execution_step(execution_log, f"step_{step_index + 1}_started", step_data)
            
            try:
                # 根据步骤类型执行不同的逻辑，传递上下文
                if step_type == "script":
                    step_result = self._execute_script_step(step_config, params, env_info, execution_log, context)
                elif step_type == "template":
                    step_result = self._execute_template_step(step_config, params, env_info, execution_log, context)
                elif step_type == "api_call":
                    step_result = self._execute_api_step(step_config, params, env_info, execution_log, context)
                else:
                    step_result = f"未知步骤类型: {step_type}"
                
                results.append({
                    "step": step_name,
                    "type": step_type,
                    "result": step_result
                })
                
                # 更新执行步骤，包含上下文信息
                step_data = {
                    "message": f"步骤执行完成: {step_name}",
                    "result": step_result
                }
                if context:
                    step_data["context"] = context
                self._update_execution_step(execution_log, f"step_{step_index + 1}_completed", step_data)
                
            except Exception as e:
                # 记录步骤执行错误
                self._update_execution_step(execution_log, f"step_{step_index + 1}_failed", {
                    "message": f"步骤执行失败: {step_name}",
                    "error": str(e)
                })
                raise e
        
        # 生成最终结果和artifacts
        final_result = self._generate_final_result(results, skill, params)
        
        # 生成artifacts
        artifacts = self._generate_artifacts(final_result, skill, execution_log)
        
        return final_result, artifacts
    
    def _execute_single_step_logic(self, skill: Skill, params: Dict[str, Any], env_info: Dict[str, Any], execution_log: SkillExecutionLog, 
                                  context: Optional[Dict[str, Any]] = None) -> tuple:
        """执行单步骤逻辑"""
        # 这里是技能执行的核心逻辑
        # 根据技能的内容和参数执行相应的操作
        
        # 在结果中包含上下文信息
        result = f"技能 {skill.name} 执行成功，参数: {json.dumps(params, ensure_ascii=False)}"
        if context:
            result += f"，上下文: {json.dumps(context, ensure_ascii=False)}"
        
        # 生成artifacts
        artifacts = self._generate_artifacts(result, skill, execution_log)
        
        return result, artifacts
    
    def _execute_script_step(self, step_config: Dict[str, Any], params: Dict[str, Any], env_info: Dict[str, Any], execution_log: SkillExecutionLog, 
                            context: Optional[Dict[str, Any]] = None) -> str:
        """执行脚本步骤"""
        script_content = step_config.get("script", "")
        # 这里可以扩展为执行实际的脚本逻辑，上下文可用于脚本执行
        result = f"脚本步骤执行完成: {script_content[:100]}..."
        if context:
            result += f" (上下文: {json.dumps(context, ensure_ascii=False)[:50]}...)"
        return result
    
    def _execute_template_step(self, step_config: Dict[str, Any], params: Dict[str, Any], env_info: Dict[str, Any], execution_log: SkillExecutionLog, 
                              context: Optional[Dict[str, Any]] = None) -> str:
        """执行模板步骤"""
        template_name = step_config.get("template", "")
        # 这里可以扩展为模板渲染逻辑，上下文可用于模板变量替换
        result = f"模板步骤执行完成: {template_name}"
        if context:
            result += f" (上下文: {json.dumps(context, ensure_ascii=False)[:50]}...)"
        return result
    
    def _execute_api_step(self, step_config: Dict[str, Any], params: Dict[str, Any], env_info: Dict[str, Any], execution_log: SkillExecutionLog, 
                         context: Optional[Dict[str, Any]] = None) -> str:
        """执行API调用步骤"""
        api_url = step_config.get("url", "")
        # 这里可以扩展为实际的API调用逻辑，上下文可用于API请求头或参数
        result = f"API步骤执行完成: {api_url}"
        if context:
            result += f" (上下文: {json.dumps(context, ensure_ascii=False)[:50]}...)"
        return result
    
    def _generate_final_result(self, step_results: List[Dict[str, Any]], skill: Skill, params: Dict[str, Any]) -> str:
        """生成最终执行结果"""
        if len(step_results) == 0:
            return f"技能 {skill.name} 执行完成，无步骤结果"
        
        result_summary = f"技能 {skill.name} 执行完成，共 {len(step_results)} 个步骤:\n"
        for i, step_result in enumerate(step_results):
            result_summary += f"\n步骤 {i+1} ({step_result['step']}): {step_result['result']}"
        
        return result_summary
    
    def _generate_artifacts(self, result: str, skill: Skill, execution_log: SkillExecutionLog) -> List[SkillArtifact]:
        """生成交互式artifacts"""
        artifacts = []
        
        # 获取技能支持的artifact类型
        artifact_types = skill.artifact_types or []
        
        # 生成HTML artifact
        if "html" in artifact_types:
            html_artifact = self._generate_html_artifact(result, skill, execution_log)
            if html_artifact:
                artifacts.append(html_artifact)
        
        # 生成JavaScript artifact
        if "js" in artifact_types:
            js_artifact = self._generate_js_artifact(result, skill, execution_log)
            if js_artifact:
                artifacts.append(js_artifact)
        
        # 生成Markdown artifact
        if "md" in artifact_types:
            md_artifact = self._generate_markdown_artifact(result, skill, execution_log)
            if md_artifact:
                artifacts.append(md_artifact)
        
        # 生成JSON artifact
        if "json" in artifact_types:
            json_artifact = self._generate_json_artifact(result, skill, execution_log)
            if json_artifact:
                artifacts.append(json_artifact)
        
        # 生成图表artifact
        if "chart" in artifact_types:
            chart_artifact = self._generate_chart_artifact(result, skill, execution_log)
            if chart_artifact:
                artifacts.append(chart_artifact)
        
        return artifacts
    
    def _generate_html_artifact(self, result: str, skill: Skill, execution_log: SkillExecutionLog) -> Optional[SkillArtifact]:
        """生成交互式HTML artifact"""
        try:
            # 创建动态HTML内容
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{skill.display_name or skill.name} - 执行结果</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 2px solid #007bff; padding-bottom: 15px; margin-bottom: 20px; }}
        h1 {{ color: #333; margin: 0; }}
        .metadata {{ color: #666; font-size: 14px; margin-top: 5px; }}
        .result-section {{ margin-top: 20px; }}
        .result-content {{ background: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 4px solid #007bff; white-space: pre-wrap; }}
        .timestamp {{ color: #999; font-size: 12px; text-align: right; margin-top: 20px; }}
        
        /* 交互式样式 */
        .toggle-btn {{ background: #007bff; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; margin-bottom: 10px; }}
        .toggle-btn:hover {{ background: #0056b3; }}
        .hidden {{ display: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{skill.display_name or skill.name}</h1>
            <div class="metadata">
                <strong>版本:</strong> {skill.version} | 
                <strong>作者:</strong> {skill.author or '未知'} |
                <strong>执行ID:</strong> {execution_log.id}
            </div>
        </div>
        
        <div class="result-section">
            <h2>执行结果</h2>
            <button class="toggle-btn" onclick="toggleRawResult()">切换显示原始结果</button>
            <div id="formatted-result">
                {self._format_result_for_html(result)}
            </div>
            <div id="raw-result" class="hidden">
                <pre class="result-content">{result}</pre>
            </div>
        </div>
        
        <div class="timestamp">
            生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>

    <script>
        function toggleRawResult() {{
            const formatted = document.getElementById('formatted-result');
            const raw = document.getElementById('raw-result');
            const btn = document.querySelector('.toggle-btn');
            
            if (formatted.style.display === 'none') {{
                formatted.style.display = 'block';
                raw.style.display = 'none';
                btn.textContent = '切换显示原始结果';
            }} else {{
                formatted.style.display = 'none';
                raw.style.display = 'block';
                btn.textContent = '切换显示格式化结果';
            }}
        }}
    </script>
</body>
</html>
            """
            
            return self.artifact_manager.create_artifact(
                execution_id=execution_log.id,
                name=f"{skill.name}_interactive_result",
                artifact_type="html",
                content=html_content
            )
        except Exception as e:
            print(f"生成HTML artifact失败: {e}")
            return None
    
    def _generate_js_artifact(self, result: str, skill: Skill, execution_log: SkillExecutionLog) -> Optional[SkillArtifact]:
        """生成JavaScript artifact"""
        try:
            # 创建交互式JavaScript内容
            js_content = f"""
// {skill.name} 执行结果处理脚本
const skillData = {{
    name: '{skill.name}',
    displayName: '{skill.display_name or skill.name}',
    version: '{skill.version}',
    executionId: {execution_log.id},
    result: `{result.replace('`', '\\`')}`,
    timestamp: '{datetime.now().isoformat()}'
}};

// 数据处理函数
function processResult(result) {{
    try {{
        // 尝试解析JSON结果
        return JSON.parse(result);
    }} catch {{
        // 如果是文本，返回格式化文本
        return result.split('\\n').map(line => ({{ type: 'text', content: line }}));
    }}
}}

// 渲染函数
function renderResult(containerId) {{
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const processed = processResult(skillData.result);
    
    if (Array.isArray(processed)) {{
        processed.forEach(item => {{
            const div = document.createElement('div');
            div.className = 'result-item';
            div.textContent = item.content || item;
            container.appendChild(div);
        }});
    }} else if (typeof processed === 'object') {{
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(processed, null, 2);
        container.appendChild(pre);
    }} else {{
        const div = document.createElement('div');
        div.textContent = processed;
        container.appendChild(div);
    }}
}}

// 导出函数供外部使用
window.skillResultRenderer = {{ renderResult, skillData }};
            """
            
            return self.artifact_manager.create_artifact(
                execution_id=execution_log.id,
                name=f"{skill.name}_processor",
                artifact_type="js",
                content=js_content
            )
        except Exception as e:
            print(f"生成JavaScript artifact失败: {e}")
            return None
    
    def _generate_markdown_artifact(self, result: str, skill: Skill, execution_log: SkillExecutionLog) -> Optional[SkillArtifact]:
        """生成Markdown artifact"""
        try:
            md_content = f"""
# {skill.display_name or skill.name}

**版本**: {skill.version}  
**执行ID**: {execution_log.id}  
**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

## 执行结果

```
{result}
```

## 技能信息

- **名称**: {skill.name}
- **描述**: {skill.description or '暂无描述'}
- **作者**: {skill.author or '未知'}
- **标签**: {', '.join(skill.tags or [])}

---
*此文档由技能执行引擎自动生成*
            """
            
            return self.artifact_manager.create_artifact(
                execution_id=execution_log.id,
                name=f"{skill.name}_report",
                artifact_type="md",
                content=md_content
            )
        except Exception as e:
            print(f"生成Markdown artifact失败: {e}")
            return None
    
    def _generate_json_artifact(self, result: str, skill: Skill, execution_log: SkillExecutionLog) -> Optional[SkillArtifact]:
        """生成JSON artifact"""
        try:
            json_data = {{
                "skill": {{
                    "id": skill.id,
                    "name": skill.name,
                    "display_name": skill.display_name,
                    "version": skill.version,
                    "description": skill.description
                }},
                "execution": {{
                    "id": execution_log.id,
                    "timestamp": datetime.now().isoformat(),
                    "status": execution_log.status
                }},
                "result": result,
                "metadata": {{
                    "artifact_type": "json",
                    "generated_at": datetime.now().isoformat()
                }}
            }}
            
            json_content = json.dumps(json_data, ensure_ascii=False, indent=2)
            
            return self.artifact_manager.create_artifact(
                execution_id=execution_log.id,
                name=f"{skill.name}_data",
                artifact_type="json",
                content=json_content
            )
        except Exception as e:
            print(f"生成JSON artifact失败: {e}")
            return None
    
    def _generate_chart_artifact(self, result: str, skill: Skill, execution_log: SkillExecutionLog) -> Optional[SkillArtifact]:
        """生成图表artifact"""
        try:
            # 创建简单的图表HTML
            chart_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{skill.name} - 数据图表</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .chart-container {{ width: 600px; height: 400px; margin: 20px auto; }}
    </style>
</head>
<body>
    <h1>{skill.display_name or skill.name} - 执行结果图表</h1>
    <div class="chart-container">
        <canvas id="resultChart"></canvas>
    </div>
    
    <script>
        // 解析结果数据
        const resultData = {self._parse_result_for_chart(result)};
        
        // 创建图表
        const ctx = document.getElementById('resultChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: resultData.labels || ['结果'],
                datasets: [{{
                    label: '{skill.name} 执行结果',
                    data: resultData.values || [1],
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
            """
            
            return self.artifact_manager.create_artifact(
                execution_id=execution_log.id,
                name=f"{skill.name}_chart",
                artifact_type="html",
                content=chart_html
            )
        except Exception as e:
            print(f"生成图表artifact失败: {e}")
            return None
    
    def _format_result_for_html(self, result: str) -> str:
        """为HTML格式化结果"""
        try:
            # 尝试解析JSON
            data = json.loads(result)
            if isinstance(data, dict):
                return self._format_dict_as_html(data)
            elif isinstance(data, list):
                return self._format_list_as_html(data)
        except:
            pass
        
        # 如果是纯文本，按行格式化
        lines = result.split('\n')
        formatted_lines = []
        for line in lines:
            if line.strip():
                if line.startswith('#'):
                    # 标题行
                    level = line.count('#')
                    content = line.replace('#', '').strip()
                    formatted_lines.append(f'<h{level}>{content}</h{level}>')
                elif line.startswith('- ') or line.startswith('* '):
                    # 列表项
                    content = line[2:].strip()
                    formatted_lines.append(f'<li>{content}</li>')
                else:
                    # 普通段落
                    formatted_lines.append(f'<p>{line}</p>')
        
        return '\n'.join(formatted_lines)
    
    def _format_dict_as_html(self, data: dict) -> str:
        """将字典格式化为HTML表格"""
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr><th style="border: 1px solid #ddd; padding: 8px; background: #f2f2f2;">属性</th><th style="border: 1px solid #ddd; padding: 8px; background: #f2f2f2;">值</th></tr>'
        
        for key, value in data.items():
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + '...'
            html += f'<tr><td style="border: 1px solid #ddd; padding: 8px;"><strong>{key}</strong></td><td style="border: 1px solid #ddd; padding: 8px;">{value_str}</td></tr>'
        
        html += '</table>'
        return html
    
    def _format_list_as_html(self, data: list) -> str:
        """将列表格式化为HTML"""
        if len(data) == 0:
            return '<p>空列表</p>'
        
        html = '<ul>'
        for item in data:
            html += f'<li>{str(item)}</li>'
        html += '</ul>'
        return html
    
    def _parse_result_for_chart(self, result: str) -> dict:
        """解析结果数据用于图表"""
        try:
            data = json.loads(result)
            if isinstance(data, dict):
                # 如果是字典，使用键作为标签，值作为数据
                return {
                    'labels': list(data.keys()),
                    'values': list(data.values())
                }
            elif isinstance(data, list):
                # 如果是列表，使用索引作为标签
                return {
                    'labels': [f'项目 {i+1}' for i in range(len(data))],
                    'values': data
                }
        except:
            pass
        
        # 默认返回简单数据
        return {
            'labels': ['结果'],
            'values': [1]
        }
    
    def _update_execution_step(self, execution_log: SkillExecutionLog, step_name: str, details: Dict[str, Any]) -> None:
        """更新执行步骤"""
        if not execution_log.execution_steps:
            execution_log.execution_steps = []
            
        execution_log.execution_steps.append({
            "step": step_name,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        self.db.commit()
        self.db.refresh(execution_log)
    
    def get_execution_result(self, execution_id: int) -> Dict[str, Any]:
        """获取执行结果"""
        execution_log = self.db.query(SkillExecutionLog).filter(SkillExecutionLog.id == execution_id).first()
        if not execution_log:
            raise ValueError(f"执行ID {execution_id} 不存在")
        
        # 获取artifacts
        artifacts = self.artifact_manager.get_artifacts(execution_id)
        artifact_list = []
        for artifact in artifacts:
            artifact_list.append({
                "id": artifact.id,
                "name": artifact.name,
                "type": artifact.type,
                "created_at": artifact.created_at.isoformat()
            })
        
        return {
            "execution_id": execution_log.id,
            "skill_id": execution_log.skill_id,
            "status": execution_log.status,
            "input_params": execution_log.input_params,
            "output_result": execution_log.output_result,
            "error_message": execution_log.error_message,
            "execution_time_ms": execution_log.execution_time_ms,
            "execution_steps": execution_log.execution_steps,
            "artifacts": artifact_list,
            "created_at": execution_log.created_at.isoformat()
        }
