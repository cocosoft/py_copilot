"""技能匹配服务"""
from typing import List
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.skill import Skill
from app.core.logging_config import logger


class SkillMatchingService:
    """技能匹配服务，用于根据任务描述匹配相关技能"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def match_skills(self, task_description: str, limit: int = 5) -> List[Skill]:
        """根据任务描述匹配相关技能，使用TF-IDF和余弦相似度优化"""
        try:
            # 获取所有启用的技能
            skills = self.db.query(Skill).filter(Skill.status == 'enabled').all()
            
            if not skills:
                return []
            
            # 构建技能文本集合
            skill_texts = []
            
            for skill in skills:
                # 合并技能的所有文本字段
                text_parts = []
                if skill.name:
                    text_parts.append(skill.name)
                if skill.display_name:
                    text_parts.append(skill.display_name)
                if skill.description:
                    text_parts.append(skill.description)
                if skill.tags:
                    text_parts.extend(skill.tags)
                
                skill_text = " ".join(text_parts)
                skill_texts.append(skill_text)
            
            # 添加任务描述到文本集合
            all_texts = skill_texts + [task_description]
            
            # 创建TF-IDF向量器并计算相似度
            vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # 计算任务描述与每个技能的余弦相似度
            task_vector = tfidf_matrix[-1]
            skill_vectors = tfidf_matrix[:-1]
            
            # 使用余弦相似度计算相关性
            similarities = cosine_similarity(task_vector, skill_vectors).flatten()
            
            # 按相似度排序技能
            scored_skills = list(zip(skills, similarities))
            scored_skills = [(s, score) for s, score in scored_skills if score > 0]
            scored_skills.sort(key=lambda x: x[1], reverse=True)
            
            # 返回前N个匹配的技能
            return [skill for skill, _ in scored_skills[:limit]]
        except Exception as e:
            logger.error(f"技能匹配失败: {e}")
            return []
