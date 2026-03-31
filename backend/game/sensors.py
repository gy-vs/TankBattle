"""
传感器系统
"""

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from .tank import Direction
from .config import GameConfig
from .map import MapElement

if TYPE_CHECKING:
    from .tank import Tank
    from .map import GameMap
    from .missile import Missile


class BlockedSensor:
    """
    障碍传感器
    感知坦克前/后/左/右的网格是否被阻塞
    无法区分障碍物和坦克
    """
    
    @staticmethod
    def sense(tank: 'Tank', game_map: 'GameMap', all_tanks: List['Tank']) -> Dict[str, str]:
        """
        获取传感器数据
        返回: {forward, backward, left, right} 各方向是否被阻挡
        """
        result = {
            'forward': 'no',
            'backward': 'no',
            'left': 'no',
            'right': 'no'
        }
        
        # 获取各方向的坐标增量
        directions = {
            'forward': tank.direction.get_delta(),
            'backward': (-tank.direction.get_delta()[0], -tank.direction.get_delta()[1]),
            'left': tank.direction.turn_left().get_delta(),
            'right': tank.direction.turn_right().get_delta()
        }
        
        for dir_name, (dx, dy) in directions.items():
            check_x = tank.x + dx
            check_y = tank.y + dy
            
            # 检查是否超出边界或是障碍物
            if game_map.is_blocked(check_x, check_y):
                result[dir_name] = 'yes'
                continue
                
            # 检查是否有其他坦克
            for other_tank in all_tanks:
                if other_tank.id != tank.id and other_tank.is_alive():
                    if other_tank.x == check_x and other_tank.y == check_y:
                        result[dir_name] = 'yes'
                        break
                        
        return result


class IncomingSensor:
    """
    导弹传感器
    感知是否有来袭炮弹
    """
    
    @staticmethod
    def sense(tank: 'Tank', missiles: List['Missile'], game_map: 'GameMap', 
              all_tanks: List['Tank']) -> Dict[str, str]:
        """
        获取传感器数据
        返回: {forward, backward, left, right} 各方向是否有来袭导弹
        """
        result = {
            'forward': 'no',
            'backward': 'no',
            'left': 'no',
            'right': 'no'
        }
        
        for missile in missiles:
            if not missile.is_active():
                continue
                
            # 检查导弹是否朝向坦克方向
            # 计算导弹到坦克的相对位置
            dx = tank.x - missile.x
            dy = tank.y - missile.y
            
            # 导弹必须朝向坦克才能被感知
            missile_dx, missile_dy = missile.direction.get_delta()
            
            # 检查导弹是否在坦克的某个方向上，且正在向坦克移动
            is_incoming = False
            incoming_direction = None
            
            # 导弹在坦克前方
            if missile_dx != 0 and (dx * missile_dx > 0) and dy == 0:
                is_incoming = True
            elif missile_dy != 0 and (dy * missile_dy > 0) and dx == 0:
                is_incoming = True
                
            if not is_incoming:
                continue
                
            # 计算导弹距离发射点的距离，如果<=2则在盲区内
            distance_from_launch = missile.get_distance_from_launch()
            if distance_from_launch <= GameConfig.MISSILE_BLIND_RANGE:
                continue
                
            # 检查导弹和坦克之间是否有障碍物或其他坦克阻挡
            blocked = False
            check_x, check_y = missile.x, missile.y
            
            while (check_x, check_y) != (tank.x, tank.y):
                check_x += missile_dx
                check_y += missile_dy
                
                if check_x == tank.x and check_y == tank.y:
                    break
                    
                # 检查障碍物
                if game_map.is_obstacle(check_x, check_y):
                    blocked = True
                    break
                    
                # 检查其他坦克
                for other_tank in all_tanks:
                    if other_tank.id != tank.id and other_tank.is_alive():
                        if other_tank.x == check_x and other_tank.y == check_y:
                            blocked = True
                            break
                            
                if blocked:
                    break
                    
            if blocked:
                continue
                
            # 确定导弹来自哪个方向（相对于坦克朝向）
            relative_dir = tank.get_relative_direction(missile.x, missile.y)
            result[relative_dir] = 'yes'
            
        return result


class RadarSensor:
    """
    雷达传感器
    探测坦克前方扇形区域内的物体
    """
    
    @staticmethod
    def sense(tank: 'Tank', game_map: 'GameMap', all_tanks: List['Tank']) -> Dict:
        """
        获取雷达数据
        返回探测到的各类物体
        """
        result = {
            'energy': [],
            'health': [],
            'ammo': [],
            'tree': [],
            'stone': [],
            'open': [],
            'tank': []
        }
        
        if not tank.radar_on:
            return result
            
        # 雷达探测范围：前方 radar_setting 格，左中右3列
        dx, dy = tank.direction.get_delta()
        
        # 计算左右偏移
        if dx != 0:  # 朝东或西
            offsets = {'left': (0, -1), 'center': (0, 0), 'right': (0, 1)}
        else:  # 朝北或南
            offsets = {'left': (-1, 0), 'center': (0, 0), 'right': (1, 0)}
            
        # 如果朝南或西，需要翻转左右
        if tank.direction in [Direction.SOUTH, Direction.WEST]:
            offsets['left'], offsets['right'] = offsets['right'], offsets['left']
            
        # 记录各方向的有效探测距离
        effective_distance = {'left': 0, 'center': 0, 'right': 0}
        
        # 逐格扫描
        for position, (off_x, off_y) in offsets.items():
            for dist in range(1, tank.radar_setting + 1):
                scan_x = tank.x + dx * dist + off_x
                scan_y = tank.y + dy * dist + off_y
                
                # 检查是否超出边界
                if not game_map.is_valid_position(scan_x, scan_y):
                    break
                    
                element = game_map.get_element(scan_x, scan_y)
                
                # 更新有效探测距离
                effective_distance[position] = dist
                
                # 检查是否是障碍物（会阻挡雷达）
                if element == MapElement.TREE:
                    result['tree'].append({
                        'distance': dist,
                        'position': position
                    })
                    break  # 被障碍物阻挡，停止该方向扫描
                    
                elif element == MapElement.STONE:
                    result['stone'].append({
                        'distance': dist,
                        'position': position
                    })
                    break  # 被障碍物阻挡
                    
                elif element == MapElement.HEALTH:
                    # 检查是否有坦克在维修站（如果有则只显示维修站）
                    tank_at_station = False
                    for other_tank in all_tanks:
                        if other_tank.id != tank.id and other_tank.is_alive():
                            if other_tank.x == scan_x and other_tank.y == scan_y:
                                tank_at_station = True
                                break
                    result['health'].append({
                        'distance': dist,
                        'position': position
                    })
                    # 坦克在补给站时只显示补给站，不显示坦克
                    
                elif element == MapElement.ENERGY:
                    result['energy'].append({
                        'distance': dist,
                        'position': position
                    })
                    
                elif element == MapElement.AMMO or game_map.is_ammo_box(scan_x, scan_y):
                    result['ammo'].append({
                        'distance': dist,
                        'position': position
                    })
                    
                else:
                    # 检查是否有坦克
                    tank_found = False
                    for other_tank in all_tanks:
                        if other_tank.id != tank.id and other_tank.is_alive():
                            if other_tank.x == scan_x and other_tank.y == scan_y:
                                # 检查坦克是否在补给站
                                if not (game_map.is_health_station(scan_x, scan_y) or 
                                        game_map.is_energy_station(scan_x, scan_y)):
                                    result['tank'].append({
                                        'distance': dist,
                                        'position': position,
                                        'color': other_tank.team
                                    })
                                tank_found = True
                                break
                                
                    if not tank_found:
                        result['open'].append({
                            'distance': dist,
                            'position': position
                        })
                        
        # 更新坦克的雷达实际探测距离
        tank.radar_distance = effective_distance
        
        return result


class RwaveSensor:
    """
    雷达波传感器
    探测是否被其他坦克的雷达扫描
    """
    
    @staticmethod
    def sense(tank: 'Tank', all_tanks: List['Tank']) -> Dict[str, str]:
        """
        获取传感器数据
        返回: {forward, backward, left, right} 各方向是否被雷达探测
        """
        result = {
            'forward': 'no',
            'backward': 'no',
            'left': 'no',
            'right': 'no'
        }
        
        for other_tank in all_tanks:
            if other_tank.id == tank.id or not other_tank.is_alive():
                continue
                
            if not other_tank.radar_on:
                continue
                
            # 检查该坦克的雷达是否能扫描到自己
            # 计算相对位置
            dx = tank.x - other_tank.x
            dy = tank.y - other_tank.y
            
            # 检查是否在雷达扫描范围内
            other_dx, other_dy = other_tank.direction.get_delta()
            
            # 计算在雷达方向上的距离
            if other_dx != 0:
                forward_dist = dx * other_dx
                side_dist = abs(dy)
            else:
                forward_dist = dy * other_dy
                side_dist = abs(dx)
                
            # 检查是否在雷达范围内（前方 radar_setting 格，左右1格）
            if forward_dist > 0 and forward_dist <= other_tank.radar_setting and side_dist <= 1:
                # 确定探测来自哪个方向
                relative_dir = tank.get_relative_direction(other_tank.x, other_tank.y)
                result[relative_dir] = other_tank.team
                
        return result


class SmellSensor:
    """
    气味传感器
    感知最近坦克的曼哈顿距离和阵营
    """
    
    @staticmethod
    def sense(tank: 'Tank', all_tanks: List['Tank']) -> Dict:
        """
        获取传感器数据
        返回: {color, distance} 最近坦克的信息
        """
        result = {
            'color': None,
            'distance': None
        }
        
        min_distance = float('inf')
        nearest_tanks = []
        
        for other_tank in all_tanks:
            if other_tank.id == tank.id or not other_tank.is_alive():
                continue
                
            # 计算曼哈顿距离
            distance = abs(tank.x - other_tank.x) + abs(tank.y - other_tank.y)
            
            if distance > GameConfig.SMELL_MAX_DISTANCE:
                continue
                
            if distance < min_distance:
                min_distance = distance
                nearest_tanks = [other_tank]
            elif distance == min_distance:
                nearest_tanks.append(other_tank)
                
        if nearest_tanks:
            # 随机选一辆
            import random
            chosen = random.choice(nearest_tanks)
            result['color'] = chosen.team
            result['distance'] = min_distance
            
        return result


class VisualSensor:
    """
    近距离视觉传感器
    感知坦克周围1-2格内的敌方坦克
    - 常开，不消耗能量
    - 只能探测距离1-2的位置
    - 可以区分敌友
    这模拟了人类的基本视觉能力，即使没有雷达也能看到近距离的敌人
    """
    
    VISUAL_RANGE = 2  # 视觉感知范围
    
    @staticmethod
    def sense(tank: 'Tank', game_map: 'GameMap', all_tanks: List['Tank']) -> List[Dict]:
        """
        获取视觉数据
        返回: 周围可见敌人的列表 [{distance, position, color}, ...]
        position: forward/backward/left/right
        """
        result = []
        
        # 获取各方向的坐标增量
        dx, dy = tank.direction.get_delta()
        
        # 定义4个相对方向及其偏移
        direction_offsets = {
            'forward': (dx, dy),
            'backward': (-dx, -dy),
            'left': tank.direction.turn_left().get_delta(),
            'right': tank.direction.turn_right().get_delta()
        }
        
        for dir_name, (off_x, off_y) in direction_offsets.items():
            # 检查1-2格距离
            for dist in range(1, VisualSensor.VISUAL_RANGE + 1):
                check_x = tank.x + off_x * dist
                check_y = tank.y + off_y * dist
                
                # 检查边界
                if not game_map.is_valid_position(check_x, check_y):
                    break
                
                # 检查是否有障碍物阻挡视线（距离>1时才检查）
                if dist > 1:
                    prev_x = tank.x + off_x * (dist - 1)
                    prev_y = tank.y + off_y * (dist - 1)
                    if game_map.is_obstacle(prev_x, prev_y):
                        break  # 视线被阻挡
                
                # 检查当前位置是否有坦克
                for other_tank in all_tanks:
                    if other_tank.id != tank.id and other_tank.is_alive():
                        if other_tank.x == check_x and other_tank.y == check_y:
                            result.append({
                                'distance': dist,
                                'position': dir_name,
                                'color': other_tank.team
                            })
                            break
                
                # 如果当前格是障碍物，后面的也看不到了
                if game_map.is_obstacle(check_x, check_y):
                    break
        
        return result


class SoundSensor:
    """
    声音传感器
    感知最近的上一步移动的坦克
    使用 BFS 算法计算真正的最短路径方向
    """
    
    @staticmethod
    def _bfs_shortest_path_direction(tank: 'Tank', target_x: int, target_y: int, 
                                      game_map: 'GameMap', all_tanks: List['Tank']) -> Optional[str]:
        """
        使用 BFS 算法计算从坦克位置到目标位置的最短路径
        返回最短路径的第一步方向（相对于坦克朝向）
        当有多个等距方向时，随机选择一个返回
        """
        from collections import deque
        import random
        
        if tank.x == target_x and tank.y == target_y:
            return None
            
        # BFS 队列: (x, y, first_direction, distance)
        # first_direction 记录从起点出发的第一步的绝对方向
        # distance 记录从起点到当前位置的距离
        queue = deque()
        # visited 记录每个位置的最短距离
        visited = {(tank.x, tank.y): 0}
        
        # 四个方向：北、东、南、西
        directions = [
            (Direction.NORTH, 0, -1),
            (Direction.EAST, 1, 0),
            (Direction.SOUTH, 0, 1),
            (Direction.WEST, -1, 0)
        ]
        
        # 收集所有能到达目标的最短路径的第一步方向
        shortest_distance = float('inf')
        valid_first_directions = []
        
        # 初始化：从坦克位置出发的四个方向
        for abs_dir, dx, dy in directions:
            next_x = tank.x + dx
            next_y = tank.y + dy
            
            if not game_map.is_valid_position(next_x, next_y):
                continue
            if game_map.is_blocked(next_x, next_y):
                continue
            
            # 检查是否有其他坦克阻挡（目标坦克除外）
            blocked_by_tank = False
            for other in all_tanks:
                if other.id != tank.id and other.is_alive():
                    if other.x == next_x and other.y == next_y:
                        if not (next_x == target_x and next_y == target_y):
                            blocked_by_tank = True
                            break
            
            if blocked_by_tank:
                continue
                
            if (next_x, next_y) not in visited:
                visited[(next_x, next_y)] = 1
                
                # 如果直接到达目标（距离为1）
                if next_x == target_x and next_y == target_y:
                    if 1 < shortest_distance:
                        shortest_distance = 1
                        valid_first_directions = [abs_dir]
                    elif 1 == shortest_distance:
                        valid_first_directions.append(abs_dir)
                else:
                    queue.append((next_x, next_y, abs_dir, 1))
        
        # 如果已经找到距离为1的路径，从中随机选择
        if shortest_distance == 1:
            chosen_dir = random.choice(valid_first_directions)
            return SoundSensor._abs_to_relative(chosen_dir, tank.direction)
        
        # BFS 搜索
        while queue:
            curr_x, curr_y, first_dir, curr_dist = queue.popleft()
            
            # 如果当前距离已经超过已知最短距离，跳过
            if curr_dist >= shortest_distance:
                continue
            
            for abs_dir, dx, dy in directions:
                next_x = curr_x + dx
                next_y = curr_y + dy
                next_dist = curr_dist + 1
                
                if not game_map.is_valid_position(next_x, next_y):
                    continue
                if game_map.is_blocked(next_x, next_y):
                    continue
                    
                # 检查是否有其他坦克阻挡（目标坦克除外）
                blocked_by_tank = False
                for other in all_tanks:
                    if other.id != tank.id and other.is_alive():
                        if other.x == next_x and other.y == next_y:
                            if not (next_x == target_x and next_y == target_y):
                                blocked_by_tank = True
                                break
                
                if blocked_by_tank:
                    continue
                
                # 找到目标
                if next_x == target_x and next_y == target_y:
                    if next_dist < shortest_distance:
                        shortest_distance = next_dist
                        valid_first_directions = [first_dir]
                    elif next_dist == shortest_distance:
                        # 避免重复添加相同的第一步方向
                        if first_dir not in valid_first_directions:
                            valid_first_directions.append(first_dir)
                    continue  # 继续搜索其他等距路径
                
                # 只有当新路径不比已访问过的路径更长时才继续搜索
                if (next_x, next_y) not in visited or visited[(next_x, next_y)] >= next_dist:
                    visited[(next_x, next_y)] = next_dist
                    queue.append((next_x, next_y, first_dir, next_dist))
        
        # 从所有等距的第一步方向中随机选择一个
        if valid_first_directions:
            chosen_dir = random.choice(valid_first_directions)
            return SoundSensor._abs_to_relative(chosen_dir, tank.direction)
        
        # 无法到达，返回直线方向
        return SoundSensor._direct_direction(tank, target_x, target_y)
    
    @staticmethod
    def _abs_to_relative(abs_dir: Direction, tank_dir: Direction) -> str:
        """将绝对方向转换为相对方向"""
        if abs_dir == tank_dir:
            return 'forward'
        elif abs_dir == tank_dir.get_opposite():
            return 'backward'
        elif abs_dir == tank_dir.turn_left():
            return 'left'
        else:
            return 'right'
    
    @staticmethod
    def _direct_direction(tank: 'Tank', target_x: int, target_y: int) -> str:
        """计算直线方向（用于无法通过 BFS 到达的情况）"""
        dx = target_x - tank.x
        dy = target_y - tank.y
        
        if abs(dx) >= abs(dy):
            abs_dir = Direction.EAST if dx > 0 else Direction.WEST
        else:
            abs_dir = Direction.SOUTH if dy > 0 else Direction.NORTH
            
        return SoundSensor._abs_to_relative(abs_dir, tank.direction)
    
    @staticmethod
    def sense(tank: 'Tank', all_tanks: List['Tank'], game_map: 'GameMap') -> str:
        """
        获取传感器数据
        返回: silent/forward/backward/left/right
        使用 BFS 算法计算最短路径方向
        """
        import random
        
        min_distance = float('inf')
        nearest_tanks = []
        
        for other_tank in all_tanks:
            if other_tank.id == tank.id or not other_tank.is_alive():
                continue
                
            if not other_tank.moved_last_step:
                continue
                
            # 计算曼哈顿距离
            distance = abs(tank.x - other_tank.x) + abs(tank.y - other_tank.y)
            
            if distance > GameConfig.SOUND_MAX_DISTANCE:
                continue
                
            if distance < min_distance:
                min_distance = distance
                nearest_tanks = [other_tank]
            elif distance == min_distance:
                nearest_tanks.append(other_tank)
                
        if not nearest_tanks:
            return 'silent'
            
        # 随机选一辆
        chosen = random.choice(nearest_tanks)
        
        # 使用 BFS 算法计算最短路径方向
        direction = SoundSensor._bfs_shortest_path_direction(
            tank, chosen.x, chosen.y, game_map, all_tanks
        )
        
        return direction if direction else 'silent'


class CommunicationSensor:
    """
    内部通信传感器
    同队坦克之间可以共享信息
    - 队友的位置、方向、状态
    - 实现 Prompt 1.1 节提到的"双方坦克可进行内部通信"功能
    """
    
    @staticmethod
    def sense(tank: 'Tank', all_tanks: List['Tank']) -> List[Dict]:
        """
        获取同队友军坦克的通信数据
        返回: [{id, x, y, direction, health, energy, missiles, alive, radar_on, shield_on, distance}, ...]
        """
        teammates = []
        
        for other_tank in all_tanks:
            # 只获取同队且非自己的坦克信息
            if other_tank.id == tank.id or other_tank.team != tank.team:
                continue
                
            # 计算与队友的曼哈顿距离
            distance = abs(tank.x - other_tank.x) + abs(tank.y - other_tank.y)
            
            # 计算队友相对于自己的方向
            relative_dir = tank.get_relative_direction(other_tank.x, other_tank.y)
            
            teammates.append({
                'id': other_tank.id,
                'x': other_tank.x,
                'y': other_tank.y,
                'direction': other_tank.direction.value,
                'health': other_tank.health,
                'energy': other_tank.energy,
                'missiles': other_tank.missiles,
                'alive': other_tank.is_alive(),
                'radar_on': other_tank.radar_on,
                'shield_on': other_tank.shield_on,
                'distance': distance,
                'relative_direction': relative_dir,
                'radar_setting': other_tank.radar_setting
            })
            
        return teammates
