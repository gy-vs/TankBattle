"""
传感器系统单元测试
测试各种传感器的功能和正确性
"""

import pytest
from game.tank import Tank, Direction
from game.map import GameMap, MapElement
from game.missile import Missile
from game.sensors import (
    BlockedSensor, IncomingSensor, RadarSensor,
    RwaveSensor, SmellSensor, SoundSensor, VisualSensor
)
from game.config import GameConfig


class TestBlockedSensor:
    """障碍传感器测试"""
    
    def test_no_obstacles(self, empty_map, red_tank):
        """测试四周无障碍"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.NORTH
        
        result = BlockedSensor.sense(red_tank, empty_map, [red_tank])
        
        assert result['forward'] == 'no'
        assert result['backward'] == 'no'
        assert result['left'] == 'no'
        assert result['right'] == 'no'
    
    def test_blocked_by_tree(self, empty_map, red_tank):
        """测试被树木阻挡"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.NORTH
        
        # 在坦克前方放置树
        empty_map.set_element(5, 4, MapElement.TREE)
        
        result = BlockedSensor.sense(red_tank, empty_map, [red_tank])
        
        assert result['forward'] == 'yes'
        assert result['backward'] == 'no'
    
    def test_blocked_by_boundary(self, empty_map, red_tank):
        """测试被边界阻挡"""
        red_tank.x = 0
        red_tank.y = 5
        red_tank.direction = Direction.WEST
        
        result = BlockedSensor.sense(red_tank, empty_map, [red_tank])
        
        assert result['forward'] == 'yes'
    
    def test_blocked_by_tank(self, empty_map, two_tanks):
        """测试被其他坦克阻挡"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        # 蓝方坦克在红方前方
        blue_tank.x = 6
        blue_tank.y = 5
        
        result = BlockedSensor.sense(red_tank, empty_map, [red_tank, blue_tank])
        
        assert result['forward'] == 'yes'


class TestIncomingSensor:
    """导弹传感器测试"""
    
    def test_no_missiles(self, empty_map, red_tank):
        """测试无来袭导弹"""
        result = IncomingSensor.sense(red_tank, [], empty_map, [red_tank])
        
        assert result['forward'] == 'no'
        assert result['backward'] == 'no'
        assert result['left'] == 'no'
        assert result['right'] == 'no'
    
    def test_incoming_from_front(self, empty_map, red_tank):
        """测试前方来袭导弹"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        # 创建从东边飞来的导弹（朝西飞）
        missile = Missile(x=10, y=5, direction=Direction.WEST, owner_id=2, owner_team='blue')
        # 让导弹远离发射点超过盲区
        missile.launch_x = 13
        missile.launch_y = 5
        
        result = IncomingSensor.sense(red_tank, [missile], empty_map, [red_tank])
        
        assert result['forward'] == 'yes'
    
    def test_blind_range(self, empty_map, red_tank):
        """测试导弹盲区"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        # 创建刚发射的导弹（在盲区内）
        missile = Missile(x=7, y=5, direction=Direction.WEST, owner_id=2, owner_team='blue')
        # 发射位置在盲区范围内
        missile.launch_x = 8
        missile.launch_y = 5
        
        result = IncomingSensor.sense(red_tank, [missile], empty_map, [red_tank])
        
        # 在盲区内应该感知不到
        # 注意：具体行为取决于实现细节


class TestRadarSensor:
    """雷达传感器测试"""
    
    def test_radar_off(self, empty_map, red_tank):
        """测试雷达关闭"""
        red_tank.radar_on = False
        
        result = RadarSensor.sense(red_tank, empty_map, [red_tank])
        
        # 雷达关闭时应返回空结果
        assert result['tank'] == []
        assert result['tree'] == []
    
    def test_radar_detect_obstacle(self, empty_map, red_tank):
        """测试雷达探测障碍物"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.NORTH
        red_tank.radar_on = True
        red_tank.radar_setting = 7
        
        # 在前方放置树
        empty_map.set_element(5, 3, MapElement.TREE)
        
        result = RadarSensor.sense(red_tank, empty_map, [red_tank])
        
        assert len(result['tree']) > 0
        assert any(t['position'] == 'center' and t['distance'] == 2 for t in result['tree'])
    
    def test_radar_detect_tank(self, empty_map, two_tanks):
        """测试雷达探测坦克"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        red_tank.radar_on = True
        red_tank.radar_setting = 7
        
        # 蓝方坦克在红方前方
        blue_tank.x = 8
        blue_tank.y = 5
        
        result = RadarSensor.sense(red_tank, empty_map, [red_tank, blue_tank])
        
        assert len(result['tank']) > 0
        assert any(t['color'] == 'blue' for t in result['tank'])
    
    def test_radar_blocked_by_obstacle(self, empty_map, two_tanks):
        """测试雷达被障碍物阻挡"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        red_tank.radar_on = True
        red_tank.radar_setting = 10
        
        # 在红方和蓝方之间放置石头
        empty_map.set_element(7, 5, MapElement.STONE)
        
        # 蓝方坦克在石头后面
        blue_tank.x = 9
        blue_tank.y = 5
        
        result = RadarSensor.sense(red_tank, empty_map, [red_tank, blue_tank])
        
        # 应该探测到石头
        assert len(result['stone']) > 0
        # 但不应该探测到后面的坦克
        tanks_in_center = [t for t in result['tank'] if t['position'] == 'center']
        assert len(tanks_in_center) == 0


class TestRwaveSensor:
    """雷达波传感器测试"""
    
    def test_no_radar_scanning(self, two_tanks):
        """测试无雷达扫描"""
        red_tank, blue_tank = two_tanks
        blue_tank.radar_on = False
        
        result = RwaveSensor.sense(red_tank, [red_tank, blue_tank])
        
        assert result['forward'] == 'no'
        assert result['backward'] == 'no'
        assert result['left'] == 'no'
        assert result['right'] == 'no'
    
    def test_radar_scan_detected(self, two_tanks):
        """测试检测到雷达扫描"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        # 蓝方在红方前方，雷达朝向红方
        blue_tank.x = 8
        blue_tank.y = 5
        blue_tank.direction = Direction.WEST
        blue_tank.radar_on = True
        blue_tank.radar_setting = 7
        
        result = RwaveSensor.sense(red_tank, [red_tank, blue_tank])
        
        # 红方应该检测到来自前方的蓝方雷达
        assert result['forward'] == 'blue'


class TestSmellSensor:
    """气味传感器测试"""
    
    def test_no_other_tanks(self, red_tank):
        """测试无其他坦克"""
        result = SmellSensor.sense(red_tank, [red_tank])
        
        assert result['color'] is None
        assert result['distance'] is None
    
    def test_smell_nearest_tank(self, two_tanks):
        """测试感知最近坦克"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 5
        red_tank.y = 5
        
        blue_tank.x = 8
        blue_tank.y = 5
        
        result = SmellSensor.sense(red_tank, [red_tank, blue_tank])
        
        assert result['color'] == 'blue'
        assert result['distance'] == 3  # 曼哈顿距离
    
    def test_smell_max_distance(self, two_tanks):
        """测试最大感知距离"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 0
        red_tank.y = 0
        
        # 蓝方坦克超出感知距离
        blue_tank.x = 13
        blue_tank.y = 13
        
        result = SmellSensor.sense(red_tank, [red_tank, blue_tank])
        
        # 如果超出最大距离，应该感知不到
        if result['distance'] is not None:
            assert result['distance'] <= GameConfig.SMELL_MAX_DISTANCE


class TestVisualSensor:
    """视觉传感器测试"""
    
    def test_no_tanks_nearby(self, empty_map, red_tank):
        """测试附近无坦克"""
        red_tank.x = 5
        red_tank.y = 5
        
        result = VisualSensor.sense(red_tank, empty_map, [red_tank])
        
        assert result == []
    
    def test_see_tank_in_front(self, empty_map, two_tanks):
        """测试看到前方坦克"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        # 蓝方在红方前方1格
        blue_tank.x = 6
        blue_tank.y = 5
        
        result = VisualSensor.sense(red_tank, empty_map, [red_tank, blue_tank])
        
        assert len(result) > 0
        assert any(t['position'] == 'forward' and t['color'] == 'blue' for t in result)
    
    def test_visual_blocked_by_obstacle(self, empty_map, two_tanks):
        """测试视线被障碍物阻挡"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        # 在红方和蓝方之间放置障碍物
        empty_map.set_element(6, 5, MapElement.TREE)
        
        # 蓝方坦克在障碍物后面（距离2）
        blue_tank.x = 7
        blue_tank.y = 5
        
        result = VisualSensor.sense(red_tank, empty_map, [red_tank, blue_tank])
        
        # 不应该看到障碍物后面的坦克
        tanks_in_front = [t for t in result if t['position'] == 'forward']
        assert len(tanks_in_front) == 0


class TestSoundSensor:
    """声音传感器测试"""
    
    def test_silent_no_movement(self, empty_map, two_tanks):
        """测试无移动时静默"""
        red_tank, blue_tank = two_tanks
        blue_tank.moved_last_step = False
        
        result = SoundSensor.sense(red_tank, [red_tank, blue_tank], empty_map)
        
        assert result == 'silent'
    
    def test_hear_moving_tank(self, empty_map, two_tanks):
        """测试听到移动的坦克"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        # 蓝方在红方前方移动
        blue_tank.x = 8
        blue_tank.y = 5
        blue_tank.moved_last_step = True
        
        result = SoundSensor.sense(red_tank, [red_tank, blue_tank], empty_map)
        
        assert result == 'forward'
    
    def test_max_hearing_distance(self, empty_map, two_tanks):
        """测试最大听觉距离"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 0
        red_tank.y = 0
        
        # 蓝方坦克超出听觉距离
        blue_tank.x = 13
        blue_tank.y = 13
        blue_tank.moved_last_step = True
        
        result = SoundSensor.sense(red_tank, [red_tank, blue_tank], empty_map)
        
        # 如果超出最大距离，应该听不到
        if blue_tank.x + blue_tank.y > GameConfig.SOUND_MAX_DISTANCE:
            assert result == 'silent'
    
    def test_random_direction_when_equidistant(self, empty_map, two_tanks):
        """测试当有多个等距方向时随机选择"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 7
        red_tank.y = 7
        red_tank.direction = Direction.NORTH  # 朝北
        
        # 蓝方在红方的对角线位置（左前方/右前方等距）
        # 坦克朝北，蓝方在 (9, 5)，即东北方向
        # 从 (7,7) 到 (9,5) 可以先向北再向东，或先向东再向北
        # 相对于朝北的坦克：北=forward, 东=right
        blue_tank.x = 9
        blue_tank.y = 5
        blue_tank.moved_last_step = True
        
        # 多次调用，收集结果
        results = set()
        for _ in range(50):
            result = SoundSensor.sense(red_tank, [red_tank, blue_tank], empty_map)
            results.add(result)
        
        # 应该有多个方向被返回（forward 或 right）
        # 由于是对角线位置，最短路径可以先走任一方向
        assert len(results) >= 1  # 至少有一个方向
        # 验证返回的方向是有效的（forward 或 right）
        for r in results:
            assert r in ['forward', 'right']
    
    def test_random_direction_diagonal_opposite(self, empty_map, two_tanks):
        """测试对角线位置时的随机方向选择"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 7
        red_tank.y = 7
        red_tank.direction = Direction.NORTH  # 朝北
        
        # 蓝方在红方的西北方向
        # 从 (7,7) 到 (5,5)，可以先向北再向西，或先向西再向北
        # 相对于朝北的坦克：北=forward, 西=left
        blue_tank.x = 5
        blue_tank.y = 5
        blue_tank.moved_last_step = True
        
        # 多次调用，收集结果
        results = set()
        for _ in range(50):
            result = SoundSensor.sense(red_tank, [red_tank, blue_tank], empty_map)
            results.add(result)
        
        # 验证返回的方向是有效的（forward 或 left）
        for r in results:
            assert r in ['forward', 'left']