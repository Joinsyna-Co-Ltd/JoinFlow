"""
Statistics & Analytics
======================

Token consumption, cost estimation, and execution analytics.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


# 模型定价 (每1K tokens的价格，单位: USD)
MODEL_PRICING = {
    # OpenAI
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "o1": {"input": 0.015, "output": 0.06},
    "o1-mini": {"input": 0.003, "output": 0.012},
    
    # Anthropic
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    
    # DeepSeek
    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
    "deepseek-coder": {"input": 0.00014, "output": 0.00028},
    
    # Default
    "default": {"input": 0.001, "output": 0.002},
}


@dataclass
class UsageRecord:
    """使用记录"""
    id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 任务信息
    task_id: str = ""
    task_description: str = ""
    
    # 模型信息
    model: str = ""
    provider: str = ""
    
    # Token使用
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    # 成本
    estimated_cost: float = 0.0
    
    # 执行信息
    execution_time_ms: float = 0
    success: bool = True
    agent_type: str = ""
    
    # 用户
    user_id: str = "default"
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "UsageRecord":
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class DailyStats:
    """每日统计"""
    date: str = ""                    # YYYY-MM-DD
    
    # 任务统计
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    
    # Token统计
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    
    # 成本统计
    total_cost: float = 0.0
    
    # 执行时间
    total_execution_time_ms: float = 0
    
    # Agent使用
    agent_usage: Dict[str, int] = field(default_factory=dict)
    
    # 模型使用
    model_usage: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "DailyStats":
        return cls(**data)


class StatisticsManager:
    """统计管理器"""
    
    def __init__(self, storage_path: str = "./statistics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.records: List[UsageRecord] = []
        self.daily_stats: Dict[str, DailyStats] = {}
        
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        # 加载最近的记录
        records_file = self.storage_path / "records.json"
        if records_file.exists():
            try:
                with open(records_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.records = [UsageRecord.from_dict(r) for r in data.get('records', [])]
                logger.info(f"Loaded {len(self.records)} usage records")
            except Exception as e:
                logger.error(f"Failed to load usage records: {e}")
        
        # 加载每日统计
        stats_file = self.storage_path / "daily_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for stats_data in data.get('stats', []):
                    stats = DailyStats.from_dict(stats_data)
                    self.daily_stats[stats.date] = stats
            except Exception as e:
                logger.error(f"Failed to load daily stats: {e}")
    
    def _save_data(self):
        """保存数据"""
        # 只保留最近30天的详细记录
        cutoff = datetime.now() - timedelta(days=30)
        self.records = [r for r in self.records if r.timestamp > cutoff]
        
        records_file = self.storage_path / "records.json"
        try:
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'records': [r.to_dict() for r in self.records[-10000:]]  # 最多保留1万条
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save usage records: {e}")
        
        stats_file = self.storage_path / "daily_stats.json"
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'stats': [s.to_dict() for s in self.daily_stats.values()]
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save daily stats: {e}")
    
    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本"""
        # 标准化模型名称
        model_lower = model.lower()
        
        pricing = MODEL_PRICING.get("default")
        for model_key, price in MODEL_PRICING.items():
            if model_key in model_lower:
                pricing = price
                break
        
        cost = (input_tokens / 1000 * pricing["input"] + 
                output_tokens / 1000 * pricing["output"])
        
        return round(cost, 6)
    
    def record_usage(
        self,
        task_id: str,
        task_description: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        execution_time_ms: float,
        success: bool = True,
        agent_type: str = "llm",
        user_id: str = "default",
        provider: str = "openai"
    ) -> UsageRecord:
        """记录使用"""
        import uuid
        
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        record = UsageRecord(
            id=str(uuid.uuid4()),
            task_id=task_id,
            task_description=task_description[:200],
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost=cost,
            execution_time_ms=execution_time_ms,
            success=success,
            agent_type=agent_type,
            user_id=user_id
        )
        
        self.records.append(record)
        self._update_daily_stats(record)
        self._save_data()
        
        return record
    
    def _update_daily_stats(self, record: UsageRecord):
        """更新每日统计"""
        date_str = record.timestamp.strftime("%Y-%m-%d")
        
        if date_str not in self.daily_stats:
            self.daily_stats[date_str] = DailyStats(date=date_str)
        
        stats = self.daily_stats[date_str]
        stats.total_tasks += 1
        
        if record.success:
            stats.successful_tasks += 1
        else:
            stats.failed_tasks += 1
        
        stats.total_input_tokens += record.input_tokens
        stats.total_output_tokens += record.output_tokens
        stats.total_cost += record.estimated_cost
        stats.total_execution_time_ms += record.execution_time_ms
        
        # Agent使用统计
        agent = record.agent_type or "unknown"
        stats.agent_usage[agent] = stats.agent_usage.get(agent, 0) + 1
        
        # 模型使用统计
        model = record.model or "unknown"
        stats.model_usage[model] = stats.model_usage.get(model, 0) + 1
    
    def get_summary(
        self,
        days: int = 30,
        user_id: str = None
    ) -> Dict[str, Any]:
        """获取统计摘要"""
        cutoff = datetime.now() - timedelta(days=days)
        
        records = [r for r in self.records if r.timestamp > cutoff]
        if user_id:
            records = [r for r in records if r.user_id == user_id]
        
        if not records:
            return {
                "period_days": days,
                "total_tasks": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "success_rate": 0,
                "avg_execution_time": 0,
            }
        
        total_tasks = len(records)
        successful = len([r for r in records if r.success])
        total_tokens = sum(r.total_tokens for r in records)
        total_cost = sum(r.estimated_cost for r in records)
        total_time = sum(r.execution_time_ms for r in records)
        
        return {
            "period_days": days,
            "total_tasks": total_tasks,
            "successful_tasks": successful,
            "failed_tasks": total_tasks - successful,
            "success_rate": round(successful / total_tasks * 100, 1) if total_tasks > 0 else 0,
            "total_input_tokens": sum(r.input_tokens for r in records),
            "total_output_tokens": sum(r.output_tokens for r in records),
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "avg_execution_time_ms": round(total_time / total_tasks, 1) if total_tasks > 0 else 0,
            "avg_tokens_per_task": round(total_tokens / total_tasks) if total_tasks > 0 else 0,
            "avg_cost_per_task": round(total_cost / total_tasks, 6) if total_tasks > 0 else 0,
        }
    
    def get_daily_trend(
        self,
        days: int = 30,
        user_id: str = None
    ) -> List[Dict]:
        """获取每日趋势"""
        result = []
        
        for i in range(days, -1, -1):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            if date_str in self.daily_stats:
                stats = self.daily_stats[date_str]
                result.append({
                    "date": date_str,
                    "tasks": stats.total_tasks,
                    "tokens": stats.total_input_tokens + stats.total_output_tokens,
                    "cost": round(stats.total_cost, 4),
                    "success_rate": round(
                        stats.successful_tasks / stats.total_tasks * 100 
                        if stats.total_tasks > 0 else 0, 1
                    )
                })
            else:
                result.append({
                    "date": date_str,
                    "tasks": 0,
                    "tokens": 0,
                    "cost": 0,
                    "success_rate": 0
                })
        
        return result
    
    def get_agent_usage(self, days: int = 30) -> Dict[str, int]:
        """获取Agent使用统计"""
        cutoff = datetime.now() - timedelta(days=days)
        usage = defaultdict(int)
        
        for record in self.records:
            if record.timestamp > cutoff:
                usage[record.agent_type or "unknown"] += 1
        
        return dict(usage)
    
    def get_model_usage(self, days: int = 30) -> Dict[str, Dict]:
        """获取模型使用统计"""
        cutoff = datetime.now() - timedelta(days=days)
        usage = defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0})
        
        for record in self.records:
            if record.timestamp > cutoff:
                model = record.model or "unknown"
                usage[model]["count"] += 1
                usage[model]["tokens"] += record.total_tokens
                usage[model]["cost"] += record.estimated_cost
        
        # 四舍五入
        for model in usage:
            usage[model]["cost"] = round(usage[model]["cost"], 4)
        
        return dict(usage)
    
    def get_cost_breakdown(self, days: int = 30) -> Dict[str, float]:
        """获取成本分解"""
        cutoff = datetime.now() - timedelta(days=days)
        
        by_model = defaultdict(float)
        by_agent = defaultdict(float)
        
        for record in self.records:
            if record.timestamp > cutoff:
                by_model[record.model or "unknown"] += record.estimated_cost
                by_agent[record.agent_type or "unknown"] += record.estimated_cost
        
        return {
            "by_model": {k: round(v, 4) for k, v in by_model.items()},
            "by_agent": {k: round(v, 4) for k, v in by_agent.items()},
            "total": round(sum(by_model.values()), 4)
        }
    
    def get_recent_records(
        self,
        limit: int = 100,
        user_id: str = None,
        task_id: str = None
    ) -> List[UsageRecord]:
        """获取最近记录"""
        records = self.records
        
        if user_id:
            records = [r for r in records if r.user_id == user_id]
        if task_id:
            records = [r for r in records if r.task_id == task_id]
        
        return sorted(records, key=lambda r: r.timestamp, reverse=True)[:limit]
    
    def export_report(
        self,
        days: int = 30,
        format: str = "json"
    ) -> str:
        """导出报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "summary": self.get_summary(days),
            "daily_trend": self.get_daily_trend(days),
            "agent_usage": self.get_agent_usage(days),
            "model_usage": self.get_model_usage(days),
            "cost_breakdown": self.get_cost_breakdown(days),
        }
        
        if format == "json":
            return json.dumps(report, indent=2, ensure_ascii=False)
        elif format == "markdown":
            return self._format_markdown_report(report)
        else:
            return json.dumps(report, indent=2, ensure_ascii=False)
    
    def _format_markdown_report(self, report: Dict) -> str:
        """格式化Markdown报告"""
        summary = report["summary"]
        
        md = f"""# 使用统计报告

生成时间: {report['generated_at']}
统计周期: 最近 {report['period_days']} 天

## 概览

| 指标 | 数值 |
|------|------|
| 总任务数 | {summary['total_tasks']} |
| 成功任务 | {summary['successful_tasks']} |
| 失败任务 | {summary['failed_tasks']} |
| 成功率 | {summary['success_rate']}% |
| 总Token数 | {summary['total_tokens']:,} |
| 总成本 | ${summary['total_cost']:.4f} |
| 平均执行时间 | {summary['avg_execution_time_ms']:.1f}ms |

## 成本分解

### 按模型
"""
        
        for model, cost in report['cost_breakdown']['by_model'].items():
            md += f"- {model}: ${cost:.4f}\n"
        
        md += "\n### 按Agent\n"
        for agent, cost in report['cost_breakdown']['by_agent'].items():
            md += f"- {agent}: ${cost:.4f}\n"
        
        return md

