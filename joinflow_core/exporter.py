"""
Export Functionality
====================

Export task results and conversation history to various formats.
"""

import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import html

logger = logging.getLogger(__name__)


class MarkdownExporter:
    """Markdown导出器"""
    
    @staticmethod
    def export_task_result(
        task_id: str,
        description: str,
        result: str,
        steps: List[Dict],
        metadata: Dict = None
    ) -> str:
        """导出任务结果为Markdown"""
        md = f"""# 任务执行报告

## 任务信息

- **任务ID**: {task_id}
- **创建时间**: {metadata.get('created_at', datetime.now().isoformat()) if metadata else datetime.now().isoformat()}
- **状态**: {metadata.get('status', 'completed') if metadata else 'completed'}

## 任务描述

{description}

## 执行步骤

"""
        
        for i, step in enumerate(steps, 1):
            status_icon = "✅" if step.get('status') == 'completed' else "❌" if step.get('status') == 'failed' else "⏳"
            md += f"""### 步骤 {i}: {step.get('description', '')}

- **Agent**: {step.get('agent', 'unknown')}
- **状态**: {status_icon} {step.get('status', 'unknown')}

"""
            if step.get('output'):
                md += f"""**输出**:
```
{step.get('output', '')}
```

"""
        
        md += f"""## 最终结果

{result}

---
*报告生成时间: {datetime.now().isoformat()}*
"""
        
        return md
    
    @staticmethod
    def export_conversation(
        messages: List[Dict],
        session_id: str = "",
        metadata: Dict = None
    ) -> str:
        """导出对话历史为Markdown"""
        md = f"""# 对话记录

- **会话ID**: {session_id}
- **导出时间**: {datetime.now().isoformat()}
- **消息数量**: {len(messages)}

---

"""
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            if role == 'user':
                md += f"### 👤 用户\n\n"
            elif role == 'assistant':
                md += f"### 🤖 助手\n\n"
            else:
                md += f"### 📋 {role}\n\n"
            
            if timestamp:
                md += f"*{timestamp}*\n\n"
            
            md += f"{content}\n\n---\n\n"
        
        return md


class HTMLExporter:
    """HTML导出器"""
    
    @staticmethod
    def export_task_result(
        task_id: str,
        description: str,
        result: str,
        steps: List[Dict],
        metadata: Dict = None
    ) -> str:
        """导出任务结果为HTML"""
        styles = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #1a1a2e; border-bottom: 2px solid #4361ee; padding-bottom: 10px; }
            h2 { color: #16213e; margin-top: 30px; }
            h3 { color: #0f3460; }
            .meta { background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 15px 0; }
            .meta span { display: inline-block; margin-right: 20px; }
            .step { border-left: 3px solid #4361ee; padding-left: 15px; margin: 15px 0; }
            .step.completed { border-color: #2ecc71; }
            .step.failed { border-color: #e74c3c; }
            .status { display: inline-block; padding: 3px 10px; border-radius: 15px; font-size: 0.85em; }
            .status.completed { background: #d4edda; color: #155724; }
            .status.failed { background: #f8d7da; color: #721c24; }
            .status.pending { background: #fff3cd; color: #856404; }
            pre { background: #1a1a2e; color: #e0e0e0; padding: 15px; border-radius: 8px; overflow-x: auto; }
            .result { background: #e8f4fd; border: 1px solid #b6d4fe; padding: 20px; border-radius: 8px; margin-top: 20px; }
            .footer { text-align: center; color: #888; margin-top: 30px; font-size: 0.9em; }
        </style>
        """
        
        steps_html = ""
        for i, step in enumerate(steps, 1):
            status = step.get('status', 'pending')
            status_class = status
            status_text = {'completed': '已完成', 'failed': '失败', 'pending': '待执行', 'running': '执行中'}.get(status, status)
            
            output_html = ""
            if step.get('output'):
                output_html = f"<pre>{html.escape(step.get('output', ''))}</pre>"
            
            steps_html += f"""
            <div class="step {status_class}">
                <h3>步骤 {i}: {html.escape(step.get('description', ''))}</h3>
                <p><strong>Agent:</strong> {html.escape(step.get('agent', 'unknown'))} 
                   <span class="status {status_class}">{status_text}</span></p>
                {output_html}
            </div>
            """
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>任务报告 - {html.escape(task_id)}</title>
    {styles}
</head>
<body>
    <div class="container">
        <h1>📋 任务执行报告</h1>
        
        <div class="meta">
            <span><strong>任务ID:</strong> {html.escape(task_id)}</span>
            <span><strong>时间:</strong> {metadata.get('created_at', '') if metadata else ''}</span>
            <span><strong>状态:</strong> {metadata.get('status', 'completed') if metadata else 'completed'}</span>
        </div>
        
        <h2>任务描述</h2>
        <p>{html.escape(description)}</p>
        
        <h2>执行步骤</h2>
        {steps_html}
        
        <h2>最终结果</h2>
        <div class="result">
            {html.escape(result).replace(chr(10), '<br>')}
        </div>
        
        <p class="footer">报告生成时间: {datetime.now().isoformat()}</p>
    </div>
</body>
</html>"""


class JSONExporter:
    """JSON导出器"""
    
    @staticmethod
    def export_task_result(
        task_id: str,
        description: str,
        result: str,
        steps: List[Dict],
        metadata: Dict = None
    ) -> str:
        """导出任务结果为JSON"""
        data = {
            "task_id": task_id,
            "description": description,
            "result": result,
            "steps": steps,
            "metadata": metadata or {},
            "exported_at": datetime.now().isoformat()
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def export_conversation(
        messages: List[Dict],
        session_id: str = "",
        metadata: Dict = None
    ) -> str:
        """导出对话为JSON"""
        data = {
            "session_id": session_id,
            "messages": messages,
            "metadata": metadata or {},
            "exported_at": datetime.now().isoformat()
        }
        return json.dumps(data, indent=2, ensure_ascii=False)


class PDFExporter:
    """PDF导出器 (需要额外依赖)"""
    
    _font_registered = False
    _font_name = 'SimSun'  # 默认使用宋体
    
    @classmethod
    def _register_chinese_font(cls):
        """注册中文字体"""
        if cls._font_registered:
            return cls._font_name
        
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        
        # Windows 系统字体路径
        font_paths = [
            # Windows 常用中文字体
            'C:/Windows/Fonts/simsun.ttc',      # 宋体
            'C:/Windows/Fonts/simhei.ttf',      # 黑体
            'C:/Windows/Fonts/msyh.ttc',        # 微软雅黑
            'C:/Windows/Fonts/msyhbd.ttc',      # 微软雅黑粗体
            'C:/Windows/Fonts/simkai.ttf',      # 楷体
            # Linux 常用中文字体
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/arphic/uming.ttc',
            # macOS 字体
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
        ]
        
        font_names = ['SimSun', 'SimHei', 'MSYH', 'MSYHBD', 'SimKai', 'WQY', 'UMing', 'PingFang', 'STHeiti']
        
        for font_path, font_name in zip(font_paths, font_names):
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    cls._font_registered = True
                    cls._font_name = font_name
                    logger.info(f"Registered Chinese font: {font_name} from {font_path}")
                    return font_name
                except Exception as e:
                    logger.warning(f"Failed to register font {font_path}: {e}")
                    continue
        
        # 如果没有找到中文字体，使用默认字体（可能不支持中文）
        logger.warning("No Chinese font found, PDF may not display Chinese correctly")
        cls._font_registered = True
        cls._font_name = 'Helvetica'
        return 'Helvetica'
    
    @staticmethod
    def is_available() -> bool:
        """检查PDF导出是否可用"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            return True
        except ImportError:
            return False
    
    @classmethod
    def export_task_result(
        cls,
        task_id: str,
        description: str,
        result: str,
        steps: List[Dict],
        metadata: Dict = None
    ) -> bytes:
        """导出任务结果为PDF（支持中文）"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            
            # 注册中文字体
            font_name = cls._register_chinese_font()
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                    leftMargin=50, rightMargin=50,
                                    topMargin=50, bottomMargin=50)
            
            # 创建支持中文的样式
            styles = getSampleStyleSheet()
            
            # 自定义中文样式
            title_style = ParagraphStyle(
                'ChineseTitle',
                parent=styles['Title'],
                fontName=font_name,
                fontSize=24,
                spaceAfter=20,
                alignment=1  # 居中
            )
            
            heading_style = ParagraphStyle(
                'ChineseHeading',
                parent=styles['Heading2'],
                fontName=font_name,
                fontSize=16,
                spaceBefore=15,
                spaceAfter=10,
                textColor=colors.HexColor('#4361EE')
            )
            
            normal_style = ParagraphStyle(
                'ChineseNormal',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=11,
                leading=16,
                spaceBefore=5,
                spaceAfter=5
            )
            
            meta_style = ParagraphStyle(
                'ChineseMeta',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
                textColor=colors.HexColor('#666666'),
                spaceBefore=3,
                spaceAfter=3
            )
            
            story = []
            
            # 标题
            story.append(Paragraph("📋 任务执行报告", title_style))
            story.append(Spacer(1, 20))
            
            # 分隔线
            from reportlab.platypus import HRFlowable
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E0E0E0')))
            story.append(Spacer(1, 15))
            
            # 任务信息
            story.append(Paragraph("📌 任务信息", heading_style))
            created_at = metadata.get('created_at', datetime.now().isoformat()) if metadata else datetime.now().isoformat()
            status = metadata.get('status', 'completed') if metadata else 'completed'
            status_text = {'completed': '已完成', 'failed': '失败', 'running': '执行中', 'pending': '待执行'}.get(status, status)
            
            story.append(Paragraph(f"<b>任务ID:</b> {html.escape(task_id)}", meta_style))
            story.append(Paragraph(f"<b>创建时间:</b> {html.escape(str(created_at))}", meta_style))
            story.append(Paragraph(f"<b>状态:</b> {html.escape(status_text)}", meta_style))
            story.append(Spacer(1, 10))
            
            # 任务描述
            story.append(Paragraph("📝 任务描述", heading_style))
            story.append(Paragraph(html.escape(description), normal_style))
            story.append(Spacer(1, 15))
            
            # 执行步骤
            if steps:
                story.append(Paragraph("🔄 执行步骤", heading_style))
                for i, step in enumerate(steps, 1):
                    step_status = step.get('status', 'unknown')
                    status_icon = {'completed': '✅', 'failed': '❌', 'running': '🔄', 'pending': '⏳'}.get(step_status, '❓')
                    step_desc = html.escape(step.get('description', ''))
                    agent = html.escape(step.get('agent', 'unknown'))
                    story.append(Paragraph(
                        f"{status_icon} <b>步骤 {i}:</b> {step_desc} <i>(Agent: {agent})</i>",
                        normal_style
                    ))
                    if step.get('output'):
                        output_text = html.escape(step.get('output', '')[:200])
                        story.append(Paragraph(f"    └─ 输出: {output_text}...", meta_style))
                story.append(Spacer(1, 15))
            
            # 最终结果
            story.append(Paragraph("🎯 最终结果", heading_style))
            # 处理结果文本，分段显示
            result_text = html.escape(result) if result else "无结果"
            # 限制结果长度，避免 PDF 过大
            if len(result_text) > 3000:
                result_text = result_text[:3000] + "... (内容过长，已截断)"
            
            # 将换行符转换为段落
            for para in result_text.split('\n'):
                if para.strip():
                    story.append(Paragraph(para, normal_style))
            
            story.append(Spacer(1, 20))
            
            # 页脚
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E0E0E0')))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=9,
                textColor=colors.HexColor('#999999'),
                alignment=1
            )
            story.append(Paragraph(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Powered by JoinFlow", footer_style))
            
            doc.build(story)
            return buffer.getvalue()
            
        except ImportError:
            logger.warning("ReportLab not installed, cannot export PDF")
            raise ImportError("需要安装 reportlab: pip install reportlab")
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            import traceback
            traceback.print_exc()
            raise


class ExportManager:
    """导出管理器"""
    
    def __init__(self, output_dir: str = "./exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_task(
        self,
        task_id: str,
        description: str,
        result: str,
        steps: List[Dict],
        format: str = "markdown",
        metadata: Dict = None,
        save_to_file: bool = True
    ) -> str:
        """
        导出任务结果
        
        Args:
            format: markdown, html, json, pdf
            save_to_file: 是否保存到文件
            
        Returns:
            导出内容或文件路径
        """
        exporters = {
            "markdown": MarkdownExporter.export_task_result,
            "md": MarkdownExporter.export_task_result,
            "html": HTMLExporter.export_task_result,
            "json": JSONExporter.export_task_result,
        }
        
        if format.lower() == "pdf":
            if not PDFExporter.is_available():
                raise ImportError("PDF导出需要安装 reportlab")
            content = PDFExporter.export_task_result(
                task_id, description, result, steps, metadata
            )
            if save_to_file:
                file_path = self.output_dir / f"task_{task_id}.pdf"
                with open(file_path, 'wb') as f:
                    f.write(content)
                return str(file_path)
            return content
        
        exporter = exporters.get(format.lower())
        if not exporter:
            raise ValueError(f"Unsupported format: {format}")
        
        content = exporter(task_id, description, result, steps, metadata)
        
        if save_to_file:
            ext = {"markdown": "md", "md": "md", "html": "html", "json": "json"}.get(format.lower(), "txt")
            file_path = self.output_dir / f"task_{task_id}.{ext}"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return str(file_path)
        
        return content
    
    def export_conversation(
        self,
        session_id: str,
        messages: List[Dict],
        format: str = "markdown",
        metadata: Dict = None,
        save_to_file: bool = True
    ) -> str:
        """导出对话历史"""
        if format.lower() in ("markdown", "md"):
            content = MarkdownExporter.export_conversation(messages, session_id, metadata)
            ext = "md"
        elif format.lower() == "json":
            content = JSONExporter.export_conversation(messages, session_id, metadata)
            ext = "json"
        else:
            raise ValueError(f"Unsupported format for conversation: {format}")
        
        if save_to_file:
            file_path = self.output_dir / f"conversation_{session_id}.{ext}"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return str(file_path)
        
        return content
    
    def get_available_formats(self) -> List[Dict]:
        """获取可用的导出格式"""
        formats = [
            {"id": "markdown", "name": "Markdown", "extension": ".md", "available": True},
            {"id": "html", "name": "HTML", "extension": ".html", "available": True},
            {"id": "json", "name": "JSON", "extension": ".json", "available": True},
            {"id": "pdf", "name": "PDF", "extension": ".pdf", "available": PDFExporter.is_available()},
        ]
        return formats

