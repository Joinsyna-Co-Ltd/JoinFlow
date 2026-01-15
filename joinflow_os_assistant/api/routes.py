"""
API路由定义
"""
from flask import Blueprint, jsonify, request
from typing import Callable, Dict, Any


def register_routes(app, assistant_api) -> None:
    """
    注册所有API路由
    
    Args:
        app: Flask应用
        assistant_api: OSAssistantAPI实例
    """
    
    # 创建蓝图
    api_bp = Blueprint('os_assistant', __name__, url_prefix='/api/v1')
    
    # ==================
    # 核心API
    # ==================
    
    @api_bp.route('/execute', methods=['POST'])
    def execute():
        """执行自然语言命令"""
        data = request.json or {}
        command = data.get('command', '')
        auto_confirm = data.get('auto_confirm', False)
        
        if not command:
            return jsonify({'success': False, 'error': '缺少command参数'}), 400
        
        result = assistant_api.execute(command, auto_confirm)
        return jsonify(result)
    
    @api_bp.route('/context', methods=['GET'])
    def get_context():
        """获取当前上下文"""
        return jsonify(assistant_api.get_context())
    
    @api_bp.route('/operations', methods=['GET'])
    def list_operations():
        """列出可用操作"""
        return jsonify({'operations': assistant_api.get_operations()})
    
    @api_bp.route('/health', methods=['GET'])
    def health_check():
        """健康检查"""
        return jsonify({'status': 'healthy'})
    
    # ==================
    # 文件操作API
    # ==================
    
    @api_bp.route('/file', methods=['POST'])
    def file_operation():
        """文件操作"""
        data = request.json or {}
        action = data.get('action', 'read')
        path = data.get('path')
        
        if not path:
            return jsonify({'success': False, 'error': '缺少path参数'}), 400
        
        if action == 'read':
            result = assistant_api.assistant.read_file(path)
        elif action == 'create':
            content = data.get('content', '')
            result = assistant_api.assistant.create_file(path, content)
        elif action == 'delete':
            result = assistant_api.execute(f"删除文件 {path}", auto_confirm=True)
        else:
            return jsonify({'success': False, 'error': f'不支持的操作: {action}'}), 400
        
        return jsonify({
            'success': result.success,
            'message': result.message,
            'data': result.data,
        })
    
    @api_bp.route('/files/search', methods=['POST'])
    def search_files():
        """搜索文件"""
        data = request.json or {}
        query = data.get('query')
        directory = data.get('directory')
        file_type = data.get('file_type')
        
        if not query:
            return jsonify({'success': False, 'error': '缺少query参数'}), 400
        
        cmd = f"搜索文件 {query}"
        if directory:
            cmd += f" 在 {directory}"
        if file_type:
            cmd += f" 类型 {file_type}"
        
        result = assistant_api.execute(cmd)
        return jsonify(result)
    
    # ==================
    # 应用操作API
    # ==================
    
    @api_bp.route('/app/open', methods=['POST'])
    def open_application():
        """打开应用"""
        data = request.json or {}
        app_name = data.get('name') or data.get('app_name')
        
        if not app_name:
            return jsonify({'success': False, 'error': '缺少应用名称'}), 400
        
        result = assistant_api.assistant.open_app(app_name)
        return jsonify({
            'success': result.success,
            'message': result.message,
            'data': result.data,
        })
    
    @api_bp.route('/app/close', methods=['POST'])
    def close_application():
        """关闭应用"""
        data = request.json or {}
        app_name = data.get('name') or data.get('app_name')
        
        if not app_name:
            return jsonify({'success': False, 'error': '缺少应用名称'}), 400
        
        result = assistant_api.execute(f"关闭 {app_name}")
        return jsonify(result)
    
    @api_bp.route('/apps', methods=['GET'])
    def list_applications():
        """列出运行中的应用"""
        result = assistant_api.execute("列出运行中的程序")
        return jsonify(result)
    
    # ==================
    # 系统操作API
    # ==================
    
    @api_bp.route('/system/info', methods=['GET'])
    def system_info():
        """获取系统信息"""
        result = assistant_api.assistant.get_system_info()
        return jsonify({
            'success': result.success,
            'data': result.data,
        })
    
    @api_bp.route('/system/screenshot', methods=['POST'])
    def take_screenshot():
        """截图"""
        data = request.json or {}
        path = data.get('path')
        
        result = assistant_api.assistant.screenshot(path)
        return jsonify({
            'success': result.success,
            'message': result.message,
            'data': result.data,
        })
    
    @api_bp.route('/system/clipboard', methods=['GET', 'POST'])
    def clipboard():
        """剪贴板操作"""
        if request.method == 'GET':
            result = assistant_api.execute("获取剪贴板内容")
        else:
            data = request.json or {}
            content = data.get('content', '')
            result = assistant_api.execute(f"复制到剪贴板: {content}")
        
        return jsonify(result)
    
    # ==================
    # 浏览器操作API
    # ==================
    
    @api_bp.route('/browser/search', methods=['POST'])
    def browser_search():
        """浏览器搜索"""
        data = request.json or {}
        query = data.get('query')
        engine = data.get('engine', 'google')
        
        if not query:
            return jsonify({'success': False, 'error': '缺少query参数'}), 400
        
        result = assistant_api.assistant.search_web(query, engine)
        return jsonify({
            'success': result.success,
            'message': result.message,
            'data': result.data,
        })
    
    @api_bp.route('/browser/open', methods=['POST'])
    def browser_open():
        """打开URL"""
        data = request.json or {}
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': '缺少url参数'}), 400
        
        result = assistant_api.execute(f"访问网址 {url}")
        return jsonify(result)
    
    # ==================
    # 命令执行API
    # ==================
    
    @api_bp.route('/command', methods=['POST'])
    def execute_command():
        """执行Shell命令"""
        data = request.json or {}
        command = data.get('command')
        
        if not command:
            return jsonify({'success': False, 'error': '缺少command参数'}), 400
        
        result = assistant_api.assistant.run_command(command)
        return jsonify({
            'success': result.success,
            'message': result.message,
            'data': result.data,
        })
    
    # 注册蓝图
    app.register_blueprint(api_bp)

