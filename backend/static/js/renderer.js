/**
 * TankBattle 赛博朋克风格渲染器
 * 使用 Canvas 渲染游戏画面，带霓虹光效和粒子特效
 */

class GameRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // 网格配置
        this.gridSize = 14;
        this.cellSize = this.canvas.width / this.gridSize;
        
        // 赛博朋克配色
        this.colors = {
            // 背景
            background: '#0a0e17',
            gridLine: 'rgba(30, 58, 95, 0.5)',
            gridGlow: 'rgba(0, 212, 255, 0.1)',
            
            // 地形
            open: '#1a2030',
            tree: '#00ff88',
            stone: '#6b7280',
            health: '#ff3366',
            energy: '#ff9500',
            ammo: '#bf5fff',
            
            // 坦克
            tankRed: '#ff3366',
            tankRedDark: '#cc0044',
            tankBlue: '#00d4ff',
            tankBlueDark: '#0099cc',
            
            // 导弹
            missile: '#ffd700',
            missileTrail: '#ff9500',
            
            // 特效
            shield: 'rgba(0, 212, 255, 0.3)',
            radar: 'rgba(0, 255, 136, 0.1)',
            explosion: '#ff9500',
            muzzleFlash: '#ffff00'
        };
        
        // 动画状态
        this.explosions = [];
        this.particles = [];
        this.time = 0;
        this.missileTrails = [];  // 导弹尾迹
        this.muzzleFlashes = [];  // 开火闪光
        this.hitSparks = [];      // 命中火花
        this.smokeParticles = []; // 烟雾
        
        // 开始动画循环
        this.animate();
    }
    
    /**
     * 动画循环
     */
    animate() {
        this.time += 0.02;
        requestAnimationFrame(() => this.animate());
    }
    
    /**
     * 清空画布并绘制背景
     */
    clear() {
        // 深色背景
        this.ctx.fillStyle = this.colors.background;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 添加微弱的渐变效果
        const gradient = this.ctx.createRadialGradient(
            this.canvas.width / 2, this.canvas.height / 2, 0,
            this.canvas.width / 2, this.canvas.height / 2, this.canvas.width
        );
        gradient.addColorStop(0, 'rgba(0, 212, 255, 0.03)');
        gradient.addColorStop(1, 'transparent');
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    /**
     * 绘制科技感网格
     */
    drawGrid() {
        const ctx = this.ctx;
        
        // 绘制发光网格线
        ctx.strokeStyle = this.colors.gridLine;
        ctx.lineWidth = 1;
        
        for (let i = 0; i <= this.gridSize; i++) {
            const pos = i * this.cellSize;
            
            // 主网格线
            ctx.beginPath();
            ctx.moveTo(pos, 0);
            ctx.lineTo(pos, this.canvas.height);
            ctx.stroke();
            
            ctx.beginPath();
            ctx.moveTo(0, pos);
            ctx.lineTo(this.canvas.width, pos);
            ctx.stroke();
        }
        
        // 添加脉冲扫描线效果
        const scanY = (Math.sin(this.time) * 0.5 + 0.5) * this.canvas.height;
        const scanGradient = ctx.createLinearGradient(0, scanY - 20, 0, scanY + 20);
        scanGradient.addColorStop(0, 'transparent');
        scanGradient.addColorStop(0.5, 'rgba(0, 212, 255, 0.1)');
        scanGradient.addColorStop(1, 'transparent');
        ctx.fillStyle = scanGradient;
        ctx.fillRect(0, scanY - 20, this.canvas.width, 40);
    }
    
    /**
     * 绘制地图元素
     */
    drawMap(mapData) {
        if (!mapData || !mapData.grid) return;
        
        const grid = mapData.grid;
        
        for (let y = 0; y < grid.length; y++) {
            for (let x = 0; x < grid[y].length; x++) {
                const element = grid[y][x];
                this.drawCell(x, y, element);
            }
        }
        
        // 绘制弹药箱
        if (mapData.ammoPositions) {
            for (const [ax, ay] of mapData.ammoPositions) {
                this.drawCell(ax, ay, 'ammo');
            }
        }
    }
    
    /**
     * 绘制单个格子（带发光效果）
     */
    drawCell(x, y, type) {
        const ctx = this.ctx;
        const px = x * this.cellSize;
        const py = y * this.cellSize;
        const cx = px + this.cellSize / 2;
        const cy = py + this.cellSize / 2;
        const padding = 3;
        const size = this.cellSize - padding * 2;
        
        switch (type) {
            case 'tree':
                this.drawTree(cx, cy, size);
                break;
                
            case 'stone':
                this.drawStone(px + padding, py + padding, size);
                break;
                
            case 'health':
                this.drawHealthStation(cx, cy, size);
                break;
                
            case 'energy':
                this.drawEnergyStation(cx, cy, size);
                break;
                
            case 'ammo':
                this.drawAmmoBox(cx, cy, size);
                break;
                
            default:
                // 空地 - 不绘制
                break;
        }
    }
    
    /**
     * 绘制树木图标（松树形状）
     */
    drawTree(cx, cy, size) {
        const ctx = this.ctx;
        const scale = size / 40;
        
        // 发光效果
        ctx.shadowBlur = 12;
        ctx.shadowColor = this.colors.tree;
        
        // 树干
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(cx - 3 * scale, cy + 8 * scale, 6 * scale, 10 * scale);
        
        // 树冠 - 三层三角形（松树形状）
        const treeGradient = ctx.createLinearGradient(cx, cy - 18 * scale, cx, cy + 10 * scale);
        treeGradient.addColorStop(0, '#00ff88');
        treeGradient.addColorStop(0.5, '#00dd66');
        treeGradient.addColorStop(1, '#00aa44');
        ctx.fillStyle = treeGradient;
        
        // 顶层
        ctx.beginPath();
        ctx.moveTo(cx, cy - 16 * scale);
        ctx.lineTo(cx - 8 * scale, cy - 4 * scale);
        ctx.lineTo(cx + 8 * scale, cy - 4 * scale);
        ctx.closePath();
        ctx.fill();
        
        // 中层
        ctx.beginPath();
        ctx.moveTo(cx, cy - 10 * scale);
        ctx.lineTo(cx - 11 * scale, cy + 4 * scale);
        ctx.lineTo(cx + 11 * scale, cy + 4 * scale);
        ctx.closePath();
        ctx.fill();
        
        // 底层
        ctx.beginPath();
        ctx.moveTo(cx, cy - 3 * scale);
        ctx.lineTo(cx - 14 * scale, cy + 12 * scale);
        ctx.lineTo(cx + 14 * scale, cy + 12 * scale);
        ctx.closePath();
        ctx.fill();
        
        // 树顶高光
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.beginPath();
        ctx.moveTo(cx, cy - 16 * scale);
        ctx.lineTo(cx - 4 * scale, cy - 8 * scale);
        ctx.lineTo(cx + 2 * scale, cy - 8 * scale);
        ctx.closePath();
        ctx.fill();
        
        ctx.shadowBlur = 0;
    }
    
    /**
     * 绘制岩石图标（山石形状）
     */
    drawStone(x, y, size) {
        const ctx = this.ctx;
        const cx = x + size / 2;
        const cy = y + size / 2;
        const scale = size / 40;
        
        // 阴影
        ctx.shadowBlur = 8;
        ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
        
        // 主岩石 - 不规则多边形
        const stoneGradient = ctx.createLinearGradient(cx - 15 * scale, cy - 15 * scale, cx + 15 * scale, cy + 15 * scale);
        stoneGradient.addColorStop(0, '#9ca3af');
        stoneGradient.addColorStop(0.3, '#6b7280');
        stoneGradient.addColorStop(0.7, '#4b5563');
        stoneGradient.addColorStop(1, '#374151');
        ctx.fillStyle = stoneGradient;
        
        ctx.beginPath();
        ctx.moveTo(cx - 2 * scale, cy - 14 * scale);
        ctx.lineTo(cx + 10 * scale, cy - 10 * scale);
        ctx.lineTo(cx + 14 * scale, cy - 2 * scale);
        ctx.lineTo(cx + 12 * scale, cy + 10 * scale);
        ctx.lineTo(cx + 4 * scale, cy + 14 * scale);
        ctx.lineTo(cx - 8 * scale, cy + 12 * scale);
        ctx.lineTo(cx - 14 * scale, cy + 4 * scale);
        ctx.lineTo(cx - 12 * scale, cy - 8 * scale);
        ctx.closePath();
        ctx.fill();
        
        ctx.shadowBlur = 0;
        
        // 岩石裂纹
        ctx.strokeStyle = 'rgba(55, 65, 81, 0.8)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(cx - 8 * scale, cy - 6 * scale);
        ctx.lineTo(cx - 2 * scale, cy + 2 * scale);
        ctx.lineTo(cx + 6 * scale, cy - 4 * scale);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.moveTo(cx + 2 * scale, cy + 4 * scale);
        ctx.lineTo(cx + 8 * scale, cy + 8 * scale);
        ctx.stroke();
        
        // 高光
        ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.beginPath();
        ctx.moveTo(cx - 2 * scale, cy - 14 * scale);
        ctx.lineTo(cx + 6 * scale, cy - 11 * scale);
        ctx.lineTo(cx - 4 * scale, cy - 4 * scale);
        ctx.lineTo(cx - 10 * scale, cy - 6 * scale);
        ctx.closePath();
        ctx.fill();
    }
    
    /**
     * 绘制维修站图标（扳手+齿轮）
     */
    drawHealthStation(cx, cy, size) {
        const ctx = this.ctx;
        const scale = size / 40;
        
        // 发光底座
        ctx.shadowBlur = 15;
        ctx.shadowColor = this.colors.health;
        
        // 底座圆盘
        const baseGradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 16 * scale);
        baseGradient.addColorStop(0, 'rgba(255, 51, 102, 0.4)');
        baseGradient.addColorStop(1, 'rgba(255, 51, 102, 0.1)');
        ctx.fillStyle = baseGradient;
        ctx.beginPath();
        ctx.arc(cx, cy, 16 * scale, 0, Math.PI * 2);
        ctx.fill();
        
        // 旋转的齿轮
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(this.time * 0.5);
        
        // 齿轮主体
        ctx.fillStyle = '#ff3366';
        ctx.beginPath();
        ctx.arc(0, 0, 10 * scale, 0, Math.PI * 2);
        ctx.fill();
        
        // 齿轮齿
        for (let i = 0; i < 8; i++) {
            ctx.save();
            ctx.rotate(i * Math.PI / 4);
            ctx.fillRect(-2 * scale, -14 * scale, 4 * scale, 6 * scale);
            ctx.restore();
        }
        
        // 齿轮中心孔
        ctx.fillStyle = '#1a2030';
        ctx.beginPath();
        ctx.arc(0, 0, 4 * scale, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
        
        // 扳手图标
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(-this.time * 0.3);
        
        ctx.fillStyle = '#ffcc00';
        ctx.strokeStyle = '#cc9900';
        ctx.lineWidth = 1;
        
        // 扳手柄
        ctx.fillRect(-2 * scale, -2 * scale, 14 * scale, 4 * scale);
        
        // 扳手头
        ctx.beginPath();
        ctx.arc(-6 * scale, 0, 6 * scale, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#1a2030';
        ctx.beginPath();
        ctx.arc(-6 * scale, 0, 3 * scale, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
        
        // 红十字标志（小）
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(cx - 1.5 * scale, cy - 5 * scale, 3 * scale, 10 * scale);
        ctx.fillRect(cx - 5 * scale, cy - 1.5 * scale, 10 * scale, 3 * scale);
        
        ctx.shadowBlur = 0;
    }
    
    /**
     * 绘制能量站图标（电池+闪电）
     */
    drawEnergyStation(cx, cy, size) {
        const ctx = this.ctx;
        const scale = size / 40;
        
        // 发光效果
        ctx.shadowBlur = 18;
        ctx.shadowColor = this.colors.energy;
        
        // 电池外壳
        const batteryGradient = ctx.createLinearGradient(cx - 10 * scale, cy, cx + 10 * scale, cy);
        batteryGradient.addColorStop(0, '#4a5568');
        batteryGradient.addColorStop(0.5, '#718096');
        batteryGradient.addColorStop(1, '#4a5568');
        ctx.fillStyle = batteryGradient;
        
        // 电池主体
        ctx.beginPath();
        ctx.roundRect(cx - 10 * scale, cy - 14 * scale, 20 * scale, 28 * scale, 3 * scale);
        ctx.fill();
        
        // 电池正极
        ctx.fillStyle = '#718096';
        ctx.beginPath();
        ctx.roundRect(cx - 4 * scale, cy - 17 * scale, 8 * scale, 4 * scale, 1 * scale);
        ctx.fill();
        
        // 电量填充（动画）
        const fillLevel = 0.6 + Math.sin(this.time * 2) * 0.2;
        const fillHeight = 22 * scale * fillLevel;
        const energyGradient = ctx.createLinearGradient(cx, cy + 12 * scale, cx, cy + 12 * scale - fillHeight);
        energyGradient.addColorStop(0, '#ff6600');
        energyGradient.addColorStop(0.5, '#ffaa00');
        energyGradient.addColorStop(1, '#ffcc00');
        ctx.fillStyle = energyGradient;
        ctx.beginPath();
        ctx.roundRect(cx - 7 * scale, cy + 12 * scale - fillHeight, 14 * scale, fillHeight, 2 * scale);
        ctx.fill();
        
        // 闪电图标
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.moveTo(cx + 3 * scale, cy - 8 * scale);
        ctx.lineTo(cx - 4 * scale, cy + 2 * scale);
        ctx.lineTo(cx + 1 * scale, cy + 2 * scale);
        ctx.lineTo(cx - 3 * scale, cy + 10 * scale);
        ctx.lineTo(cx + 5 * scale, cy - 1 * scale);
        ctx.lineTo(cx, cy - 1 * scale);
        ctx.closePath();
        ctx.fill();
        
        // 电弧动画
        if (Math.random() > 0.6) {
            ctx.strokeStyle = '#ffff00';
            ctx.lineWidth = 2;
            ctx.beginPath();
            const startAngle = Math.random() * Math.PI * 2;
            const arcLength = 0.3 + Math.random() * 0.4;
            ctx.arc(cx, cy, 18 * scale, startAngle, startAngle + arcLength);
            ctx.stroke();
            
            // 小火花
            for (let i = 0; i < 3; i++) {
                const sparkAngle = startAngle + Math.random() * arcLength;
                const sparkDist = 18 * scale + Math.random() * 5;
                ctx.fillStyle = `rgba(255, 255, 0, ${0.5 + Math.random() * 0.5})`;
                ctx.beginPath();
                ctx.arc(
                    cx + Math.cos(sparkAngle) * sparkDist,
                    cy + Math.sin(sparkAngle) * sparkDist,
                    1 + Math.random() * 2, 0, Math.PI * 2
                );
                ctx.fill();
            }
        }
        
        ctx.shadowBlur = 0;
    }
    
    /**
     * 绘制弹药箱图标（军用弹药箱）
     */
    drawAmmoBox(cx, cy, size) {
        const ctx = this.ctx;
        const scale = size / 40;
        
        // 浮动效果
        const floatY = Math.sin(this.time * 2) * 2;
        cy += floatY;
        
        // 发光效果
        ctx.shadowBlur = 12;
        ctx.shadowColor = this.colors.ammo;
        
        // 弹药箱主体 - 3D效果
        // 箱子顶部
        ctx.fillStyle = '#9933ff';
        ctx.beginPath();
        ctx.moveTo(cx - 14 * scale, cy - 8 * scale);
        ctx.lineTo(cx - 10 * scale, cy - 14 * scale);
        ctx.lineTo(cx + 14 * scale, cy - 14 * scale);
        ctx.lineTo(cx + 14 * scale, cy - 8 * scale);
        ctx.closePath();
        ctx.fill();
        
        // 箱子正面
        const frontGradient = ctx.createLinearGradient(cx, cy - 8 * scale, cx, cy + 12 * scale);
        frontGradient.addColorStop(0, '#bf5fff');
        frontGradient.addColorStop(1, '#8b2fd0');
        ctx.fillStyle = frontGradient;
        ctx.fillRect(cx - 14 * scale, cy - 8 * scale, 28 * scale, 20 * scale);
        
        // 箱子侧面
        ctx.fillStyle = '#7722bb';
        ctx.beginPath();
        ctx.moveTo(cx + 14 * scale, cy - 8 * scale);
        ctx.lineTo(cx + 14 * scale, cy + 12 * scale);
        ctx.lineTo(cx + 18 * scale, cy + 8 * scale);
        ctx.lineTo(cx + 18 * scale, cy - 10 * scale);
        ctx.closePath();
        ctx.fill();
        
        // 顶部侧面
        ctx.fillStyle = '#aa44ee';
        ctx.beginPath();
        ctx.moveTo(cx + 14 * scale, cy - 14 * scale);
        ctx.lineTo(cx + 18 * scale, cy - 10 * scale);
        ctx.lineTo(cx + 18 * scale, cy - 10 * scale);
        ctx.lineTo(cx + 14 * scale, cy - 8 * scale);
        ctx.closePath();
        ctx.fill();
        
        // 金属边框
        ctx.strokeStyle = '#ffcc00';
        ctx.lineWidth = 2 * scale;
        ctx.strokeRect(cx - 13 * scale, cy - 7 * scale, 26 * scale, 18 * scale);
        
        // 锁扣
        ctx.fillStyle = '#ffcc00';
        ctx.fillRect(cx - 4 * scale, cy - 10 * scale, 8 * scale, 4 * scale);
        ctx.fillStyle = '#1a1a1a';
        ctx.beginPath();
        ctx.arc(cx, cy - 8 * scale, 2 * scale, 0, Math.PI * 2);
        ctx.fill();
        
        // 弹药标志（三颗子弹）
        ctx.fillStyle = '#ffcc00';
        for (let i = -1; i <= 1; i++) {
            const bx = cx + i * 6 * scale;
            const by = cy + 2 * scale;
            // 弹壳
            ctx.fillStyle = '#ffcc00';
            ctx.beginPath();
            ctx.roundRect(bx - 2 * scale, by - 4 * scale, 4 * scale, 10 * scale, 1 * scale);
            ctx.fill();
            // 弹头
            ctx.fillStyle = '#cc8800';
            ctx.beginPath();
            ctx.arc(bx, by - 4 * scale, 2 * scale, Math.PI, 0);
            ctx.fill();
        }
        
        // 危险标志
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.font = `bold ${8 * scale}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('!', cx - 10 * scale, cy + 2 * scale);
        
        ctx.shadowBlur = 0;
    }
    
    /**
     * 绘制所有坦克
     */
    drawTanks(tanks) {
        if (!tanks) return;
        
        for (const tank of tanks) {
            if (!tank.alive) continue;
            this.drawTank(tank);
        }
    }
    
    /**
     * 绘制单个坦克（带霓虹边缘）
     */
    drawTank(tank) {
        const ctx = this.ctx;
        const px = tank.x * this.cellSize + this.cellSize / 2;
        const py = tank.y * this.cellSize + this.cellSize / 2;
        const size = this.cellSize * 0.7;
        
        ctx.save();
        ctx.translate(px, py);
        
        // 根据方向旋转
        const rotations = {
            'north': 0,
            'east': Math.PI / 2,
            'south': Math.PI,
            'west': -Math.PI / 2
        };
        ctx.rotate(rotations[tank.direction] || 0);
        
        // 绘制雷达范围
        if (tank.radarOn) {
            this.drawRadarRange(tank.radarSetting);
        }
        
        // 绘制护盾
        if (tank.shieldOn) {
            this.drawShield(size);
        }
        
        // 坦克颜色
        const isRed = tank.team === 'red';
        const mainColor = isRed ? this.colors.tankRed : this.colors.tankBlue;
        const darkColor = isRed ? this.colors.tankRedDark : this.colors.tankBlueDark;
        
        // 发光效果
        ctx.shadowBlur = 15;
        ctx.shadowColor = mainColor;
        
        // 坦克主体
        const bodyGradient = ctx.createLinearGradient(-size / 2, 0, size / 2, 0);
        bodyGradient.addColorStop(0, darkColor);
        bodyGradient.addColorStop(0.5, mainColor);
        bodyGradient.addColorStop(1, darkColor);
        ctx.fillStyle = bodyGradient;
        
        // 履带
        ctx.fillRect(-size / 2, -size / 2 + 2, size / 5, size - 4);
        ctx.fillRect(size / 2 - size / 5, -size / 2 + 2, size / 5, size - 4);
        
        // 车身
        ctx.fillStyle = 'rgba(20, 30, 50, 0.9)';
        ctx.fillRect(-size / 2 + size / 5, -size / 2 + 4, size - size / 2.5, size - 8);
        
        // 炮塔
        const turretGradient = ctx.createRadialGradient(0, 0, 0, 0, 0, size / 3);
        turretGradient.addColorStop(0, mainColor);
        turretGradient.addColorStop(1, darkColor);
        ctx.fillStyle = turretGradient;
        ctx.beginPath();
        ctx.arc(0, 0, size / 3.5, 0, Math.PI * 2);
        ctx.fill();
        
        // 炮管
        ctx.fillStyle = mainColor;
        ctx.fillRect(-3, -size / 2 - 6, 6, size / 2 + 2);
        
        // 炮口发光
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.beginPath();
        ctx.arc(0, -size / 2 - 6, 3, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.shadowBlur = 0;
        
        // 坦克ID
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 11px "Orbitron", sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(tank.id.toString(), 0, 0);
        
        ctx.restore();
    }
    
    /**
     * 绘制雷达范围
     */
    drawRadarRange(radarSetting) {
        const ctx = this.ctx;
        const radarDist = radarSetting * this.cellSize;
        
        // 扇形雷达区域
        const gradient = ctx.createLinearGradient(0, 0, 0, -radarDist);
        gradient.addColorStop(0, 'rgba(0, 255, 136, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 255, 136, 0.02)');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(-this.cellSize * 1.5, -radarDist);
        ctx.lineTo(this.cellSize * 1.5, -radarDist);
        ctx.closePath();
        ctx.fill();
        
        // 扫描线
        ctx.save();
        ctx.rotate(Math.sin(this.time * 3) * 0.3);
        ctx.strokeStyle = 'rgba(0, 255, 136, 0.5)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -radarDist);
        ctx.stroke();
        ctx.restore();
    }
    
    /**
     * 绘制护盾
     */
    drawShield(size) {
        const ctx = this.ctx;
        const radius = size * 0.75;
        
        // 护盾脉冲效果
        const pulse = Math.sin(this.time * 4) * 0.2 + 0.8;
        
        // 外圈
        ctx.strokeStyle = `rgba(0, 212, 255, ${0.6 * pulse})`;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(0, 0, radius, 0, Math.PI * 2);
        ctx.stroke();
        
        // 内部填充
        ctx.fillStyle = `rgba(0, 212, 255, ${0.15 * pulse})`;
        ctx.beginPath();
        ctx.arc(0, 0, radius - 2, 0, Math.PI * 2);
        ctx.fill();
        
        // 六边形能量场
        ctx.strokeStyle = `rgba(0, 212, 255, ${0.3 * pulse})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const angle = (i / 6) * Math.PI * 2 + this.time;
            const x = Math.cos(angle) * radius * 0.8;
            const y = Math.sin(angle) * radius * 0.8;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.stroke();
    }
    
    /**
     * 绘制导弹
     */
    drawMissiles(missiles) {
        if (!missiles) return;
        
        for (const missile of missiles) {
            if (!missile.active) continue;
            this.drawMissile(missile);
        }
    }
    
    /**
     * 绘制单个导弹（带尾焰）
     */
    drawMissile(missile) {
        const ctx = this.ctx;
        const px = missile.x * this.cellSize + this.cellSize / 2;
        const py = missile.y * this.cellSize + this.cellSize / 2;
        const size = 12;
        
        // 添加尾迹
        this.addMissileTrail(missile.x, missile.y);
        
        ctx.save();
        ctx.translate(px, py);
        
        // 根据方向旋转
        const rotations = {
            'north': 0,
            'east': Math.PI / 2,
            'south': Math.PI,
            'west': -Math.PI / 2
        };
        ctx.rotate(rotations[missile.direction] || 0);
        
        // 发光效果
        ctx.shadowBlur = 25;
        ctx.shadowColor = this.colors.missile;
        
        // 动态尾焰粒子
        const flameIntensity = Math.sin(this.time * 10) * 0.3 + 0.7;
        for (let i = 0; i < 8; i++) {
            const offset = i * 3 + Math.random() * 4;
            const alpha = (1 - i * 0.12) * flameIntensity;
            const flameSize = (4 - i * 0.3) * (0.8 + Math.random() * 0.4);
            
            // 火焰核心（白-黄-橙渐变）
            const colorIdx = i / 8;
            let r = 255, g = Math.floor(255 - colorIdx * 100), b = Math.floor(colorIdx < 0.3 ? 255 - colorIdx * 500 : 0);
            
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.8})`;
            ctx.beginPath();
            ctx.arc(
                (Math.random() - 0.5) * 5,
                size / 2 + offset,
                flameSize,
                0, Math.PI * 2
            );
            ctx.fill();
        }
        
        // 导弹主体 - 更精细的设计
        const gradient = ctx.createLinearGradient(0, -size, 0, size / 2);
        gradient.addColorStop(0, '#ffffff');
        gradient.addColorStop(0.2, '#ffffaa');
        gradient.addColorStop(0.5, this.colors.missile);
        gradient.addColorStop(1, this.colors.missileTrail);
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.moveTo(0, -size);
        ctx.lineTo(size / 2, size / 3);
        ctx.lineTo(size / 4, size / 2);
        ctx.lineTo(0, size / 2 + 2);
        ctx.lineTo(-size / 4, size / 2);
        ctx.lineTo(-size / 2, size / 3);
        ctx.closePath();
        ctx.fill();
        
        // 导弹头部高光
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.beginPath();
        ctx.arc(0, -size + 3, 2, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.shadowBlur = 0;
        ctx.restore();
    }
    
    /**
     * 添加爆炸效果
     */
    addExplosion(x, y) {
        this.explosions.push({
            x: x * this.cellSize + this.cellSize / 2,
            y: y * this.cellSize + this.cellSize / 2,
            frame: 0,
            maxFrame: 30
        });
        
        // 添加粒子
        for (let i = 0; i < 30; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = 2 + Math.random() * 6;
            this.particles.push({
                x: x * this.cellSize + this.cellSize / 2,
                y: y * this.cellSize + this.cellSize / 2,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                life: 1,
                color: Math.random() > 0.5 ? this.colors.explosion : this.colors.missile,
                size: 2 + Math.random() * 3
            });
        }
        
        // 添加烟雾
        for (let i = 0; i < 10; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = 0.5 + Math.random() * 1;
            this.smokeParticles.push({
                x: x * this.cellSize + this.cellSize / 2,
                y: y * this.cellSize + this.cellSize / 2,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed - 0.5,
                life: 1,
                size: 8 + Math.random() * 8
            });
        }
    }
    
    /**
     * 添加开火闪光效果
     */
    addMuzzleFlash(x, y, direction) {
        const px = x * this.cellSize + this.cellSize / 2;
        const py = y * this.cellSize + this.cellSize / 2;
        
        // 计算炮口位置
        const rotations = {
            'north': { dx: 0, dy: -1 },
            'east': { dx: 1, dy: 0 },
            'south': { dx: 0, dy: 1 },
            'west': { dx: -1, dy: 0 }
        };
        const dir = rotations[direction] || { dx: 0, dy: -1 };
        const muzzleX = px + dir.dx * this.cellSize * 0.4;
        const muzzleY = py + dir.dy * this.cellSize * 0.4;
        
        this.muzzleFlashes.push({
            x: muzzleX,
            y: muzzleY,
            direction: direction,
            frame: 0,
            maxFrame: 12
        });
        
        // 添加开火粒子
        for (let i = 0; i < 15; i++) {
            const spreadAngle = (Math.random() - 0.5) * 0.8;
            const baseAngle = Math.atan2(dir.dy, dir.dx);
            const angle = baseAngle + spreadAngle;
            const speed = 3 + Math.random() * 5;
            this.particles.push({
                x: muzzleX,
                y: muzzleY,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                life: 0.6,
                color: i % 3 === 0 ? '#ffffff' : (i % 3 === 1 ? '#ffff00' : '#ff9500'),
                size: 1 + Math.random() * 2
            });
        }
    }
    
    /**
     * 添加命中火花效果
     */
    addHitSpark(x, y) {
        const px = x * this.cellSize + this.cellSize / 2;
        const py = y * this.cellSize + this.cellSize / 2;
        
        this.hitSparks.push({
            x: px,
            y: py,
            frame: 0,
            maxFrame: 15
        });
        
        // 添加火花粒子
        for (let i = 0; i < 20; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = 2 + Math.random() * 4;
            this.particles.push({
                x: px,
                y: py,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                life: 0.8,
                color: Math.random() > 0.3 ? '#ff9500' : '#ffff00',
                size: 1 + Math.random() * 2
            });
        }
    }
    
    /**
     * 添加导弹尾迹
     */
    addMissileTrail(x, y) {
        const px = x * this.cellSize + this.cellSize / 2;
        const py = y * this.cellSize + this.cellSize / 2;
        
        this.missileTrails.push({
            x: px,
            y: py,
            life: 1
        });
    }
    
    /**
     * 绘制所有特效
     */
    drawExplosions() {
        const ctx = this.ctx;
        
        // 绘制导弹尾迹
        for (let i = this.missileTrails.length - 1; i >= 0; i--) {
            const trail = this.missileTrails[i];
            const alpha = trail.life * 0.5;
            const size = trail.life * 6;
            
            ctx.fillStyle = `rgba(255, 149, 0, ${alpha})`;
            ctx.beginPath();
            ctx.arc(trail.x, trail.y, size, 0, Math.PI * 2);
            ctx.fill();
            
            trail.life -= 0.08;
            if (trail.life <= 0) {
                this.missileTrails.splice(i, 1);
            }
        }
        
        // 绘制开火闪光
        for (let i = this.muzzleFlashes.length - 1; i >= 0; i--) {
            const flash = this.muzzleFlashes[i];
            const progress = flash.frame / flash.maxFrame;
            const alpha = 1 - progress;
            const size = (1 - progress * 0.5) * 25;
            
            ctx.save();
            
            // 闪光核心
            const gradient = ctx.createRadialGradient(flash.x, flash.y, 0, flash.x, flash.y, size);
            gradient.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
            gradient.addColorStop(0.3, `rgba(255, 255, 0, ${alpha * 0.8})`);
            gradient.addColorStop(0.6, `rgba(255, 150, 0, ${alpha * 0.5})`);
            gradient.addColorStop(1, 'rgba(255, 100, 0, 0)');
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(flash.x, flash.y, size, 0, Math.PI * 2);
            ctx.fill();
            
            // 光晕
            ctx.shadowBlur = 20;
            ctx.shadowColor = '#ffff00';
            ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.5})`;
            ctx.beginPath();
            ctx.arc(flash.x, flash.y, size * 0.3, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.restore();
            
            flash.frame++;
            if (flash.frame >= flash.maxFrame) {
                this.muzzleFlashes.splice(i, 1);
            }
        }
        
        // 绘制命中火花
        for (let i = this.hitSparks.length - 1; i >= 0; i--) {
            const spark = this.hitSparks[i];
            const progress = spark.frame / spark.maxFrame;
            const alpha = 1 - progress;
            const size = 15 + progress * 10;
            
            ctx.save();
            ctx.shadowBlur = 15;
            ctx.shadowColor = '#ff9500';
            
            // 火花核心
            const gradient = ctx.createRadialGradient(spark.x, spark.y, 0, spark.x, spark.y, size);
            gradient.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
            gradient.addColorStop(0.4, `rgba(255, 200, 0, ${alpha * 0.7})`);
            gradient.addColorStop(1, 'rgba(255, 100, 0, 0)');
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(spark.x, spark.y, size, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.restore();
            
            spark.frame++;
            if (spark.frame >= spark.maxFrame) {
                this.hitSparks.splice(i, 1);
            }
        }
        
        // 绘制烟雾
        for (let i = this.smokeParticles.length - 1; i >= 0; i--) {
            const smoke = this.smokeParticles[i];
            const alpha = smoke.life * 0.4;
            
            ctx.fillStyle = `rgba(80, 80, 80, ${alpha})`;
            ctx.beginPath();
            ctx.arc(smoke.x, smoke.y, smoke.size, 0, Math.PI * 2);
            ctx.fill();
            
            smoke.x += smoke.vx;
            smoke.y += smoke.vy;
            smoke.size += 0.3;
            smoke.life -= 0.02;
            
            if (smoke.life <= 0) {
                this.smokeParticles.splice(i, 1);
            }
        }
        
        // 绘制爆炸
        for (let i = this.explosions.length - 1; i >= 0; i--) {
            const exp = this.explosions[i];
            const progress = exp.frame / exp.maxFrame;
            const radius = 5 + progress * 40;
            const alpha = 1 - progress;
            
            ctx.save();
            
            // 外圈冲击波
            ctx.strokeStyle = `rgba(255, 149, 0, ${alpha * 0.6})`;
            ctx.lineWidth = 4 - progress * 3;
            ctx.beginPath();
            ctx.arc(exp.x, exp.y, radius + 15, 0, Math.PI * 2);
            ctx.stroke();
            
            // 第二层冲击波
            ctx.strokeStyle = `rgba(255, 255, 0, ${alpha * 0.3})`;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(exp.x, exp.y, radius + 25, 0, Math.PI * 2);
            ctx.stroke();
            
            // 火球
            const gradient = ctx.createRadialGradient(exp.x, exp.y, 0, exp.x, exp.y, radius);
            gradient.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
            gradient.addColorStop(0.2, `rgba(255, 255, 0, ${alpha})`);
            gradient.addColorStop(0.4, `rgba(255, 150, 0, ${alpha * 0.9})`);
            gradient.addColorStop(0.7, `rgba(255, 50, 0, ${alpha * 0.6})`);
            gradient.addColorStop(1, 'rgba(100, 0, 0, 0)');
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(exp.x, exp.y, radius, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.restore();
            
            exp.frame++;
            if (exp.frame >= exp.maxFrame) {
                this.explosions.splice(i, 1);
            }
        }
        
        // 绘制粒子
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            const size = p.size || (2 + p.life * 2);
            
            // 处理颜色透明度
            let color = p.color;
            if (color.startsWith('#')) {
                const r = parseInt(color.slice(1, 3), 16);
                const g = parseInt(color.slice(3, 5), 16);
                const b = parseInt(color.slice(5, 7), 16);
                color = `rgba(${r}, ${g}, ${b}, ${p.life})`;
            } else if (color.startsWith('rgb(')) {
                color = color.replace('rgb(', 'rgba(').replace(')', `, ${p.life})`);
            }
            
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
            ctx.fill();
            
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.15; // 重力
            p.vx *= 0.98; // 空气阻力
            p.life -= 0.025;
            
            if (p.life <= 0) {
                this.particles.splice(i, 1);
            }
        }
    }
    
    /**
     * 完整渲染一帧
     */
    render(gameState) {
        this.clear();
        this.drawGrid();
        
        if (gameState) {
            this.drawMap(gameState.map);
            this.drawTanks(gameState.tanks);
            this.drawMissiles(gameState.missiles);
        }
        
        this.drawExplosions();
    }
}
