# 🎮 TankBattle - 坦克对战仿真环境

## 📖 项目简介

TankBattle 是一个基于 Python 的坦克对战仿真环境，支持红蓝双方各 3 辆坦克在 14×14 网格地图上进行回合制战斗。系统提供完整的传感器系统、动作系统和 AI 接口，可用于策略算法的开发和测试。

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

# 一键启动
docker compose up --build

# 访问
# http://localhost:8080
```

### 方式二：本地运行

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py

# 访问 http://localhost:8080
```

### ✨ 特性

- 🎯 **完整仿真逻辑** - 6 种传感器、6 种动作、导弹系统
- 🎨 **赛博朋克 UI** - 霓虹光效、粒子特效、动态动画
- 🤖 **AI 接口** - 支持自定义策略算法
- 🐳 **Docker 部署** - 一键启动，开箱即用
- ⚡ **实时可视化** - WebSocket 实时同步战场状态

---

## 🎮 游戏规则

### 胜负判定

| 条件 | 结果 |
|------|------|
| 敌方坦克全部阵亡 | 己方胜利 |
| 达到最大步数，己方坦克数 > 敌方 | 己方胜利 |
| 达到最大步数，坦克数相等，己方平均HP > 敌方 | 己方胜利 |
| 达到最大步数，坦克数和平均HP都相等 | 平局 |

### 坦克属性

| 属性 | 初始值 | 最大值 | 说明 |
|------|--------|--------|------|
| 生命值 (HP) | 1000 | 1000 | 归零时坦克被击毁 |
| 能量值 (EP) | 1000 | 1000 | 用于雷达和护盾 |
| 炮弹数 | 20 | 20 | 每次攻击消耗 1 枚 |

### 伤害规则

| 攻击方向 | 伤害值 |
|----------|--------|
| 前方 | 200 |
| 侧方 | 300 |
| 后方 | 400 |

> ⚠️ **注意**：在维修站或能量站被攻击，生命值直接归零！

---

## 🔧 传感器系统

| 传感器 | 功能 | 特性 |
|--------|------|------|
| **障碍传感器** | 感知四周是否被阻挡 | 常开，无法区分障碍物和坦克 |
| **导弹传感器** | 感知来袭导弹 | 常开，2格内盲区 |
| **雷达** | 探测前方扇形区域 | 消耗能量，可设置范围 |
| **雷达波传感器** | 感知被雷达扫描 | 常开，返回扫描方阵营 |
| **气味传感器** | 感知最近坦克 | 最大距离 28 格，可穿透障碍 |
| **声音传感器** | 感知移动坦克 | 最大距离 7 格，返回最短路径方向 |

---

## 🎬 动作系统

| 动作 | 参数 | 说明 |
|------|------|------|
| `AMove` | forward/backward | 移动一格 |
| `ATurn` | left/right | 转向 90° |
| `ARadar` | on/off | 开关雷达 |
| `ARadarPowerSet` | 1-13 | 设置雷达范围 |
| `AShields` | on/off | 开关护盾 |
| `AFire` | - | 发射导弹 |

---

## 📁 项目结构

```
tankbattle/
├── docker-compose.yml      # Docker 编排配置
├── README.md               # 项目说明
├── backend/
│   ├── app.py              # Flask 应用入口
│   ├── Dockerfile          # Docker 镜像定义
│   ├── requirements.txt    # Python 依赖
│   ├── game/               # 游戏核心模块
│   │   ├── config.py       # 游戏配置
│   │   ├── map.py          # 地图系统
│   │   ├── tank.py         # 坦克实体
│   │   ├── missile.py      # 导弹系统
│   │   ├── sensors.py      # 传感器系统
│   │   ├── actions.py      # 动作系统
│   │   ├── engine.py       # 游戏引擎
│   │   └── ai.py           # AI 策略
│   ├── templates/          # HTML 模板
│   └── static/             # 静态资源
│       ├── css/            # 样式表
│       └── js/             # JavaScript
└── docs/
    ├── Requirements.md     # 需求规格
    ├── Roadmap.md          # 开发路线图
    └── DesignSpec.md       # 设计规范
```

---

## 🤖 自定义 AI

在 `backend/game/ai.py` 中实现自定义策略：

```python
class MyAI:
    def __init__(self, tank_id: int, team: str):
        self.tank_id = tank_id
        self.team = team
    
    def decide(self, sensor_data: dict, tank) -> Action:
        """
        根据传感器数据决定动作
        
        sensor_data 包含:
        - blocked: 障碍传感器数据
        - incoming: 导弹传感器数据
        - radar: 雷达数据
        - rwave: 雷达波传感器数据
        - smell: 气味传感器数据
        - sound: 声音传感器数据
        - self: 坦克自身属性
        """
        # 你的策略逻辑
        return Action.move('forward')
```

---

## 📊 API 接口

### WebSocket 事件

| 事件 | 方向 | 说明 |
|------|------|------|
| `game:init` | Client → Server | 初始化游戏 |
| `game:start` | Client → Server | 开始游戏 |
| `game:pause` | Client → Server | 暂停游戏 |
| `game:step` | Client → Server | 执行一步 |
| `game:reset` | Client → Server | 重置游戏 |
| `game:state` | Server → Client | 游戏状态更新 |
| `game:over` | Server → Client | 游戏结束 |

### REST API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 游戏页面 |
| `/health` | GET | 健康检查 |
| `/api/config` | GET | 获取游戏配置 |

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | Flask 3.0 |
| 实时通信 | Flask-SocketIO |
| 前端渲染 | HTML5 Canvas |
| 容器化 | Docker |

---

## 🧪 测试

项目包含完整的测试套件，覆盖核心游戏逻辑：

```bash
cd backend

# 安装测试依赖
pip install pytest pytest-cov

# 运行所有测试
pytest

# 运行并显示详细输出
pytest -v

# 生成覆盖率报告
pytest --cov=game --cov-report=html
```

### 测试覆盖

| 模块 | 测试文件 | 说明 |
|------|----------|------|
| 坦克系统 | `test_tank.py` | 属性、伤害、移动、资源消耗 |
| 地图系统 | `test_map.py` | 地图生成、元素访问、补给站 |
| 导弹系统 | `test_missile.py` | 创建、移动、路径计算 |
| 传感器系统 | `test_sensors.py` | 6种传感器功能验证 |
| 动作系统 | `test_actions.py` | 动作创建和执行 |
| 游戏引擎 | `test_engine.py` | 集成测试、胜负判定 |

---

## 📚 文档

详细文档位于 `docs/` 目录：

- [**Requirements.md**](docs/Requirements.md) - 需求规格说明书
- [**API.md**](docs/API.md) - 完整 API 文档
- [**DeveloperGuide.md**](docs/DeveloperGuide.md) - 开发者指南
- [**DesignSpec.md**](docs/DesignSpec.md) - 设计规范
- [**Roadmap.md**](docs/Roadmap.md) - 开发路线图

---

## 📝 许可证

MIT License

---

## 🙏 致谢

- 设计灵感：赛博朋克 2077、EVE Online
- 字体：Orbitron、JetBrains Mono
