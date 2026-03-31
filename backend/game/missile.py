"""
导弹系统
"""

from typing import Dict, Optional, Tuple
from .tank import Direction
from .config import GameConfig


class Missile:
    """导弹类"""
    
    _id_counter = 0
    
    def __init__(self, x: int, y: int, direction: Direction, owner_id: int, owner_team: str):
        Missile._id_counter += 1
        self.id = Missile._id_counter
        
        # 位置和方向
        self.x = x
        self.y = y
        self.direction = direction
        
        # 所属坦克
        self.owner_id = owner_id
        self.owner_team = owner_team
        
        # 状态
        self.active = True
        
        # 发射位置（用于计算盲区）
        self.launch_x = x
        self.launch_y = y
        
    @classmethod
    def reset_id_counter(cls):
        """重置 ID 计数器"""
        cls._id_counter = 0
        
    def move(self) -> Tuple[int, int]:
        """
        导弹移动（速度是坦克的2倍，所以每步移动2格）
        返回移动后的位置
        """
        dx, dy = self.direction.get_delta()
        # 导弹速度是坦克的2倍
        self.x += dx * GameConfig.MISSILE_SPEED
        self.y += dy * GameConfig.MISSILE_SPEED
        return self.x, self.y
    
    def get_path(self) -> list:
        """
        获取导弹这一步经过的所有格子
        用于碰撞检测
        """
        path = []
        dx, dy = self.direction.get_delta()
        
        current_x = self.x
        current_y = self.y
        
        for _ in range(GameConfig.MISSILE_SPEED):
            current_x += dx
            current_y += dy
            path.append((current_x, current_y))
            
        return path
    
    def deactivate(self):
        """使导弹失效"""
        self.active = False
        
    def is_active(self) -> bool:
        """检查导弹是否仍然有效"""
        return self.active
    
    def get_distance_from_launch(self) -> int:
        """获取距离发射点的距离"""
        return abs(self.x - self.launch_x) + abs(self.y - self.launch_y)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'direction': self.direction.value,
            'ownerTeam': self.owner_team,
            'active': self.active
        }
