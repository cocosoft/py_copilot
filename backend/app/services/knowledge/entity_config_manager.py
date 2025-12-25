"""
实体配置管理器 - 支持用户自定义实体类型和提取规则
"""
import json
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class EntityConfigManager:
    """实体配置管理器，支持用户自定义实体类型和提取规则"""
    
    def __init__(self, config_file: str = "entity_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config_dir = Path("config")
        self.config_path = self.config_dir / config_file
        
        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = {
            "entity_types": {
                "PERSON": {
                    "name": "人名",
                    "description": "人物姓名",
                    "color": "#FF6B6B",
                    "enabled": True
                },
                "ORG": {
                    "name": "组织",
                    "description": "组织机构名称",
                    "color": "#4ECDC4",
                    "enabled": True
                },
                "LOC": {
                    "name": "地点",
                    "description": "地理位置名称",
                    "color": "#45B7D1",
                    "enabled": True
                },
                "TECH": {
                    "name": "技术术语",
                    "description": "技术相关术语和缩写",
                    "color": "#96CEB4",
                    "enabled": True
                },
                "PRODUCT": {
                    "name": "产品",
                    "description": "产品和服务名称",
                    "color": "#FECA57",
                    "enabled": True
                },
                "EVENT": {
                    "name": "事件",
                    "description": "事件和活动名称",
                    "color": "#FF9FF3",
                    "enabled": True
                },
                "CONCEPT": {
                    "name": "概念",
                    "description": "概念和理论名称",
                    "color": "#54A0FF",
                    "enabled": True
                }
            },
            "extraction_rules": {
                "PERSON": [
                    {
                        "name": "中文人名",
                        "pattern": r'(?:^|\\s)([张王李赵刘陈杨黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程曹袁邓许傅沈曾彭吕][\\u4e00-\\u9fff]{1,2})(?=\\s|$|[，。！？])',
                        "description": "基于常见姓氏的中文人名识别",
                        "enabled": True
                    }
                ],
                "ORG": [
                    {
                        "name": "中文组织名",
                        "pattern": r'(?:^|\\s)([\\u4e00-\\u9fff]{2,6}(?:公司|集团|企业|机构|组织|大学|学院|医院|学校|研究所|实验室|中心|部门|局|委员会))(?=\\s|$|[，。！？])',
                        "description": "基于组织关键词的中文组织名识别",
                        "enabled": True
                    }
                ],
                "TECH": [
                    {
                        "name": "技术缩写",
                        "pattern": r'\\b[A-Z]{2,}\\b',
                        "description": "大写字母技术缩写",
                        "enabled": True
                    },
                    {
                        "name": "技术术语",
                        "pattern": r'[\\u4e00-\\u9fff]{2,6}(?:技术|系统|框架|算法|模型|架构)',
                        "description": "中文技术术语识别",
                        "enabled": True
                    }
                ]
            },
            "dictionaries": {
                "TECH": [
                    "AI", "ML", "NLP", "CV", "区块链", "云计算", "大数据", "物联网",
                    "人工智能", "机器学习", "深度学习", "神经网络", "自然语言处理",
                    "计算机视觉", "数据挖掘", "知识图谱", "推荐系统", "Python",
                    "Java", "JavaScript", "React", "Vue", "Angular", "Docker",
                    "Kubernetes", "微服务"
                ],
                "PRODUCT": [
                    "微信", "支付宝", "淘宝", "京东", "百度", "腾讯", "阿里云",
                    "华为云", "微软Office", "Google搜索"
                ],
                "EVENT": [
                    "人工智能大会", "技术峰会", "开发者大会", "产品发布会"
                ]
            }
        }
        
        # 加载配置
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和用户配置
                    return self._merge_configs(self.default_config, loaded_config)
            else:
                # 配置文件不存在，创建默认配置
                self._save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self.default_config.copy()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """合并默认配置和用户配置"""
        merged = default.copy()
        
        # 深度合并
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存到: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def get_entity_types(self) -> Dict[str, Dict]:
        """获取所有启用的实体类型"""
        return {k: v for k, v in self.config['entity_types'].items() if v.get('enabled', True)}
    
    def get_extraction_rules(self, entity_type: str = None) -> List[Dict]:
        """获取提取规则"""
        if entity_type:
            return self.config['extraction_rules'].get(entity_type, [])
        else:
            # 返回所有启用的规则
            all_rules = []
            for rules in self.config['extraction_rules'].values():
                all_rules.extend([r for r in rules if r.get('enabled', True)])
            return all_rules
    
    def get_dictionary(self, entity_type: str) -> List[str]:
        """获取指定实体类型的词典"""
        return self.config['dictionaries'].get(entity_type, [])
    
    def add_entity_type(self, entity_type: str, config: Dict[str, Any]) -> bool:
        """添加新的实体类型"""
        try:
            if entity_type in self.config['entity_types']:
                logger.warning(f"实体类型 {entity_type} 已存在")
                return False
            
            self.config['entity_types'][entity_type] = config
            self._save_config(self.config)
            logger.info(f"成功添加实体类型: {entity_type}")
            return True
        except Exception as e:
            logger.error(f"添加实体类型失败: {e}")
            return False
    
    def update_entity_type(self, entity_type: str, config: Dict[str, Any]) -> bool:
        """更新实体类型配置"""
        try:
            if entity_type not in self.config['entity_types']:
                logger.warning(f"实体类型 {entity_type} 不存在")
                return False
            
            self.config['entity_types'][entity_type].update(config)
            self._save_config(self.config)
            logger.info(f"成功更新实体类型: {entity_type}")
            return True
        except Exception as e:
            logger.error(f"更新实体类型失败: {e}")
            return False
    
    def add_extraction_rule(self, entity_type: str, rule: Dict[str, Any]) -> bool:
        """添加提取规则"""
        try:
            if entity_type not in self.config['extraction_rules']:
                self.config['extraction_rules'][entity_type] = []
            
            self.config['extraction_rules'][entity_type].append(rule)
            self._save_config(self.config)
            logger.info(f"成功为 {entity_type} 添加提取规则: {rule.get('name', '未命名')}")
            return True
        except Exception as e:
            logger.error(f"添加提取规则失败: {e}")
            return False
    
    def add_to_dictionary(self, entity_type: str, terms: List[str]) -> bool:
        """向词典添加术语"""
        try:
            if entity_type not in self.config['dictionaries']:
                self.config['dictionaries'][entity_type] = []
            
            # 去重添加
            existing_terms = set(self.config['dictionaries'][entity_type])
            new_terms = [term for term in terms if term not in existing_terms]
            self.config['dictionaries'][entity_type].extend(new_terms)
            
            self._save_config(self.config)
            logger.info(f"成功向 {entity_type} 词典添加 {len(new_terms)} 个术语")
            return True
        except Exception as e:
            logger.error(f"添加词典术语失败: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """导出配置到文件"""
        try:
            export_dir = Path(export_path).parent
            export_dir.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已导出到: {export_path}")
            return True
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """从文件导入配置"""
        try:
            if not Path(import_path).exists():
                logger.error(f"导入文件不存在: {import_path}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 验证配置格式
            if not self._validate_config(imported_config):
                logger.error("导入的配置格式无效")
                return False
            
            self.config = self._merge_configs(self.default_config, imported_config)
            self._save_config(self.config)
            logger.info(f"配置已从 {import_path} 导入")
            return True
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def _validate_config(self, config: Dict) -> bool:
        """验证配置格式"""
        required_keys = ['entity_types', 'extraction_rules', 'dictionaries']
        return all(key in config for key in required_keys)
    
    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        try:
            self.config = self.default_config.copy()
            self._save_config(self.config)
            logger.info("配置已重置为默认值")
            return True
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            return False