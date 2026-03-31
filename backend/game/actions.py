"""
动作系统
"""

from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .tank import Tank
    from .map import GameMap
    from .missile import Missile


class ActionType(Enum):
    """动作类型"""
    MOVE = 'move'           # 移动
    TURN = 'turn'           # 转向
    RADAR = 'radar'         # 雷达开关
    RADAR_POWER = 'radar_power'  # 雷达范围设置
    SHIELDS = 'shields'     # 护盾开关
    FIRE = 'fire'           # 开火
    NONE = 'none'           # 无动作


class Action:
    """动作类"""
    
    def __init__(self, action_type: ActionType, param: Optional[str] = None):
        self.action_type = action_type
        self.param = param
        
    @staticmethod
    def move(direction: str) -> 'Action':
        """
        创建移动动作
        direction: 'forward' 或 'backward'
        """
        return Action(ActionType.MOVE, direction)
    
    @staticmethod
    def turn(direction: str) -> 'Action':
        """
        创建转向动作
        direction: 'left' 或 'right'
        """
        return Action(ActionType.TURN, direction)
    
    @staticmethod
    def radar(state: str) -> 'Action':
        """
        创建雷达开关动作
        state: 'on' 或 'off'
        """
        return Action(ActionType.RADAR, state)
    
    @staticmethod
    def radar_power(distance: int) -> 'Action':
        """
        创建雷达范围设置动作
        distance: 1-14
        """
        return Action(ActionType.RADAR_POWER, str(distance))
    
    @staticmethod
    def shields(state: str) -> 'Action':
        """
        创建护盾开关动作
        state: 'on' 或 'off'
        """
        return Action(ActionType.SHIELDS, state)
    
    @staticmethod
    def fire() -> 'Action':
        """创建开火动作"""
        return Action(ActionType.FIRE)
    
    @staticmethod
    def none() -> 'Action':
        """创建空动作"""
        return Action(ActionType.NONE)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'type': self.action_type.value,
            'param': self.param
        }


class ActionExecutor:
    """动作执行器"""
    
    @staticmethod
    def execute_move(tank: 'Tank', game_map: 'GameMap', all_tanks: list, 
                     direction: str) -> bool:
        """
        执行移动动作
        返回是否成功
        """
        if direction == 'forward':
            new_x, new_y = tank.move_forward()
        elif direction == 'backward':
            new_x, new_y = tank.move_backward()
        else:
            return False
            
        # 检查目标位置是否有效
        if not game_map.is_valid_position(new_x, new_y):
            return False
            
        # 检查是否被阻挡
        if game_map.is_blocked(new_x, new_y):
            return False
            
        # 检查是否有其他坦克
        for other_tank in all_tanks:
            if other_tank.id != tank.id and other_tank.is_alive():
                if other_tank.x == new_x and other_tank.y == new_y:
                    return False
                    
        # 执行移动
        tank.set_position(new_x, new_y)
        tank.moved_last_step = True
        
        # 检查是否拾取弹药箱
        if game_map.is_ammo_box(new_x, new_y):
            tank.add_missiles()
            game_map.pickup_ammo(new_x, new_y)
            
        return True
    
    @staticmethod
    def execute_turn(tank: 'Tank', direction: str) -> bool:
        """执行转向动作"""
        if direction == 'left':
            tank.turn_left()
            return True
        elif direction == 'right':
            tank.turn_right()
            return True
        return False
    
    @staticmethod
    def execute_radar(tank: 'Tank', state: str) -> bool:
        """执行雷达开关动作"""
        if state == 'on':
            if tank.energy > 0:
                tank.radar_on = True
                return True
        elif state == 'off':
            tank.radar_on = False
            return True
        return False
    
    @staticmethod
    def execute_radar_power(tank: 'Tank', distance: int) -> bool:
        """执行雷达范围设置动作"""
        from .config import GameConfig
        if GameConfig.RADAR_MIN_DISTANCE <= distance <= GameConfig.RADAR_MAX_DISTANCE:
            tank.radar_setting = distance
            return True
        return False
    
    @staticmethod
    def execute_shields(tank: 'Tank', state: str) -> bool:
        """执行护盾开关动作"""
        if state == 'on':
            if tank.energy > 0:
                tank.shield_on = True
                return True
        elif state == 'off':
            tank.shield_on = False
            return True
        return False
    
    @staticmethod
    def execute_fire(tank: 'Tank') -> Optional['Missile']:
        """
        执行开火动作
        返回创建的导弹对象，如果失败返回 None
        """
        from .missile import Missile
        
        if not tank.consume_missile():
            return None
            
        # 计算导弹初始位置（坦克前方一格）
        dx, dy = tank.direction.get_delta()
        missile_x = tank.x + dx
        missile_y = tank.y + dy
        
        missile = Missile(
            x=missile_x,
            y=missile_y,
            direction=tank.direction,
            owner_id=tank.id,
            owner_team=tank.team
        )
        
        return missile
