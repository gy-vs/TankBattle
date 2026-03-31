"""
动作系统单元测试
测试各种动作的执行和效果
"""

import pytest
from game.tank import Tank, Direction
from game.map import GameMap, MapElement
from game.missile import Missile
from game.actions import Action, ActionType, ActionExecutor
from game.config import GameConfig


class TestActionCreation:
    """动作创建测试"""
    
    def test_create_move_forward(self):
        """测试创建前进动作"""
        action = Action.move('forward')
        
        assert action.action_type == ActionType.MOVE
        assert action.param == 'forward'
    
    def test_create_move_backward(self):
        """测试创建后退动作"""
        action = Action.move('backward')
        
        assert action.action_type == ActionType.MOVE
        assert action.param == 'backward'
    
    def test_create_turn_left(self):
        """测试创建左转动作"""
        action = Action.turn('left')
        
        assert action.action_type == ActionType.TURN
        assert action.param == 'left'
    
    def test_create_turn_right(self):
        """测试创建右转动作"""
        action = Action.turn('right')
        
        assert action.action_type == ActionType.TURN
        assert action.param == 'right'
    
    def test_create_radar_on(self):
        """测试创建开启雷达动作"""
        action = Action.radar('on')
        
        assert action.action_type == ActionType.RADAR
        assert action.param == 'on'
    
    def test_create_radar_off(self):
        """测试创建关闭雷达动作"""
        action = Action.radar('off')
        
        assert action.action_type == ActionType.RADAR
        assert action.param == 'off'
    
    def test_create_radar_power(self):
        """测试创建雷达功率设置动作"""
        action = Action.radar_power(10)
        
        assert action.action_type == ActionType.RADAR_POWER
        assert action.param == '10'
    
    def test_create_shields_on(self):
        """测试创建开启护盾动作"""
        action = Action.shields('on')
        
        assert action.action_type == ActionType.SHIELDS
        assert action.param == 'on'
    
    def test_create_shields_off(self):
        """测试创建关闭护盾动作"""
        action = Action.shields('off')
        
        assert action.action_type == ActionType.SHIELDS
        assert action.param == 'off'
    
    def test_create_fire(self):
        """测试创建开火动作"""
        action = Action.fire()
        
        assert action.action_type == ActionType.FIRE
    
    def test_create_none(self):
        """测试创建空动作"""
        action = Action.none()
        
        assert action.action_type == ActionType.NONE
    
    def test_action_to_dict(self):
        """测试动作序列化"""
        action = Action.move('forward')
        data = action.to_dict()
        
        assert data['type'] == 'move'
        assert data['param'] == 'forward'


class TestMoveExecution:
    """移动动作执行测试"""
    
    def test_move_forward_success(self, empty_map, red_tank):
        """测试前进成功"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        result = ActionExecutor.execute_move(red_tank, empty_map, [red_tank], 'forward')
        
        assert result is True
        assert red_tank.x == 6
        assert red_tank.y == 5
        assert red_tank.moved_last_step is True
    
    def test_move_backward_success(self, empty_map, red_tank):
        """测试后退成功"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        result = ActionExecutor.execute_move(red_tank, empty_map, [red_tank], 'backward')
        
        assert result is True
        assert red_tank.x == 4
        assert red_tank.y == 5
    
    def test_move_blocked_by_obstacle(self, empty_map, red_tank):
        """测试被障碍物阻挡"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        empty_map.set_element(6, 5, MapElement.STONE)
        
        result = ActionExecutor.execute_move(red_tank, empty_map, [red_tank], 'forward')
        
        assert result is False
        assert red_tank.x == 5  # 位置不变
    
    def test_move_blocked_by_boundary(self, empty_map, red_tank):
        """测试被边界阻挡"""
        red_tank.x = 0
        red_tank.y = 5
        red_tank.direction = Direction.WEST
        
        result = ActionExecutor.execute_move(red_tank, empty_map, [red_tank], 'forward')
        
        assert result is False
        assert red_tank.x == 0
    
    def test_move_blocked_by_tank(self, empty_map, two_tanks):
        """测试被其他坦克阻挡"""
        red_tank, blue_tank = two_tanks
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        
        blue_tank.x = 6
        blue_tank.y = 5
        
        result = ActionExecutor.execute_move(red_tank, empty_map, [red_tank, blue_tank], 'forward')
        
        assert result is False
        assert red_tank.x == 5
    
    def test_move_pickup_ammo(self, empty_map, red_tank):
        """测试移动时拾取弹药"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        red_tank.missiles = 5
        
        # 在前方放置弹药箱
        empty_map.set_element(6, 5, MapElement.AMMO)
        empty_map.ammo_positions.append((6, 5))
        
        result = ActionExecutor.execute_move(red_tank, empty_map, [red_tank], 'forward')
        
        assert result is True
        assert red_tank.x == 6
        assert red_tank.missiles == 5 + GameConfig.AMMO_PICKUP_AMOUNT
        assert empty_map.is_ammo_box(6, 5) is False


class TestTurnExecution:
    """转向动作执行测试"""
    
    def test_turn_left(self, red_tank):
        """测试左转"""
        red_tank.direction = Direction.NORTH
        
        result = ActionExecutor.execute_turn(red_tank, 'left')
        
        assert result is True
        assert red_tank.direction == Direction.WEST
    
    def test_turn_right(self, red_tank):
        """测试右转"""
        red_tank.direction = Direction.NORTH
        
        result = ActionExecutor.execute_turn(red_tank, 'right')
        
        assert result is True
        assert red_tank.direction == Direction.EAST
    
    def test_turn_invalid_direction(self, red_tank):
        """测试无效转向"""
        result = ActionExecutor.execute_turn(red_tank, 'up')
        
        assert result is False


class TestRadarExecution:
    """雷达动作执行测试"""
    
    def test_radar_on(self, red_tank):
        """测试开启雷达"""
        red_tank.energy = 500
        
        result = ActionExecutor.execute_radar(red_tank, 'on')
        
        assert result is True
        assert red_tank.radar_on is True
    
    def test_radar_on_no_energy(self, red_tank):
        """测试无能量开启雷达"""
        red_tank.energy = 0
        
        result = ActionExecutor.execute_radar(red_tank, 'on')
        
        assert result is False
        assert red_tank.radar_on is False
    
    def test_radar_off(self, red_tank):
        """测试关闭雷达"""
        red_tank.radar_on = True
        
        result = ActionExecutor.execute_radar(red_tank, 'off')
        
        assert result is True
        assert red_tank.radar_on is False
    
    def test_radar_power_valid(self, red_tank):
        """测试设置有效雷达功率"""
        result = ActionExecutor.execute_radar_power(red_tank, 10)
        
        assert result is True
        assert red_tank.radar_setting == 10
    
    def test_radar_power_invalid_low(self, red_tank):
        """测试设置过低雷达功率"""
        original = red_tank.radar_setting
        
        result = ActionExecutor.execute_radar_power(red_tank, 0)
        
        assert result is False
        assert red_tank.radar_setting == original
    
    def test_radar_power_invalid_high(self, red_tank):
        """测试设置过高雷达功率"""
        original = red_tank.radar_setting
        
        result = ActionExecutor.execute_radar_power(red_tank, 20)
        
        assert result is False
        assert red_tank.radar_setting == original


class TestShieldsExecution:
    """护盾动作执行测试"""
    
    def test_shields_on(self, red_tank):
        """测试开启护盾"""
        red_tank.energy = 500
        
        result = ActionExecutor.execute_shields(red_tank, 'on')
        
        assert result is True
        assert red_tank.shield_on is True
    
    def test_shields_on_no_energy(self, red_tank):
        """测试无能量开启护盾"""
        red_tank.energy = 0
        
        result = ActionExecutor.execute_shields(red_tank, 'on')
        
        assert result is False
        assert red_tank.shield_on is False
    
    def test_shields_off(self, red_tank):
        """测试关闭护盾"""
        red_tank.shield_on = True
        
        result = ActionExecutor.execute_shields(red_tank, 'off')
        
        assert result is True
        assert red_tank.shield_on is False


class TestFireExecution:
    """开火动作执行测试"""
    
    def test_fire_success(self, red_tank):
        """测试开火成功"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.EAST
        red_tank.missiles = 10
        
        missile = ActionExecutor.execute_fire(red_tank)
        
        assert missile is not None
        assert missile.direction == Direction.EAST
        assert missile.owner_id == red_tank.id
        assert missile.owner_team == red_tank.team
        assert red_tank.missiles == 9
    
    def test_fire_no_missiles(self, red_tank):
        """测试无炮弹开火"""
        red_tank.missiles = 0
        
        missile = ActionExecutor.execute_fire(red_tank)
        
        assert missile is None
        assert red_tank.missiles == 0
    
    def test_fire_missile_position(self, red_tank):
        """测试导弹初始位置"""
        red_tank.x = 5
        red_tank.y = 5
        red_tank.direction = Direction.NORTH
        red_tank.missiles = 10
        
        missile = ActionExecutor.execute_fire(red_tank)
        
        # 导弹应该在坦克前方一格
        assert missile.x == 5
        assert missile.y == 4
