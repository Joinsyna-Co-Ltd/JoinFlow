"""
Data Processing Agent
=====================

Provides data processing and analysis capabilities:
- CSV/Excel file handling
- Data transformation and cleaning
- Statistical analysis
- Chart generation
- Data export
"""

import io
import json
import base64
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Dict, List, Union
from pathlib import Path
import logging

from .base import (
    BaseAgent, AgentResult, AgentConfig, AgentType,
    AgentAction, Tool
)

logger = logging.getLogger(__name__)


@dataclass
class DataFrameInfo:
    """Information about a DataFrame"""
    rows: int
    columns: int
    column_names: List[str]
    dtypes: Dict[str, str]
    memory_mb: float
    sample_data: List[Dict]
    statistics: Optional[Dict] = None


class DataProcessingAgent(BaseAgent):
    """
    Agent for data processing and analysis.
    
    Capabilities:
    - Load and parse CSV, Excel, JSON files
    - Data transformation and cleaning
    - Statistical analysis
    - Generate visualizations
    - Export data in various formats
    
    Requires: pandas, numpy, matplotlib (optional)
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config)
        self._workspace = Path(config.os_workspace if config else "./workspace")
        self._workspace.mkdir(parents=True, exist_ok=True)
        self._dataframes: Dict[str, Any] = {}  # Store loaded DataFrames
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are available"""
        self._has_pandas = False
        self._has_numpy = False
        self._has_matplotlib = False
        
        try:
            import pandas
            self._has_pandas = True
            self._pd = pandas
        except ImportError:
            logger.warning("pandas not available. Install with: pip install pandas")
        
        try:
            import numpy
            self._has_numpy = True
            self._np = numpy
        except ImportError:
            logger.warning("numpy not available. Install with: pip install numpy")
        
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            self._has_matplotlib = True
            self._plt = plt
        except ImportError:
            logger.warning("matplotlib not available. Install with: pip install matplotlib")
    
    @property
    def agent_type(self) -> AgentType:
        return AgentType.OS  # Data processing is similar to file operations
    
    @property
    def name(self) -> str:
        return "Data Processing Agent"
    
    @property
    def description(self) -> str:
        return """Data processing agent capable of:
        - Loading CSV, Excel, JSON data files
        - Data cleaning and transformation
        - Statistical analysis and summaries
        - Generating charts and visualizations
        - Exporting processed data
        """
    
    def can_handle(self, task: str) -> bool:
        """Check if this is a data processing task"""
        data_keywords = [
            "数据", "csv", "excel", "xlsx", "统计", "分析", "图表",
            "data", "dataframe", "statistics", "analysis", "chart",
            "plot", "graph", "表格", "处理", "清洗", "转换",
            "pandas", "numpy", "visualization"
        ]
        return any(kw in task.lower() for kw in data_keywords)
    
    def execute(self, task: str, context: Optional[dict] = None) -> AgentResult:
        """Execute a data processing task"""
        result = self._create_result()
        
        if not self._has_pandas:
            result.output = "pandas is required for data processing. Install with: pip install pandas"
            result.finalize(success=False, error="pandas not installed")
            return result
        
        try:
            # Parse task
            action, params = self._parse_task(task)
            output = self._execute_action(action, params, result)
            
            result.output = str(output) if output else "数据处理完成"
            result.data = output if isinstance(output, dict) else {"result": output}
            result.finalize(success=True)
            
        except Exception as e:
            self._handle_error(result, e)
        
        return result
    
    def _parse_task(self, task: str) -> tuple[str, dict]:
        """Parse task into action and parameters"""
        task_lower = task.lower()
        
        # Load data
        if any(kw in task_lower for kw in ["加载", "读取", "打开", "load", "read", "open"]):
            path = self._extract_path(task)
            return "load", {"path": path}
        
        # Describe data
        if any(kw in task_lower for kw in ["描述", "信息", "describe", "info", "summary"]):
            name = self._extract_df_name(task)
            return "describe", {"name": name}
        
        # Statistics
        if any(kw in task_lower for kw in ["统计", "statistics", "stats", "mean", "median"]):
            name = self._extract_df_name(task)
            return "statistics", {"name": name}
        
        # Filter/Query
        if any(kw in task_lower for kw in ["筛选", "过滤", "filter", "query", "where"]):
            name = self._extract_df_name(task)
            condition = self._extract_condition(task)
            return "filter", {"name": name, "condition": condition}
        
        # Sort
        if any(kw in task_lower for kw in ["排序", "sort"]):
            name = self._extract_df_name(task)
            column = self._extract_column(task)
            return "sort", {"name": name, "column": column}
        
        # Plot
        if any(kw in task_lower for kw in ["绘图", "图表", "plot", "chart", "graph", "visualize"]):
            name = self._extract_df_name(task)
            chart_type = self._extract_chart_type(task)
            return "plot", {"name": name, "type": chart_type}
        
        # Export
        if any(kw in task_lower for kw in ["导出", "保存", "export", "save"]):
            name = self._extract_df_name(task)
            path = self._extract_path(task)
            return "export", {"name": name, "path": path}
        
        # Default: try to load if path found
        path = self._extract_path(task)
        if path:
            return "load", {"path": path}
        
        return "describe", {"name": "default"}
    
    def _extract_path(self, task: str) -> str:
        """Extract file path from task"""
        import re
        patterns = [
            r'["\']([^"\']+\.(csv|xlsx|xls|json))["\']',
            r'(\S+\.(csv|xlsx|xls|json))'
        ]
        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
    
    def _extract_df_name(self, task: str) -> str:
        """Extract DataFrame name from task"""
        if self._dataframes:
            return list(self._dataframes.keys())[-1]  # Last loaded
        return "default"
    
    def _extract_column(self, task: str) -> str:
        """Extract column name from task"""
        import re
        match = re.search(r'["\'](\w+)["\']|按\s*(\w+)|by\s+(\w+)', task)
        if match:
            return match.group(1) or match.group(2) or match.group(3)
        return ""
    
    def _extract_condition(self, task: str) -> str:
        """Extract filter condition from task"""
        import re
        match = re.search(r'["\']([^"\']+)["\']|条件[：:]\s*(.+)', task)
        if match:
            return match.group(1) or match.group(2)
        return ""
    
    def _extract_chart_type(self, task: str) -> str:
        """Extract chart type from task"""
        task_lower = task.lower()
        if any(kw in task_lower for kw in ["柱状", "bar"]):
            return "bar"
        if any(kw in task_lower for kw in ["折线", "line"]):
            return "line"
        if any(kw in task_lower for kw in ["饼", "pie"]):
            return "pie"
        if any(kw in task_lower for kw in ["散点", "scatter"]):
            return "scatter"
        if any(kw in task_lower for kw in ["直方", "hist"]):
            return "hist"
        return "bar"  # Default
    
    def _execute_action(self, action: str, params: dict, result: AgentResult) -> Any:
        """Execute the parsed action"""
        
        if action == "load":
            return self.load_data(params["path"], result)
        
        elif action == "describe":
            return self.describe_data(params.get("name", "default"), result)
        
        elif action == "statistics":
            return self.get_statistics(params.get("name", "default"), result)
        
        elif action == "filter":
            return self.filter_data(
                params.get("name", "default"),
                params.get("condition", ""),
                result
            )
        
        elif action == "sort":
            return self.sort_data(
                params.get("name", "default"),
                params.get("column", ""),
                result
            )
        
        elif action == "plot":
            return self.create_plot(
                params.get("name", "default"),
                params.get("type", "bar"),
                result
            )
        
        elif action == "export":
            return self.export_data(
                params.get("name", "default"),
                params.get("path", "output.csv"),
                result
            )
        
        return None
    
    # -------------------------
    # Data Operations
    # -------------------------
    
    def load_data(self, path: str, result: AgentResult) -> DataFrameInfo:
        """Load data from file"""
        self._log_action(result, "load_data", f"Loading: {path}")
        
        file_path = self._workspace / path if not Path(path).is_absolute() else Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Load based on extension
        ext = file_path.suffix.lower()
        
        if ext == ".csv":
            df = self._pd.read_csv(file_path)
        elif ext in (".xlsx", ".xls"):
            df = self._pd.read_excel(file_path)
        elif ext == ".json":
            df = self._pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
        # Store DataFrame
        name = file_path.stem
        self._dataframes[name] = df
        
        return self._get_df_info(df, name)
    
    def describe_data(self, name: str, result: AgentResult) -> DataFrameInfo:
        """Get DataFrame description"""
        self._log_action(result, "describe", f"Describing: {name}")
        
        df = self._get_df(name)
        return self._get_df_info(df, name)
    
    def get_statistics(self, name: str, result: AgentResult) -> Dict:
        """Get statistical summary"""
        self._log_action(result, "statistics", f"Computing statistics: {name}")
        
        df = self._get_df(name)
        
        stats = {
            "numeric_summary": df.describe().to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "unique_counts": df.nunique().to_dict(),
        }
        
        # Add correlation for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 1:
            stats["correlation"] = df[numeric_cols].corr().to_dict()
        
        return stats
    
    def filter_data(self, name: str, condition: str, result: AgentResult) -> DataFrameInfo:
        """Filter DataFrame by condition"""
        self._log_action(result, "filter", f"Filtering {name}: {condition}")
        
        df = self._get_df(name)
        
        try:
            filtered_df = df.query(condition)
        except Exception:
            # Try eval as fallback
            filtered_df = df[df.eval(condition)]
        
        # Store filtered result
        filtered_name = f"{name}_filtered"
        self._dataframes[filtered_name] = filtered_df
        
        return self._get_df_info(filtered_df, filtered_name)
    
    def sort_data(self, name: str, column: str, result: AgentResult, ascending: bool = True) -> DataFrameInfo:
        """Sort DataFrame by column"""
        self._log_action(result, "sort", f"Sorting {name} by {column}")
        
        df = self._get_df(name)
        
        if column not in df.columns:
            raise ValueError(f"Column not found: {column}")
        
        sorted_df = df.sort_values(by=column, ascending=ascending)
        
        # Store sorted result
        sorted_name = f"{name}_sorted"
        self._dataframes[sorted_name] = sorted_df
        
        return self._get_df_info(sorted_df, sorted_name)
    
    def create_plot(self, name: str, chart_type: str, result: AgentResult) -> Dict:
        """Create a visualization"""
        if not self._has_matplotlib:
            return {"error": "matplotlib not installed"}
        
        self._log_action(result, "plot", f"Creating {chart_type} chart for {name}")
        
        df = self._get_df(name)
        
        # Create figure
        fig, ax = self._plt.subplots(figsize=(10, 6))
        
        # Select numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if chart_type == "bar":
            if len(numeric_cols) > 0:
                df[numeric_cols[:5]].plot(kind='bar', ax=ax)
        elif chart_type == "line":
            if len(numeric_cols) > 0:
                df[numeric_cols[:5]].plot(kind='line', ax=ax)
        elif chart_type == "pie":
            if len(numeric_cols) > 0:
                df[numeric_cols[0]].value_counts().head(10).plot(kind='pie', ax=ax)
        elif chart_type == "scatter":
            if len(numeric_cols) >= 2:
                df.plot(kind='scatter', x=numeric_cols[0], y=numeric_cols[1], ax=ax)
        elif chart_type == "hist":
            if len(numeric_cols) > 0:
                df[numeric_cols[0]].hist(ax=ax, bins=20)
        
        ax.set_title(f"{chart_type.title()} Chart - {name}")
        
        # Save to buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Also save to file
        output_path = self._workspace / f"{name}_{chart_type}.png"
        fig.savefig(output_path, dpi=100, bbox_inches='tight')
        
        self._plt.close(fig)
        
        return {
            "chart_type": chart_type,
            "saved_to": str(output_path),
            "image_base64": base64.b64encode(buf.getvalue()).decode()
        }
    
    def export_data(self, name: str, path: str, result: AgentResult) -> str:
        """Export DataFrame to file"""
        self._log_action(result, "export", f"Exporting {name} to {path}")
        
        df = self._get_df(name)
        
        output_path = self._workspace / path if not Path(path).is_absolute() else Path(path)
        ext = output_path.suffix.lower()
        
        if ext == ".csv":
            df.to_csv(output_path, index=False)
        elif ext in (".xlsx", ".xls"):
            df.to_excel(output_path, index=False)
        elif ext == ".json":
            df.to_json(output_path, orient='records')
        else:
            df.to_csv(output_path, index=False)
        
        return f"Data exported to {output_path}"
    
    # -------------------------
    # Helper Methods
    # -------------------------
    
    def _get_df(self, name: str) -> Any:
        """Get DataFrame by name"""
        if name in self._dataframes:
            return self._dataframes[name]
        if self._dataframes:
            return list(self._dataframes.values())[-1]
        raise ValueError(f"No data loaded. Load data first.")
    
    def _get_df_info(self, df: Any, name: str) -> DataFrameInfo:
        """Get DataFrame information"""
        return DataFrameInfo(
            rows=len(df),
            columns=len(df.columns),
            column_names=df.columns.tolist(),
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            memory_mb=df.memory_usage(deep=True).sum() / 1024 / 1024,
            sample_data=df.head(5).to_dict('records'),
            statistics=df.describe().to_dict() if len(df) > 0 else None
        )
    
    def get_tools(self) -> List[Tool]:
        """Get tools for LLM function calling"""
        return [
            Tool(
                name="data_load",
                description="Load data from CSV, Excel, or JSON file",
                func=lambda path: self.load_data(path, self._create_result()).__dict__,
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to data file"}
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="data_describe",
                description="Get description and statistics of loaded data",
                func=lambda name="default": self.describe_data(name, self._create_result()).__dict__,
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of loaded dataset"}
                    }
                }
            ),
            Tool(
                name="data_plot",
                description="Create a chart/visualization of the data",
                func=lambda name="default", chart_type="bar": self.create_plot(name, chart_type, self._create_result()),
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of dataset"},
                        "chart_type": {"type": "string", "enum": ["bar", "line", "pie", "scatter", "hist"]}
                    }
                }
            ),
        ]

