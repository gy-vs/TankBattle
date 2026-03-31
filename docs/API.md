# TankBattle API 文档

本文档详细描述了 TankBattle 坦克对战仿真系统的所有接口，包括 WebSocket 事件、REST API 和内部模块 API。

---

## 目录

- [WebSocket API](#websocket-api)
- [REST API](#rest-api)
- [游戏引擎 API](#游戏引擎-api)
- [坦克 API](#坦克-api)
- [传感器 API](#传感器-api)
- [动作 API](#动作-api)
- [AI 接口](#ai-接口)

---

## WebSocket API

WebSocket 连接地址：`ws://localhost:8080/socket.io/`

### 客户端 → 服务器事件

#### `game:init`

初始化游戏，创建地图和坦克。

**请求参数：** 无

**响应：** 服务器广播 `game:state` 事件

**示例：**
```javascript
socket.emit('game:init');
```

---

#### `game:start`

开始游戏仿真。

**请求参数：** 无

**响应：** 服务器开始定时广播 `game:state` 事件

**示例：**
```javascript
socket.emit('game:start');
```

---

#### `game:pause`

暂停游戏仿真。

**请求参数：** 无

**响应：** 服务器停止定时广播

**示例：**
```javascript
socket.emit('game:pause');
```

---

#### `game:step`

执行单步仿真。

**请求参数：** 无

**响应：** 服务器执行一步仿真并广播 `game:state` 事件

**示例：**
```javascript
socket.emit('game:step');
```

---

#### `game:reset`

重置游戏到初始状态。

**请求参数：** 无

**响应：** 服务器重新初始化游戏并广播 `game:state` 事件

**示例：**
```javascript
socket.emit('game:reset');
```

---

### 服务器 → 客户端事件

#### `game:state`

游戏状态更新。

**数据结构：**
```typescript
interface GameState {
  clock: number;              // 当前时钟步数
  state: string;              // 游戏状态: 'waiting' | 'running' | 'paused' | 'finished'
  map: MapData;               // 地图数据
  tanks: TankData[];          // 所有坦克数据
  missiles: MissileData[];    // 所有导弹数据
  events: GameEvent[];        // 最近的游戏事件
  winner: string | null;      // 胜利方: 'red' | 'blue' | 'draw' | null
  fire_events: FireEvent[];   // 本步的开火特效事件
  hit_events: HitEvent[];     // 本步的命中特效事件
}
```

---

#### `game:over`

游戏结束通知。

**数据结构：**
```typescript
interface GameResult {
  winner: string;             // 'red' | 'blue' | 'draw'
  clock: number;              // 最终时钟步数
  red: TeamResult;            // 红方结果
  blue: TeamResult;           // 蓝方结果
}

interface TeamResult {
  alive: number;              // 存活坦克数
  total: number;              // 总坦克数
  avgHealth: number;          // 平均生命值
}
```

---

## REST API

> 💡 **在线 API 文档**：访问 `/api/docs` 可以查看交互式 Swagger UI 文档

### `GET /`

返回游戏主页面。

**响应：** HTML 页面

---

### `GET /api/docs`

Swagger UI 交互式 API 文档。

**响应：** Swagger UI 页面

---

### `GET /health`

健康检查接口。

**响应：**
```json
{
  "status": "ok",
  "service": "tankbattle"
}
```

---

### `GET /api/config`

获取游戏配置。

**响应：**
```json
{
  "mapWidth": 14,
  "mapHeight": 14,
  "tanksPerTeam": 3,
  "maxSteps": 1000,
  "tankInitialHealth": 1000,
  "tankInitialEnergy": 1000,
  "tankInitialMissiles": 20
}
```

---

## 游戏引擎 API

### `GameEngine` 类

游戏核心引擎，管理游戏状态和仿真逻辑。

#### 初始化

```python
from game.engine import GameEngine

engine = GameEngine()
```

#### 方法

##### `init_game(map_config=None)`

初始化游戏，创建地图和坦克。

**参数：**
- `map_config` (dict, 可选): 地图配置

**示例：**
```python
engine.init_game()
```

---

##### `start()`

开始游戏。

**示例：**
```python
engine.start()
```

---

##### `pause()`

暂停游戏。

**示例：**
```python
engine.pause()
```

---

##### `step()`

执行一步仿真。

**示例：**
```python
engine.step()
```

---

##### `get_state() -> dict`

获取完整游戏状态。

**返回值：** 包含所有游戏数据的字典

**示例：**
```python
state = engine.get_state()
print(f"当前步数: {state['clock']}")
print(f"存活坦克: {len([t for t in state['tanks'] if t['alive']])}")
```

---

##### `get_result() -> dict`

获取游戏结果。

**返回值：** 包含胜负信息的字典

**示例：**
```python
result = engine.get_result()
print(f"胜利方: {result['winner']}")
```

---

##### `is_game_over() -> bool`

检查游戏是否结束。

**返回值：** 布尔值

---

## 坦克 API

### `Tank` 类

坦克实体，管理坦克的属性和状态。

#### 初始化

```python
from game.tank import Tank, Direction

tank = Tank(x=5, y=5, team='red', direction=Direction.NORTH)
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | int | 唯一标识符 |
| `x` | int | X 坐标 |
| `y` | int | Y 坐标 |
| `direction` | Direction | 朝向 |
| `team` | str | 阵营 ('red' / 'blue') |
| `health` | int | 生命值 (0-1000) |
| `energy` | int | 能量值 (0-1000) |
| `missiles` | int | 炮弹数 |
| `shield_on` | bool | 护盾状态 |
| `radar_on` | bool | 雷达状态 |
| `radar_setting` | int | 雷达范围设置 (1-14) |
| `alive` | bool | 是否存活 |

#### 方法

##### `is_alive() -> bool`

检查坦克是否存活。

---

##### `take_damage(damage, from_direction)`

受到伤害。

**参数：**
- `damage` (int): 伤害值（实际伤害根据方向计算）
- `from_direction` (str): 伤害来源方向 ('front' / 'back' / 'left' / 'right')

---

##### `heal(amount=None)`

恢复生命值。

**参数：**
- `amount` (int, 可选): 恢复量，默认使用配置值

---

##### `recharge_energy(amount=None)`

恢复能量。

---

##### `add_missiles(amount=None)`

补充炮弹。

---

##### `move_forward() -> tuple`

获取向前移动后的位置坐标。

**返回值：** (x, y) 元组

---

##### `move_backward() -> tuple`

获取向后移动后的位置坐标。

---

##### `turn_left()`

左转 90 度。

---

##### `turn_right()`

右转 90 度。

---

##### `to_dict() -> dict`

序列化为字典。

---

### `Direction` 枚举

方向枚举类。

```python
from game.tank import Direction

Direction.NORTH  # 北（上）
Direction.SOUTH  # 南（下）
Direction.EAST   # 东（右）
Direction.WEST   # 西（左）
```

#### 方法

- `turn_left()` - 获取左转后的方向
- `turn_right()` - 获取右转后的方向
- `get_delta()` - 获取坐标增量 (dx, dy)
- `get_opposite()` - 获取相反方向

---

## 传感器 API

### 障碍传感器 (BlockedSensor)

感知四周是否被阻塞。

**调用：**
```python
from game.sensors import BlockedSensor

result = BlockedSensor.sense(tank, game_map, all_tanks)
```

**返回值：**
```python
{
    'forward': 'yes' | 'no',
    'backward': 'yes' | 'no',
    'left': 'yes' | 'no',
    'right': 'yes' | 'no'
}
```

---

### 导弹传感器 (IncomingSensor)

感知来袭导弹。

**调用：**
```python
from game.sensors import IncomingSensor

result = IncomingSensor.sense(tank, missiles, game_map, all_tanks)
```

**返回值：** 同障碍传感器格式

---

### 雷达传感器 (RadarSensor)

探测前方扇形区域。

**调用：**
```python
from game.sensors import RadarSensor

result = RadarSensor.sense(tank, game_map, all_tanks)
```

**返回值：**
```python
{
    'energy': [{'distance': int, 'position': str}, ...],
    'health': [...],
    'ammo': [...],
    'tree': [...],
    'stone': [...],
    'open': [...],
    'tank': [{'distance': int, 'position': str, 'color': str}, ...]
}
```

---

### 雷达波传感器 (RwaveSensor)

感知被雷达扫描。

**调用：**
```python
from game.sensors import RwaveSensor

result = RwaveSensor.sense(tank, all_tanks)
```

**返回值：**
```python
{
    'forward': 'red' | 'blue' | 'no',
    'backward': ...,
    'left': ...,
    'right': ...
}
```

---

### 气味传感器 (SmellSensor)

感知最近坦克的距离和阵营。

**调用：**
```python
from game.sensors import SmellSensor

result = SmellSensor.sense(tank, all_tanks)
```

**返回值：**
```python
{
    'color': 'red' | 'blue' | None,
    'distance': int | None  # 曼哈顿距离
}
```

---

### 声音传感器 (SoundSensor)

感知移动的坦克方向。

**调用：**
```python
from game.sensors import SoundSensor

result = SoundSensor.sense(tank, all_tanks, game_map)
```

**返回值：** `'silent' | 'forward' | 'backward' | 'left' | 'right'`

---

### 视觉传感器 (VisualSensor)

近距离（1-2格）识别坦克。

**调用：**
```python
from game.sensors import VisualSensor

result = VisualSensor.sense(tank, game_map, all_tanks)
```

**返回值：**
```python
[
    {'distance': int, 'position': str, 'color': str},
    ...
]
```

---

### 内部通信传感器 (CommunicationSensor)

同队坦克间的内部通信，获取友军坦克的完整状态信息。

**特点：**
- 只能获取同阵营坦克的信息
- 提供队友的位置、方向、生命、能量、弹药等完整状态
- 实现 Prompt 1.1 节提到的"双方坦克可进行内部通信"功能

**调用：**
```python
from game.sensors import CommunicationSensor

result = CommunicationSensor.sense(tank, all_tanks)
```

**返回值：**
```python
[
    {
        'id': int,                    # 队友坦克 ID
        'x': int,                     # X 坐标
        'y': int,                     # Y 坐标
        'direction': str,             # 朝向 ('north'/'south'/'east'/'west')
        'health': int,                # 生命值
        'energy': int,                # 能量值
        'missiles': int,              # 炮弹数
        'alive': bool,                # 是否存活
        'radar_on': bool,             # 雷达是否开启
        'shield_on': bool,            # 护盾是否开启
        'distance': int,              # 与本坦克的曼哈顿距离
        'relative_direction': str,    # 队友相对于本坦克的方向
        'radar_setting': int          # 队友的雷达设置
    },
    ...
]
```

**使用示例：**
```python
def decide(self, sensor_data, tank):
    teammates = sensor_data['communication']
    
    # 检查队友状态
    for mate in teammates:
        if mate['alive'] and mate['health'] < 300:
            # 队友血量较低，可以协调战术
            pass
        
        if mate['distance'] < 3:
            # 队友距离很近，避免堵塞
            pass
```

---

## 动作 API

### `Action` 类

动作创建类。

**创建动作：**
```python
from game.actions import Action

# 移动
Action.move('forward')      # 前进
Action.move('backward')     # 后退

# 转向
Action.turn('left')         # 左转
Action.turn('right')        # 右转

# 雷达
Action.radar('on')          # 开启雷达
Action.radar('off')         # 关闭雷达
Action.radar_power(10)      # 设置雷达范围

# 护盾
Action.shields('on')        # 开启护盾
Action.shields('off')       # 关闭护盾

# 开火
Action.fire()               # 发射导弹

# 空动作
Action.none()               # 不执行任何操作
```

---

### `ActionExecutor` 类

动作执行器。

**执行动作：**
```python
from game.actions import ActionExecutor

# 执行移动
success = ActionExecutor.execute_move(tank, game_map, all_tanks, 'forward')

# 执行转向
success = ActionExecutor.execute_turn(tank, 'left')

# 执行开火
missile = ActionExecutor.execute_fire(tank)  # 返回 Missile 或 None
```

---

## AI 接口

### 自定义 AI 类

实现自定义 AI 策略。

**基本结构：**
```python
from game.actions import Action

class MyCustomAI:
    def __init__(self, tank_id: int, team: str):
        """
        初始化 AI
        
        参数：
            tank_id: 控制的坦克 ID
            team: 所属阵营 ('red' / 'blue')
        """
        self.tank_id = tank_id
        self.team = team
    
    def decide(self, sensor_data: dict, tank) -> Action:
        """
        决策方法 - 每步调用一次
        
        参数：
            sensor_data: 传感器数据字典
            tank: 坦克对象
        
        返回：
            Action 对象
        """
        # 传感器数据结构
        blocked = sensor_data['blocked']    # 障碍传感器
        incoming = sensor_data['incoming']  # 导弹传感器
        radar = sensor_data['radar']        # 雷达数据
        rwave = sensor_data['rwave']        # 雷达波传感器
        smell = sensor_data['smell']        # 气味传感器
        sound = sensor_data['sound']        # 声音传感器
        visual = sensor_data['visual']      # 视觉传感器
        communication = sensor_data['communication']  # 内部通信（同队友军信息）
        self_data = sensor_data['self']     # 自身属性
        
        # 示例：简单的前进策略
        if blocked['forward'] == 'no':
            return Action.move('forward')
        else:
            return Action.turn('left')
```

### 传感器数据结构 (sensor_data)

**self (自身属性)：**
```python
{
    'clock': int,              # 当前时钟
    'direction': str,          # 朝向 ('north'/'south'/'east'/'west')
    'energy': int,             # 能量值
    'energyrecharger': str,    # 是否在能量站 ('yes'/'no')
    'health': int,             # 生命值
    'healthrecharger': str,    # 是否在维修站 ('yes'/'no')
    'missiles': int,           # 炮弹数
    'my_color': str,           # 阵营
    'radar_setting': int,      # 雷达设置
    'radar_distance': dict,    # 实际探测距离
    'radar_status': str,       # 雷达状态
    'shield_status': str,      # 护盾状态
    'x': int,                  # X 坐标
    'y': int,                  # Y 坐标
    'id': int                  # 坦克 ID
}
```

---

## 数据类型参考

### MapData

```typescript
interface MapData {
  width: number;
  height: number;
  grid: string[][];           // 二维数组，元素类型
  ammoPositions: [number, number][];
}
```

### TankData

```typescript
interface TankData {
  id: number;
  x: number;
  y: number;
  direction: string;
  team: string;
  health: number;
  energy: number;
  missiles: number;
  shieldOn: boolean;
  radarOn: boolean;
  radarSetting: number;
  radarDistance: { left: number, center: number, right: number };
  alive: boolean;
}
```

### MissileData

```typescript
interface MissileData {
  id: number;
  x: number;
  y: number;
  direction: string;
  ownerTeam: string;
  active: boolean;
}
```

---

## 错误处理

所有 API 调用在出错时会抛出相应异常：

| 异常类型 | 说明 |
|----------|------|
| `ValueError` | 参数值无效 |
| `IndexError` | 索引越界 |
| `RuntimeError` | 运行时错误 |

建议使用 try-except 包装 API 调用：

```python
try:
    engine.step()
except Exception as e:
    print(f"执行出错: {e}")
```
