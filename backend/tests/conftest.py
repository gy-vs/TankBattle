"""
pytest 配置文件
定义共享的 fixtures 和测试配置
"""

import pytest
import sys
import os

# 将 backend 目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.tank import Tank, Direction
from game.map import GameMap
from game.missile import Missile
from game.engine import GameEngine
from game.config import GameConfig


@pytest.fixture
def game_engine():
    """创建一个初始化的游戏引擎实例"""
    engine = GameEngine()
    engine.init_game()
    return engine


@pytest.fixture
def empty_map():
    """创建一个空白地图（无障碍物）"""
    game_map = GameMap()
    game_map.init_empty()
    return game_map


@pytest.fixture
def red_tank():
    """创建一辆红方坦克"""
    Tank.reset_id_counter()
    return Tank(x=3, y=3, team='red', direction=Direction.EAST)


@pytest.fixture
def blue_tank():
    """创建一辆蓝方坦克"""
    Tank.reset_id_counter()
    return Tank(x=10, y=10, team='blue', direction=Direction.WEST)


@pytest.fixture
def two_tanks():
    """创建红蓝各一辆坦克"""
    Tank.reset_id_counter()
    red = Tank(x=3, y=3, team='red', direction=Direction.EAST)
    blue = Tank(x=7, y=3, team='blue', direction=Direction.WEST)
    return red, blue


@pytest.fixture
def missile_heading_east():
    """创建一枚向东飞行的导弹"""
    Missile.reset_id_counter()
    return Missile(x=5, y=5, direction=Direction.EAST, owner_id=1, owner_team='red')


@pytest.fixture(autouse=True)
def reset_counters():
    """每个测试前重置 ID 计数器"""
    Tank.reset_id_counter()
    Missile.reset_id_counter()
    yield
    Tank.reset_id_counter()
    Missile.reset_id_counter()
