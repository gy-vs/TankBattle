/**
 * TankBattle 游戏控制器
 * 赛博朋克风格 UI 交互
 */

class GameController {
    constructor() {
        // 初始化渲染器
        this.renderer = new GameRenderer('gameCanvas');
        
        // 初始化 Socket.IO
        this.socket = io();
        
        // 游戏状态
        this.gameState = null;
        this.isAutoRunning = false;
        this.autoRunInterval = null;
        this.speed = 500;
        this.previousTankStates = {};
        this.isLoading = false;
        this.gameInitialized = false;
        
        // 加载状态元素
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingText = document.getElementById('loadingText');
        this.loadingProgress = document.getElementById('loadingProgress');
        
        // 创建Toast容器
        this.createToastContainer();
        
        // 绑定 UI 元素
        this.bindUI();
        
        // 绑定 Socket 事件
        this.bindSocketEvents();
        
        // 初始渲染
        this.renderer.render(null);
        
        // 启动渲染循环
        this.startRenderLoop();
    }
    
    /**
     * 创建Toast容器
     */
    createToastContainer() {
        if (!document.querySelector('.toast-container')) {
            const container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
    }
    
    /**
     * 显示Toast通知
     * @param {string} message - 通知消息
     * @param {string} type - 类型: info, success, warning, error
     * @param {number} duration - 显示时长（毫秒）
     */
    showToast(message, type = 'info', duration = 3000) {
        const container = document.querySelector('.toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
    
    /**
     * 显示加载状态
     */
    showLoading(text = '正在加载', progress = '') {
        this.isLoading = true;
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('hidden');
            if (this.loadingText) this.loadingText.textContent = text;
            if (this.loadingProgress) this.loadingProgress.textContent = progress;
        }
    }
    
    /**
     * 隐藏加载状态
     */
    hideLoading() {
        this.isLoading = false;
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('hidden');
        }
    }
    
    /**
     * 启动渲染循环
     */
    startRenderLoop() {
        const loop = () => {
            this.renderer.render(this.gameState);
            requestAnimationFrame(loop);
        };
        loop();
    }
    
    /**
     * 绑定 UI 事件
     */
    bindUI() {
        // 按钮
        this.btnInit = document.getElementById('btnInit');
        this.btnStart = document.getElementById('btnStart');
        this.btnPause = document.getElementById('btnPause');
        this.btnStep = document.getElementById('btnStep');
        this.btnReset = document.getElementById('btnReset');
        
        // 速度控制
        this.speedSlider = document.getElementById('speedSlider');
        this.speedValue = document.getElementById('speedValue');
        this.autoRunCheckbox = document.getElementById('autoRun');
        
        // 信息元素
        this.clockValue = document.getElementById('clockValue');
        this.gameStateElem = document.getElementById('gameState');
        this.eventLog = document.getElementById('eventLog');
        this.overlay = document.getElementById('gameOverlay');
        this.overlayTitle = document.getElementById('overlayTitle');
        this.overlayMessage = document.getElementById('overlayMessage');
        
        // 绑定事件
        this.btnInit.addEventListener('click', () => this.initGame());
        this.btnStart.addEventListener('click', () => this.startGame());
        this.btnPause.addEventListener('click', () => this.pauseGame());
        this.btnStep.addEventListener('click', () => this.stepGame());
        this.btnReset.addEventListener('click', () => this.resetGame());
        
        this.speedSlider.addEventListener('input', (e) => {
            this.speed = parseInt(e.target.value);
            this.speedValue.textContent = `${this.speed}ms`;
            
            if (this.isAutoRunning) {
                this.stopAutoRun();
                this.startAutoRun();
            }
        });
        
        this.autoRunCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.startAutoRun();
            } else {
                this.stopAutoRun();
            }
        });
    }
    
    /**
     * 绑定 Socket 事件
     */
    bindSocketEvents() {
        this.socket.on('connect', () => {
            console.log('[SYSTEM] Connected to server');
            this.addEvent('系统已连接', 'success');
            this.hideLoading();
        });
        
        this.socket.on('disconnect', () => {
            console.log('[SYSTEM] Disconnected');
            this.addEvent('连接断开', 'danger');
            this.showLoading('连接已断开', '请刷新页面重新连接');
        });
        
        this.socket.on('game:state', (state) => {
            // 隐藏加载状态
            this.hideLoading();
            
            // 游戏开始后隐藏overlay
            if (state.state === 'running' && !this.gameInitialized) {
                this.hideOverlay();
                this.gameInitialized = true;
            }
            
            // 检测击毁事件
            this.detectDestroyedTanks(state);
            
            // 处理开火特效
            if (state.fire_events) {
                for (const fire of state.fire_events) {
                    this.renderer.addMuzzleFlash(fire.x, fire.y, fire.direction);
                }
            }
            
            // 处理命中特效
            if (state.hit_events) {
                for (const hit of state.hit_events) {
                    this.renderer.addHitSpark(hit.x, hit.y);
                }
            }
            
            this.gameState = state;
            this.updateUI();
        });
        
        this.socket.on('game:started', () => {
            this.addEvent('战斗开始', 'success');
            this.updateButtons('running');
            this.hideOverlay();
            this.hideLoading();
            this.gameInitialized = true;
            this.showToast('战斗开始！', 'success');
        });
        
        this.socket.on('game:paused', () => {
            this.addEvent('仿真暂停');
            this.updateButtons('paused');
        });
        
        this.socket.on('game:reset', () => {
            this.addEvent('系统重置');
            this.stopAutoRun();
            this.autoRunCheckbox.checked = false;
            this.previousTankStates = {};
            this.hideLoading();
        });
        
        this.socket.on('game:over', (result) => {
            this.handleGameOver(result);
        });
        
        // 监听错误事件（用户友好消息）
        this.socket.on('game:error', (error) => {
            this.hideLoading();
            const message = error.message || '操作失败，请重试';
            this.addEvent(message, 'danger');
            console.error('[GAME ERROR]', error);
            
            // 显示错误提示
            this.showErrorToast(message);
        });
        
        // 监听开火事件
        this.socket.on('game:fire', (data) => {
            this.renderer.addMuzzleFlash(data.x, data.y, data.direction);
        });
        
        // 监听命中事件
        this.socket.on('game:hit', (data) => {
            this.renderer.addHitSpark(data.x, data.y);
        });
    }
    
    /**
     * 显示错误提示
     */
    showErrorToast(message) {
        // 创建临时提示元素
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 51, 102, 0.9);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 12px;
            z-index: 1000;
            animation: fadeInOut 3s ease forwards;
        `;
        
        // 添加动画样式
        if (!document.querySelector('#error-toast-style')) {
            const style = document.createElement('style');
            style.id = 'error-toast-style';
            style.textContent = `
                @keyframes fadeInOut {
                    0% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
                    10% { opacity: 1; transform: translateX(-50%) translateY(0); }
                    90% { opacity: 1; transform: translateX(-50%) translateY(0); }
                    100% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
    
    /**
     * 检测被击毁的坦克并播放爆炸效果
     */
    detectDestroyedTanks(newState) {
        if (!newState || !newState.tanks) return;
        
        for (const tank of newState.tanks) {
            const prevState = this.previousTankStates[tank.id];
            
            // 如果之前存活现在死亡，播放爆炸
            if (prevState && prevState.alive && !tank.alive) {
                this.renderer.addExplosion(tank.x, tank.y);
            }
            
            this.previousTankStates[tank.id] = { ...tank };
        }
    }
    
    /**
     * 初始化游戏
     */
    initGame() {
        this.showToast('正在初始化战场...', 'info');
        this.socket.emit('game:init');
        this.updateButtons('ready');
        this.gameInitialized = false;
        this.showOverlay('待命', '// 按开始键启动战斗');
        this.addEvent('仿真已初始化');
    }
    
    /**
     * 开始游戏
     */
    startGame() {
        this.socket.emit('game:start');
    }
    
    /**
     * 暂停游戏
     */
    pauseGame() {
        this.socket.emit('game:pause');
        this.stopAutoRun();
        this.autoRunCheckbox.checked = false;
    }
    
    /**
     * 单步执行
     */
    stepGame() {
        this.socket.emit('game:step');
    }
    
    /**
     * 重置游戏
     */
    resetGame() {
        this.showToast('正在重置战场...', 'info');
        this.socket.emit('game:reset');
        this.updateButtons('ready');
        this.gameInitialized = false;
        this.showOverlay('重置完成', '// 系统准备就绪，可开始新仿真');
    }
    
    /**
     * 开始自动运行
     */
    startAutoRun() {
        if (this.autoRunInterval) return;
        
        this.isAutoRunning = true;
        this.autoRunInterval = setInterval(() => {
            if (this.gameState && this.gameState.state !== 'finished') {
                this.socket.emit('game:step');
            } else {
                this.stopAutoRun();
            }
        }, this.speed);
    }
    
    /**
     * 停止自动运行
     */
    stopAutoRun() {
        this.isAutoRunning = false;
        if (this.autoRunInterval) {
            clearInterval(this.autoRunInterval);
            this.autoRunInterval = null;
        }
    }
    
    /**
     * 更新按钮状态
     */
    updateButtons(state) {
        const states = {
            ready: { init: false, start: false, pause: true, step: false, reset: false },
            running: { init: true, start: true, pause: false, step: false, reset: false },
            paused: { init: true, start: false, pause: true, step: false, reset: false },
            finished: { init: true, start: true, pause: true, step: true, reset: false }
        };
        
        const s = states[state] || states.ready;
        this.btnInit.disabled = s.init;
        this.btnStart.disabled = s.start;
        this.btnPause.disabled = s.pause;
        this.btnStep.disabled = s.step;
        this.btnReset.disabled = s.reset;
    }
    
    /**
     * 更新 UI
     */
    updateUI() {
        if (!this.gameState) return;
        
        // 更新回合数
        this.clockValue.textContent = this.gameState.clock;
        
        // 更新游戏状态
        const stateMap = {
            'waiting': '待命',
            'running': '运行中',
            'paused': '已暂停',
            'finished': '已完成'
        };
        this.gameStateElem.textContent = stateMap[this.gameState.state] || '未知';
        
        // 更新坦克信息
        const redTanks = this.gameState.tanks.filter(t => t.team === 'red');
        const blueTanks = this.gameState.tanks.filter(t => t.team === 'blue');
        
        this.updateTeamInfo('red', redTanks);
        this.updateTeamInfo('blue', blueTanks);
        
        // 更新存活统计
        this.updateTeamStats('red', redTanks);
        this.updateTeamStats('blue', blueTanks);
        
        // 更新事件日志
        this.updateEventLog();
    }
    
    /**
     * 更新队伍存活统计
     */
    updateTeamStats(team, tanks) {
        const aliveCount = tanks.filter(t => t.alive).length;
        const totalCount = tanks.length;
        const statsElem = document.getElementById(`${team}Alive`);
        if (statsElem) {
            statsElem.textContent = `${aliveCount}/${totalCount}`;
        }
    }
    
    /**
     * 更新队伍信息
     */
    updateTeamInfo(team, tanks) {
        const container = document.getElementById(`${team}TeamInfo`);
        container.innerHTML = '';
        
        tanks.forEach((tank) => {
            const card = document.createElement('div');
            card.className = `tank-card ${!tank.alive ? 'dead' : ''}`;
            
            const healthPercent = (tank.health / 1000) * 100;
            const energyPercent = (tank.energy / 1000) * 100;
            const missilePercent = (tank.missiles / 20) * 100;
            const healthClass = healthPercent < 30 ? 'low' : '';
            
            // 朝向图标映射
            const directionIcons = {
                'north': '↑',
                'east': '→',
                'south': '↓',
                'west': '←'
            };
            const dirIcon = directionIcons[tank.direction] || '?';
            
            // 补给站状态
            const atHealthStation = tank.healthRecharger === 'yes' || tank.atHealthStation;
            const atEnergyStation = tank.energyRecharger === 'yes' || tank.atEnergyStation;
            
            card.innerHTML = `
                <div class="tank-header">
                    <span>单元-${tank.id}</span>
                    ${!tank.alive ? '<span class="status-dead">已摧毁</span>' : ''}
                </div>
                <div class="tank-stats">
                    <div class="stat-bar health-bar">
                        <span class="stat-label">生命</span>
                        <div class="bar-track">
                            <div class="bar-fill ${healthClass}" style="width: ${healthPercent}%"></div>
                        </div>
                        <span class="stat-value">${tank.health}</span>
                    </div>
                    <div class="stat-bar energy-bar">
                        <span class="stat-label">能量</span>
                        <div class="bar-track">
                            <div class="bar-fill" style="width: ${energyPercent}%"></div>
                        </div>
                        <span class="stat-value">${tank.energy}</span>
                    </div>
                    <div class="stat-bar missile-bar">
                        <span class="stat-label">炮弹</span>
                        <div class="bar-track">
                            <div class="bar-fill" style="width: ${missilePercent}%"></div>
                        </div>
                        <span class="stat-value">${tank.missiles}/20</span>
                    </div>
                    <div class="tank-info-grid">
                        <div class="info-item">
                            <span class="info-label">位置</span>
                            <span class="info-value">(${tank.x}, ${tank.y})</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">朝向</span>
                            <span class="info-value direction-icon">${dirIcon}</span>
                        </div>
                    </div>
                    <div class="tank-status-row">
                        <span class="status-badge ${tank.shieldOn ? 'active' : ''}">
                            <i class="icon-shield">⬡</i> 护盾
                        </span>
                        <span class="status-badge ${tank.radarOn ? 'active' : ''}">
                            <i class="icon-radar">◎</i> 雷达${tank.radarOn && tank.radarSetting ? ' ' + tank.radarSetting : ''}
                        </span>
                    </div>
                    ${(atHealthStation || atEnergyStation) ? `
                    <div class="station-alert">
                        ${atHealthStation ? '<span class="station-badge health">⚕ 维修中</span>' : ''}
                        ${atEnergyStation ? '<span class="station-badge energy">⚡ 充能中</span>' : ''}
                    </div>
                    ` : ''}
                </div>
            `;
            
            container.appendChild(card);
        });
        
        // 添加队伍汇总统计
        this.updateTeamSummary(team, tanks);
    }
    
    /**
     * 更新队伍汇总统计
     */
    updateTeamSummary(team, tanks) {
        const container = document.getElementById(`${team}TeamInfo`);
        
        // 计算统计数据
        const aliveTanks = tanks.filter(t => t.alive);
        const totalHealth = aliveTanks.reduce((sum, t) => sum + t.health, 0);
        const totalEnergy = aliveTanks.reduce((sum, t) => sum + t.energy, 0);
        const totalMissiles = aliveTanks.reduce((sum, t) => sum + t.missiles, 0);
        const avgHealth = aliveTanks.length > 0 ? Math.round(totalHealth / aliveTanks.length) : 0;
        
        const summaryCard = document.createElement('div');
        summaryCard.className = 'team-summary-card';
        summaryCard.innerHTML = `
            <div class="summary-header">战队统计</div>
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="summary-label">存活</span>
                    <span class="summary-value">${aliveTanks.length}/${tanks.length}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">总血量</span>
                    <span class="summary-value health-color">${totalHealth}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">总能量</span>
                    <span class="summary-value energy-color">${totalEnergy}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">总炮弹</span>
                    <span class="summary-value missile-color">${totalMissiles}</span>
                </div>
            </div>
            <div class="summary-bar">
                <span class="summary-avg-label">平均生命</span>
                <div class="mini-bar-track">
                    <div class="mini-bar-fill" style="width: ${avgHealth / 10}%"></div>
                </div>
                <span class="summary-avg-value">${avgHealth}</span>
            </div>
        `;
        
        container.appendChild(summaryCard);
    }
    
    /**
     * 更新事件日志（横向滚动）
     */
    updateEventLog() {
        if (!this.gameState || !this.gameState.events) return;
        
        const recentEvents = this.gameState.events.slice(-15);
        
        this.eventLog.innerHTML = '';
        recentEvents.forEach(event => {
            const item = document.createElement('div');
            item.className = 'event-item';
            
            if (event.type === 'tank_destroyed' || event.type === 'tank_destroyed_at_station') {
                item.classList.add('danger');
            } else if (event.type === 'tank_hit') {
                item.classList.add('important');
            } else if (event.type === 'game_over') {
                item.classList.add('success');
            }
            
            item.textContent = `[R${event.clock}] ${event.message}`;
            this.eventLog.appendChild(item);
        });
        
        // 自动滚动到最新事件
        this.eventLog.scrollLeft = this.eventLog.scrollWidth;
    }
    
    /**
     * 添加事件到日志（横向滚动）
     */
    addEvent(message, type = '') {
        const item = document.createElement('div');
        item.className = `event-item ${type}`;
        item.textContent = `// ${message}`;
        this.eventLog.appendChild(item);
        
        // 限制日志数量
        while (this.eventLog.children.length > 20) {
            this.eventLog.removeChild(this.eventLog.firstChild);
        }
        
        // 自动滚动到最新
        this.eventLog.scrollLeft = this.eventLog.scrollWidth;
    }
    
    /**
     * 处理游戏结束
     */
    handleGameOver(result) {
        this.stopAutoRun();
        this.autoRunCheckbox.checked = false;
        this.updateButtons('finished');
        
        let title, message;
        if (result.winner === 'draw') {
            title = '◈ 平局';
            message = '// 双方全军覆没';
            this.overlay.className = 'game-overlay';
        } else if (result.winner === 'red') {
            title = '◈ 红方胜利';
            message = `// 存活单位: ${result.red.alive}/${result.red.total}`;
            this.overlay.className = 'game-overlay victory-red';
        } else {
            title = '◈ 蓝方胜利';
            message = `// 存活单位: ${result.blue.alive}/${result.blue.total}`;
            this.overlay.className = 'game-overlay victory-blue';
        }
        
        this.showOverlay(title, message);
        this.addEvent(`仿真结束: ${title}`, 'success');
    }
    
    /**
     * 显示覆盖层
     */
    showOverlay(title, message) {
        this.overlayTitle.textContent = title;
        this.overlayMessage.textContent = message;
        this.overlay.classList.remove('hidden');
    }
    
    /**
     * 隐藏覆盖层
     */
    hideOverlay() {
        this.overlay.classList.add('hidden');
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.gameController = new GameController();
});
