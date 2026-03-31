"""
坦克实体
"""

from enum import Enum
from typing import Dict, Optional, Tuple, List
from .config import GameConfig


class Direction(Enum):
    """方向枚举"""
    NORTH = 'north'
    EAST = 'east'
    SOUTH = 'south'
    WEST = 'west'
    
    def turn_left(self) -> 'Direction':
        """左转"""
        mapping = {
            Direction.NORTH: Direction.WEST,
            Direction.WEST: Direction.SOUTH,
            Direction.SOUTH: Direction.EAST,
            Direction.EAST: Direction.NORTH
        }
        return mapping[self]
    
    def turn_right(self) -> 'Direction':
        """右转"""
        mapping = {
            Direction.NORTH: Direction.EAST,
            Direction.EAST: Direction.SOUTH,
            Direction.SOUTH: Direction.WEST,
            Direction.WEST: Direction.NORTH
        }
        return mapping[self]
    
    def get_delta(self) -> Tuple[int, int]:
        """获取方向对应的坐标增量"""
        mapping = {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0)
        }
        return mapping[self]
    
    def get_opposite(self) -> 'Direction':
        """获取相反方向"""
        mapping = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST
        }
        return mapping[self]


class Tank:
    """坦克类"""
    
    _id_counter = 0
    
    def __init__(self, x: int, y: int, team: str, direction: Direction = Direction.NORTH):
        Tank._id_counter += 1
        self.id = Tank._id_counter
        
        # 位置和方向
        self.x = x
        self.y = y
        self.direction = direction
        
        # 阵营
        self.team = team  # 'red' 或 'blue'
        
        # 属性值
        self.health = GameConfig.TANK_INITIAL_HEALTH
        self.energy = GameConfig.TANK_INITIAL_ENERGY
        self.missiles = GameConfig.TANK_INITIAL_MISSILES
        
        # 状态
        self.shield_on = False
        self.radar_on = False
        self.radar_setting = 7  # 默认雷达距离
        self.radar_distance = {'left': 0, 'center': 0, 'right': 0}  # 实际探测距离
        
        # 是否存活
        self.alive = True
        
        # 上一步是否移动（用于声音传感器）
        self.moved_last_step = False
        
    @classmethod
    def reset_id_counter(cls):
        """重置 ID 计数器"""
        cls._id_counter = 0
        
    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.alive and self.health > 0
    
    def take_damage(self, damage: int, from_direction: str):
        """
        受到伤害
        from_direction: 'forward', 'backward', 'left', 'right' (相对于坦克朝向)
        """
        if not self.alive:
            return
            
        # 根据方向计算实际伤害
        if from_direction == 'forward':
            actual_damage = GameConfig.DAMAGE_BACK
        elif from_direction == 'backward':
            actual_damage = GameConfig.DAMAGE_FRONT
        else:  # left 或 right
            actual_damage = GameConfig.DAMAGE_SIDE
            
        # 如果开启护盾且能量足够，护盾抵消伤害（只扣能量，不扣血）
        if self.shield_on and self.energy >= GameConfig.SHIELD_HIT_ENERGY_COST:
            self.energy -= GameConfig.SHIELD_HIT_ENERGY_COST
            # 护盾成功抵消伤害，不扣血
            return
            
        # 护盾未开启或能量不足，正常扣血
        self.health -= actual_damage
        
        if self.health <= 0:
            self.health = 0
            self.alive = False
            
    def instant_death(self):
        """立即死亡（在补给站被攻击）"""
        self.health = 0
        self.alive = False
        
    def heal(self, amount: int = None):
        """恢复生命值"""
        if amount is None:
            amount = GameConfig.HEALTH_REGEN_PER_STEP
        self.health = min(self.health + amount, GameConfig.TANK_MAX_HEALTH)
        
    def recharge_energy(self, amount: int = None):
        """恢复能量"""
        if amount is None:
            amount = GameConfig.ENERGY_REGEN_PER_STEP
        self.energy = min(self.energy + amount, GameConfig.TANK_MAX_ENERGY)
        
    def add_missiles(self, amount: int = None):
        """增加炮弹"""
        if amount is None:
            amount = GameConfig.AMMO_PICKUP_AMOUNT
        self.missiles = min(self.missiles + amount, GameConfig.TANK_MAX_MISSILES)
        
    def consume_energy(self, amount: int) -> bool:
        """消耗能量，返回是否成功"""
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False
    
    def consume_missile(self) -> bool:
        """消耗一枚炮弹，返回是否成功"""
        if self.missiles > 0:
            self.missiles -= 1
            return True
        return False
    
    def update_radar_cost(self):
        """更新雷达能量消耗"""
        if self.radar_on:
            cost = self.radar_setting * GameConfig.RADAR_ENERGY_COST_MULTIPLIER
            if not self.consume_energy(cost):
                # 能量不足，自动关闭雷达
                self.radar_on = False
                
    def update_shield_cost(self):
        """更新护盾能量消耗"""
        if self.shield_on:
            if not self.consume_energy(GameConfig.SHIELD_ENERGY_COST_PER_STEP):
                # 能量不足，自动关闭护盾
                self.shield_on = False
                
    def move_forward(self) -> Tuple[int, int]:
        """获取向前移动后的位置"""
        dx, dy = self.direction.get_delta()
        return self.x + dx, self.y + dy
    
    def move_backward(self) -> Tuple[int, int]:
        """获取向后移动后的位置"""
        dx, dy = self.direction.get_delta()
        return self.x - dx, self.y - dy
    
    def set_position(self, x: int, y: int):
        """设置位置"""
        self.x = x
        self.y = y
        
    def turn_left(self):
        """左转"""
        self.direction = self.direction.turn_left()
        
    def turn_right(self):
        """右转"""
        self.direction = self.direction.turn_right()
        
    def get_relative_direction(self, from_x: int, from_y: int) -> str:
        """
        获取指定位置相对于坦克的方向（相对于坦克朝向）
        返回: 'forward', 'backward', 'left', 'right'
        
        例如：坦克在 (5,5) 朝向东，目标在 (10,5)（东边），返回 'forward'
        """
        # 计算目标相对于坦克的位置偏移
        dx = from_x - self.x
        dy = from_y - self.y
        
        if dx == 0 and dy == 0:
            return 'forward'  # 同一位置
            
        # 确定目标所在的绝对方向
        # dx > 0 表示目标在东边，dx < 0 表示目标在西边
        # dy > 0 表示目标在南边，dy < 0 表示目标在北边
        if abs(dx) >= abs(dy):
            abs_dir = Direction.EAST if dx > 0 else Direction.WEST
        else:
            abs_dir = Direction.SOUTH if dy > 0 else Direction.NORTH
            
        # 转换为相对方向
        if abs_dir == self.direction:
            return 'forward'
        elif abs_dir == self.direction.get_opposite():
            return 'backward'
        elif abs_dir == self.direction.turn_left():
            return 'left'
        else:
            return 'right'
            
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'direction': self.direction.value,
            'team': self.team,
            'health': self.health,
            'energy': self.energy,
            'missiles': self.missiles,
            'shieldOn': self.shield_on,
            'radarOn': self.radar_on,
            'radarSetting': self.radar_setting,
            'radarDistance': self.radar_distance,
            'alive': self.alive
        }
