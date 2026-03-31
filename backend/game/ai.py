"""
AI 策略模块
智能坦克行为控制
"""

import random
from typing import Dict, List, Optional, TYPE_CHECKING
from .actions import Action, ActionType

if TYPE_CHECKING:
    from .tank import Tank


class TacticalAI:
    """
    战术AI策略
    基于状态机的智能决策系统，充分利用所有传感器
    """
    
    # 状态定义
    STATE_PATROL = 'patrol'       # 巡逻寻敌
    STATE_ENGAGE = 'engage'       # 交战攻击
    STATE_EVADE = 'evade'         # 规避危险
    STATE_PURSUE = 'pursue'       # 追击敌人
    STATE_RECHARGE = 'recharge'   # 补给恢复
    STATE_STUCK = 'stuck'         # 被困脱离
    
    def __init__(self, tank_id: int, team: str):
        self.tank_id = tank_id
        self.team = team
        self.state = self.STATE_PATROL
        
        # 历史记录（用于检测被困）
        self.position_history: List[tuple] = []
        self.direction_history: List[str] = []
        self.action_history: List[str] = []
        self.stuck_counter = 0
        self.stuck_escape_dir = None
        
        # 战术状态
        self.last_enemy_pos = None  # 最后一次发现敌人的位置
        self.engagement_timer = 0   # 交战计时器
        self.patrol_timer = 0       # 巡逻计时器
        self.search_pattern = 0     # 搜索模式计数
        
    def decide(self, sensor_data: Dict, tank: 'Tank') -> Action:
        """
        核心决策逻辑
        优先级：躲避导弹 > 近距离视觉交战 > 雷达交战 > 追击 > 补给 > 巡逻
        """
        # 解析传感器数据
        blocked = sensor_data['blocked']
        incoming = sensor_data['incoming']
        radar = sensor_data['radar']
        rwave = sensor_data['rwave']
        smell = sensor_data['smell']
        sound = sensor_data['sound']
        visual = sensor_data.get('visual', [])  # 近距离视觉传感器
        self_data = sensor_data['self']
        
        # 更新位置历史
        self._update_history(self_data)
        
        # 1. 最高优先级：躲避来袭导弹
        evade_action = self._check_incoming_missiles(incoming, blocked, self_data)
        if evade_action:
            self.state = self.STATE_EVADE
            return evade_action
        
        # 关闭护盾节省能量（无威胁时）
        if self._is_safe(incoming) and self_data['shield_status'] == 'on':
            return Action.shields('off')
        
        # 2. 检测被困状态
        if self._is_stuck():
            self.state = self.STATE_STUCK
            escape_action = self._escape_stuck(blocked, self_data)
            if escape_action:
                return escape_action
        
        # 3. 【重要】近距离视觉检测敌人 - 不需要雷达！
        # 即使没有能量，坦克也能在1-2格内"看到"敌人
        visual_enemy = self._find_enemy_in_visual(visual)
        if visual_enemy:
            self.state = self.STATE_ENGAGE
            self.last_enemy_pos = visual_enemy
            self.engagement_timer = 10
            return self._engage_enemy(visual_enemy, blocked, self_data)
        
        # 4. 检查雷达发现的敌人（需要雷达开启）
        enemy = self._find_enemy_in_radar(radar)
        if enemy:
            self.state = self.STATE_ENGAGE
            self.last_enemy_pos = enemy
            self.engagement_timer = 10  # 保持交战状态
            return self._engage_enemy(enemy, blocked, self_data)
        
        # 4. 检查是否被敌方雷达扫描 - 说明附近有敌人
        threat_dir = self._check_radar_threat(rwave)
        if threat_dir:
            # 被敌人雷达扫描到，开启雷达反制并准备战斗
            if self_data['radar_status'] == 'off' and self_data['energy'] > 50:
                return Action.radar('on')
            # 转向威胁方向
            return self._turn_to_direction(threat_dir, self_data['direction'])
        
        # 5. 使用气味传感器追踪敌人
        if smell['color'] and smell['color'] != self.team:
            self.state = self.STATE_PURSUE
            return self._pursue_by_smell(smell, sound, blocked, self_data)
        
        # 6. 使用声音传感器追踪移动的敌人
        if sound != 'silent':
            self.state = self.STATE_PURSUE
            return self._pursue_by_sound(sound, blocked, self_data)
        
        # 7. 检查是否需要补给
        if self._need_recharge(self_data):
            recharge_action = self._seek_recharge(radar, blocked, self_data)
            if recharge_action:
                self.state = self.STATE_RECHARGE
                return recharge_action
        
        # 8. 巡逻搜索模式（传递气味和声音数据用于追踪）
        self.state = self.STATE_PATROL
        return self._patrol(blocked, self_data, smell, sound)
    
    def _update_history(self, self_data: Dict):
        """更新历史记录"""
        pos = (self_data['x'], self_data['y'])
        direction = self_data['direction']
        
        self.position_history.append(pos)
        self.direction_history.append(direction)
        
        # 只保留最近20条记录
        if len(self.position_history) > 20:
            self.position_history.pop(0)
            self.direction_history.pop(0)
    
    def _is_stuck(self) -> bool:
        """检测是否被困（原地打转）"""
        if len(self.position_history) < 8:
            return False
        
        # 检查最近8步的位置变化
        recent_pos = self.position_history[-8:]
        unique_pos = set(recent_pos)
        
        # 如果最近8步只在2个或更少的位置，说明被困
        if len(unique_pos) <= 2:
            self.stuck_counter += 1
            return self.stuck_counter > 3
        
        self.stuck_counter = max(0, self.stuck_counter - 1)
        return False
    
    def _escape_stuck(self, blocked: Dict, self_data: Dict) -> Optional[Action]:
        """脱困策略"""
        # 选择一个新的脱困方向
        if self.stuck_escape_dir is None or random.random() < 0.3:
            # 找一个没被阻挡的方向
            directions = ['forward', 'backward', 'left', 'right']
            available = [d for d in directions if blocked.get(d) == 'no']
            
            if available:
                self.stuck_escape_dir = random.choice(available)
            else:
                # 全被堵住，尝试开火清障
                if self_data['missiles'] > 0:
                    return Action.fire()
                self.stuck_escape_dir = random.choice(['left', 'right'])
        
        # 执行脱困
        if self.stuck_escape_dir in ['left', 'right']:
            self.stuck_counter = 0
            self.stuck_escape_dir = None
            return Action.turn(random.choice(['left', 'right']))
        elif self.stuck_escape_dir == 'backward' and blocked['backward'] == 'no':
            return Action.move('backward')
        elif self.stuck_escape_dir == 'forward' and blocked['forward'] == 'no':
            return Action.move('forward')
        else:
            # 切换脱困策略
            self.stuck_escape_dir = None
            return Action.turn(random.choice(['left', 'right']))
    
    def _check_incoming_missiles(self, incoming: Dict, blocked: Dict, self_data: Dict) -> Optional[Action]:
        """检测并躲避来袭导弹"""
        has_incoming = any(v == 'yes' for v in incoming.values())
        
        if not has_incoming:
            return None
        
        # 优先开启护盾
        if self_data['energy'] > 150 and self_data['shield_status'] == 'off':
            return Action.shields('on')
        
        # 尝试侧向移动躲避
        if incoming['forward'] == 'yes':
            if blocked['left'] == 'no':
                return Action.move('backward') if blocked['backward'] == 'no' else Action.turn('left')
            elif blocked['right'] == 'no':
                return Action.move('backward') if blocked['backward'] == 'no' else Action.turn('right')
            elif blocked['backward'] == 'no':
                return Action.move('backward')
        
        # 侧面来袭
        if incoming['left'] == 'yes' and blocked['right'] == 'no':
            return Action.move('forward') if blocked['forward'] == 'no' else Action.turn('right')
        if incoming['right'] == 'yes' and blocked['left'] == 'no':
            return Action.move('forward') if blocked['forward'] == 'no' else Action.turn('left')
        
        # 背后来袭，向前移动
        if incoming['backward'] == 'yes' and blocked['forward'] == 'no':
            return Action.move('forward')
        
        return None
    
    def _is_safe(self, incoming: Dict) -> bool:
        """检查是否安全（无来袭导弹）"""
        return all(v == 'no' for v in incoming.values())
    
    def _find_enemy_in_visual(self, visual: List) -> Optional[Dict]:
        """
        在视觉传感器数据中查找敌人
        视觉传感器不需要能量，可以在1-2格内识别敌方坦克
        """
        enemies = []
        for tank_data in visual:
            if tank_data.get('color') != self.team:
                enemies.append(tank_data)
        
        if not enemies:
            return None
        
        # 返回最近的敌人
        return min(enemies, key=lambda e: e['distance'])
    
    def _find_enemy_in_radar(self, radar: Dict) -> Optional[Dict]:
        """在雷达数据中查找敌人"""
        enemies = []
        for tank_data in radar.get('tank', []):
            if tank_data.get('color') != self.team:
                enemies.append(tank_data)
        
        if not enemies:
            return None
        
        # 返回最近的敌人
        return min(enemies, key=lambda e: e['distance'])
    
    def _engage_enemy(self, enemy: Dict, blocked: Dict, self_data: Dict) -> Action:
        """交战逻辑 - 核心战斗AI"""
        distance = enemy['distance']
        position = enemy['position']
        
        # 确保雷达开启（如果有能量）
        if self_data['radar_status'] == 'off' and self_data['energy'] > 30:
            return Action.radar('on')
        
        # 敌人在正前方（radar返回'center'，visual返回'forward'）
        if position in ['center', 'forward']:
            # 有弹药就开火！
            if self_data['missiles'] > 0:
                return Action.fire()
            # 没弹药，但敌人很近，尝试撞击
            if distance <= 2:
                if blocked['forward'] == 'no':
                    return Action.move('forward')  # 撞击
        
        # 敌人在左边 - 转向瞄准
        if position == 'left':
            return Action.turn('left')
        
        # 敌人在右边 - 转向瞄准
        if position == 'right':
            return Action.turn('right')
        
        # 敌人在后方 - 转身
        if position == 'backward':
            return Action.turn('left')  # 转身面对敌人
        
        # 敌人距离远，追击
        if distance > 3 and blocked['forward'] == 'no':
            return Action.move('forward')
        
        # 距离太近，后退寻找射击角度
        if distance <= 2 and blocked['backward'] == 'no':
            return Action.move('backward')
        
        return Action.none()
    
    def _check_radar_threat(self, rwave: Dict) -> Optional[str]:
        """检测雷达威胁"""
        for direction, value in rwave.items():
            if value != 'no' and value != self.team:
                return direction
        return None
    
    def _turn_to_direction(self, target_dir: str, current_dir: str) -> Action:
        """转向指定方向"""
        if target_dir == 'forward':
            return Action.move('forward')  # 已经面向目标
        elif target_dir == 'backward':
            return Action.turn('left')  # 转180度
        elif target_dir == 'left':
            return Action.turn('left')
        else:
            return Action.turn('right')
    
    def _pursue_by_smell(self, smell: Dict, sound: str, blocked: Dict, self_data: Dict) -> Action:
        """根据气味追踪敌人 - 即使没有能量也能追踪"""
        distance = smell['distance']
        
        # 有能量时开启雷达
        if self_data['radar_status'] == 'off' and self_data['energy'] > 50:
            return Action.radar('on')
        
        # 结合声音定位（声音传感器也是常开的）
        if sound != 'silent':
            return self._pursue_by_sound(sound, blocked, self_data)
        
        # 气味追踪 - 随机选择策略增加不确定性
        # 敌人在附近，优先向前搜索
        if blocked['forward'] == 'no':
            # 80%概率前进，20%概率转向（增加搜索面积）
            if random.random() < 0.8:
                return Action.move('forward')
            else:
                return Action.turn(random.choice(['left', 'right']))
        
        # 前方被阻挡，随机选择绕路方向
        available_dirs = []
        if blocked['left'] == 'no':
            available_dirs.append('left')
        if blocked['right'] == 'no':
            available_dirs.append('right')
        
        if available_dirs:
            return Action.turn(random.choice(available_dirs))
        elif blocked['backward'] == 'no':
            return Action.move('backward')
        
        return Action.turn(random.choice(['left', 'right']))
    
    def _pursue_by_sound(self, sound: str, blocked: Dict, self_data: Dict) -> Action:
        """根据声音追踪敌人"""
        # 开启雷达
        if self_data['radar_status'] == 'off' and self_data['energy'] > 50:
            return Action.radar('on')
        
        if sound == 'forward':
            if blocked['forward'] == 'no':
                return Action.move('forward')
        elif sound == 'backward':
            return Action.turn('left')  # 转身追击
        elif sound == 'left':
            return Action.turn('left')
        elif sound == 'right':
            return Action.turn('right')
        
        return Action.none()
    
    def _need_recharge(self, self_data: Dict) -> bool:
        """检查是否需要补给"""
        return self_data['health'] < 400 or self_data['energy'] < 200 or self_data['missiles'] < 5
    
    def _seek_recharge(self, radar: Dict, blocked: Dict, self_data: Dict) -> Optional[Action]:
        """寻找补给站和弹药箱"""
        # 已经在维修站
        if self_data['healthrecharger'] == 'yes':
            # 停留补给，直到血量恢复到较高水平
            if self_data['health'] < 900:
                return Action.none()
        
        # 已经在能量站
        if self_data['energyrecharger'] == 'yes':
            # 停留补给，直到能量恢复到较高水平
            if self_data['energy'] < 900:
                return Action.none()
        
        # 在雷达中寻找补给站
        targets = []
        
        # 需要维修
        if self_data['health'] < 600:
            for station in radar.get('health', []):
                targets.append({'target': station, 'priority': 1})
        
        # 需要能量
        if self_data['energy'] < 400:
            for station in radar.get('energy', []):
                targets.append({'target': station, 'priority': 2})
        
        # 需要弹药
        if self_data['missiles'] < 10:
            for ammo in radar.get('ammo', []):
                targets.append({'target': ammo, 'priority': 3})
        
        if targets:
            # 按优先级和距离排序
            targets.sort(key=lambda t: (t['priority'], t['target']['distance']))
            nearest = targets[0]['target']
            
            if nearest['position'] == 'center' and blocked['forward'] == 'no':
                return Action.move('forward')
            elif nearest['position'] == 'left':
                return Action.turn('left')
            elif nearest['position'] == 'right':
                return Action.turn('right')
        
        return None
    
    def _patrol(self, blocked: Dict, self_data: Dict, smell: Dict = None, sound: str = 'silent') -> Action:
        """
        随机巡逻搜索 - 增加随机性避免所有坦克行为一致
        即使没有能量，也要通过随机移动来增加与敌人相遇的概率
        """
        self.patrol_timer += 1
        
        # 有能量时尝试开启雷达
        if self_data['radar_status'] == 'off' and self_data['energy'] > 100:
            return Action.radar('on')
        
        # 【重要】即使没有雷达，也要利用气味传感器追踪敌人
        # 气味传感器是常开的，可以感知最近坦克的距离
        if smell and smell.get('color') and smell['color'] != self_data['my_color']:
            # 敌人在附近，积极搜索
            enemy_distance = smell.get('distance', 999)
            
            # 敌人很近时（<5格），更积极地移动
            if enemy_distance <= 5:
                if sound != 'silent':
                    # 有声音，朝声音方向移动
                    if sound == 'forward' and blocked['forward'] == 'no':
                        return Action.move('forward')
                    elif sound == 'left':
                        return Action.turn('left')
                    elif sound == 'right':
                        return Action.turn('right')
                    elif sound == 'backward':
                        return Action.turn(random.choice(['left', 'right']))
                
                # 没有声音，随机搜索
                if blocked['forward'] == 'no' and random.random() < 0.7:
                    return Action.move('forward')
                return Action.turn(random.choice(['left', 'right']))
        
        # 随机行为模式 - 打破规律性
        rand = random.random()
        
        # 40% 概率：尝试前进
        if rand < 0.4:
            if blocked['forward'] == 'no':
                return Action.move('forward')
            # 前方被堵，随机转向
            return Action.turn(random.choice(['left', 'right']))
        
        # 30% 概率：随机转向（增加搜索覆盖面）
        elif rand < 0.7:
            return Action.turn(random.choice(['left', 'right']))
        
        # 20% 概率：如果可以，后退一步（改变位置）
        elif rand < 0.9:
            if blocked['backward'] == 'no':
                return Action.move('backward')
            return Action.turn(random.choice(['left', 'right']))
        
        # 10% 概率：原地等待（让其他坦克来找自己）
        else:
            return Action.none()


# 使用 TacticalAI 作为默认 AI
SimpleAI = TacticalAI


class AggressiveAI:
    """
    激进AI策略
    全面进攻，高风险高回报
    """
    
    def __init__(self, tank_id: int, team: str):
        self.tank_id = tank_id
        self.team = team
        self.attack_timer = 0
        
    def decide(self, sensor_data: Dict, tank: 'Tank') -> Action:
        """激进策略 - 主动进攻"""
        blocked = sensor_data['blocked']
        incoming = sensor_data['incoming']
        radar = sensor_data['radar']
        smell = sensor_data['smell']
        visual = sensor_data.get('visual', [])  # 近距离视觉
        self_data = sensor_data['self']
        
        self.attack_timer += 1
        
        # 来袭导弹时开护盾并反击
        if any(v == 'yes' for v in incoming.values()):
            if self_data['shield_status'] == 'off' and self_data['energy'] > 100:
                return Action.shields('on')
            # 有弹药直接反击
            if self_data['missiles'] > 0:
                return Action.fire()
        
        # 【重要】近距离视觉发现敌人 - 不需要雷达也能攻击！
        for tank_data in visual:
            if tank_data.get('color') != self.team:
                position = tank_data['position']
                distance = tank_data.get('distance', 2)
                
                if position in ['forward', 'center']:
                    if self_data['missiles'] > 0:
                        return Action.fire()
                    # 没弹药则冲撞
                    elif distance <= 2 and blocked['forward'] == 'no':
                        return Action.move('forward')
                elif position == 'left':
                    return Action.turn('left')
                elif position == 'right':
                    return Action.turn('right')
                elif position == 'backward':
                    return Action.turn('left')  # 转身面对
        
        # 有能量时开启雷达
        if self_data['radar_status'] == 'off' and self_data['energy'] > 50:
            return Action.radar('on')
        
        # 最大雷达功率
        if self_data['radar_setting'] < 10 and self_data['energy'] > 100:
            return Action.radar_power(10)
        
        # 雷达发现敌人 - 立即攻击
        for tank_data in radar.get('tank', []):
            if tank_data.get('color') != self.team:
                position = tank_data['position']
                
                if position == 'center' and self_data['missiles'] > 0:
                    return Action.fire()
                elif position == 'left':
                    return Action.turn('left')
                elif position == 'right':
                    return Action.turn('right')
                
                if blocked['forward'] == 'no':
                    return Action.move('forward')
        
        # 气味追踪 - 即使没有雷达也能追踪
        if smell['color'] and smell['color'] != self.team:
            enemy_dist = smell.get('distance', 999)
            # 敌人在附近，随机搜索
            if enemy_dist <= 7:
                if blocked['forward'] == 'no' and random.random() < 0.6:
                    return Action.move('forward')
                return Action.turn(random.choice(['left', 'right']))
        
        # 随机主动搜索 - 打破规律性
        rand = random.random()
        if rand < 0.5:
            if blocked['forward'] == 'no':
                return Action.move('forward')
            return Action.turn(random.choice(['left', 'right']))
        elif rand < 0.8:
            return Action.turn(random.choice(['left', 'right']))
        else:
            if blocked['backward'] == 'no':
                return Action.move('backward')
            return Action.turn(random.choice(['left', 'right']))


class DefensiveAI:
    """
    防御AI策略
    注重生存，谨慎作战
    """
    
    def __init__(self, tank_id: int, team: str):
        self.tank_id = tank_id
        self.team = team
        
    def decide(self, sensor_data: Dict, tank: 'Tank') -> Action:
        """防御策略"""
        blocked = sensor_data['blocked']
        incoming = sensor_data['incoming']
        radar = sensor_data['radar']
        visual = sensor_data.get('visual', [])  # 近距离视觉
        self_data = sensor_data['self']
        
        # 最高优先级：躲避导弹
        if any(v == 'yes' for v in incoming.values()):
            if self_data['shield_status'] == 'off' and self_data['energy'] > 50:
                return Action.shields('on')
            if blocked['backward'] == 'no':
                return Action.move('backward')
            if blocked['left'] == 'no':
                return Action.turn('left')
            if blocked['right'] == 'no':
                return Action.turn('right')
        
        # 保持护盾（如果能量充足）
        if self_data['energy'] > 500 and self_data['shield_status'] == 'off':
            return Action.shields('on')
        
        # 【重要】近距离视觉发现敌人 - 即使没雷达也能反击！
        for tank_data in visual:
            if tank_data.get('color') != self.team:
                distance = tank_data.get('distance', 2)
                position = tank_data['position']
                
                # 防御策略：近距离也要反击
                if position in ['forward', 'center'] and self_data['missiles'] > 0:
                    return Action.fire()
                elif position == 'left':
                    return Action.turn('left')
                elif position == 'right':
                    return Action.turn('right')
                elif position == 'backward':
                    return Action.turn('left')
        
        # 低血量时寻找维修站
        if self_data['health'] < 600:
            for health_station in radar.get('health', []):
                if health_station['position'] == 'center' and blocked['forward'] == 'no':
                    return Action.move('forward')
                elif health_station['position'] == 'left':
                    return Action.turn('left')
                elif health_station['position'] == 'right':
                    return Action.turn('right')
        
        # 雷达发现敌人 - 只有在安全距离才攻击
        for tank_data in radar.get('tank', []):
            if tank_data.get('color') != self.team:
                distance = tank_data['distance']
                position = tank_data['position']
                
                if position == 'center' and distance >= 4 and self_data['missiles'] > 0:
                    return Action.fire()
                elif position == 'left':
                    return Action.turn('left')
                elif position == 'right':
                    return Action.turn('right')
        
        # 随机保守巡逻 - 增加随机性
        rand = random.random()
        if rand < 0.5:
            if blocked['forward'] == 'no':
                return Action.move('forward')
            return Action.turn(random.choice(['left', 'right']))
        elif rand < 0.85:
            return Action.turn(random.choice(['left', 'right']))
        else:
            # 偶尔原地等待
            return Action.none()
