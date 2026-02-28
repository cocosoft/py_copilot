"""搜索管理API（已废弃，请使用能力中心）

⚠️ 警告：该模块中的所有API已废弃
请使用新的能力中心API：/api/v1/capability-center/*
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get(
    "/settings",
    deprecated=True,
    summary="⚠️ 已废弃 - 获取搜索设置",
    description="该接口已废弃，请使用 `/api/v1/capability-center/capabilities?type=tool&category=search`"
)
async def get_search_settings_deprecated():
    """
    ⚠️ 已废弃
    
    该接口已废弃，请使用 `/api/v1/capability-center/capabilities?type=tool&category=search`
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="该接口已废弃，请使用能力中心API: /api/v1/capability-center/capabilities?type=tool&category=search"
    )


@router.put(
    "/settings",
    deprecated=True,
    summary="⚠️ 已废弃 - 更新搜索设置",
    description="该接口已废弃，请使用 `/api/v1/capability-center/capabilities/{capability_id}`"
)
async def update_search_settings_deprecated():
    """
    ⚠️ 已废弃
    
    该接口已废弃，请使用 `/api/v1/capability-center/capabilities/{capability_id}`
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="该接口已废弃，请使用能力中心API: /api/v1/capability-center/capabilities/{capability_id}"
    )


@router.delete(
    "/settings",
    deprecated=True,
    summary="⚠️ 已废弃 - 删除搜索设置",
    description="该接口已废弃，请使用 `/api/v1/capability-center/capabilities/{capability_id}`"
)
async def delete_search_settings_deprecated():
    """
    ⚠️ 已废弃
    
    该接口已废弃，请使用 `/api/v1/capability-center/capabilities/{capability_id}`
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="该接口已废弃，请使用能力中心API: /api/v1/capability-center/capabilities/{capability_id}"
    )


@router.get(
    "/engines",
    deprecated=True,
    summary="⚠️ 已废弃 - 获取搜索引擎列表",
    description="该接口已废弃，请使用 `/api/v1/capability-center/capabilities/categories`"
)
async def get_search_engines_deprecated():
    """
    ⚠️ 已废弃
    
    该接口已废弃，请使用 `/api/v1/capability-center/capabilities/categories`
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="该接口已废弃，请使用能力中心API: /api/v1/capability-center/capabilities/categories"
    )
