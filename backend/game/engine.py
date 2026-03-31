"""
游戏引擎
"""

import random
from typing import Dict, List, Optional, Tuple
from .config import GameConfig
from .map import GameMap
from .tank import Tank, Direction
from .missile import Missile
from .sensors import (
    BlockedSensor, IncomingSensor, RadarSensor,
    RwaveSensor, SmellSensor, SoundSensor, VisualSensor, CommunicationSensor
)
from .actions import Action, ActionType, ActionExecutor
from .ai import SimpleAI


class GameState:
    """游戏状态"""
    WAITING = 'waiting'
    RUNNING = 'running'
    PAUSED = 'paused'
    FINISHED = 'finished'


class GameEngine:
    """游戏引擎"""
    
    def __init__(self):
        self.game_map: Optional[GameMap] = None
        self.tanks: List[Tank] = []
        self.missiles: List[Missile] = []
        self.clock = 0
        self.state = GameState.WAITING
        self.winner = None
        self.events: List[Dict] = []  # 游戏事件日志
        
        # AI 控制器
        self.ai_controllers: Dict[int, SimpleAI] = {}
        
        # 特效事件（开火、命中等，每步重置）
        self.fire_events: List[Dict] = []
        self.hit_events: List[Dict] = []
        
    def init_game(self, map_config: Dict = None):
        """初始化游戏"""
        # 重置 ID 计数器
        Tank.reset_id_counter()
        Missile.reset_id_counter()
        
        # 创建地图
        self.game_map = GameMap()
        self.game_map.generate_random()
        
        # 创建坦克
        self.tanks = []
        self.missiles = []
        self.events = []
        
        # 红方坦克（左侧，朝东）
        red_positions = self.game_map.get_spawn_positions('red', GameConfig.TANKS_PER_TEAM)
        for x, y in red_positions:
            tank = Tank(x, y, 'red', Direction.EAST)
            self.tanks.append(tank)
            self.ai_controllers[tank.id] = SimpleAI(tank.id, 'red')
            
        # 蓝方坦克（右侧，朝西）
        blue_positions = self.game_map.get_spawn_positions('blue', GameConfig.TANKS_PER_TEAM)
        for x, y in blue_positions:
            tank = Tank(x, y, 'blue', Direction.WEST)
            self.tanks.append(tank)
            self.ai_controllers[tank.id] = SimpleAI(tank.id, 'blue')
            
        self.clock = 0
        self.state = GameState.WAITING
        self.winner = None
        
        self._add_event('game_init', '游戏初始化完成')
        
    def start(self):
        """开始游戏"""
        if self.state in [GameState.WAITING, GameState.PAUSED]:
            self.state = GameState.RUNNING
            self._add_event('game_start', '游戏开始')
            
    def pause(self):
        """暂停游戏"""
        if self.state == GameState.RUNNING:
            self.state = GameState.PAUSED
            self._add_event('game_pause', '游戏暂停')
            
    def step(self):
        """执行一步仿真"""
        if self.state == GameState.FINISHED:
            return
            
        self.clock += 1
        
        # 重置特效事件
        self.fire_events = []
        self.hit_events = []
        
        # 重置移动标记
        for tank in self.tanks:
            tank.moved_last_step = False
            
        # 1. 处理坦克在补给站的恢复
        self._process_stations()
        
        # 2. 处理能量消耗（雷达、护盾）
        self._process_energy_costs()
        
        # 3. 获取每个坦克的传感器数据并决定动作
        tank_actions = {}
        for tank in self.tanks:
            if tank.is_alive():
                sensor_data = self._get_sensor_data(tank)
                # 使用 AI 决定动作
                if tank.id in self.ai_controllers:
                    action = self.ai_controllers[tank.id].decide(sensor_data, tank)
                else:
                    action = Action.none()
                tank_actions[tank.id] = action
                
        # 4. 执行动作
        new_missiles = []
        for tank in self.tanks:
            if tank.is_alive() and tank.id in tank_actions:
                action = tank_actions[tank.id]
                missile = self._execute_action(tank, action)
                if missile:
                    new_missiles.append(missile)
                    
        self.missiles.extend(new_missiles)
        
        # 5. 更新导弹位置和碰撞检测
        self._update_missiles()
        
        # 6. 检查胜负
        self._check_game_over()
        
    def _process_stations(self):
        """处理补给站和弹药箱效果"""
        for tank in self.tanks:
            if not tank.is_alive():
                continue
                
            # 维修厂
            if self.game_map.is_health_station(tank.x, tank.y):
                tank.heal()
                
            # 能量补给站
            if self.game_map.is_energy_station(tank.x, tank.y):
                tank.recharge_energy()
                
            # 弹药箱（拾取后消失）
            if self.game_map.is_ammo_box(tank.x, tank.y):
                if self.game_map.pickup_ammo(tank.x, tank.y):
                    tank.add_missiles()
                    self._add_event('ammo_pickup', 
                                   f'{tank.team} 坦克 {tank.id} 拾取弹药箱，炮弹 +{GameConfig.AMMO_PICKUP_AMOUNT}')
                
    def _process_energy_costs(self):
        """处理能量消耗"""
        for tank in self.tanks:
            if not tank.is_alive():
                continue
            tank.update_radar_cost()
            tank.update_shield_cost()
            
    def _get_sensor_data(self, tank: Tank) -> Dict:
        """获取坦克的传感器数据"""
        return {
            'blocked': BlockedSensor.sense(tank, self.game_map, self.tanks),
            'incoming': IncomingSensor.sense(tank, self.missiles, self.game_map, self.tanks),
            'radar': RadarSensor.sense(tank, self.game_map, self.tanks),
            'rwave': RwaveSensor.sense(tank, self.tanks),
            'smell': SmellSensor.sense(tank, self.tanks),
            'sound': SoundSensor.sense(tank, self.tanks, self.game_map),
            'visual': VisualSensor.sense(tank, self.game_map, self.tanks),  # 近距离视觉
            'communication': CommunicationSensor.sense(tank, self.tanks),  # 内部通信
            'self': {
                'clock': self.clock,
                'direction': tank.direction.value,
                'energy': tank.energy,
                'energyrecharger': 'yes' if self.game_map.is_energy_station(tank.x, tank.y) else 'no',
                'health': tank.health,
                'healthrecharger': 'yes' if self.game_map.is_health_station(tank.x, tank.y) else 'no',
                'missiles': tank.missiles,
                'my_color': tank.team,
                'radar_setting': tank.radar_setting,
                'radar_distance': tank.radar_distance,
                'radar_status': 'on' if tank.radar_on else 'off',
                'shield_status': 'on' if tank.shield_on else 'off',
                'x': tank.x,
                'y': tank.y,
                'id': tank.id
            }
        }
        
    def _execute_action(self, tank: Tank, action: Action) -> Optional[Missile]:
        """执行动作，返回可能产生的导弹"""
        if action.action_type == ActionType.MOVE:
            ActionExecutor.execute_move(tank, self.game_map, self.tanks, action.param)
        elif action.action_type == ActionType.TURN:
            ActionExecutor.execute_turn(tank, action.param)
        elif action.action_type == ActionType.RADAR:
            ActionExecutor.execute_radar(tank, action.param)
        elif action.action_type == ActionType.RADAR_POWER:
            ActionExecutor.execute_radar_power(tank, int(action.param))
        elif action.action_type == ActionType.SHIELDS:
            ActionExecutor.execute_shields(tank, action.param)
        elif action.action_type == ActionType.FIRE:
            missile = ActionExecutor.execute_fire(tank)
            if missile:
                # 记录开火事件
                self.fire_events.append({
                    'x': tank.x,
                    'y': tank.y,
                    'direction': tank.direction.value,
                    'tank_id': tank.id,
                    'team': tank.team
                })
            return missile
            
        return None
        
    def _update_missiles(self):
        """更新导弹状态"""
        for missile in self.missiles:
            if not missile.is_active():
                continue
                
            # 获取导弹经过的路径
            old_x, old_y = missile.x, missile.y
            path = []
            
            dx, dy = missile.direction.get_delta()
            for step in range(GameConfig.MISSILE_SPEED):
                next_x = old_x + dx * (step + 1)
                next_y = old_y + dy * (step + 1)
                path.append((next_x, next_y))
                
            # 检查路径上的碰撞
            for check_x, check_y in path:
                # 检查边界
                if not self.game_map.is_valid_position(check_x, check_y):
                    missile.deactivate()
                    break
                    
                # 检查障碍物
                if self.game_map.is_obstacle(check_x, check_y):
                    missile.deactivate()
                    self._add_event('missile_hit_obstacle', 
                                   f'导弹 {missile.id} 击中障碍物 ({check_x}, {check_y})')
                    break
                    
                # 检查坦克
                for tank in self.tanks:
                    if not tank.is_alive():
                        continue
                    if tank.x == check_x and tank.y == check_y:
                        # 命中坦克
                        missile.deactivate()
                        
                        # 记录命中事件
                        self.hit_events.append({
                            'x': tank.x,
                            'y': tank.y,
                            'tank_id': tank.id,
                            'team': tank.team
                        })
                        
                        # 检查坦克是否在补给站
                        if (self.game_map.is_health_station(tank.x, tank.y) or 
                            self.game_map.is_energy_station(tank.x, tank.y)):
                            tank.instant_death()
                            self._add_event('tank_destroyed_at_station',
                                          f'{tank.team} 坦克 {tank.id} 在补给站被击毁')
                        else:
                            # 计算伤害方向
                            relative_dir = tank.get_relative_direction(old_x, old_y)
                            tank.take_damage(0, relative_dir)  # 伤害在 take_damage 中计算
                            
                            if not tank.is_alive():
                                self._add_event('tank_destroyed',
                                              f'{tank.team} 坦克 {tank.id} 被击毁')
                            else:
                                self._add_event('tank_hit',
                                              f'{tank.team} 坦克 {tank.id} 被击中，剩余生命 {tank.health}')
                        break
                        
                if not missile.is_active():
                    break
                    
            # 如果导弹仍然有效，更新位置
            if missile.is_active():
                missile.x = old_x + dx * GameConfig.MISSILE_SPEED
                missile.y = old_y + dy * GameConfig.MISSILE_SPEED
                
        # 移除失效的导弹
        self.missiles = [m for m in self.missiles if m.is_active()]
        
    def _check_game_over(self):
        """检查游戏是否结束"""
        red_tanks = [t for t in self.tanks if t.team == 'red' and t.is_alive()]
        blue_tanks = [t for t in self.tanks if t.team == 'blue' and t.is_alive()]
        
        red_count = len(red_tanks)
        blue_count = len(blue_tanks)
        
        # 一方全灭
        if red_count == 0:
            self.state = GameState.FINISHED
            self.winner = 'blue'
            self._add_event('game_over', '蓝方获胜 - 红方全灭')
            return
            
        if blue_count == 0:
            self.state = GameState.FINISHED
            self.winner = 'red'
            self._add_event('game_over', '红方获胜 - 蓝方全灭')
            return
            
        # 达到最大步数
        if self.clock >= GameConfig.MAX_STEPS:
            if red_count > blue_count:
                self.winner = 'red'
                self._add_event('game_over', '红方获胜 - 坦克数量优势')
            elif blue_count > red_count:
                self.winner = 'blue'
                self._add_event('game_over', '蓝方获胜 - 坦克数量优势')
            else:
                # 数量相等，比较平均生命值
                red_avg_health = sum(t.health for t in red_tanks) / red_count
                blue_avg_health = sum(t.health for t in blue_tanks) / blue_count
                
                if red_avg_health > blue_avg_health:
                    self.winner = 'red'
                    self._add_event('game_over', '红方获胜 - 平均生命值优势')
                elif blue_avg_health > red_avg_health:
                    self.winner = 'blue'
                    self._add_event('game_over', '蓝方获胜 - 平均生命值优势')
                else:
                    self.winner = 'draw'
                    self._add_event('game_over', '平局')
                    
            self.state = GameState.FINISHED
            
    def _add_event(self, event_type: str, message: str):
        """添加游戏事件"""
        self.events.append({
            'clock': self.clock,
            'type': event_type,
            'message': message
        })
        
    def is_game_over(self) -> bool:
        """检查游戏是否结束"""
        return self.state == GameState.FINISHED
    
    def get_result(self) -> Dict:
        """获取游戏结果"""
        red_tanks = [t for t in self.tanks if t.team == 'red']
        blue_tanks = [t for t in self.tanks if t.team == 'blue']
        
        return {
            'winner': self.winner,
            'clock': self.clock,
            'red': {
                'alive': sum(1 for t in red_tanks if t.is_alive()),
                'total': len(red_tanks),
                'avgHealth': sum(t.health for t in red_tanks if t.is_alive()) / max(1, sum(1 for t in red_tanks if t.is_alive()))
            },
            'blue': {
                'alive': sum(1 for t in blue_tanks if t.is_alive()),
                'total': len(blue_tanks),
                'avgHealth': sum(t.health for t in blue_tanks if t.is_alive()) / max(1, sum(1 for t in blue_tanks if t.is_alive()))
            }
        }
        
    def get_state(self) -> Dict:
        """获取完整游戏状态"""
        # 增强坦克数据，添加补给站状态
        tanks_data = []
        for t in self.tanks:
            tank_dict = t.to_dict()
            # 添加补给站状态
            if self.game_map:
                tank_dict['atHealthStation'] = self.game_map.is_health_station(t.x, t.y)
                tank_dict['atEnergyStation'] = self.game_map.is_energy_station(t.x, t.y)
            else:
                tank_dict['atHealthStation'] = False
                tank_dict['atEnergyStation'] = False
            tanks_data.append(tank_dict)
        
        return {
            'clock': self.clock,
            'state': self.state,
            'map': self.game_map.to_dict() if self.game_map else None,
            'tanks': tanks_data,
            'missiles': [m.to_dict() for m in self.missiles],
            'events': self.events[-20:],  # 最近20条事件
            'winner': self.winner,
            'fire_events': self.fire_events,  # 开火特效
            'hit_events': self.hit_events     # 命中特效
        }
