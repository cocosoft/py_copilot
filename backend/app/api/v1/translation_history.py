"""翻译历史API"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func

from app.core.database import get_db
from app.models.translation_history import TranslationHistory
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter()


@router.get("/translation-history")
def get_translation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    source_language: Optional[str] = Query(None),
    target_language: Optional[str] = Query(None),
    date_range: Optional[str] = Query(None),  # "today", "week", "month", "year"
    agent_id: Optional[int] = Query(None),
    scene: Optional[str] = Query(None),
    use_knowledge_base: Optional[bool] = Query(None),
    use_memory_enhancement: Optional[bool] = Query(None)
):
    """获取翻译历史记录"""
    try:
        # 构建查询条件
        query = db.query(TranslationHistory).filter(
            TranslationHistory.user_id == current_user.id
        )
        
        # 搜索条件
        if search:
            query = query.filter(
                or_(
                    TranslationHistory.source_text.ilike(f"%{search}%"),
                    TranslationHistory.target_text.ilike(f"%{search}%")
                )
            )
        
        # 语言筛选条件
        if source_language:
            query = query.filter(TranslationHistory.source_language == source_language)
        if target_language:
            query = query.filter(TranslationHistory.target_language == target_language)
        
        # 智能体和场景筛选条件
        if agent_id:
            query = query.filter(TranslationHistory.agent_id == agent_id)
        if scene:
            query = query.filter(TranslationHistory.scene == scene)
        
        # 知识库和记忆增强筛选条件
        if use_knowledge_base is not None:
            query = query.filter(TranslationHistory.use_knowledge_base == use_knowledge_base)
        if use_memory_enhancement is not None:
            query = query.filter(TranslationHistory.use_memory_enhancement == use_memory_enhancement)
        
        # 时间范围筛选
        if date_range:
            now = datetime.utcnow()
            if date_range == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(TranslationHistory.created_at >= start_date)
            elif date_range == "week":
                start_date = now - timedelta(days=7)
                query = query.filter(TranslationHistory.created_at >= start_date)
            elif date_range == "month":
                start_date = now - timedelta(days=30)
                query = query.filter(TranslationHistory.created_at >= start_date)
            elif date_range == "year":
                start_date = now - timedelta(days=365)
                query = query.filter(TranslationHistory.created_at >= start_date)
        
        # 计算总数
        total_count = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        history_items = query.order_by(desc(TranslationHistory.created_at)).offset(offset).limit(page_size).all()
        
        # 转换为字典格式
        items = [item.to_dict() for item in history_items]
        
        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取翻译历史失败: {str(e)}")


@router.post("/translation-history")
def save_translation_history(
    translation_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存翻译历史记录"""
    try:
        # 创建新的翻译历史记录
        history_item = TranslationHistory(
            user_id=current_user.id,
            source_text=translation_data.get("source_text", ""),
            target_text=translation_data.get("target_text", ""),
            source_language=translation_data.get("source_language", ""),
            target_language=translation_data.get("target_language", ""),
            model_name=translation_data.get("model_name", ""),
            tokens_used=translation_data.get("tokens_used", 0),
            agent_id=translation_data.get("agent_id"),
            scene=translation_data.get("scene"),
            knowledge_base_id=translation_data.get("knowledge_base_id"),
            use_knowledge_base=translation_data.get("use_knowledge_base", False),
            use_memory_enhancement=translation_data.get("use_memory_enhancement", False),
            term_consistency=translation_data.get("term_consistency", False),
            execution_time_ms=translation_data.get("execution_time_ms"),
            quality_score=translation_data.get("quality_score"),
            user_feedback=translation_data.get("user_feedback"),
            additional_metadata=translation_data.get("additional_metadata")
        )
        
        db.add(history_item)
        db.commit()
        db.refresh(history_item)
        
        return {
            "success": True, 
            "message": "翻译历史记录已保存",
            "history_id": history_item.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存翻译历史失败: {str(e)}")


@router.delete("/translation-history/{history_id}")
def delete_translation_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除指定的翻译历史记录"""
    try:
        history_item = db.query(TranslationHistory).filter(
            TranslationHistory.id == history_id,
            TranslationHistory.user_id == current_user.id
        ).first()
        
        if not history_item:
            raise HTTPException(status_code=404, detail="翻译历史记录不存在")
        
        db.delete(history_item)
        db.commit()
        
        return {"success": True, "message": "翻译历史记录已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除翻译历史记录失败: {str(e)}")


@router.delete("/translation-history/clear")
def clear_translation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清空当前用户的所有翻译历史记录"""
    try:
        deleted_count = db.query(TranslationHistory).filter(
            TranslationHistory.user_id == current_user.id
        ).delete()
        
        db.commit()
        
        return {"success": True, "message": f"已删除{deleted_count}条翻译历史记录"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空翻译历史失败: {str(e)}")


@router.post("/translation-history/{history_id}/rate")
def rate_translation_history(
    history_id: int,
    rating: int = Query(..., ge=1, le=5),
    feedback: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为翻译历史记录评分"""
    try:
        history_item = db.query(TranslationHistory).filter(
            TranslationHistory.id == history_id,
            TranslationHistory.user_id == current_user.id
        ).first()
        
        if not history_item:
            raise HTTPException(status_code=404, detail="翻译历史记录不存在")
        
        history_item.quality_score = rating
        history_item.user_feedback = feedback
        
        db.commit()
        
        return {"success": True, "message": "评分已保存"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评分失败: {str(e)}")


@router.get("/translation-history/stats")
def get_translation_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取翻译统计信息"""
    try:
        # 总翻译次数
        total_translations = db.query(TranslationHistory).filter(
            TranslationHistory.user_id == current_user.id
        ).count()
        
        # 今日翻译次数
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_translations = db.query(TranslationHistory).filter(
            TranslationHistory.user_id == current_user.id,
            TranslationHistory.created_at >= today_start
        ).count()
        
        # 最常用语言对
        language_pairs = db.query(
            TranslationHistory.source_language,
            TranslationHistory.target_language
        ).filter(
            TranslationHistory.user_id == current_user.id
        ).group_by(
            TranslationHistory.source_language,
            TranslationHistory.target_language
        ).order_by(
            func.count().desc()
        ).limit(5).all()
        
        # 最常用模型
        models = db.query(
            TranslationHistory.model_name
        ).filter(
            TranslationHistory.user_id == current_user.id
        ).group_by(
            TranslationHistory.model_name
        ).order_by(
            func.count().desc()
        ).limit(5).all()
        
        # 知识库使用统计
        kb_usage = db.query(
            TranslationHistory.use_knowledge_base
        ).filter(
            TranslationHistory.user_id == current_user.id
        ).group_by(
            TranslationHistory.use_knowledge_base
        ).all()
        
        kb_usage_count = {True: 0, False: 0}
        for usage in kb_usage:
            kb_usage_count[usage[0]] += 1
        
        # 记忆增强使用统计
        memory_usage = db.query(
            TranslationHistory.use_memory_enhancement
        ).filter(
            TranslationHistory.user_id == current_user.id
        ).group_by(
            TranslationHistory.use_memory_enhancement
        ).all()
        
        memory_usage_count = {True: 0, False: 0}
        for usage in memory_usage:
            memory_usage_count[usage[0]] += 1
        
        return {
            "total_translations": total_translations,
            "today_translations": today_translations,
            "top_language_pairs": [
                {"source": pair[0], "target": pair[1]} for pair in language_pairs
            ],
            "top_models": [model[0] for model in models],
            "knowledge_base_usage": kb_usage_count,
            "memory_enhancement_usage": memory_usage_count
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Statistics endpoint error: {error_details}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/languages")
def get_supported_languages():
    """获取支持的语言列表"""
    # 定义支持的语言列表
    supported_languages = [
        {"code": "zh", "name": "中文", "native_name": "中文"},
        {"code": "en", "name": "英语", "native_name": "English"},
        {"code": "ja", "name": "日语", "native_name": "日本語"},
        {"code": "ko", "name": "韩语", "native_name": "한국어"},
        {"code": "fr", "name": "法语", "native_name": "Français"},
        {"code": "de", "name": "德语", "native_name": "Deutsch"},
        {"code": "es", "name": "西班牙语", "native_name": "Español"},
        {"code": "ru", "name": "俄语", "native_name": "Русский"},
        {"code": "ar", "name": "阿拉伯语", "native_name": "العربية"},
        {"code": "pt", "name": "葡萄牙语", "native_name": "Português"},
        {"code": "it", "name": "意大利语", "native_name": "Italiano"},
        {"code": "nl", "name": "荷兰语", "native_name": "Nederlands"},
        {"code": "sv", "name": "瑞典语", "native_name": "Svenska"},
        {"code": "da", "name": "丹麦语", "native_name": "Dansk"},
        {"code": "no", "name": "挪威语", "native_name": "Norsk"},
        {"code": "fi", "name": "芬兰语", "native_name": "Suomi"},
        {"code": "pl", "name": "波兰语", "native_name": "Polski"},
        {"code": "tr", "name": "土耳其语", "native_name": "Türkçe"},
        {"code": "vi", "name": "越南语", "native_name": "Tiếng Việt"},
        {"code": "th", "name": "泰语", "native_name": "ไทย"},
        {"code": "id", "name": "印尼语", "native_name": "Bahasa Indonesia"},
        {"code": "hi", "name": "印地语", "native_name": "हिन्दी"},
        {"code": "bn", "name": "孟加拉语", "native_name": "বাংলা"},
        {"code": "ta", "name": "泰米尔语", "native_name": "தமிழ்"},
        {"code": "te", "name": "泰卢固语", "native_name": "తెలుగు"},
        {"code": "mr", "name": "马拉地语", "native_name": "मराठी"},
        {"code": "gu", "name": "古吉拉特语", "native_name": "ગુજરાતી"},
        {"code": "kn", "name": "卡纳达语", "native_name": "ಕನ್ನಡ"},
        {"code": "ml", "name": "马拉雅拉姆语", "native_name": "മലയാളം"},
        {"code": "pa", "name": "旁遮普语", "native_name": "ਪੰਜਾਬੀ"},
        {"code": "ur", "name": "乌尔都语", "native_name": "اردو"},
        {"code": "fa", "name": "波斯语", "native_name": "فارسی"},
        {"code": "he", "name": "希伯来语", "native_name": "עברית"},
        {"code": "el", "name": "希腊语", "native_name": "Ελληνικά"},
        {"code": "cs", "name": "捷克语", "native_name": "Čeština"},
        {"code": "hu", "name": "匈牙利语", "native_name": "Magyar"},
        {"code": "ro", "name": "罗马尼亚语", "native_name": "Română"},
        {"code": "bg", "name": "保加利亚语", "native_name": "Български"},
        {"code": "hr", "name": "克罗地亚语", "native_name": "Hrvatski"},
        {"code": "sr", "name": "塞尔维亚语", "native_name": "Српски"},
        {"code": "sk", "name": "斯洛伐克语", "native_name": "Slovenčina"},
        {"code": "sl", "name": "斯洛文尼亚语", "native_name": "Slovenščina"},
        {"code": "lt", "name": "立陶宛语", "native_name": "Lietuvių"},
        {"code": "lv", "name": "拉脱维亚语", "native_name": "Latviešu"},
        {"code": "et", "name": "爱沙尼亚语", "native_name": "Eesti"},
        {"code": "uk", "name": "乌克兰语", "native_name": "Українська"},
        {"code": "be", "name": "白俄罗斯语", "native_name": "Беларуская"},
        {"code": "kk", "name": "哈萨克语", "native_name": "Қазақ"},
        {"code": "uz", "name": "乌兹别克语", "native_name": "Oʻzbek"},
        {"code": "az", "name": "阿塞拜疆语", "native_name": "Azərbaycan"},
        {"code": "hy", "name": "亚美尼亚语", "native_name": "Հայերեն"},
        {"code": "ka", "name": "格鲁吉亚语", "native_name": "ქართული"},
        {"code": "km", "name": "高棉语", "native_name": "ខ្មែរ"},
        {"code": "lo", "name": "老挝语", "native_name": "ລາວ"},
        {"code": "my", "name": "缅甸语", "native_name": "မြန်မာ"},
        {"code": "ne", "name": "尼泊尔语", "native_name": "नेपाली"},
        {"code": "si", "name": "僧伽罗语", "native_name": "සිංහල"},
        {"code": "am", "name": "阿姆哈拉语", "native_name": "አማርኛ"},
        {"code": "sw", "name": "斯瓦希里语", "native_name": "Kiswahili"},
        {"code": "yo", "name": "约鲁巴语", "native_name": "Yorùbá"},
        {"code": "zu", "name": "祖鲁语", "native_name": "isiZulu"},
        {"code": "af", "name": "南非荷兰语", "native_name": "Afrikaans"},
        {"code": "is", "name": "冰岛语", "native_name": "Íslenska"},
        {"code": "ga", "name": "爱尔兰语", "native_name": "Gaeilge"},
        {"code": "cy", "name": "威尔士语", "native_name": "Cymraeg"},
        {"code": "mt", "name": "马耳他语", "native_name": "Malti"},
        {"code": "sq", "name": "阿尔巴尼亚语", "native_name": "Shqip"},
        {"code": "mk", "name": "马其顿语", "native_name": "Македонски"},
        {"code": "bs", "name": "波斯尼亚语", "native_name": "Bosanski"},
        {"code": "ca", "name": "加泰罗尼亚语", "native_name": "Català"},
        {"code": "eu", "name": "巴斯克语", "native_name": "Euskara"},
        {"code": "gl", "name": "加利西亚语", "native_name": "Galego"},
        {"code": "br", "name": "布列塔尼语", "native_name": "Brezhoneg"},
        {"code": "gd", "name": "苏格兰盖尔语", "native_name": "Gàidhlig"},
        {"code": "fy", "name": "西弗里西亚语", "native_name": "Frysk"},
        {"code": "lb", "name": "卢森堡语", "native_name": "Lëtzebuergesch"},
        {"code": "mi", "name": "毛利语", "native_name": "Māori"},
        {"code": "sm", "name": "萨摩亚语", "native_name": "Gagana Samoa"},
        {"code": "haw", "name": "夏威夷语", "native_name": "ʻŌlelo Hawaiʻi"},
        {"code": "jw", "name": "爪哇语", "native_name": "Basa Jawa"},
        {"code": "su", "name": "巽他语", "native_name": "Basa Sunda"},
        {"code": "jv", "name": "爪哇语", "native_name": "Basa Jawa"},
        {"code": "mg", "name": "马尔加什语", "native_name": "Malagasy"},
        {"code": "ny", "name": "齐切瓦语", "native_name": "Chichewa"},
        {"code": "sn", "name": "修纳语", "native_name": "chiShona"},
        {"code": "so", "name": "索马里语", "native_name": "Soomaali"},
        {"code": "st", "name": "塞索托语", "native_name": "Sesotho"},
        {"code": "tn", "name": "茨瓦纳语", "native_name": "Setswana"},
        {"code": "ts", "name": "宗加语", "native_name": "Xitsonga"},
        {"code": "ve", "name": "文达语", "native_name": "Tshivenḓa"},
        {"code": "xh", "name": "科萨语", "native_name": "isiXhosa"},
        {"code": "zu", "name": "祖鲁语", "native_name": "isiZulu"},
        {"code": "auto", "name": "自动检测", "native_name": "Auto Detect"}
    ]
    
    return {"languages": supported_languages}