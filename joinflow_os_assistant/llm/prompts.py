"""
提示词模板
"""
from typing import Dict


class PromptTemplates:
    """
    提示词模板集合
    """
    
    # 系统提示词
    SYSTEM_PROMPT = """你是一个智能操作系统助手，可以帮助用户完成各种计算机操作任务。

你的能力包括：
1. 理解用户的自然语言指令
2. 执行文件操作（创建、读取、写入、删除、复制、移动、搜索）
3. 管理应用程序（打开、关闭、列表）
4. 执行系统命令
5. 浏览器搜索和网页访问
6. 截图和剪贴板操作
7. 生成文本和代码

请始终：
- 准确理解用户意图
- 选择最合适的操作
- 提供清晰的执行反馈
- 对危险操作进行警告
"""
    
    # 意图识别提示词
    INTENT_RECOGNITION = """分析用户输入，识别意图和提取实体。

用户输入: "{user_input}"

返回JSON格式：
{{
    "intent_type": "意图类型",
    "confidence": 0.0-1.0,
    "entities": [
        {{"type": "实体类型", "value": "实体值", "text": "原文"}}
    ],
    "description": "意图描述",
    "is_compound": false,
    "sub_intents": [],
    "requires_confirmation": false
}}

意图类型：
- FILE_CREATE/READ/WRITE/DELETE/COPY/MOVE/OPEN: 文件操作
- DIR_CREATE/LIST/DELETE/NAVIGATE: 目录操作
- SEARCH_FILE/CONTENT: 搜索
- APP_OPEN/CLOSE/LIST: 应用管理
- BROWSER_OPEN/SEARCH/NAVIGATE: 浏览器
- SYSTEM_INFO/SCREENSHOT/NOTIFY: 系统
- CLIPBOARD_GET/SET: 剪贴板
- EXECUTE_COMMAND/SCRIPT: 执行
- COMPOSE_TEXT/CODE: 编写
- HELP/CANCEL/CONFIRM/UNKNOWN: 其他

实体类型：
- FILE_PATH, DIR_PATH, FILE_NAME, FILE_TYPE
- APP_NAME, URL, SEARCH_QUERY
- TEXT_CONTENT, COMMAND

只返回JSON。"""

    # 任务规划提示词
    TASK_PLANNING = """将用户请求分解为具体执行步骤。

用户请求: "{user_input}"
识别意图: {intent_info}

返回JSON格式：
{{
    "plan_name": "计划名称",
    "strategy": "sequential/parallel",
    "tasks": [
        {{
            "name": "任务名称",
            "description": "描述",
            "operation": "操作类型",
            "parameters": {{}},
            "dependencies": [],
            "priority": "NORMAL"
        }}
    ]
}}

操作类型：
- file.create/read/write/delete/copy/move/open
- dir.create/list/delete/navigate
- search.file/content
- app.open/close/list
- browser.open/search/navigate
- system.info/screenshot/notify
- clipboard.get/set
- command.execute
- compose.text/code

只返回JSON。"""

    # 智能对话提示词
    SMART_CONVERSATION = """你是一个智能助手，正在与用户进行对话。

上下文信息：
- 当前目录: {current_dir}
- 平台: {platform}
- 最近文件: {recent_files}
- 最近应用: {recent_apps}
- 上一个操作: {last_action}

用户说: "{user_input}"

请理解用户意图并给出适当的回应。如果用户想要执行操作，请返回：
{{
    "action": "execute",
    "command": "要执行的命令描述",
    "response": "给用户的回复"
}}

如果只是对话，请返回：
{{
    "action": "chat",
    "response": "给用户的回复"
}}
"""

    # 错误恢复提示词
    ERROR_RECOVERY = """任务执行失败，请分析原因并建议恢复方案。

失败的任务: {task_name}
操作: {operation}
参数: {parameters}
错误信息: {error}

请返回：
{{
    "analysis": "错误原因分析",
    "suggestions": ["建议1", "建议2"],
    "alternative_approach": "替代方案（可选）"
}}
"""

    # 参数补全提示词
    PARAMETER_COMPLETION = """根据上下文补全缺失的参数。

操作: {operation}
已有参数: {parameters}
上下文:
- 当前目录: {current_dir}
- 最近文件: {recent_files}

请推断并补全缺失的参数：
{{
    "completed_parameters": {{
        "参数名": "推断值"
    }},
    "confidence": 0.0-1.0,
    "reasoning": "推断理由"
}}
"""

    @classmethod
    def get_intent_prompt(cls, user_input: str) -> str:
        """获取意图识别提示词"""
        return cls.INTENT_RECOGNITION.format(user_input=user_input)
    
    @classmethod
    def get_planning_prompt(cls, user_input: str, intent_info: str) -> str:
        """获取任务规划提示词"""
        return cls.TASK_PLANNING.format(
            user_input=user_input,
            intent_info=intent_info
        )
    
    @classmethod
    def get_conversation_prompt(cls, user_input: str, context: Dict) -> str:
        """获取对话提示词"""
        return cls.SMART_CONVERSATION.format(
            user_input=user_input,
            current_dir=context.get("current_dir", "."),
            platform=context.get("platform", "unknown"),
            recent_files=context.get("recent_files", [])[:5],
            recent_apps=context.get("recent_apps", [])[:5],
            last_action=context.get("last_action", "无"),
        )
    
    @classmethod
    def get_error_prompt(cls, task_name: str, operation: str, 
                         parameters: Dict, error: str) -> str:
        """获取错误恢复提示词"""
        return cls.ERROR_RECOVERY.format(
            task_name=task_name,
            operation=operation,
            parameters=parameters,
            error=error,
        )
    
    @classmethod
    def get_completion_prompt(cls, operation: str, parameters: Dict,
                              context: Dict) -> str:
        """获取参数补全提示词"""
        return cls.PARAMETER_COMPLETION.format(
            operation=operation,
            parameters=parameters,
            current_dir=context.get("current_dir", "."),
            recent_files=context.get("recent_files", [])[:5],
        )

