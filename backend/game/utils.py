"""
工具函数和日志系统
"""

import logging
import functools
import time
from typing import Callable, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger('TankBattle')


def log_performance(func: Callable) -> Callable:
    """性能日志装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        if elapsed > 50:  # 超过 50ms 记录警告
            logger.warning(f'{func.__name__} took {elapsed:.2f}ms')
        return result
    return wrapper


def safe_execute(func: Callable) -> Callable:
    """安全执行装饰器，捕获异常"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f'Error in {func.__name__}: {e}')
            return None
    return wrapper


def clamp(value: int, min_val: int, max_val: int) -> int:
    """限制值在指定范围内"""
    return max(min_val, min(value, max_val))


def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """计算曼哈顿距离"""
    return abs(x1 - x2) + abs(y1 - y2)


class GameError(Exception):
    """游戏异常基类"""
    pass


class InvalidActionError(GameError):
    """无效动作异常"""
    pass


class InvalidPositionError(GameError):
    """无效位置异常"""
    pass
