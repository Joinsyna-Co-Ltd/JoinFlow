"""
Agent OS Web服务器
"""
import os
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

from ..core.agent import AgentOS
from ..core.config import AgentConfig

logger = logging.getLogger(__name__)


def create_app(config: AgentConfig = None, llm_client=None) -> Flask:
    """
    创建Flask应用
    """
    # 获取模板和静态文件路径
    ui_dir = Path(__file__).parent
    template_dir = ui_dir / 'templates'
    static_dir = ui_dir / 'static'
    
    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
        static_url_path='/static'
    )
    
    CORS(app)
    
    # 创建Agent
    agent = AgentOS(config=config, llm_client=llm_client)
    
    # ==================== 页面路由 ====================
    
    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')
    
    # ==================== API路由 ====================
    
    @app.route('/api/execute', methods=['POST'])
    def execute():
        """执行命令"""
        data = request.json or {}
        command = data.get('command', '')
        auto_confirm = data.get('auto_confirm', False)
        
        if not command:
            return jsonify({'success': False, 'message': '缺少command参数'}), 400
        
        try:
            result = agent.run(command, auto_confirm)
            return jsonify({
                'success': result.success,
                'action': result.action,
                'message': result.message,
                'data': result.data,
                'error': result.error,
                'duration_ms': result.duration_ms,
            })
        except Exception as e:
            logger.error(f"执行错误: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/api/system/info', methods=['GET'])
    def system_info():
        """系统信息"""
        result = agent.get_system_info()
        return jsonify({
            'success': result.success,
            'data': result.data,
        })
    
    @app.route('/api/session', methods=['GET'])
    def get_session():
        """获取会话信息"""
        session = agent.get_session()
        return jsonify({
            'id': session.id,
            'context': session.get_context_summary(),
            'messages': session.get_conversation_history(50),
            'tasks': session.get_task_history(20),
        })
    
    @app.route('/api/session/new', methods=['POST'])
    def new_session():
        """创建新会话"""
        session = agent.new_session()
        return jsonify({
            'success': True,
            'session_id': session.id,
        })
    
    @app.route('/api/health', methods=['GET'])
    def health():
        """健康检查"""
        return jsonify({
            'status': 'ok',
            'agent': 'running',
            'version': '2.0.0',
        })
    
    # ==================== 快捷API ====================
    
    @app.route('/api/app/open', methods=['POST'])
    def open_app():
        """打开应用"""
        data = request.json or {}
        app_name = data.get('name') or data.get('app_name')
        
        if not app_name:
            return jsonify({'success': False, 'message': '缺少应用名称'}), 400
        
        result = agent.open_app(app_name)
        return jsonify({
            'success': result.success,
            'message': result.message,
            'data': result.data,
        })
    
    @app.route('/api/search', methods=['POST'])
    def search_files():
        """搜索文件"""
        data = request.json or {}
        query = data.get('query')
        path = data.get('path')
        
        if not query:
            return jsonify({'success': False, 'message': '缺少query参数'}), 400
        
        result = agent.search_files(query, path)
        return jsonify({
            'success': result.success,
            'message': result.message,
            'data': result.data,
        })
    
    @app.route('/api/browser/search', methods=['POST'])
    def browser_search():
        """浏览器搜索"""
        data = request.json or {}
        query = data.get('query')
        engine = data.get('engine', 'google')
        
        if not query:
            return jsonify({'success': False, 'message': '缺少query参数'}), 400
        
        result = agent.search_web(query, engine)
        return jsonify({
            'success': result.success,
            'message': result.message,
            'data': result.data,
        })
    
    @app.route('/api/screenshot', methods=['POST'])
    def screenshot():
        """截图"""
        data = request.json or {}
        path = data.get('path')
        
        result = agent.screenshot(path)
        return jsonify({
            'success': result.success,
            'message': result.message,
            'data': result.data,
        })
    
    return app


def run_server(host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
    """运行服务器"""
    app = create_app()
    
    print("")
    print("=" * 60)
    print("  Agent OS v2.0 - Intelligent Operating System Agent")
    print("=" * 60)
    print(f"  Server running at: http://{host}:{port}")
    print("=" * 60)
    print("")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)

