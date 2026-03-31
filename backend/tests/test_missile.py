"""
导弹模块单元测试
测试导弹的创建、移动和碰撞
"""

import pytest
from game.missile import Missile
from game.tank import Direction
from game.config import GameConfig


class TestMissileInitialization:
    """导弹初始化测试"""
    
    def test_missile_creation(self):
        """测试导弹创建"""
        missile = Missile(
            x=5, y=5, 
            direction=Direction.EAST, 
            owner_id=1, 
            owner_team='red'
        )
        
        assert missile.x == 5
        assert missile.y == 5
        assert missile.direction == Direction.EAST
        assert missile.owner_id == 1
        assert missile.owner_team == 'red'
        assert missile.active is True
    
    def test_missile_id_auto_increment(self):
        """测试导弹 ID 自动递增"""
        Missile.reset_id_counter()
        
        missile1 = Missile(x=1, y=1, direction=Direction.EAST, owner_id=1, owner_team='red')
        missile2 = Missile(x=2, y=2, direction=Direction.WEST, owner_id=2, owner_team='blue')
        
        assert missile1.id == 1
        assert missile2.id == 2
    
    def test_launch_position_recorded(self):
        """测试记录发射位置"""
        missile = Missile(
            x=5, y=5, 
            direction=Direction.EAST, 
            owner_id=1, 
            owner_team='red'
        )
        
        assert missile.launch_x == 5
        assert missile.launch_y == 5


class TestMissileMovement:
    """导弹移动测试"""
    
    def test_move_east(self, missile_heading_east):
        """测试向东移动"""
        initial_x = missile_heading_east.x
        new_x, new_y = missile_heading_east.move()
        
        # 导弹速度是坦克的2倍
        expected_x = initial_x + GameConfig.MISSILE_SPEED
        assert new_x == expected_x
        assert missile_heading_east.x == expected_x
    
    def test_move_west(self):
        """测试向西移动"""
        missile = Missile(x=10, y=5, direction=Direction.WEST, owner_id=1, owner_team='red')
        new_x, new_y = missile.move()
        
        expected_x = 10 - GameConfig.MISSILE_SPEED
        assert new_x == expected_x
    
    def test_move_north(self):
        """测试向北移动"""
        missile = Missile(x=5, y=10, direction=Direction.NORTH, owner_id=1, owner_team='red')
        new_x, new_y = missile.move()
        
        expected_y = 10 - GameConfig.MISSILE_SPEED
        assert new_y == expected_y
        assert new_x == 5
    
    def test_move_south(self):
        """测试向南移动"""
        missile = Missile(x=5, y=5, direction=Direction.SOUTH, owner_id=1, owner_team='red')
        new_x, new_y = missile.move()
        
        expected_y = 5 + GameConfig.MISSILE_SPEED
        assert new_y == expected_y


class TestMissilePath:
    """导弹路径测试"""
    
    def test_get_path_east(self, missile_heading_east):
        """测试向东移动的路径"""
        path = missile_heading_east.get_path()
        
        assert len(path) == GameConfig.MISSILE_SPEED
        
        # 检查路径中的每一格
        expected_positions = []
        for i in range(1, GameConfig.MISSILE_SPEED + 1):
            expected_positions.append((missile_heading_east.x + i, missile_heading_east.y))
        
        assert path == expected_positions
    
    def test_get_path_west(self):
        """测试向西移动的路径"""
        missile = Missile(x=10, y=5, direction=Direction.WEST, owner_id=1, owner_team='red')
        path = missile.get_path()
        
        assert len(path) == GameConfig.MISSILE_SPEED
        assert path[0] == (9, 5)
    
    def test_get_path_north(self):
        """测试向北移动的路径"""
        missile = Missile(x=5, y=10, direction=Direction.NORTH, owner_id=1, owner_team='red')
        path = missile.get_path()
        
        assert len(path) == GameConfig.MISSILE_SPEED
        assert path[0] == (5, 9)


class TestMissileState:
    """导弹状态测试"""
    
    def test_initial_state_active(self, missile_heading_east):
        """测试初始状态为激活"""
        assert missile_heading_east.is_active() is True
    
    def test_deactivate(self, missile_heading_east):
        """测试导弹失效"""
        missile_heading_east.deactivate()
        
        assert missile_heading_east.is_active() is False
        assert missile_heading_east.active is False


class TestMissileDistance:
    """导弹距离计算测试"""
    
    def test_distance_from_launch_initial(self):
        """测试初始距离"""
        missile = Missile(x=5, y=5, direction=Direction.EAST, owner_id=1, owner_team='red')
        
        assert missile.get_distance_from_launch() == 0
    
    def test_distance_from_launch_after_move(self):
        """测试移动后的距离"""
        missile = Missile(x=5, y=5, direction=Direction.EAST, owner_id=1, owner_team='red')
        missile.move()
        
        assert missile.get_distance_from_launch() == GameConfig.MISSILE_SPEED
    
    def test_distance_from_launch_multiple_moves(self):
        """测试多次移动后的距离"""
        missile = Missile(x=5, y=5, direction=Direction.EAST, owner_id=1, owner_team='red')
        missile.move()
        missile.move()
        
        expected_distance = GameConfig.MISSILE_SPEED * 2
        assert missile.get_distance_from_launch() == expected_distance


class TestMissileSerialization:
    """导弹序列化测试"""
    
    def test_to_dict(self, missile_heading_east):
        """测试导弹序列化"""
        data = missile_heading_east.to_dict()
        
        assert 'id' in data
        assert 'x' in data
        assert 'y' in data
        assert 'direction' in data
        assert 'ownerTeam' in data
        assert 'active' in data
        
        assert data['x'] == missile_heading_east.x
        assert data['y'] == missile_heading_east.y
        assert data['direction'] == missile_heading_east.direction.value
        assert data['active'] is True
