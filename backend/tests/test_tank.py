"""
坦克模块单元测试
测试坦克的属性、状态和行为
"""

import pytest
from game.tank import Tank, Direction
from game.config import GameConfig


class TestDirection:
    """方向枚举测试"""
    
    def test_turn_left(self):
        """测试左转"""
        assert Direction.NORTH.turn_left() == Direction.WEST
        assert Direction.WEST.turn_left() == Direction.SOUTH
        assert Direction.SOUTH.turn_left() == Direction.EAST
        assert Direction.EAST.turn_left() == Direction.NORTH
    
    def test_turn_right(self):
        """测试右转"""
        assert Direction.NORTH.turn_right() == Direction.EAST
        assert Direction.EAST.turn_right() == Direction.SOUTH
        assert Direction.SOUTH.turn_right() == Direction.WEST
        assert Direction.WEST.turn_right() == Direction.NORTH
    
    def test_get_delta(self):
        """测试坐标增量"""
        assert Direction.NORTH.get_delta() == (0, -1)
        assert Direction.SOUTH.get_delta() == (0, 1)
        assert Direction.EAST.get_delta() == (1, 0)
        assert Direction.WEST.get_delta() == (-1, 0)
    
    def test_get_opposite(self):
        """测试相反方向"""
        assert Direction.NORTH.get_opposite() == Direction.SOUTH
        assert Direction.SOUTH.get_opposite() == Direction.NORTH
        assert Direction.EAST.get_opposite() == Direction.WEST
        assert Direction.WEST.get_opposite() == Direction.EAST


class TestTankInitialization:
    """坦克初始化测试"""
    
    def test_tank_creation(self):
        """测试坦克创建"""
        tank = Tank(x=5, y=5, team='red', direction=Direction.NORTH)
        
        assert tank.x == 5
        assert tank.y == 5
        assert tank.team == 'red'
        assert tank.direction == Direction.NORTH
    
    def test_tank_initial_stats(self):
        """测试坦克初始属性"""
        tank = Tank(x=1, y=1, team='blue')
        
        assert tank.health == GameConfig.TANK_INITIAL_HEALTH
        assert tank.energy == GameConfig.TANK_INITIAL_ENERGY
        assert tank.missiles == GameConfig.TANK_INITIAL_MISSILES
        assert tank.alive is True
        assert tank.shield_on is False
        assert tank.radar_on is False
    
    def test_tank_id_auto_increment(self):
        """测试坦克 ID 自动递增"""
        Tank.reset_id_counter()
        tank1 = Tank(x=1, y=1, team='red')
        tank2 = Tank(x=2, y=2, team='blue')
        
        assert tank1.id == 1
        assert tank2.id == 2
    
    def test_reset_id_counter(self):
        """测试重置 ID 计数器"""
        Tank.reset_id_counter()
        tank1 = Tank(x=1, y=1, team='red')
        assert tank1.id == 1
        
        Tank.reset_id_counter()
        tank2 = Tank(x=2, y=2, team='blue')
        assert tank2.id == 1


class TestTankDamage:
    """坦克伤害系统测试"""
    
    def test_front_damage(self, red_tank):
        """测试前方伤害"""
        initial_health = red_tank.health
        red_tank.take_damage(0, 'forward')
        
        assert red_tank.health == initial_health - GameConfig.DAMAGE_FRONT
    
    def test_back_damage(self, red_tank):
        """测试后方伤害"""
        initial_health = red_tank.health
        red_tank.take_damage(0, 'backward')
        
        assert red_tank.health == initial_health - GameConfig.DAMAGE_BACK
    
    def test_side_damage(self, red_tank):
        """测试侧方伤害"""
        initial_health = red_tank.health
        red_tank.take_damage(0, 'left')
        
        assert red_tank.health == initial_health - GameConfig.DAMAGE_SIDE
    
    def test_tank_death(self, red_tank):
        """测试坦克死亡"""
        # 多次伤害直到死亡
        while red_tank.is_alive():
            red_tank.take_damage(0, 'backward')
        
        assert red_tank.health == 0
        assert red_tank.alive is False
    
    def test_instant_death(self, red_tank):
        """测试立即死亡（在补给站被攻击）"""
        red_tank.instant_death()
        
        assert red_tank.health == 0
        assert red_tank.alive is False
    
    def test_shield_blocks_damage(self, red_tank):
        """测试护盾抵消伤害（只扣能量，不扣血）"""
        red_tank.shield_on = True
        initial_energy = red_tank.energy
        initial_health = red_tank.health
        red_tank.take_damage(0, 'forward')
        
        # 护盾消耗能量
        assert red_tank.energy == initial_energy - GameConfig.SHIELD_HIT_ENERGY_COST
        # 护盾抵消伤害，血量不变
        assert red_tank.health == initial_health
    
    def test_shield_no_energy_takes_damage(self, red_tank):
        """测试护盾能量不足时无法抵消伤害"""
        red_tank.shield_on = True
        red_tank.energy = 100  # 不足200
        initial_health = red_tank.health
        red_tank.take_damage(0, 'forward')
        
        # 能量不足，护盾无法抵消，正常扣血
        assert red_tank.health == initial_health - GameConfig.DAMAGE_FRONT
        # 能量不变（护盾未触发）
        assert red_tank.energy == 100


class TestTankRecovery:
    """坦克恢复系统测试"""
    
    def test_heal(self, red_tank):
        """测试生命恢复"""
        red_tank.health = 500
        red_tank.heal()
        
        assert red_tank.health == 500 + GameConfig.HEALTH_REGEN_PER_STEP
    
    def test_heal_custom_amount(self, red_tank):
        """测试自定义恢复量"""
        red_tank.health = 500
        red_tank.heal(100)
        
        assert red_tank.health == 600
    
    def test_heal_cap(self, red_tank):
        """测试生命值上限"""
        red_tank.health = 950
        red_tank.heal(100)
        
        assert red_tank.health == GameConfig.TANK_MAX_HEALTH
    
    def test_recharge_energy(self, red_tank):
        """测试能量恢复"""
        red_tank.energy = 500
        red_tank.recharge_energy()
        
        assert red_tank.energy == 500 + GameConfig.ENERGY_REGEN_PER_STEP
    
    def test_energy_cap(self, red_tank):
        """测试能量上限"""
        red_tank.energy = 950
        red_tank.recharge_energy(100)
        
        assert red_tank.energy == GameConfig.TANK_MAX_ENERGY
    
    def test_add_missiles(self, red_tank):
        """测试炮弹补充"""
        red_tank.missiles = 5
        red_tank.add_missiles()
        
        assert red_tank.missiles == 5 + GameConfig.AMMO_PICKUP_AMOUNT


class TestTankMovement:
    """坦克移动测试"""
    
    def test_move_forward(self, red_tank):
        """测试向前移动"""
        # 坦克朝东
        red_tank.direction = Direction.EAST
        red_tank.x = 5
        red_tank.y = 5
        
        new_x, new_y = red_tank.move_forward()
        
        assert new_x == 6
        assert new_y == 5
    
    def test_move_backward(self, red_tank):
        """测试向后移动"""
        red_tank.direction = Direction.EAST
        red_tank.x = 5
        red_tank.y = 5
        
        new_x, new_y = red_tank.move_backward()
        
        assert new_x == 4
        assert new_y == 5
    
    def test_turn_left(self, red_tank):
        """测试左转"""
        red_tank.direction = Direction.NORTH
        red_tank.turn_left()
        
        assert red_tank.direction == Direction.WEST
    
    def test_turn_right(self, red_tank):
        """测试右转"""
        red_tank.direction = Direction.NORTH
        red_tank.turn_right()
        
        assert red_tank.direction == Direction.EAST
    
    def test_set_position(self, red_tank):
        """测试设置位置"""
        red_tank.set_position(10, 10)
        
        assert red_tank.x == 10
        assert red_tank.y == 10


class TestTankResourceConsumption:
    """资源消耗测试"""
    
    def test_consume_energy_success(self, red_tank):
        """测试能量消耗成功"""
        red_tank.energy = 100
        result = red_tank.consume_energy(50)
        
        assert result is True
        assert red_tank.energy == 50
    
    def test_consume_energy_failure(self, red_tank):
        """测试能量不足"""
        red_tank.energy = 30
        result = red_tank.consume_energy(50)
        
        assert result is False
        assert red_tank.energy == 30  # 能量不变
    
    def test_consume_missile_success(self, red_tank):
        """测试消耗炮弹成功"""
        red_tank.missiles = 5
        result = red_tank.consume_missile()
        
        assert result is True
        assert red_tank.missiles == 4
    
    def test_consume_missile_failure(self, red_tank):
        """测试炮弹不足"""
        red_tank.missiles = 0
        result = red_tank.consume_missile()
        
        assert result is False
        assert red_tank.missiles == 0
    
    def test_radar_energy_cost(self, red_tank):
        """测试雷达能量消耗"""
        red_tank.radar_on = True
        red_tank.radar_setting = 7
        red_tank.energy = 100
        
        red_tank.update_radar_cost()
        
        expected_cost = 7 * GameConfig.RADAR_ENERGY_COST_MULTIPLIER
        assert red_tank.energy == 100 - expected_cost
    
    def test_radar_auto_off_no_energy(self, red_tank):
        """测试能量不足时雷达自动关闭"""
        red_tank.radar_on = True
        red_tank.radar_setting = 7
        red_tank.energy = 5  # 能量不足
        
        red_tank.update_radar_cost()
        
        assert red_tank.radar_on is False
    
    def test_shield_energy_cost(self, red_tank):
        """测试护盾能量消耗"""
        red_tank.shield_on = True
        red_tank.energy = 100
        
        red_tank.update_shield_cost()
        
        assert red_tank.energy == 100 - GameConfig.SHIELD_ENERGY_COST_PER_STEP
    
    def test_shield_auto_off_no_energy(self, red_tank):
        """测试能量不足时护盾自动关闭"""
        red_tank.shield_on = True
        red_tank.energy = 5  # 能量不足
        
        red_tank.update_shield_cost()
        
        assert red_tank.shield_on is False


class TestTankRelativeDirection:
    """相对方向计算测试"""
    
    def test_relative_direction_front(self, red_tank):
        """测试正前方"""
        red_tank.direction = Direction.EAST
        red_tank.x = 5
        red_tank.y = 5
        
        # 来自东边（坦克正前方）
        rel_dir = red_tank.get_relative_direction(10, 5)
        assert rel_dir == 'forward'
    
    def test_relative_direction_back(self, red_tank):
        """测试后方"""
        red_tank.direction = Direction.EAST
        red_tank.x = 5
        red_tank.y = 5
        
        # 来自西边（坦克正后方）
        rel_dir = red_tank.get_relative_direction(1, 5)
        assert rel_dir == 'backward'
    
    def test_to_dict(self, red_tank):
        """测试序列化"""
        data = red_tank.to_dict()
        
        assert 'id' in data
        assert 'x' in data
        assert 'y' in data
        assert 'direction' in data
        assert 'team' in data
        assert 'health' in data
        assert 'energy' in data
        assert 'missiles' in data
        assert 'alive' in data
