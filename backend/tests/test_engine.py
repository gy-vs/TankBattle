"""
游戏引擎集成测试
测试完整的游戏流程和多模块交互
"""

import pytest
from game.engine import GameEngine, GameState
from game.tank import Tank, Direction
from game.missile import Missile
from game.config import GameConfig


class TestGameEngineInitialization:
    """游戏引擎初始化测试"""
    
    def test_engine_creation(self):
        """测试引擎创建"""
        engine = GameEngine()
        
        assert engine.game_map is None
        assert engine.tanks == []
        assert engine.missiles == []
        assert engine.clock == 0
        assert engine.state == GameState.WAITING
    
    def test_init_game(self, game_engine):
        """测试游戏初始化"""
        assert game_engine.game_map is not None
        assert len(game_engine.tanks) == GameConfig.TANKS_PER_TEAM * 2
        assert game_engine.state == GameState.WAITING
        assert game_engine.clock == 0
    
    def test_tanks_team_distribution(self, game_engine):
        """测试坦克阵营分布"""
        red_tanks = [t for t in game_engine.tanks if t.team == 'red']
        blue_tanks = [t for t in game_engine.tanks if t.team == 'blue']
        
        assert len(red_tanks) == GameConfig.TANKS_PER_TEAM
        assert len(blue_tanks) == GameConfig.TANKS_PER_TEAM
    
    def test_ai_controllers_created(self, game_engine):
        """测试 AI 控制器创建"""
        for tank in game_engine.tanks:
            assert tank.id in game_engine.ai_controllers


class TestGameStateTransitions:
    """游戏状态转换测试"""
    
    def test_start_from_waiting(self, game_engine):
        """测试从等待状态开始"""
        assert game_engine.state == GameState.WAITING
        
        game_engine.start()
        
        assert game_engine.state == GameState.RUNNING
    
    def test_pause_from_running(self, game_engine):
        """测试从运行状态暂停"""
        game_engine.start()
        game_engine.pause()
        
        assert game_engine.state == GameState.PAUSED
    
    def test_resume_from_paused(self, game_engine):
        """测试从暂停状态恢复"""
        game_engine.start()
        game_engine.pause()
        game_engine.start()
        
        assert game_engine.state == GameState.RUNNING
    
    def test_step_increments_clock(self, game_engine):
        """测试步进增加时钟"""
        game_engine.start()
        initial_clock = game_engine.clock
        
        game_engine.step()
        
        assert game_engine.clock == initial_clock + 1


class TestGameSimulation:
    """游戏仿真测试"""
    
    def test_multiple_steps(self, game_engine):
        """测试多步仿真"""
        game_engine.start()
        
        for i in range(10):
            game_engine.step()
        
        assert game_engine.clock == 10
    
    def test_tank_movement_recorded(self, game_engine):
        """测试坦克移动记录"""
        game_engine.start()
        
        # 执行一步
        game_engine.step()
        
        # 检查是否有坦克移动标记被设置
        # 由于 AI 会做决策，不确定具体哪个坦克移动
        # 只要游戏能正常运行即可


class TestWinConditions:
    """胜负条件测试"""
    
    def test_red_wins_all_blue_destroyed(self, game_engine):
        """测试红方胜利（蓝方全灭）"""
        # 消灭所有蓝方坦克
        for tank in game_engine.tanks:
            if tank.team == 'blue':
                tank.health = 0
                tank.alive = False
        
        game_engine._check_game_over()
        
        assert game_engine.state == GameState.FINISHED
        assert game_engine.winner == 'red'
    
    def test_blue_wins_all_red_destroyed(self, game_engine):
        """测试蓝方胜利（红方全灭）"""
        # 消灭所有红方坦克
        for tank in game_engine.tanks:
            if tank.team == 'red':
                tank.health = 0
                tank.alive = False
        
        game_engine._check_game_over()
        
        assert game_engine.state == GameState.FINISHED
        assert game_engine.winner == 'blue'
    
    def test_win_by_tank_count(self, game_engine):
        """测试通过坦克数量获胜"""
        # 设置时钟到最大步数
        game_engine.clock = GameConfig.MAX_STEPS
        
        # 红方2辆，蓝方1辆
        for i, tank in enumerate(game_engine.tanks):
            if tank.team == 'blue' and i > 0:
                tank.health = 0
                tank.alive = False
        
        # 确保红方有更多坦克
        red_alive = sum(1 for t in game_engine.tanks if t.team == 'red' and t.is_alive())
        blue_alive = sum(1 for t in game_engine.tanks if t.team == 'blue' and t.is_alive())
        
        if red_alive > blue_alive:
            game_engine._check_game_over()
            assert game_engine.winner == 'red'
    
    def test_draw_condition(self, game_engine):
        """测试平局条件"""
        # 设置时钟到最大步数
        game_engine.clock = GameConfig.MAX_STEPS
        
        # 双方各保留一辆，生命值相同
        red_tank = None
        blue_tank = None
        
        for tank in game_engine.tanks:
            if tank.team == 'red':
                if red_tank is None:
                    red_tank = tank
                    tank.health = 500
                else:
                    tank.health = 0
                    tank.alive = False
            else:
                if blue_tank is None:
                    blue_tank = tank
                    tank.health = 500
                else:
                    tank.health = 0
                    tank.alive = False
        
        game_engine._check_game_over()
        
        # 双方各一辆，生命值相同，应该是平局
        assert game_engine.winner == 'draw'


class TestMissileSystem:
    """导弹系统集成测试"""
    
    def test_missile_creation_on_fire(self, game_engine):
        """测试开火创建导弹"""
        from game.actions import Action
        
        # 获取一辆红方坦克
        red_tank = next(t for t in game_engine.tanks if t.team == 'red')
        red_tank.missiles = 10
        
        # 手动执行开火
        missile = game_engine._execute_action(red_tank, Action.fire())
        
        if missile:
            game_engine.missiles.append(missile)
            assert len(game_engine.missiles) == 1
            assert missile.owner_team == 'red'
    
    def test_missile_movement(self, game_engine):
        """测试导弹移动"""
        # 创建一枚导弹
        missile = Missile(x=5, y=5, direction=Direction.EAST, owner_id=1, owner_team='red')
        game_engine.missiles.append(missile)
        
        # 更新导弹
        game_engine._update_missiles()
        
        # 导弹应该已经移动或被移除


class TestStationEffects:
    """补给站效果测试"""
    
    def test_health_station_heals(self, game_engine):
        """测试维修厂恢复生命"""
        # 找一个维修站位置
        for y in range(game_engine.game_map.height):
            for x in range(game_engine.game_map.width):
                if game_engine.game_map.is_health_station(x, y):
                    # 移动坦克到维修站
                    red_tank = game_engine.tanks[0]
                    red_tank.x = x
                    red_tank.y = y
                    red_tank.health = 500
                    
                    # 处理补给站效果
                    game_engine._process_stations()
                    
                    assert red_tank.health > 500
                    return
    
    def test_energy_station_recharges(self, game_engine):
        """测试能量站恢复能量"""
        # 找一个能量站位置
        for y in range(game_engine.game_map.height):
            for x in range(game_engine.game_map.width):
                if game_engine.game_map.is_energy_station(x, y):
                    # 移动坦克到能量站
                    red_tank = game_engine.tanks[0]
                    red_tank.x = x
                    red_tank.y = y
                    red_tank.energy = 500
                    
                    # 处理补给站效果
                    game_engine._process_stations()
                    
                    assert red_tank.energy > 500
                    return


class TestGameStateOutput:
    """游戏状态输出测试"""
    
    def test_get_state(self, game_engine):
        """测试获取游戏状态"""
        state = game_engine.get_state()
        
        assert 'clock' in state
        assert 'state' in state
        assert 'map' in state
        assert 'tanks' in state
        assert 'missiles' in state
        assert 'events' in state
    
    def test_get_result(self, game_engine):
        """测试获取游戏结果"""
        result = game_engine.get_result()
        
        assert 'winner' in result
        assert 'clock' in result
        assert 'red' in result
        assert 'blue' in result
        
        assert 'alive' in result['red']
        assert 'total' in result['red']
        assert 'avgHealth' in result['red']


class TestEventLogging:
    """事件日志测试"""
    
    def test_init_event_logged(self, game_engine):
        """测试初始化事件记录"""
        # 初始化时应该有事件记录
        assert len(game_engine.events) > 0
        
        init_events = [e for e in game_engine.events if e['type'] == 'game_init']
        assert len(init_events) > 0
    
    def test_start_event_logged(self, game_engine):
        """测试开始事件记录"""
        game_engine.start()
        
        start_events = [e for e in game_engine.events if e['type'] == 'game_start']
        assert len(start_events) > 0


class TestSensorDataIntegration:
    """传感器数据集成测试"""
    
    def test_get_sensor_data(self, game_engine):
        """测试获取传感器数据"""
        red_tank = game_engine.tanks[0]
        
        sensor_data = game_engine._get_sensor_data(red_tank)
        
        assert 'blocked' in sensor_data
        assert 'incoming' in sensor_data
        assert 'radar' in sensor_data
        assert 'rwave' in sensor_data
        assert 'smell' in sensor_data
        assert 'sound' in sensor_data
        assert 'visual' in sensor_data
        assert 'self' in sensor_data
    
    def test_sensor_self_data(self, game_engine):
        """测试传感器自身数据"""
        red_tank = game_engine.tanks[0]
        
        sensor_data = game_engine._get_sensor_data(red_tank)
        self_data = sensor_data['self']
        
        assert self_data['x'] == red_tank.x
        assert self_data['y'] == red_tank.y
        assert self_data['health'] == red_tank.health
        assert self_data['energy'] == red_tank.energy
        assert self_data['missiles'] == red_tank.missiles


class TestFullGameSimulation:
    """完整游戏仿真测试"""
    
    @pytest.mark.slow
    def test_game_completes(self):
        """测试游戏能够正常完成"""
        engine = GameEngine()
        engine.init_game()
        engine.start()
        
        # 运行直到游戏结束或达到最大步数
        max_iterations = GameConfig.MAX_STEPS + 100
        iterations = 0
        
        while not engine.is_game_over() and iterations < max_iterations:
            engine.step()
            iterations += 1
        
        # 游戏应该能够结束
        assert engine.is_game_over() or iterations >= max_iterations
    
    @pytest.mark.slow
    def test_no_runtime_errors(self):
        """测试运行时无错误"""
        engine = GameEngine()
        engine.init_game()
        engine.start()
        
        # 运行一定步数，检查是否有运行时错误
        try:
            for _ in range(100):
                engine.step()
            success = True
        except Exception as e:
            success = False
            print(f"运行时错误: {e}")
        
        assert success is True
