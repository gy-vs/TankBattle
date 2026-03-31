"""
TankBattle - 坦克对战仿真环境
主应用入口
"""

import logging
from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from game.engine import GameEngine
from game.config import GameConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('TankBattle')

# 创建 Flask 应用
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'tankbattle-secret-key'

# 启用 CORS
CORS(app)

# Swagger UI 配置
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "TankBattle API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# 创建 SocketIO 实例
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# 游戏引擎实例
game_engine = None

# 错误消息映射（技术错误 -> 用户友好提示）
ERROR_MESSAGES = {
    'game_not_initialized': '游戏尚未初始化，请先点击"初始化"按钮',
    'connection_lost': '连接已断开，请刷新页面重新连接',
    'invalid_action': '无效的操作，请重试',
    'server_error': '服务器出现异常，请稍后重试',
    'initialization_failed': '游戏初始化失败，请刷新页面重试',
    'step_failed': '执行步骤失败，请检查游戏状态'
}


def get_friendly_error(error_type: str, original_error: str = None) -> dict:
    """将技术错误转换为用户友好的错误信息"""
    friendly_message = ERROR_MESSAGES.get(error_type, '操作失败，请稍后重试')
    return {
        'message': friendly_message,
        'code': error_type,
        'detail': original_error if logger.level <= logging.DEBUG else None
    }


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/health')
def health():
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'service': 'TankBattle'})


@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理"""
    logger.error(f'Unhandled exception: {e}')
    return jsonify({'error': '服务器内部错误，请稍后重试', 'code': 'server_error'}), 500


@app.route('/api/config')
def get_config():
    """获取游戏配置"""
    return jsonify(GameConfig.to_dict())


# ==================== WebSocket 事件 ====================

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('客户端已连接')
    emit('connected', {'message': '连接成功'})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print('客户端已断开')


@socketio.on('game:init')
def handle_game_init(data=None):
    """初始化游戏"""
    global game_engine
    try:
        game_engine = GameEngine()
        game_engine.init_game()
        state = game_engine.get_state()
        emit('game:state', state)
        logger.info('游戏已初始化')
    except Exception as e:
        logger.error(f'初始化失败: {e}')
        emit('game:error', get_friendly_error('initialization_failed', str(e)))


@socketio.on('game:start')
def handle_game_start():
    """开始游戏"""
    global game_engine
    if game_engine:
        game_engine.start()
        emit('game:started', {'message': '游戏开始'})


@socketio.on('game:pause')
def handle_game_pause():
    """暂停游戏"""
    global game_engine
    if game_engine:
        game_engine.pause()
        emit('game:paused', {'message': '游戏暂停'})


@socketio.on('game:step')
def handle_game_step():
    """执行一步"""
    global game_engine
    if game_engine:
        try:
            game_engine.step()
            state = game_engine.get_state()
            emit('game:state', state)
            
            # 检查游戏是否结束
            if game_engine.is_game_over():
                result = game_engine.get_result()
                emit('game:over', result)
        except Exception as e:
            logger.error(f'执行步骤失败: {e}')
            emit('game:error', get_friendly_error('step_failed', str(e)))
    else:
        emit('game:error', get_friendly_error('game_not_initialized'))


@socketio.on('game:reset')
def handle_game_reset():
    """重置游戏"""
    global game_engine
    game_engine = GameEngine()
    game_engine.init_game()
    state = game_engine.get_state()
    emit('game:state', state)
    emit('game:reset', {'message': '游戏已重置'})


@socketio.on('game:auto')
def handle_game_auto(data):
    """自动运行模式"""
    global game_engine
    if game_engine and data.get('enabled'):
        speed = data.get('speed', 500)  # 默认 500ms 每步
        # 自动运行将在客户端通过定时器控制
        emit('game:auto_mode', {'enabled': True, 'speed': speed})


if __name__ == '__main__':
    print('=' * 50)
    print('TankBattle - 坦克对战仿真环境')
    print('=' * 50)
    print('Startup Success')
    print('Frontend: http://localhost:8080')
    print('=' * 50)
    
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)
