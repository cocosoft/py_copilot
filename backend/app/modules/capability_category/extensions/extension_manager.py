"""扩展点管理模块

该模块提供了一个扩展点管理系统，允许开发者在分类管理的关键流程中注册自定义扩展函数。

主要扩展点包括：
1. 分类创建前后钩子
2. 分类更新前后钩子  
3. 分类删除前后钩子
4. 分类查询结果转换钩子
5. 分类参数验证钩子

使用方法：
1. 定义扩展函数
2. 使用register_extension装饰器注册到相应的扩展点
3. 系统会在对应流程中自动调用所有注册的扩展函数
"""
from typing import Dict, List, Callable, Any, Optional
from functools import wraps


# 扩展点类型定义
extension_hook = Callable[..., Any]


class ExtensionManager:
    """扩展点管理器
    
    负责管理所有扩展点和注册的扩展函数
    """
    
    def __init__(self):
        # 扩展点注册表
        self.extensions: Dict[str, List[extension_hook]] = {
            # 分类创建钩子
            'before_create_category': [],
            'after_create_category': [],
            
            # 分类更新钩子
            'before_update_category': [],
            'after_update_category': [],
            
            # 分类删除钩子
            'before_delete_category': [],
            'after_delete_category': [],
            
            # 分类查询钩子
            'before_get_category': [],
            'after_get_category': [],
            'before_get_categories': [],
            'after_get_categories': [],
            
            # 分类参数验证钩子
            'validate_category_params': [],
            
            # 模型分类关联钩子
            'before_add_category_to_model': [],
            'after_add_category_to_model': [],
            'before_remove_category_from_model': [],
            'after_remove_category_from_model': [],
        }
    
    def register_extension(self, extension_point: str, func: extension_hook) -> extension_hook:
        """注册扩展函数到指定的扩展点
        
        Args:
            extension_point: 扩展点名称
            func: 扩展函数
            
        Returns:
            原始扩展函数（用于装饰器链式调用）
        """
        if extension_point not in self.extensions:
            raise ValueError(f"未知的扩展点: {extension_point}")
        
        self.extensions[extension_point].append(func)
        return func
    
    def register_extension_decorator(self, extension_point: str):
        """用于注册扩展函数的装饰器工厂
        
        Args:
            extension_point: 扩展点名称
            
        Returns:
            装饰器函数
        """
        def decorator(func: extension_hook) -> extension_hook:
            return self.register_extension(extension_point, func)
        return decorator
    
    def execute_extensions(self, extension_point: str, *args, **kwargs) -> List[Any]:
        """执行指定扩展点的所有扩展函数
        
        Args:
            extension_point: 扩展点名称
            *args: 传递给扩展函数的位置参数
            **kwargs: 传递给扩展函数的关键字参数
            
        Returns:
            所有扩展函数的返回值列表
        """
        results = []
        if extension_point in self.extensions:
            for func in self.extensions[extension_point]:
                try:
                    result = func(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    # 记录错误但不中断流程
                    import logging
                    logging.error(f"执行扩展函数 {func.__name__} 失败: {str(e)}")
        return results
    
    def execute_extensions_with_result(self, extension_point: str, initial_result: Any, *args, **kwargs) -> Any:
        """执行指定扩展点的所有扩展函数，并传递和返回处理结果
        
        适用于需要对数据进行链式处理的扩展点（如查询结果转换）
        
        Args:
            extension_point: 扩展点名称
            initial_result: 初始结果
            *args: 传递给扩展函数的位置参数
            **kwargs: 传递给扩展函数的关键字参数
            
        Returns:
            经过所有扩展函数处理后的最终结果
        """
        result = initial_result
        if extension_point in self.extensions:
            for func in self.extensions[extension_point]:
                try:
                    result = func(result, *args, **kwargs)
                except Exception as e:
                    # 记录错误但不中断流程
                    import logging
                    logging.error(f"执行扩展函数 {func.__name__} 失败: {str(e)}")
        return result


# 创建全局扩展管理器实例
extension_manager = ExtensionManager()


# 导出常用的扩展点装饰器
before_create_category = extension_manager.register_extension_decorator('before_create_category')
after_create_category = extension_manager.register_extension_decorator('after_create_category')

before_update_category = extension_manager.register_extension_decorator('before_update_category')
after_update_category = extension_manager.register_extension_decorator('after_update_category')

before_delete_category = extension_manager.register_extension_decorator('before_delete_category')
after_delete_category = extension_manager.register_extension_decorator('after_delete_category')

before_get_category = extension_manager.register_extension_decorator('before_get_category')
after_get_category = extension_manager.register_extension_decorator('after_get_category')

before_get_categories = extension_manager.register_extension_decorator('before_get_categories')
after_get_categories = extension_manager.register_extension_decorator('after_get_categories')

validate_category_params = extension_manager.register_extension_decorator('validate_category_params')

before_add_category_to_model = extension_manager.register_extension_decorator('before_add_category_to_model')
after_add_category_to_model = extension_manager.register_extension_decorator('after_add_category_to_model')

before_remove_category_from_model = extension_manager.register_extension_decorator('before_remove_category_from_model')
after_remove_category_from_model = extension_manager.register_extension_decorator('after_remove_category_from_model')


# 导出扩展管理器
__all__ = [
    'extension_manager',
    'before_create_category',
    'after_create_category',
    'before_update_category', 
    'after_update_category',
    'before_delete_category',
    'after_delete_category',
    'before_get_category',
    'after_get_category',
    'before_get_categories',
    'after_get_categories',
    'validate_category_params',
    'before_add_category_to_model',
    'after_add_category_to_model',
    'before_remove_category_from_model',
    'after_remove_category_from_model',
]