# TankBattle 开发者指南

本指南面向希望参与 TankBattle 开发、扩展功能或自定义 AI 策略的开发者。

---

## 目录

- [开发环境设置](#开发环境设置)
- [项目架构](#项目架构)
- [核心模块详解](#核心模块详解)
- [自定义 AI 开发](#自定义-ai-开发)
- [测试指南](#测试指南)
- [代码规范](#代码规范)
- [常见问题](#常见问题)

---

## 开发环境设置

### 系统要求

- Python 3.11+
- Docker 和 Docker Compose（用于容器化部署）
- 现代浏览器（Chrome/Firefox/Safari）

### 本地开发环境

1. **克隆项目**

```bash
git clone <repository-url>
cd tankbattle
```

2. **创建虚拟环境**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **运行开发服务器**

```bash
python app.py
```

5. **访问应用**

打开浏览器访问 `http://localhost:8080`

### Docker 开发环境

```bash
# 构建并启动
docker compose up --build

# 后台运行
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

---

## 项目架构

### 目录结构

```
tankbattle/
├── docker-compose.yml          # Docker 编排配置
├── README.md                   # 项目说明
├── backend/
│   ├── app.py                  # Flask 应用入口
│   ├── Dockerfile              # Docker 镜像定义
│   ├── requirements.txt        # Python 依赖
│   ├── pytest.ini              # pytest 配置
│   ├── game/                   # 游戏核心模块
│   │   ├── __init__.py
│   │   ├── config.py           # 游戏配置常量
│   │   ├── map.py              # 地图系统
│   │   ├── tank.py             # 坦克实体
│   │   ├── missile.py          # 导弹系统
│   │   ├── sensors.py          # 传感器系统
│   │   ├── actions.py          # 动作系统
│   │   ├── engine.py           # 游戏引擎
│   │   ├── ai.py               # AI 策略
│   │   └── utils.py            # 工具函数
│   ├── tests/                  # 测试代码
│   │   ├── __init__.py
│   │   ├── conftest.py         # pytest fixtures
│   │   ├── test_tank.py        # 坦克测试
│   │   ├── test_map.py         # 地图测试
│   │   ├── test_missile.py     # 导弹测试
│   │   ├── test_sensors.py     # 传感器测试
│   │   ├── test_actions.py     # 动作测试
│   │   └── test_engine.py      # 引擎集成测试
│   ├── templates/              # HTML 模板
│   │   └── index.html
│   └── static/                 # 静态资源
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── game.js
│           └── renderer.js
└── docs/
    ├── Requirements.md         # 需求规格
    ├── Roadmap.md              # 开发路线图
    ├── DesignSpec.md           # 设计规范
    ├── API.md                  # API 文档
    └── DeveloperGuide.md       # 开发者指南
```

### 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              HTML5 Canvas Renderer                   │    │
│  │         (renderer.js + game.js + style.css)         │    │
│  └─────────────────────────────────────────────────────┘    │
│                            ↑                                 │
│                      WebSocket (Socket.IO)                   │
└────────────────────────────┼────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────┐
│                      Flask Server                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    app.py                            │    │
│  │          (路由、WebSocket 事件处理)                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                            ↓                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Game Engine                         │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │    │
│  │  │  Map    │  │  Tank   │  │ Missile │             │    │
│  │  └─────────┘  └─────────┘  └─────────┘             │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │    │
│  │  │ Sensors │  │ Actions │  │   AI    │             │    │
│  │  └─────────┘  └─────────┘  └─────────┘             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

1. **用户操作** → WebSocket 事件 → Flask 服务器
2. **Flask 服务器** → 游戏引擎执行步进
3. **游戏引擎** → 收集传感器数据 → AI 决策 → 执行动作
4. **状态更新** → WebSocket 广播 → 前端渲染

---

## 核心模块详解

### 1. 配置模块 (config.py)

存储所有游戏配置常量：

```python
class GameConfig:
    # 地图配置
    MAP_WIDTH = 14
    MAP_HEIGHT = 14
    
    # 坦克配置
    TANK_INITIAL_HEALTH = 1000
    TANK_INITIAL_ENERGY = 1000
    TANK_INITIAL_MISSILES = 20
    TANKS_PER_TEAM = 3
    
    # 伤害配置
    DAMAGE_FRONT = 200
    DAMAGE_SIDE = 300
    DAMAGE_BACK = 400
    
    # 导弹配置
    MISSILE_SPEED = 2
    MISSILE_BLIND_RANGE = 2
```

### 2. 地图模块 (map.py)

管理游戏地图和地形：

- `MapElement` 枚举：定义地图元素类型
- `GameMap` 类：地图管理，包括生成、查询、修改

```python
# 地图元素类型
class MapElement(Enum):
    OPEN = 'open'       # 空地
    TREE = 'tree'       # 树（障碍）
    STONE = 'stone'     # 石头（障碍）
    HEALTH = 'health'   # 维修厂
    ENERGY = 'energy'   # 能量站
    AMMO = 'ammo'       # 弹药箱
```

### 3. 坦克模块 (tank.py)

定义坦克实体和行为：

- `Direction` 枚举：四个方向
- `Tank` 类：坦克属性、伤害、恢复、移动

### 4. 传感器模块 (sensors.py)

实现各种传感器：

| 传感器 | 功能 | 能耗 | 阻挡 |
|--------|------|------|------|
| BlockedSensor | 感知四周阻挡 | 无 | - |
| IncomingSensor | 感知来袭导弹 | 无 | 有 |
| RadarSensor | 扇形区域探测 | 有 | 有 |
| RwaveSensor | 感知被雷达扫描 | 无 | - |
| SmellSensor | 感知最近坦克距离 | 无 | 无 |
| SoundSensor | 感知移动坦克方向 | 无 | 无 |
| VisualSensor | 近距离视觉 | 无 | 有 |

### 5. 动作模块 (actions.py)

定义和执行动作：

- `ActionType` 枚举：动作类型
- `Action` 类：动作创建
- `ActionExecutor` 类：动作执行

### 6. 游戏引擎 (engine.py)

核心仿真循环：

```python
def step(self):
    """单步仿真流程"""
    # 1. 处理补给站效果
    self._process_stations()
    
    # 2. 处理能量消耗
    self._process_energy_costs()
    
    # 3. 收集传感器数据，AI 决策
    tank_actions = {}
    for tank in self.tanks:
        if tank.is_alive():
            sensor_data = self._get_sensor_data(tank)
            action = self.ai_controllers[tank.id].decide(sensor_data, tank)
            tank_actions[tank.id] = action
    
    # 4. 执行动作
    for tank in self.tanks:
        if tank.is_alive():
            self._execute_action(tank, tank_actions[tank.id])
    
    # 5. 更新导弹
    self._update_missiles()
    
    # 6. 检查胜负
    self._check_game_over()
```

---

## 自定义 AI 开发

### 基本结构

创建新的 AI 类：

```python
# backend/game/my_ai.py

from game.actions import Action
from typing import Dict

class MyCustomAI:
    """自定义 AI 策略"""
    
    def __init__(self, tank_id: int, team: str):
        self.tank_id = tank_id
        self.team = team
        # 初始化状态变量
        self.state = 'patrol'
        self.target = None
    
    def decide(self, sensor_data: Dict, tank) -> Action:
        """
        每步调用的决策方法
        
        参数:
            sensor_data: 传感器数据
            tank: 坦克对象
        
        返回:
            Action 对象
        """
        # 解析传感器数据
        blocked = sensor_data['blocked']
        incoming = sensor_data['incoming']
        radar = sensor_data['radar']
        visual = sensor_data['visual']
        smell = sensor_data['smell']
        self_data = sensor_data['self']
        
        # 实现你的策略逻辑
        return self._make_decision(blocked, incoming, radar, visual, smell, self_data)
    
    def _make_decision(self, blocked, incoming, radar, visual, smell, self_data):
        """决策逻辑"""
        # 1. 优先躲避导弹
        if self._has_incoming(incoming):
            return self._evade(incoming, blocked)
        
        # 2. 检查视觉范围内的敌人
        enemy = self._find_enemy(visual, radar)
        if enemy:
            return self._engage(enemy, blocked, self_data)
        
        # 3. 巡逻搜索
        return self._patrol(blocked, smell)
    
    # ... 其他辅助方法
```

### 注册自定义 AI

在 `engine.py` 中注册：

```python
from game.my_ai import MyCustomAI

# 在 init_game 中修改 AI 分配
for tank in self.tanks:
    if tank.team == 'red':
        self.ai_controllers[tank.id] = MyCustomAI(tank.id, 'red')
    else:
        self.ai_controllers[tank.id] = MyCustomAI(tank.id, 'blue')
```

### AI 策略技巧

1. **优先级处理**
   - 最高：躲避导弹
   - 高：近距离交战
   - 中：追击敌人
   - 低：补给恢复
   - 最低：巡逻搜索

2. **传感器利用**
   - 视觉传感器不消耗能量，是发现近距离敌人的关键
   - 气味传感器可穿透障碍物，用于追踪
   - 声音传感器感知移动的敌人

3. **资源管理**
   - 合理控制雷达开关节省能量
   - 低血量时优先寻找维修站
   - 保留一定炮弹用于关键时刻

4. **避免被困**
   - 记录位置历史
   - 检测原地打转
   - 随机化移动打破僵局

---

## 测试指南

### 运行测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_tank.py

# 运行特定测试类
pytest tests/test_tank.py::TestTankDamage

# 运行特定测试方法
pytest tests/test_tank.py::TestTankDamage::test_front_damage

# 显示详细输出
pytest -v

# 显示代码覆盖率
pytest --cov=game --cov-report=html
```

### 测试标记

```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 跳过慢速测试
pytest -m "not slow"
```

### 编写测试

测试文件结构：

```python
# tests/test_my_module.py

import pytest
from game.my_module import MyClass

class TestMyClass:
    """测试类，以 Test 开头"""
    
    def test_feature_one(self):
        """测试方法，以 test_ 开头"""
        obj = MyClass()
        result = obj.do_something()
        assert result == expected_value
    
    def test_feature_two(self, red_tank):
        """使用 fixture"""
        # red_tank 由 conftest.py 提供
        assert red_tank.team == 'red'

# 使用 fixture
@pytest.fixture
def my_fixture():
    """创建测试数据"""
    return MyClass(param=value)
```

---

## 代码规范

### Python 代码风格

遵循 PEP 8 规范：

- 缩进使用 4 个空格
- 行长度不超过 100 字符
- 类名使用 CamelCase
- 函数/变量名使用 snake_case
- 常量使用 UPPER_SNAKE_CASE

### 注释规范

使用中文注释：

```python
class Tank:
    """
    坦克类
    
    管理坦克的属性、状态和行为。
    
    属性:
        id: 唯一标识符
        x, y: 位置坐标
        team: 阵营 ('red' / 'blue')
    """
    
    def move_forward(self) -> tuple:
        """
        获取向前移动后的位置
        
        返回:
            (x, y) 坐标元组
        """
        # 计算坐标增量
        dx, dy = self.direction.get_delta()
        return self.x + dx, self.y + dy
```

### Git 提交规范

提交信息格式：

```
<类型>: <简短描述>

<详细描述（可选）>
```

类型：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具

示例：
```
feat: 添加视觉传感器

- 实现 VisualSensor 类
- 支持 1-2 格近距离探测
- 不消耗能量，常开状态
```

---

## 常见问题

### Q: 如何调试 AI 策略？

A: 可以添加日志输出：

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MyAI:
    def decide(self, sensor_data, tank):
        logger.debug(f"坦克 {tank.id} 位置: ({tank.x}, {tank.y})")
        logger.debug(f"传感器数据: {sensor_data['blocked']}")
        # ...
```

### Q: 如何修改游戏配置？

A: 修改 `game/config.py` 中的常量：

```python
class GameConfig:
    MAP_WIDTH = 20  # 修改地图大小
    MAX_STEPS = 2000  # 修改最大步数
```

### Q: 如何添加新的地图元素？

A: 1. 在 `MapElement` 枚举中添加新类型
   2. 在 `GameMap` 中实现相关逻辑
   3. 在前端渲染器中添加对应图形

### Q: 测试运行失败怎么办？

A: 检查以下几点：
   1. 确保安装了测试依赖：`pip install pytest pytest-cov`
   2. 确保在 `backend` 目录下运行
   3. 检查 Python 版本是否为 3.11+

### Q: 如何贡献代码？

A: 1. Fork 项目
   2. 创建功能分支
   3. 编写代码和测试
   4. 提交 Pull Request

---

## 联系与支持

如有问题或建议，欢迎：
- 提交 Issue
- 发起 Pull Request
- 参与讨论
