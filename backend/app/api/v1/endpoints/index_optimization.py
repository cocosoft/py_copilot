"""
索引优化 API - DB-002

提供索引分析、优化建议、性能测试等接口

@task DB-002
@phase 数据库任务
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.index_optimizer import (
    IndexAnalyzer,
    IndexOptimizer,
    QueryPerformanceTester,
    IndexRecommendationResult,
    get_index_usage_stats
)
from app.schemas.base import ResponseModel

router = APIRouter()


@router.get("/analyze", response_model=ResponseModel[Dict[str, Any]])
async def analyze_indexes_api(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    分析数据库索引使用情况
    
    返回所有表的索引信息和优化建议
    """
    try:
        analyzer = IndexAnalyzer(db.bind)
        report = analyzer.generate_optimization_report()
        
        return ResponseModel(
            code=200,
            message="索引分析完成",
            data=report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"索引分析失败: {str(e)}")


@router.get("/usage-stats", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_index_usage_stats_api(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取索引使用统计
    
    返回所有索引的扫描次数、大小等统计信息
    """
    try:
        stats = get_index_usage_stats(db.bind)
        
        return ResponseModel(
            code=200,
            message="获取索引使用统计成功",
            data=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取索引统计失败: {str(e)}")


@router.get("/unused", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_unused_indexes_api(
    min_days: int = Query(30, description="最少未使用天数"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取未使用的索引列表
    
    返回指定天数内未被使用的索引
    """
    try:
        analyzer = IndexAnalyzer(db.bind)
        unused = analyzer.find_unused_indexes(min_days=min_days)
        
        data = [
            {
                "table_name": rec.table_name,
                "index_name": rec.index_name,
                "reason": rec.reason,
                "expected_benefit": rec.expected_benefit,
                "priority": rec.priority
            }
            for rec in unused
        ]
        
        return ResponseModel(
            code=200,
            message=f"发现 {len(data)} 个未使用的索引",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找未使用索引失败: {str(e)}")


@router.get("/duplicates", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_duplicate_indexes_api(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取重复/冗余索引列表
    
    返回可以删除的重复索引
    """
    try:
        analyzer = IndexAnalyzer(db.bind)
        duplicates = analyzer.find_duplicate_indexes()
        
        data = [
            {
                "table_name": rec.table_name,
                "index_name": rec.index_name,
                "columns": rec.columns,
                "reason": rec.reason,
                "expected_benefit": rec.expected_benefit,
                "priority": rec.priority
            }
            for rec in duplicates
        ]
        
        return ResponseModel(
            code=200,
            message=f"发现 {len(data)} 个重复索引",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找重复索引失败: {str(e)}")


@router.post("/optimize", response_model=ResponseModel[Dict[str, Any]])
async def optimize_indexes_api(
    dry_run: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    执行索引优化
    
    - dry_run=true: 仅预览优化建议，不实际执行
    - dry_run=false: 执行实际的索引创建/删除操作
    """
    try:
        from app.db.index_optimizer import optimize_indexes
        
        results = optimize_indexes(db.bind, dry_run=dry_run)
        
        return ResponseModel(
            code=200,
            message="索引优化完成" if not dry_run else "索引优化预览完成",
            data={
                "dry_run": dry_run,
                "executed_count": len(results["executed"]),
                "failed_count": len(results["failed"]),
                "skipped_count": len(results["skipped"]),
                "details": results
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"索引优化失败: {str(e)}")


@router.post("/test-performance", response_model=ResponseModel[Dict[str, Any]])
async def test_query_performance_api(
    query: str,
    iterations: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    测试查询性能
    
    执行指定查询多次，返回性能统计
    """
    try:
        tester = QueryPerformanceTester(db.bind)
        stats = tester.test_query_performance(query, iterations=iterations)
        
        return ResponseModel(
            code=200,
            message="性能测试完成",
            data={
                "query": query,
                "iterations": iterations,
                "statistics": stats
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"性能测试失败: {str(e)}")


@router.get("/table/{table_name}", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_table_indexes_api(
    table_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取指定表的索引信息
    
    返回表的所有索引详情
    """
    try:
        analyzer = IndexAnalyzer(db.bind)
        indexes = analyzer.analyze_table_indexes(table_name)
        
        data = [
            {
                "name": idx.name,
                "columns": idx.columns,
                "is_unique": idx.is_unique,
                "is_primary": idx.is_primary,
                "index_type": idx.index_type,
                "size_bytes": idx.size_bytes,
                "usage_count": idx.usage_count
            }
            for idx in indexes
        ]
        
        return ResponseModel(
            code=200,
            message=f"表 {table_name} 共有 {len(data)} 个索引",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表索引信息失败: {str(e)}")


@router.post("/create", response_model=ResponseModel[Dict[str, Any]])
async def create_index_api(
    table_name: str,
    index_name: str,
    columns: List[str],
    unique: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    创建新索引
    
    为指定表的指定列创建索引
    """
    try:
        optimizer = IndexOptimizer(db.bind)
        success = optimizer.create_index(
            table_name=table_name,
            index_name=index_name,
            columns=columns,
            unique=unique
        )
        
        if success:
            return ResponseModel(
                code=200,
                message=f"索引 {index_name} 创建成功",
                data={
                    "table_name": table_name,
                    "index_name": index_name,
                    "columns": columns,
                    "unique": unique
                }
            )
        else:
            raise HTTPException(status_code=500, detail="索引创建失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建索引失败: {str(e)}")


@router.delete("/drop/{table_name}/{index_name}", response_model=ResponseModel[Dict[str, Any]])
async def drop_index_api(
    table_name: str,
    index_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    删除索引
    
    删除指定的索引
    """
    try:
        optimizer = IndexOptimizer(db.bind)
        success = optimizer.drop_index(table_name, index_name)
        
        if success:
            return ResponseModel(
                code=200,
                message=f"索引 {index_name} 删除成功",
                data={
                    "table_name": table_name,
                    "index_name": index_name
                }
            )
        else:
            raise HTTPException(status_code=500, detail="索引删除失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除索引失败: {str(e)}")


@router.get("/recommendations", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_index_recommendations_api(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取索引优化建议
    
    综合分析后返回所有优化建议
    """
    try:
        analyzer = IndexAnalyzer(db.bind)
        
        # 获取各类建议
        unused = analyzer.find_unused_indexes()
        duplicates = analyzer.find_duplicate_indexes()
        
        all_recommendations = unused + duplicates
        
        data = [
            {
                "type": rec.recommendation.value,
                "table_name": rec.table_name,
                "index_name": rec.index_name,
                "columns": rec.columns,
                "reason": rec.reason,
                "expected_benefit": rec.expected_benefit,
                "priority": rec.priority
            }
            for rec in all_recommendations
        ]
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        data.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return ResponseModel(
            code=200,
            message=f"共 {len(data)} 条优化建议",
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取优化建议失败: {str(e)}")
