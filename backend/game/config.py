"""
游戏配置
"""


class GameConfig:
    """游戏配置类"""
    
    # 地图配置
    MAP_WIDTH = 14
    MAP_HEIGHT = 14
    
    # 坦克配置
    TANK_INITIAL_HEALTH = 1000
    TANK_MAX_HEALTH = 1000
    TANK_INITIAL_ENERGY = 1000
    TANK_MAX_ENERGY = 1000
    TANK_INITIAL_MISSILES = 20
    TANK_MAX_MISSILES = 20
    
    # 伤害配置
    DAMAGE_FRONT = 200
    DAMAGE_SIDE = 300
    DAMAGE_BACK = 400
    
    # 资源恢复配置
    HEALTH_REGEN_PER_STEP = 150
    ENERGY_REGEN_PER_STEP = 250
    AMMO_PICKUP_AMOUNT = 7
    
    # 能量消耗配置
    RADAR_ENERGY_COST_MULTIPLIER = 2  # 雷达消耗 = 距离 * 2
    SHIELD_ENERGY_COST_PER_STEP = 20
    SHIELD_HIT_ENERGY_COST = 200
    
    # 传感器配置
    RADAR_MIN_DISTANCE = 1
    RADAR_MAX_DISTANCE = 14
    SMELL_MAX_DISTANCE = 28
    SOUND_MAX_DISTANCE = 7
    MISSILE_BLIND_RANGE = 2  # 导弹传感器盲区
    
    # 导弹配置
    MISSILE_SPEED = 1  # 相对于坦克速度的倍数
    
    # 游戏配置
    MAX_STEPS = 1000
    TANKS_PER_TEAM = 3
    
    @classmethod
    def to_dict(cls):
        """转换为字典"""
        return {
            'map': {
                'width': cls.MAP_WIDTH,
                'height': cls.MAP_HEIGHT
            },
            'tank': {
                'initialHealth': cls.TANK_INITIAL_HEALTH,
                'maxHealth': cls.TANK_MAX_HEALTH,
                'initialEnergy': cls.TANK_INITIAL_ENERGY,
                'maxEnergy': cls.TANK_MAX_ENERGY,
                'initialMissiles': cls.TANK_INITIAL_MISSILES,
                'maxMissiles': cls.TANK_MAX_MISSILES
            },
            'damage': {
                'front': cls.DAMAGE_FRONT,
                'side': cls.DAMAGE_SIDE,
                'back': cls.DAMAGE_BACK
            },
            'game': {
                'maxSteps': cls.MAX_STEPS,
                'tanksPerTeam': cls.TANKS_PER_TEAM
            }
        }
