"""
地图系统
"""

import random
from enum import Enum
from typing import List, Optional, Tuple, Dict
from .config import GameConfig


class MapElement(Enum):
    """地图元素类型"""
    OPEN = 'open'           # 空地
    TREE = 'tree'           # 树（障碍物）
    STONE = 'stone'         # 石头（障碍物）
    HEALTH = 'health'       # 维修厂
    ENERGY = 'energy'       # 能量补给站
    AMMO = 'ammo'           # 弹药箱


class GameMap:
    """游戏地图类"""
    
    def __init__(self, width: int = None, height: int = None):
        self.width = width or GameConfig.MAP_WIDTH
        self.height = height or GameConfig.MAP_HEIGHT
        self.grid: List[List[MapElement]] = []
        self.ammo_positions: List[Tuple[int, int]] = []  # 弹药箱位置（可被拾取）
        
    def init_empty(self):
        """初始化空地图"""
        self.grid = [
            [MapElement.OPEN for _ in range(self.width)]
            for _ in range(self.height)
        ]
        
    def generate_random(self, 
                        num_trees: int = 15,
                        num_stones: int = 10,
                        num_health: int = 2,
                        num_energy: int = 2,
                        num_ammo: int = 4):
        """生成随机地图"""
        self.init_empty()
        
        # 获取所有可用位置（排除边缘和角落）
        available = []
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                available.append((x, y))
        
        random.shuffle(available)
        
        # 放置元素
        elements = (
            [(MapElement.TREE, num_trees)] +
            [(MapElement.STONE, num_stones)] +
            [(MapElement.HEALTH, num_health)] +
            [(MapElement.ENERGY, num_energy)] +
            [(MapElement.AMMO, num_ammo)]
        )
        
        idx = 0
        for element_type, count in elements:
            for _ in range(count):
                if idx < len(available):
                    x, y = available[idx]
                    self.grid[y][x] = element_type
                    if element_type == MapElement.AMMO:
                        self.ammo_positions.append((x, y))
                    idx += 1
                    
    def get_element(self, x: int, y: int) -> Optional[MapElement]:
        """获取指定位置的元素"""
        if self.is_valid_position(x, y):
            return self.grid[y][x]
        return None
    
    def set_element(self, x: int, y: int, element: MapElement):
        """设置指定位置的元素"""
        if self.is_valid_position(x, y):
            self.grid[y][x] = element
            
    def is_valid_position(self, x: int, y: int) -> bool:
        """检查位置是否有效"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def is_blocked(self, x: int, y: int) -> bool:
        """检查位置是否被障碍物阻挡"""
        element = self.get_element(x, y)
        if element is None:
            return True  # 超出边界视为阻挡
        return element in [MapElement.TREE, MapElement.STONE]
    
    def is_obstacle(self, x: int, y: int) -> bool:
        """检查是否是障碍物（树或石头）"""
        element = self.get_element(x, y)
        return element in [MapElement.TREE, MapElement.STONE]
    
    def is_health_station(self, x: int, y: int) -> bool:
        """检查是否是维修厂"""
        return self.get_element(x, y) == MapElement.HEALTH
    
    def is_energy_station(self, x: int, y: int) -> bool:
        """检查是否是能量补给站"""
        return self.get_element(x, y) == MapElement.ENERGY
    
    def is_ammo_box(self, x: int, y: int) -> bool:
        """检查是否是弹药箱"""
        return (x, y) in self.ammo_positions
    
    def pickup_ammo(self, x: int, y: int) -> bool:
        """拾取弹药箱"""
        if (x, y) in self.ammo_positions:
            self.ammo_positions.remove((x, y))
            self.grid[y][x] = MapElement.OPEN
            return True
        return False
    
    def get_spawn_positions(self, team: str, count: int) -> List[Tuple[int, int]]:
        """获取出生点位置"""
        positions = []
        
        if team == 'red':
            # 红方在左侧
            for i in range(count):
                y = 2 + i * 4
                x = 1
                positions.append((x, y))
        else:
            # 蓝方在右侧
            for i in range(count):
                y = 2 + i * 4
                x = self.width - 2
                positions.append((x, y))
                
        return positions
    
    def to_dict(self) -> Dict:
        """转换为字典用于序列化"""
        grid_data = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(self.grid[y][x].value)
            grid_data.append(row)
            
        return {
            'width': self.width,
            'height': self.height,
            'grid': grid_data,
            'ammoPositions': self.ammo_positions
        }
