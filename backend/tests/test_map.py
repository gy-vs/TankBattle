"""
地图模块单元测试
测试地图的生成、元素和功能
"""

import pytest
from game.map import GameMap, MapElement
from game.config import GameConfig


class TestMapInitialization:
    """地图初始化测试"""
    
    def test_default_size(self):
        """测试默认地图大小"""
        game_map = GameMap()
        
        assert game_map.width == GameConfig.MAP_WIDTH
        assert game_map.height == GameConfig.MAP_HEIGHT
    
    def test_custom_size(self):
        """测试自定义地图大小"""
        game_map = GameMap(width=20, height=20)
        
        assert game_map.width == 20
        assert game_map.height == 20
    
    def test_init_empty(self, empty_map):
        """测试初始化空地图"""
        # 检查所有格子都是空地
        for y in range(empty_map.height):
            for x in range(empty_map.width):
                assert empty_map.get_element(x, y) == MapElement.OPEN
    
    def test_generate_random(self):
        """测试随机地图生成"""
        game_map = GameMap()
        game_map.generate_random(
            num_trees=10,
            num_stones=5,
            num_health=2,
            num_energy=2,
            num_ammo=3
        )
        
        # 统计各类型元素数量
        tree_count = 0
        stone_count = 0
        health_count = 0
        energy_count = 0
        
        for y in range(game_map.height):
            for x in range(game_map.width):
                element = game_map.get_element(x, y)
                if element == MapElement.TREE:
                    tree_count += 1
                elif element == MapElement.STONE:
                    stone_count += 1
                elif element == MapElement.HEALTH:
                    health_count += 1
                elif element == MapElement.ENERGY:
                    energy_count += 1
        
        assert tree_count == 10
        assert stone_count == 5
        assert health_count == 2
        assert energy_count == 2


class TestMapElementAccess:
    """地图元素访问测试"""
    
    def test_get_element_valid(self, empty_map):
        """测试获取有效位置元素"""
        element = empty_map.get_element(0, 0)
        assert element == MapElement.OPEN
    
    def test_get_element_invalid(self, empty_map):
        """测试获取无效位置元素"""
        element = empty_map.get_element(-1, 0)
        assert element is None
        
        element = empty_map.get_element(100, 100)
        assert element is None
    
    def test_set_element(self, empty_map):
        """测试设置元素"""
        empty_map.set_element(5, 5, MapElement.TREE)
        
        assert empty_map.get_element(5, 5) == MapElement.TREE
    
    def test_is_valid_position(self, empty_map):
        """测试位置有效性检查"""
        assert empty_map.is_valid_position(0, 0) is True
        assert empty_map.is_valid_position(empty_map.width - 1, empty_map.height - 1) is True
        assert empty_map.is_valid_position(-1, 0) is False
        assert empty_map.is_valid_position(empty_map.width, 0) is False


class TestMapObstacles:
    """障碍物测试"""
    
    def test_is_blocked_by_tree(self, empty_map):
        """测试树木阻挡"""
        empty_map.set_element(5, 5, MapElement.TREE)
        
        assert empty_map.is_blocked(5, 5) is True
        assert empty_map.is_obstacle(5, 5) is True
    
    def test_is_blocked_by_stone(self, empty_map):
        """测试石头阻挡"""
        empty_map.set_element(5, 5, MapElement.STONE)
        
        assert empty_map.is_blocked(5, 5) is True
        assert empty_map.is_obstacle(5, 5) is True
    
    def test_is_blocked_by_boundary(self, empty_map):
        """测试边界阻挡"""
        assert empty_map.is_blocked(-1, 0) is True
        assert empty_map.is_blocked(100, 100) is True
    
    def test_not_blocked_by_open(self, empty_map):
        """测试空地不阻挡"""
        assert empty_map.is_blocked(5, 5) is False
        assert empty_map.is_obstacle(5, 5) is False
    
    def test_not_blocked_by_station(self, empty_map):
        """测试补给站不阻挡"""
        empty_map.set_element(5, 5, MapElement.HEALTH)
        
        assert empty_map.is_blocked(5, 5) is False
        assert empty_map.is_obstacle(5, 5) is False


class TestMapStations:
    """补给站测试"""
    
    def test_health_station(self, empty_map):
        """测试维修厂"""
        empty_map.set_element(5, 5, MapElement.HEALTH)
        
        assert empty_map.is_health_station(5, 5) is True
        assert empty_map.is_energy_station(5, 5) is False
    
    def test_energy_station(self, empty_map):
        """测试能量补给站"""
        empty_map.set_element(5, 5, MapElement.ENERGY)
        
        assert empty_map.is_energy_station(5, 5) is True
        assert empty_map.is_health_station(5, 5) is False


class TestMapAmmo:
    """弹药箱测试"""
    
    def test_ammo_box_detection(self):
        """测试弹药箱检测"""
        game_map = GameMap()
        game_map.init_empty()
        game_map.set_element(5, 5, MapElement.AMMO)
        game_map.ammo_positions.append((5, 5))
        
        assert game_map.is_ammo_box(5, 5) is True
        assert game_map.is_ammo_box(6, 6) is False
    
    def test_pickup_ammo(self):
        """测试拾取弹药箱"""
        game_map = GameMap()
        game_map.init_empty()
        game_map.set_element(5, 5, MapElement.AMMO)
        game_map.ammo_positions.append((5, 5))
        
        result = game_map.pickup_ammo(5, 5)
        
        assert result is True
        assert game_map.is_ammo_box(5, 5) is False
        assert game_map.get_element(5, 5) == MapElement.OPEN
    
    def test_pickup_ammo_nonexistent(self):
        """测试拾取不存在的弹药箱"""
        game_map = GameMap()
        game_map.init_empty()
        
        result = game_map.pickup_ammo(5, 5)
        
        assert result is False


class TestMapSpawnPositions:
    """出生点测试"""
    
    def test_red_spawn_positions(self, empty_map):
        """测试红方出生点"""
        positions = empty_map.get_spawn_positions('red', 3)
        
        assert len(positions) == 3
        # 红方在左侧
        for x, y in positions:
            assert x == 1
    
    def test_blue_spawn_positions(self, empty_map):
        """测试蓝方出生点"""
        positions = empty_map.get_spawn_positions('blue', 3)
        
        assert len(positions) == 3
        # 蓝方在右侧
        for x, y in positions:
            assert x == empty_map.width - 2


class TestMapSerialization:
    """地图序列化测试"""
    
    def test_to_dict(self, empty_map):
        """测试地图序列化"""
        data = empty_map.to_dict()
        
        assert 'width' in data
        assert 'height' in data
        assert 'grid' in data
        assert 'ammoPositions' in data
        
        assert data['width'] == empty_map.width
        assert data['height'] == empty_map.height
        assert len(data['grid']) == empty_map.height
        assert len(data['grid'][0]) == empty_map.width
