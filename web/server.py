#!/usr/bin/env python3
"""
JoinFlow Web Server
====================

Serves the workflow-centric web UI and API endpoints.
"""

import os
import sys
import json
import uuid
import asyncio
import logging
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from copy import deepcopy
import shutil
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# Configuration Manager
# ============================================

class ConfigManager:
    """Manages application configuration from JSON file"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        # Config file is in project root directory
        self.config_path = Path(__file__).parent.parent / "config.json"
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "models": [
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "provider": "openai",
                    "enabled": True,
                    "is_default": True
                }
            ],
            "settings": {
                "max_parallel_tasks": 3,
                "auto_retry": True,
                "timeout_seconds": 300
            }
        }
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def reload(self):
        """Reload configuration from file"""
        self._config = self._load_config()
        return self._config
    
    @property
    def config(self) -> Dict[str, Any]:
        return self._config
    
    # Model management
    def get_models(self) -> List[Dict]:
        """Get all models"""
        return self._config.get("models", [])
    
    def get_enabled_models(self) -> List[Dict]:
        """Get enabled models only"""
        return [m for m in self.get_models() if m.get("enabled", False)]
    
    def get_default_model(self) -> Optional[Dict]:
        """Get the default model"""
        for model in self.get_models():
            if model.get("is_default", False) or model.get("default", False):
                return model
        models = self.get_enabled_models()
        return models[0] if models else None
    
    def get_model(self, model_id: str) -> Optional[Dict]:
        """Get model by ID"""
        for model in self.get_models():
            if model.get("id") == model_id:
                return model
        return None
    
    def _detect_provider(self, model_id: str) -> str:
        """Auto-detect provider based on model ID"""
        try:
            from joinflow_core.llm_providers import detect_provider
            return detect_provider(model_id)
        except ImportError:
            # Fallback to basic detection
            model_id_lower = model_id.lower()
            
            keyword_mapping = {
                'openai': ['gpt', 'o1', 'o3', 'davinci', 'text-embedding'],
                'anthropic': ['claude'],
                'google': ['gemini', 'palm', 'bard'],
                'mistral': ['mistral', 'mixtral', 'codestral', 'pixtral'],
                'deepseek': ['deepseek'],
                'qwen': ['qwen'],
                'baidu': ['ernie'],
                'zhipu': ['glm', 'codegeex'],
                'moonshot': ['moonshot'],
                'yi': ['yi-'],
                'minimax': ['abab'],
                'doubao': ['doubao'],
                'spark': ['spark'],
                'baichuan': ['baichuan'],
                'stepfun': ['step-'],
                'cohere': ['command'],
                'groq': ['llama', 'gemma'],
                'together': ['meta-llama/', 'mistralai/'],
                'perplexity': ['sonar'],
                'fireworks': ['accounts/fireworks'],
                'azure': ['azure'],
                'ollama': [':latest'],
            }
            
            for provider, keywords in keyword_mapping.items():
                if any(kw in model_id_lower for kw in keywords):
                    return provider
            
            return 'openai'
    
    def _get_default_api_base(self, provider: str) -> str:
        """Get default API base URL for provider"""
        try:
            from joinflow_core.llm_providers import get_api_base
            return get_api_base(provider)
        except ImportError:
            # Fallback
            base_urls = {
                # International
                'openai': 'https://api.openai.com/v1',
                'anthropic': 'https://api.anthropic.com/v1',
                'google': 'https://generativelanguage.googleapis.com/v1beta',
                'mistral': 'https://api.mistral.ai/v1',
                'cohere': 'https://api.cohere.ai/v1',
                'groq': 'https://api.groq.com/openai/v1',
                'together': 'https://api.together.xyz/v1',
                'perplexity': 'https://api.perplexity.ai',
                'fireworks': 'https://api.fireworks.ai/inference/v1',
                # Chinese
                'deepseek': 'https://api.deepseek.com/v1',
                'qwen': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                'baidu': 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1',
                'zhipu': 'https://open.bigmodel.cn/api/paas/v4',
                'moonshot': 'https://api.moonshot.cn/v1',
                'yi': 'https://api.lingyiwanwu.com/v1',
                'minimax': 'https://api.minimax.chat/v1',
                'doubao': 'https://ark.cn-beijing.volces.com/api/v3',
                'spark': 'https://spark-api-open.xf-yun.com/v1',
                'baichuan': 'https://api.baichuan-ai.com/v1',
                'stepfun': 'https://api.stepfun.com/v1',
                'sensenova': 'https://api.sensenova.cn/v1',
                # Cloud
                'azure': '',
                'bedrock': '',
                # Local
                'ollama': 'http://localhost:11434/v1',
                'lmstudio': 'http://localhost:1234/v1',
                'vllm': 'http://localhost:8000/v1',
                'xinference': 'http://localhost:9997/v1',
            }
            return base_urls.get(provider, 'https://api.openai.com/v1')
    
    def add_model(self, model: Dict) -> Dict:
        """Add a new model"""
        if not model.get("id"):
            raise ValueError("Model ID is required")
        
        # Check for duplicate ID
        if self.get_model(model["id"]):
            raise ValueError(f"Model with ID '{model['id']}' already exists")
        
        # Auto-detect provider from model ID
        provider = self._detect_provider(model["id"])
        model["provider"] = provider
        
        # Set default API base if not provided
        if not model.get("api_base"):
            model["api_base"] = self._get_default_api_base(provider)
        
        # Set defaults
        model.setdefault("enabled", True)
        model.setdefault("is_default", False)
        model.setdefault("name", model["id"])
        
        # If this is the first model or marked as default, ensure only one default
        if model.get("is_default"):
            for m in self._config["models"]:
                m["is_default"] = False
        
        # If no models exist, make this one default
        if not self._config.get("models"):
            self._config["models"] = []
            model["is_default"] = True
        
        self._config["models"].append(model)
        self._save_config()
        return self._sanitize_model(model)
    
    def _sanitize_model(self, model: Dict) -> Dict:
        """Remove sensitive data (api_key) from model for API response"""
        result = {k: v for k, v in model.items() if k != 'api_key'}
        result['has_api_key'] = bool(model.get('api_key'))
        return result
    
    def update_model(self, model_id: str, updates: Dict) -> Optional[Dict]:
        """Update an existing model"""
        for i, model in enumerate(self._config["models"]):
            if model.get("id") == model_id:
                # Handle default flag
                if updates.get("is_default"):
                    for m in self._config["models"]:
                        m["is_default"] = False
                
                # If api_key is empty string, don't update it (keep existing)
                if 'api_key' in updates and not updates['api_key']:
                    del updates['api_key']
                
                # If model ID is changing, re-detect provider
                if updates.get("id") and updates["id"] != model_id:
                    updates["provider"] = self._detect_provider(updates["id"])
                    if not updates.get("api_base"):
                        updates["api_base"] = self._get_default_api_base(updates["provider"])
                
                self._config["models"][i].update(updates)
                self._save_config()
                return self._sanitize_model(self._config["models"][i])
        return None
    
    def delete_model(self, model_id: str) -> bool:
        """Delete a model"""
        for i, model in enumerate(self._config["models"]):
            if model.get("id") == model_id:
                was_default = model.get("is_default", False) or model.get("default", False)
                del self._config["models"][i]
                
                # If deleted model was default, set first enabled model as default
                if was_default and self._config["models"]:
                    for m in self._config["models"]:
                        if m.get("enabled", False):
                            m["is_default"] = True
                            break
                
                self._save_config()
                return True
        return False
    
    # Settings management
    def get_settings(self) -> Dict:
        """Get settings"""
        return self._config.get("settings", {})
    
    def update_settings(self, updates: Dict) -> Dict:
        """Update settings"""
        if "settings" not in self._config:
            self._config["settings"] = {}
        self._config["settings"].update(updates)
        self._save_config()
        return self._config["settings"]
    
    # API Key management
    def get_api_key(self, provider: str = "openai") -> Optional[str]:
        """Get API key for a provider from environment variable"""
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "azure": "AZURE_OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "qwen": "DASHSCOPE_API_KEY",
        }
        env_var = env_var_map.get(provider.lower(), "OPENAI_API_KEY")
        return os.environ.get(env_var)
    
    def get_model_api_key(self, model_id: str) -> Optional[str]:
        """Get API key for a specific model (from config or env)"""
        model = self.get_model(model_id)
        if not model:
            return None
        
        # First check if model has its own API key
        if model.get("api_key"):
            return model["api_key"]
        
        # Fall back to environment variable based on provider
        provider = model.get("provider", "openai")
        return self.get_api_key(provider)
    
    def get_model_config(self, model_id: str) -> Optional[Dict]:
        """Get full model config including resolved API key"""
        model = self.get_model(model_id)
        if not model:
            return None
        
        config = dict(model)
        config["resolved_api_key"] = self.get_model_api_key(model_id)
        return config


# Global config manager instance
config_manager = ConfigManager()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    from contextlib import asynccontextmanager
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    logger.error("FastAPI not installed. Install with: pip install fastapi uvicorn jinja2")




# ============================================
# Data Models
# ============================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskStep:
    id: str
    description: str
    agent: str
    status: StepStatus = StepStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "agent": self.agent,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass 
class Task:
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    steps: List[TaskStep] = field(default_factory=list)
    current_step: int = -1
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    priority: int = 2
    mode: str = "auto"
    
    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "progress": self.progress,
            "steps": [s.to_dict() for s in self.steps],
            "currentStep": self.current_step,
            "result": self.result,
            "error": self.error,
            "createdAt": self.created_at.isoformat(),
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None
        }


# Request/Response Models
class TaskExecuteRequest(BaseModel):
    task_id: str
    description: str
    priority: int = 2
    mode: str = "auto"
    agents: List[str] = []


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str = "default"


class ChatResponse(BaseModel):
    message: str
    session_id: str
    tokens_used: int = 0
    execution_time_ms: float = 0
    steps: List[dict] = []


class ModelConfig(BaseModel):
    id: str
    name: str
    provider: str = "openai"
    api_base: str = "https://api.openai.com/v1"
    api_key_env: str = "OPENAI_API_KEY"
    enabled: bool = True
    is_default: bool = False


class ConfigUpdateRequest(BaseModel):
    models: Optional[List[ModelConfig]] = None
    settings: Optional[Dict[str, Any]] = None


# ============================================
# Task Manager
# ============================================

class TaskManager:
    """Manages task execution and progress tracking"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
    
    def create_task(self, task_id: str, description: str, priority: int = 2, mode: str = "auto") -> Task:
        task = Task(
            id=task_id,
            description=description,
            priority=priority,
            mode=mode
        )
        self.tasks[task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs):
        task = self.tasks.get(task_id)
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            self._notify_subscribers(task_id, task)
    
    def add_step(self, task_id: str, step: TaskStep):
        task = self.tasks.get(task_id)
        if task:
            task.steps.append(step)
            self._notify_subscribers(task_id, task)
    
    def update_step(self, task_id: str, step_index: int, **kwargs):
        task = self.tasks.get(task_id)
        if task and 0 <= step_index < len(task.steps):
            step = task.steps[step_index]
            for key, value in kwargs.items():
                if hasattr(step, key):
                    setattr(step, key, value)
            self._notify_subscribers(task_id, task)
    
    async def subscribe(self, task_id: str) -> asyncio.Queue:
        if task_id not in self.subscribers:
            self.subscribers[task_id] = []
        queue = asyncio.Queue()
        self.subscribers[task_id].append(queue)
        return queue
    
    def unsubscribe(self, task_id: str, queue: asyncio.Queue):
        if task_id in self.subscribers:
            if queue in self.subscribers[task_id]:
                self.subscribers[task_id].remove(queue)
    
    def _notify_subscribers(self, task_id: str, task: Task):
        if task_id in self.subscribers:
            for queue in self.subscribers[task_id]:
                try:
                    queue.put_nowait(task.to_dict())
                except asyncio.QueueFull:
                    pass


# ============================================
# Web Application Factory
# ============================================

def create_web_app():
    """Create the web application with workflow UI"""
    if not HAS_FASTAPI:
        raise ImportError("FastAPI not installed")
    
    # Import agent components
    from joinflow_agent import Orchestrator, AgentConfig, SessionManager, TaskQueue
    
    # Create agent system
    # 默认使用 OpenRouter API Key
    DEFAULT_API_KEY = "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"
    DEFAULT_MODEL = "openrouter/mistralai/mistral-7b-instruct:free"
    
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY") or DEFAULT_API_KEY
    model = os.environ.get("LLM_MODEL") or DEFAULT_MODEL
    
    # 确保环境变量设置正确（litellm 需要）
    os.environ["OPENAI_API_KEY"] = api_key
    
    config = AgentConfig(
        llm_model=model,
        llm_api_key=api_key,
        browser_headless=True,
        os_workspace="./workspace",
        verbose=True
    )
    logger.info(f"Using LLM model: {model}")
    
    orchestrator = Orchestrator(config=config)
    session_manager = SessionManager(storage_path="./sessions")
    task_queue = TaskQueue(max_workers=4)
    task_manager = TaskManager()
    
    # Setup Qdrant service (centralized management)
    qdrant_service = None
    try:
        from joinflow_core.qdrant_service import get_qdrant_service, QdrantConfig as QdrantServiceConfig
        
        # Use environment variable for Qdrant URL
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        qdrant_config = QdrantServiceConfig(
            url=qdrant_url,
            knowledge_collection="joinflow_kb",
            cache_enabled=True  # Enable LLM response caching to save tokens
        )
        
        qdrant_service = get_qdrant_service(qdrant_config)
        
        if qdrant_service.is_connected:
            logger.info(f"✅ Qdrant connected at {qdrant_url}")
        elif qdrant_service.is_available:
            logger.info("⚠️ Qdrant using in-memory mode (data not persistent)")
        
    except Exception as e:
        logger.warning(f"Qdrant service not available: {e}")
    
    # Setup RAG if possible
    if qdrant_service and qdrant_service.is_available:
        try:
            from joinflow_index.qdrant_store import QdrantVectorStore
            from joinflow_index.config import QdrantConfig
            from joinflow_rag.engine import RAGEngine
            from joinflow_core.cached_llm import CachedLLM
            
            store = QdrantVectorStore(
                QdrantConfig(
                    collection=qdrant_service.config.knowledge_collection,
                    vector_dim=qdrant_service.config.vector_dim,
                    url=qdrant_service.config.url
                ),
                client=qdrant_service.client
            )
            
            embedder = qdrant_service.get_embedder()
            
            # Create cached LLM wrapper to reduce token consumption
            def llm_func(prompt):
                return orchestrator._llm_agent.execute(prompt).output
            
            cached_llm = CachedLLM(
                llm_func,
                model_name=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
                cache_enabled=True,
                similarity_threshold=0.92
            )
            
            rag_engine = RAGEngine(
                embedder=embedder,
                store=store,
                llm=cached_llm.query  # Use cached LLM to save tokens
            )
            
            orchestrator.set_rag_engine(rag_engine)
            logger.info("✅ RAG engine initialized with token caching")
        except Exception as e:
            logger.warning(f"RAG not available: {e}")
    
    # Setup memory
    if qdrant_service and qdrant_service.is_available:
        try:
            from joinflow_memory import HistoryStore, MemoryConfig
            
            embedder = qdrant_service.get_embedder()
            
            memory_config = MemoryConfig(
                url=qdrant_service.config.url,
                history_collection=qdrant_service.config.history_collection,
                task_collection=qdrant_service.config.tasks_collection,
                vector_dim=qdrant_service.config.vector_dim
            )
            
            memory_store = HistoryStore(
                embedder=embedder,
                config=memory_config,
                client=qdrant_service.client
            )
            
            orchestrator.set_memory_store(memory_store)
            logger.info("✅ Memory store initialized")
        except Exception as e:
            logger.warning(f"Memory not available: {e}")
    
    # Setup paths
    web_dir = Path(__file__).parent
    static_dir = web_dir / "static"
    templates_dir = web_dir / "templates"
    
    # Setup templates
    templates = Jinja2Templates(directory=str(templates_dir))
    
    # Create app with lifespan
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting JoinFlow Web UI...")
        task_queue.start()
        yield
        logger.info("Shutting down...")
        task_queue.stop()
    
    app = FastAPI(
        title="JoinFlow Web UI",
        description="Workflow-Centric AI Agent System",
        version="0.3.0",
        lifespan=lifespan
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store references
    app.state.orchestrator = orchestrator
    app.state.session_manager = session_manager
    app.state.task_queue = task_queue
    app.state.task_manager = task_manager
    
    # ============================================
    # UI Routes
    # ============================================
    
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.get("/ui", response_class=HTMLResponse)
    async def ui(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.get("/workspace", response_class=HTMLResponse)
    async def workspace(request: Request):
        """Agent 可视化工作台"""
        return templates.TemplateResponse("workspace.html", {"request": request})
    
    @app.get("/cloud", response_class=HTMLResponse)
    async def cloud(request: Request):
        """云服务管理面板"""
        return templates.TemplateResponse("cloud.html", {"request": request})
    
    @app.get("/pricing", response_class=HTMLResponse)
    async def pricing(request: Request):
        """定价订阅页面"""
        return templates.TemplateResponse("pricing.html", {"request": request})
    
    @app.get("/terms", response_class=HTMLResponse)
    async def terms(request: Request):
        """服务条款页面"""
        return templates.TemplateResponse("terms.html", {"request": request})
    
    @app.get("/privacy", response_class=HTMLResponse)
    async def privacy(request: Request):
        """隐私政策页面"""
        return templates.TemplateResponse("privacy.html", {"request": request})
    
    @app.get("/os-control", response_class=HTMLResponse)
    async def os_control(request: Request):
        """本地OS控制页面"""
        return templates.TemplateResponse("os_control.html", {"request": request})
    
    # ============================================
    # WebSocket for Agent Stream
    # ============================================
    
    # Store active WebSocket connections
    active_connections: Dict[str, List[WebSocket]] = {}
    
    @app.websocket("/ws/agent-stream")
    async def agent_stream_websocket(websocket: WebSocket):
        """WebSocket endpoint for real-time agent stream"""
        await websocket.accept()
        
        # Generate session ID
        session_id = str(uuid.uuid4())[:8]
        
        if session_id not in active_connections:
            active_connections[session_id] = []
        active_connections[session_id].append(websocket)
        
        try:
            # Send welcome message
            await websocket.send_json({
                "type": "connected",
                "session_id": session_id,
                "message": "Connected to Agent Stream"
            })
            
            while True:
                # Receive commands from client
                data = await websocket.receive_json()
                
                if data.get("action") == "execute":
                    # Start task execution
                    task_description = data.get("task", "")
                    selected_agents = data.get("agents", [])  # 获取用户选择的 agents
                    if task_description:
                        # Execute in background and stream updates
                        asyncio.create_task(
                            stream_task_execution(websocket, orchestrator, task_manager, task_description, selected_agents)
                        )
                
                elif data.get("action") == "pause":
                    await websocket.send_json({"type": "status", "status": "paused"})
                
                elif data.get("action") == "resume":
                    await websocket.send_json({"type": "status", "status": "running"})
                
                elif data.get("action") == "stop":
                    await websocket.send_json({"type": "status", "status": "stopped"})
                    break
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            if session_id in active_connections:
                if websocket in active_connections[session_id]:
                    active_connections[session_id].remove(websocket)
    
    async def stream_task_execution(websocket: WebSocket, orchestrator, task_manager, description: str, selected_agents: List[str] = None):
        """Stream task execution updates to WebSocket
        
        Args:
            websocket: WebSocket connection
            orchestrator: Orchestrator instance
            task_manager: Task manager instance
            description: Task description
            selected_agents: User-selected agents (optional)
        """
        import base64
        
        # 存储执行结果
        execution_results = []
        
        try:
            # Send thinking update
            await websocket.send_json({
                "type": "thinking",
                "content": f"正在分析任务: {description}"
            })
            
            # Analyze task with user-selected agents
            steps = analyze_task(description, selected_agents)
            
            # Send task info
            await websocket.send_json({
                "type": "task_info",
                "task": description,
                "steps": [{"name": s.description, "agent": s.agent} for s in steps]
            })
            
            # Execute each step
            for i, step in enumerate(steps):
                # Send step start
                await websocket.send_json({
                    "type": "step",
                    "step": {
                        "index": i,
                        "name": step.description,
                        "agent": step.agent,
                        "status": "running"
                    }
                })
                
                # Send thinking for this step
                await websocket.send_json({
                    "type": "thinking",
                    "content": f"执行步骤 {i + 1}: {step.description}..."
                })
                
                # 实际执行步骤
                step_result = await execute_step_real(step, description, execution_results)
                execution_results.append({
                    "step": step.description,
                    "agent": step.agent,
                    "result": step_result
                })
                
                # Send step complete with result
                await websocket.send_json({
                    "type": "step",
                    "step": {
                        "index": i,
                        "name": step.description,
                        "agent": step.agent,
                        "status": "completed",
                        "result": step_result[:500] if step_result else ""
                    }
                })
                
                # Send action log
                await websocket.send_json({
                    "type": "action",
                    "message": f"完成: {step.description}",
                    "position": {"x": 30 + (i * 10) % 40, "y": 40 + (i * 5) % 20}
                })
            
            # 生成最终报告
            final_report = generate_task_report(description, execution_results)
            
            # 保存结果到文件
            result_file = save_task_result(description, final_report, execution_results)
            
            # Send complete with results
            await websocket.send_json({
                "type": "complete",
                "message": "任务执行完成！",
                "report": final_report,
                "result_file": result_file,
                "results": execution_results
            })
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
    
    async def execute_step_real(step: TaskStep, task_description: str, previous_results: list) -> str:
        """实际执行步骤"""
        agent_type = step.agent.lower() if step.agent else "llm"
        
        try:
            # 浏览器 Agent
            if agent_type == "browser":
                from joinflow_agent.browser_enhanced import EnhancedBrowserAgent
                agent = EnhancedBrowserAgent(headless=True)
                
                try:
                    # 搜索任务
                    if "搜索" in step.description or "search" in step.description.lower():
                        import re
                        # 提取搜索关键词
                        search_match = re.search(r'搜索[：:\s]*(.+)|search[:\s]+(.+)', task_description, re.IGNORECASE)
                        query = (search_match.group(1) or search_match.group(2)) if search_match else task_description
                        
                        logger.info(f"Browser searching: {query}")
                        result = await agent.search_and_analyze(query, num_results=2, analyze=True)
                        
                        # 格式化搜索结果
                        output = f"搜索关键词: {query}\n\n"
                        if result.get('final_summary'):
                            output += f"综合分析:\n{result['final_summary']}\n\n"
                        
                        for i, r in enumerate(result.get('results', [])[:3]):
                            output += f"--- 结果 {i+1} ---\n"
                            output += f"标题: {r.get('title', 'N/A')}\n"
                            output += f"URL: {r.get('url', 'N/A')}\n"
                            if r.get('analysis'):
                                output += f"分析: {r['analysis'][:300]}...\n"
                            output += "\n"
                        
                        return output
                    
                    # 导航任务
                    elif "http" in step.description.lower() or "www" in step.description.lower():
                        import re
                        url_match = re.search(r'https?://[^\s<>"]+', step.description)
                        if url_match:
                            page_data = await agent.navigate(url_match.group())
                            analysis = await agent.analyze_page(extract_type="summary")
                            return f"页面: {page_data.title}\nURL: {page_data.url}\n\n分析:\n{analysis.get('analysis', '')}"
                    
                    # 通用浏览器任务
                    else:
                        result = await agent.execute_task(task_description)
                        return str(result.get('results', []))[:1000]
                        
                finally:
                    await agent.close()
            
            # 系统 Agent
            elif agent_type == "os":
                import subprocess
                import platform
                import os as os_module
                import time
                
                # 获取桌面路径
                desktop_path = os_module.path.join(os_module.environ.get('USERPROFILE', 'C:\\Users\\Administrator'), 'Desktop')
                
                # 根据任务描述智能执行
                task_lower = task_description.lower()
                step_lower = step.description.lower()
                
                # 检测是否是"打开记事本写内容保存"类型的任务
                if ('记事本' in task_lower or 'notepad' in task_lower) and ('写' in task_lower or '小说' in task_lower or '保存' in task_lower):
                    try:
                        # 1. 首先使用 LLM 生成内容
                        from joinflow_agent.model_manager import get_model_manager, AgentType as ModelAgentType
                        
                        # 提取要写的主题
                        content_prompt = f"""请根据以下要求创作内容：

任务描述：{task_description}

要求：
1. 创作一段有趣的内容（如果是小说，写一个简短但完整的故事）
2. 内容长度适中（200-500字）
3. 直接输出内容，不要加任何解释或前缀

请开始创作："""
                        
                        manager = get_model_manager()
                        generated_content = manager.call_llm_sync(
                            ModelAgentType.LLM,
                            messages=[{"role": "user", "content": content_prompt}],
                            max_tokens=1000,
                            temperature=0.8
                        )
                        
                        if not generated_content:
                            generated_content = "这是一个测试内容。\n\n猪猪侠是一个勇敢的小猪，他每天都在保护着猪猪村的和平..."
                        
                        # 2. 生成文件名
                        import re
                        from datetime import datetime
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        
                        # 从任务中提取关键词作为文件名
                        if '猪猪侠' in task_description:
                            filename = f"猪猪侠小说_{timestamp}.txt"
                        elif '小说' in task_lower:
                            filename = f"小说_{timestamp}.txt"
                        else:
                            filename = f"文档_{timestamp}.txt"
                        
                        file_path = os_module.path.join(desktop_path, filename)
                        
                        # 3. 直接保存文件到桌面
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(generated_content)
                        
                        # 4. 打开记事本显示文件
                        subprocess.Popen(f'notepad "{file_path}"', shell=True)
                        
                        return f"✅ 任务完成！\n\n📝 已创作内容并保存到桌面：\n文件路径：{file_path}\n\n📖 内容预览：\n{generated_content[:300]}..."
                        
                    except Exception as e:
                        logger.error(f"OS Agent error: {e}")
                        return f"执行出错: {str(e)}"
                
                # 检测是否是打开应用类型的任务
                elif '打开' in task_lower or '启动' in task_lower:
                    app_mappings = {
                        '记事本': 'notepad',
                        'notepad': 'notepad',
                        '计算器': 'calc',
                        'calc': 'calc',
                        '画图': 'mspaint',
                        'paint': 'mspaint',
                        '浏览器': 'msedge',
                        'browser': 'msedge',
                        'edge': 'msedge',
                        'cmd': 'cmd',
                        '命令提示符': 'cmd',
                        'powershell': 'powershell',
                        '资源管理器': 'explorer',
                        'explorer': 'explorer',
                    }
                    
                    for app_name, app_cmd in app_mappings.items():
                        if app_name in task_lower:
                            subprocess.Popen(f'start {app_cmd}', shell=True)
                            return f"✅ 已打开 {app_name}"
                    
                    return "已尝试打开应用"
                
                # 默认：获取系统信息
                else:
                    if platform.system() == "Windows":
                        result = subprocess.run(
                            'systeminfo | findstr /B /C:"OS" /C:"System" /C:"Total Physical Memory"',
                            shell=True, capture_output=True, timeout=30,
                            encoding='utf-8', errors='replace'
                        )
                        return result.stdout[:500] if result.stdout else "系统操作完成"
                    return "系统操作完成"
            
            # LLM Agent
            elif agent_type == "llm":
                from joinflow_agent.model_manager import get_model_manager, AgentType
                
                # 构建上下文
                context = ""
                for prev in previous_results[-2:]:
                    if prev.get('result'):
                        context += f"\n{prev['step']}:\n{prev['result'][:500]}\n"
                
                prompt = f"任务: {task_description}\n"
                if context:
                    prompt += f"\n之前的执行结果:\n{context}\n"
                prompt += f"\n当前步骤: {step.description}\n\n请执行此步骤并给出结果。"
                
                manager = get_model_manager()
                result = manager.call_llm_sync(
                    AgentType.LLM,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.7
                )
                return result if result else "LLM 处理完成"
            
            # 展示步骤
            elif agent_type == "display":
                # 汇总之前的结果
                summary = "执行结果汇总:\n\n"
                for prev in previous_results:
                    summary += f"• {prev['step']}: 完成\n"
                return summary
            
            # 默认
            else:
                await asyncio.sleep(0.5)
                return f"步骤 '{step.description}' 完成"
                
        except Exception as e:
            logger.error(f"Step execution error: {e}")
            return f"执行出错: {str(e)[:200]}"
    
    def generate_task_report(description: str, results: list) -> str:
        """生成任务执行报告"""
        report = f"# {description} - 执行报告\n\n"
        report += f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "## 执行步骤\n\n"
        
        for i, r in enumerate(results):
            report += f"### {i+1}. {r['step']} ({r['agent']})\n\n"
            if r.get('result'):
                report += f"{r['result']}\n\n"
        
        return report
    
    def save_task_result(description: str, report: str, results: list) -> str:
        """保存任务结果到文件"""
        import os
        import re
        
        # 创建结果目录
        results_dir = Path(__file__).parent.parent / "workspace" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        safe_name = re.sub(r'[^\w\s-]', '', description)[:50].strip().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_name}_{timestamp}.md"
        filepath = results_dir / filename
        
        # 写入报告
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Task result saved to: {filepath}")
        return str(filepath)
    
    # Mount static files (after routes)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # ============================================
    # Results API Routes
    # ============================================
    
    @app.post("/api/results/save")
    async def save_result(request: Request):
        """保存任务结果到文件"""
        try:
            data = await request.json()
            task_id = data.get("taskId", "unknown")
            description = data.get("description", "任务结果")
            content = data.get("content", "")
            
            # 创建结果目录
            results_dir = Path(__file__).parent.parent / "workspace" / "results"
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            import re
            safe_name = re.sub(r'[^\w\s-]', '', description)[:50].strip().replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{safe_name}_{timestamp}.md"
            filepath = results_dir / filename
            
            # 写入内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {description}\n\n")
                f.write(f"任务ID: {task_id}\n")
                f.write(f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                f.write(content)
            
            logger.info(f"Result saved to: {filepath}")
            return {
                "success": True,
                "path": f"workspace/results/{filename}",
                "filename": filename
            }
        except Exception as e:
            logger.error(f"Failed to save result: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/results/read/{filename:path}")
    async def read_result(filename: str):
        """读取任务结果文件"""
        try:
            results_dir = Path(__file__).parent.parent / "workspace" / "results"
            filepath = results_dir / filename
            
            if not filepath.exists():
                return {"success": False, "error": "File not found"}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "filename": filename
            }
        except Exception as e:
            logger.error(f"Failed to read result: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/results/list")
    async def list_results():
        """列出所有结果文件"""
        try:
            results_dir = Path(__file__).parent.parent / "workspace" / "results"
            results_dir.mkdir(parents=True, exist_ok=True)
            
            files = []
            for f in results_dir.glob("*.md"):
                stat = f.stat()
                files.append({
                    "filename": f.name,
                    "path": f"workspace/results/{f.name}",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # 按修改时间排序
            files.sort(key=lambda x: x["modified"], reverse=True)
            
            return {"success": True, "files": files}
        except Exception as e:
            logger.error(f"Failed to list results: {e}")
            return {"success": False, "error": str(e)}
    
    # ============================================
    # Export API Routes
    # ============================================
    
    @app.post("/api/export/task/{task_id}")
    async def export_task(task_id: str, request: Request):
        """导出任务结果为指定格式（支持 md/txt/json/html/pdf/excel/pptx）"""
        try:
            data = await request.json()
            format_type = data.get("format", "md").lower()
            description = data.get("description", "任务结果")
            # 兼容 content 和 result 两种参数名
            content = data.get("content") or data.get("result") or ""
            logs = data.get("logs", [])
            steps = data.get("steps", [])
            metadata = data.get("metadata", {})
            
            # 添加调试日志
            logger.info(f"Export request - format: {format_type}, description: {description[:50]}...")
            
            # 创建导出目录
            export_dir = Path(__file__).parent.parent / "workspace" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名 - 保留中文字符
            import re
            # 移除文件系统不允许的字符: \ / : * ? " < > |
            safe_name = re.sub(r'[\\/:*?"<>|]', '', description)[:30].strip().replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 基础格式处理
            if format_type == "json":
                filename = f"{safe_name}_{timestamp}.json"
                filepath = export_dir / filename
                
                export_data = {
                    "task_id": task_id,
                    "description": description,
                    "content": content,
                    "logs": logs,
                    "steps": steps,
                    "exported_at": datetime.now().isoformat()
                }
                
                import json as json_module
                with open(filepath, 'w', encoding='utf-8') as f:
                    json_module.dump(export_data, f, ensure_ascii=False, indent=2)
                    
            elif format_type == "txt":
                filename = f"{safe_name}_{timestamp}.txt"
                filepath = export_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"任务: {description}\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(content)
            
            elif format_type == "html":
                filename = f"{safe_name}_{timestamp}.html"
                filepath = export_dir / filename
                
                # 使用 HTMLExporter
                try:
                    from joinflow_core.exporter import HTMLExporter
                    html_content = HTMLExporter.export_task_result(
                        task_id=task_id,
                        description=description,
                        result=content,
                        steps=steps,
                        metadata=metadata
                    )
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                except ImportError:
                    # 回退到简单 HTML
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{description}</title>
<style>body{{font-family:system-ui;max-width:800px;margin:0 auto;padding:20px;}}</style></head>
<body><h1>{description}</h1><p>导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p><hr><div>{content}</div></body></html>""")
            
            elif format_type == "pdf":
                filename = f"{safe_name}_{timestamp}.pdf"
                filepath = export_dir / filename
                
                try:
                    from joinflow_core.exporter import PDFExporter
                    if not PDFExporter.is_available():
                        return {"success": False, "error": "PDF导出需要安装 reportlab: pip install reportlab"}
                    
                    pdf_bytes = PDFExporter.export_task_result(
                        task_id=task_id,
                        description=description,
                        result=content,
                        steps=steps,
                        metadata=metadata
                    )
                    with open(filepath, 'wb') as f:
                        f.write(pdf_bytes)
                except ImportError as e:
                    return {"success": False, "error": f"PDF导出模块不可用: {str(e)}，请安装 reportlab: pip install reportlab"}
                except Exception as e:
                    logger.error(f"PDF export error: {e}")
                    import traceback
                    traceback.print_exc()
                    return {"success": False, "error": f"PDF导出失败: {str(e)}"}
            
            elif format_type in ("excel", "xlsx"):
                filename = f"{safe_name}_{timestamp}.xlsx"
                filepath = export_dir / filename
                
                try:
                    from joinflow_core.advanced_exporter import ExcelExporter
                    if not ExcelExporter.is_available():
                        return {"success": False, "error": "Excel导出需要安装 openpyxl: pip install openpyxl"}
                    
                    excel_bytes = ExcelExporter.export_task_result(
                        task_id=task_id,
                        description=description,
                        result=content,
                        steps=steps,
                        metadata=metadata
                    )
                    with open(filepath, 'wb') as f:
                        f.write(excel_bytes)
                except ImportError as e:
                    return {"success": False, "error": f"Excel导出模块不可用: {str(e)}，请安装 openpyxl: pip install openpyxl"}
                except Exception as e:
                    logger.error(f"Excel export error: {e}")
                    import traceback
                    traceback.print_exc()
                    return {"success": False, "error": f"Excel导出失败: {str(e)}"}
            
            elif format_type in ("pptx", "ppt", "powerpoint"):
                filename = f"{safe_name}_{timestamp}.pptx"
                filepath = export_dir / filename
                
                try:
                    from joinflow_core.advanced_exporter import PowerPointExporter
                    if not PowerPointExporter.is_available():
                        return {"success": False, "error": "PPT导出需要安装 python-pptx: pip install python-pptx"}
                    
                    pptx_bytes = PowerPointExporter.export_task_result(
                        task_id=task_id,
                        description=description,
                        result=content,
                        steps=steps,
                        metadata=metadata
                    )
                    with open(filepath, 'wb') as f:
                        f.write(pptx_bytes)
                except ImportError as e:
                    return {"success": False, "error": f"PPT导出模块不可用: {str(e)}，请安装 python-pptx: pip install python-pptx"}
                except Exception as e:
                    logger.error(f"PPT export error: {e}")
                    import traceback
                    traceback.print_exc()
                    return {"success": False, "error": f"PPT导出失败: {str(e)}"}
            
            elif format_type in ("md", "markdown"):
                # 明确处理 markdown 格式
                filename = f"{safe_name}_{timestamp}.md"
                filepath = export_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# {description}\n\n")
                    f.write(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("---\n\n")
                    f.write(content)
            
            else:
                # 不支持的格式，返回错误
                return {
                    "success": False, 
                    "error": f"不支持的导出格式: {format_type}，支持的格式: md, txt, json, html, pdf, excel, pptx"
                }
            
            logger.info(f"Task exported to: {filepath}")
            return {
                "success": True,
                "filename": filename,
                "path": str(filepath),
                "format": format_type
            }
        except Exception as e:
            logger.error(f"Failed to export task: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    @app.get("/api/export/download/{filename:path}")
    async def download_export(filename: str):
        """下载导出的文件"""
        from fastapi.responses import FileResponse
        
        try:
            export_dir = Path(__file__).parent.parent / "workspace" / "exports"
            filepath = export_dir / filename
            
            if not filepath.exists():
                return {"success": False, "error": "File not found"}
            
            # 确定 MIME 类型
            mime_types = {
                '.json': 'application/json',
                '.txt': 'text/plain',
                '.md': 'text/markdown',
                '.html': 'text/html',
                '.pdf': 'application/pdf',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.xls': 'application/vnd.ms-excel',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.ppt': 'application/vnd.ms-powerpoint',
            }
            
            ext = Path(filename).suffix.lower()
            media_type = mime_types.get(ext, 'application/octet-stream')
            
            return FileResponse(
                path=str(filepath),
                filename=filename,
                media_type=media_type
            )
        except Exception as e:
            logger.error(f"Failed to download export: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/export/formats")
    async def get_export_formats():
        """获取可用的导出格式列表"""
        formats = [
            {
                "id": "md",
                "name": "Markdown",
                "extension": ".md",
                "icon": "📝",
                "available": True,
                "description": "轻量级标记语言，适合文档和笔记"
            },
            {
                "id": "txt",
                "name": "纯文本",
                "extension": ".txt",
                "icon": "📄",
                "available": True,
                "description": "简单文本格式，兼容性最好"
            },
            {
                "id": "html",
                "name": "HTML",
                "extension": ".html",
                "icon": "🌐",
                "available": True,
                "description": "网页格式，可直接在浏览器查看"
            },
            {
                "id": "json",
                "name": "JSON",
                "extension": ".json",
                "icon": "📊",
                "available": True,
                "description": "结构化数据格式，便于程序处理"
            },
        ]
        
        # 检查 PDF 导出是否可用
        try:
            from joinflow_core.exporter import PDFExporter
            pdf_available = PDFExporter.is_available()
        except ImportError:
            pdf_available = False
        
        formats.append({
            "id": "pdf",
            "name": "PDF",
            "extension": ".pdf",
            "icon": "📕",
            "available": pdf_available,
            "description": "便携文档格式，适合打印和分享",
            "install_hint": "pip install reportlab" if not pdf_available else None
        })
        
        # 检查 Excel 导出是否可用
        try:
            from joinflow_core.advanced_exporter import ExcelExporter
            excel_available = ExcelExporter.is_available()
        except ImportError:
            excel_available = False
        
        formats.append({
            "id": "excel",
            "name": "Excel",
            "extension": ".xlsx",
            "icon": "📈",
            "available": excel_available,
            "description": "电子表格格式，支持数据分析和图表",
            "install_hint": "pip install openpyxl" if not excel_available else None
        })
        
        # 检查 PPT 导出是否可用
        try:
            from joinflow_core.advanced_exporter import PowerPointExporter
            pptx_available = PowerPointExporter.is_available()
        except ImportError:
            pptx_available = False
        
        formats.append({
            "id": "pptx",
            "name": "PowerPoint",
            "extension": ".pptx",
            "icon": "📽️",
            "available": pptx_available,
            "description": "演示文稿格式，适合汇报展示",
            "install_hint": "pip install python-pptx" if not pptx_available else None
        })
        
        return {
            "success": True,
            "formats": formats
        }
    
    @app.get("/api/file/view/{filepath:path}")
    async def view_file(filepath: str):
        """查看文件内容（用于查看结果文件）"""
        from fastapi.responses import FileResponse
        
        try:
            # 支持多种路径格式
            if filepath.startswith("workspace/"):
                full_path = Path(__file__).parent.parent / filepath
            elif filepath.startswith("C:") or filepath.startswith("/"):
                full_path = Path(filepath)
            else:
                full_path = Path(__file__).parent.parent / "workspace" / filepath
            
            if not full_path.exists():
                return {"success": False, "error": "File not found"}
            
            # 读取文件内容
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "path": str(full_path),
                "filename": full_path.name
            }
        except Exception as e:
            logger.error(f"Failed to view file: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/file/download/{filename:path}")
    async def download_file(filename: str):
        """下载结果文件"""
        from fastapi.responses import FileResponse
        import urllib.parse
        
        try:
            # 解码文件名
            decoded_filename = urllib.parse.unquote(filename)
            
            # 在多个目录中查找文件
            search_dirs = [
                Path(__file__).parent.parent / "workspace" / "results",
                Path(__file__).parent.parent / "workspace" / "exports",
                Path(__file__).parent.parent / "workspace",
            ]
            
            full_path = None
            for search_dir in search_dirs:
                candidate = search_dir / decoded_filename
                if candidate.exists():
                    full_path = candidate
                    break
            
            if not full_path or not full_path.exists():
                return {"success": False, "error": f"File not found: {decoded_filename}"}
            
            # 确定 MIME 类型
            suffix = full_path.suffix.lower()
            if suffix == '.json':
                media_type = 'application/json'
            elif suffix == '.txt':
                media_type = 'text/plain; charset=utf-8'
            elif suffix == '.md':
                media_type = 'text/markdown; charset=utf-8'
            elif suffix == '.html':
                media_type = 'text/html; charset=utf-8'
            else:
                media_type = 'application/octet-stream'
            
            return FileResponse(
                path=str(full_path),
                filename=full_path.name,
                media_type=media_type
            )
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return {"success": False, "error": str(e)}
    
    # ============================================
    # API Routes
    # ============================================
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    @app.get("/api/health")
    async def api_health():
        """API health check endpoint for cloud monitoring"""
        import psutil
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": int(datetime.now().timestamp() - psutil.boot_time()),
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_used_gb": round(disk.used / (1024**3), 2),
                    "disk_total_gb": round(disk.total / (1024**3), 2)
                },
                "services": {
                    "web": {"status": "running", "port": 8080},
                    "qdrant": {"status": "running" if hasattr(orchestrator, '_rag_engine') else "not_configured"}
                }
            }
        except ImportError:
            # psutil not installed, return basic health
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "web": {"status": "running"}
                }
            }
        except Exception as e:
            return {
                "status": "degraded",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    @app.get("/api/info")
    async def info():
        return {
            "name": "JoinFlow Agent API",
            "version": "0.3.0",
            "agents": ["browser", "llm", "os", "code", "data", "vision"],
        }
    
    # ============================================
    # Workflow APIs
    # ============================================
    
    # 内存存储工作流（生产环境应使用数据库）
    _workflows_store = {}
    
    # 预定义的工作流模板
    _default_workflows = [
        {
            "id": "research-report",
            "name": "研究报告生成",
            "description": "搜索指定主题的最新信息，整理成结构化报告",
            "icon": "fas fa-search",
            "color": "#3b82f6",
            "category": "research",
            "tags": ["研究", "报告", "搜索"],
            "task_template": "搜索关于{topic}的最新信息，整理成一份包含背景、现状、趋势的报告",
            "inputs": {"topic": {"type": "string", "description": "研究主题", "required": True}},
            "created_at": "2026-01-01T00:00:00",
            "usage_count": 0
        },
        {
            "id": "code-review",
            "name": "代码审查助手",
            "description": "分析代码质量，提供改进建议",
            "icon": "fas fa-code",
            "color": "#8b5cf6",
            "category": "code",
            "tags": ["代码", "审查", "优化"],
            "task_template": "分析以下{language}代码，检查潜在问题并提供优化建议：\n{code}",
            "inputs": {
                "language": {"type": "string", "description": "编程语言", "required": True},
                "code": {"type": "text", "description": "代码内容", "required": True}
            },
            "created_at": "2026-01-01T00:00:00",
            "usage_count": 0
        },
        {
            "id": "data-analysis",
            "name": "数据分析报告",
            "description": "分析数据并生成可视化报告",
            "icon": "fas fa-chart-bar",
            "color": "#22c55e",
            "category": "data",
            "tags": ["数据", "分析", "图表"],
            "task_template": "分析{data_description}的数据，生成包含{analysis_type}的分析报告",
            "inputs": {
                "data_description": {"type": "string", "description": "数据描述", "required": True},
                "analysis_type": {"type": "string", "description": "分析类型", "required": False, "default": "趋势分析和关键指标"}
            },
            "created_at": "2026-01-01T00:00:00",
            "usage_count": 0
        },
        {
            "id": "content-creation",
            "name": "内容创作助手",
            "description": "根据主题和风格创作文章或文案",
            "icon": "fas fa-pen-fancy",
            "color": "#f59e0b",
            "category": "content",
            "tags": ["写作", "创作", "文案"],
            "task_template": "以{style}的风格，创作一篇关于{topic}的{content_type}，字数约{word_count}字",
            "inputs": {
                "topic": {"type": "string", "description": "主题", "required": True},
                "style": {"type": "string", "description": "写作风格", "required": False, "default": "专业"},
                "content_type": {"type": "string", "description": "内容类型", "required": False, "default": "文章"},
                "word_count": {"type": "number", "description": "字数", "required": False, "default": 500}
            },
            "created_at": "2026-01-01T00:00:00",
            "usage_count": 0
        }
    ]
    
    @app.get("/api/workflows")
    async def get_workflows():
        """获取所有工作流"""
        # 合并默认工作流和用户创建的工作流
        all_workflows = _default_workflows.copy()
        all_workflows.extend(list(_workflows_store.values()))
        return {"workflows": all_workflows}
    
    @app.get("/api/workflows/{workflow_id}")
    async def get_workflow(workflow_id: str):
        """获取单个工作流"""
        # 先检查默认工作流
        for wf in _default_workflows:
            if wf["id"] == workflow_id:
                return {"workflow": wf}
        # 再检查用户工作流
        if workflow_id in _workflows_store:
            return {"workflow": _workflows_store[workflow_id]}
        raise HTTPException(404, "Workflow not found")
    
    @app.post("/api/workflows")
    async def create_workflow(request: Request):
        """创建新工作流"""
        data = await request.json()
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        workflow = {
            "id": workflow_id,
            "name": data.get("name", "未命名工作流"),
            "description": data.get("description", ""),
            "icon": data.get("icon", "fas fa-cog"),
            "color": data.get("color", "#8b5cf6"),
            "category": data.get("category", "custom"),
            "tags": data.get("tags", ["自定义"]),
            "task_template": data.get("task_template", ""),
            "inputs": data.get("inputs", {}),
            "created_at": datetime.now().isoformat(),
            "usage_count": 0
        }
        
        _workflows_store[workflow_id] = workflow
        return {"success": True, "workflow": workflow}
    
    @app.delete("/api/workflows/{workflow_id}")
    async def delete_workflow(workflow_id: str):
        """删除工作流"""
        if workflow_id in _workflows_store:
            del _workflows_store[workflow_id]
            return {"success": True}
        # 不允许删除默认工作流
        for wf in _default_workflows:
            if wf["id"] == workflow_id:
                raise HTTPException(400, "Cannot delete default workflow")
        raise HTTPException(404, "Workflow not found")
    
    @app.post("/api/workflows/{workflow_id}/execute")
    async def execute_workflow(workflow_id: str, request: Request):
        """执行工作流"""
        data = await request.json()
        inputs = data.get("inputs", {})
        
        # 获取工作流
        workflow = None
        for wf in _default_workflows:
            if wf["id"] == workflow_id:
                workflow = wf
                break
        if not workflow and workflow_id in _workflows_store:
            workflow = _workflows_store[workflow_id]
        
        if not workflow:
            raise HTTPException(404, "Workflow not found")
        
        # 渲染任务模板
        task_template = workflow.get("task_template", "")
        for key, value in inputs.items():
            task_template = task_template.replace(f"{{{key}}}", str(value))
        
        # 更新使用次数
        workflow["usage_count"] = workflow.get("usage_count", 0) + 1
        
        return {
            "success": True,
            "task_prompt": task_template,
            "workflow_id": workflow_id,
            "workflow_name": workflow.get("name")
        }
    
    # ============================================
    # Statistics APIs
    # ============================================
    
    @app.get("/api/statistics/summary")
    async def get_statistics_summary(days: int = 30):
        """获取统计摘要"""
        # 从 TaskStore 获取真实数据
        all_tasks = list(task_manager.tasks.values()) if hasattr(task_manager, 'tasks') else []
        
        total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in all_tasks if t.status == TaskStatus.FAILED])
        
        success_rate = round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
        
        # 估算 token 使用量（实际应从 LLM 调用中收集）
        total_tokens = total_tasks * 500  # 估算每个任务平均 500 tokens
        total_cost = total_tokens * 0.000002  # 估算成本
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": success_rate,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "period_days": days
        }
    
    @app.get("/api/statistics/trend")
    async def get_statistics_trend(days: int = 30):
        """获取统计趋势数据 - 基于真实任务数据"""
        from datetime import timedelta
        from collections import defaultdict
        
        # 获取所有任务
        all_tasks = list(task_manager.tasks.values()) if hasattr(task_manager, 'tasks') else []
        
        # 按日期统计任务
        tasks_by_date = defaultdict(lambda: {"total": 0, "completed": 0, "tokens": 0})
        
        for task in all_tasks:
            if task.created_at:
                task_date = task.created_at.date().isoformat()
                tasks_by_date[task_date]["total"] += 1
                if task.status == TaskStatus.COMPLETED:
                    tasks_by_date[task_date]["completed"] += 1
                # 估算每个任务使用 500 tokens
                tasks_by_date[task_date]["tokens"] += 500
        
        trend = []
        today = datetime.now().date()
        
        for i in range(days):
            date = today - timedelta(days=days-1-i)
            date_str = date.isoformat()
            day_data = tasks_by_date.get(date_str, {"total": 0, "completed": 0, "tokens": 0})
            
            success_rate = 0
            if day_data["total"] > 0:
                success_rate = round(day_data["completed"] / day_data["total"] * 100, 1)
            
            trend.append({
                "date": date_str,
                "tasks": day_data["total"],
                "tokens": day_data["tokens"],
                "success_rate": success_rate
            })
        
        return {"trend": trend, "period_days": days}
    
    @app.get("/api/statistics/export")
    async def export_statistics(days: int = 30, format: str = "json"):
        """导出统计数据"""
        summary = await get_statistics_summary(days)
        trend = await get_statistics_trend(days)
        
        data = {
            "summary": summary,
            "trend": trend["trend"],
            "exported_at": datetime.now().isoformat()
        }
        
        if format == "markdown":
            md_content = f"""# JoinFlow 使用统计报告

导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
统计周期: 最近 {days} 天

## 概览

| 指标 | 数值 |
|------|------|
| 总任务数 | {summary['total_tasks']} |
| 完成任务 | {summary['completed_tasks']} |
| 成功率 | {summary['success_rate']}% |
| Token 使用 | {summary['total_tokens']} |
| 预估成本 | ${summary['total_cost']:.4f} |

## 趋势数据

| 日期 | 任务数 | Token | 成功率 |
|------|--------|-------|--------|
"""
            for item in trend["trend"][-7:]:  # 最近7天
                md_content += f"| {item['date']} | {item['tasks']} | {item['tokens']} | {item['success_rate']}% |\n"
            
            return Response(
                content=md_content,
                media_type="text/markdown",
                headers={"Content-Disposition": "attachment; filename=statistics.md"}
            )
        
        return data
    
    @app.get("/api/status")
    async def api_status():
        """Get API configuration status from server"""
        # Get default model info
        default_model = config_manager.get_default_model()
        model_id = default_model.get("id") if default_model else None
        model_name = default_model.get("name") if default_model else None
        
        # Get provider and API key (check model-specific key first, then env var)
        provider = default_model.get("provider", "openai") if default_model else "openai"
        api_key = ""
        if default_model:
            # First check model's own API key
            api_key = default_model.get("api_key", "")
            # If not set, fall back to environment variable
            if not api_key:
                api_key = config_manager.get_api_key(provider) or ""
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "")
        
        model = model_id or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        
        # Check if API key is configured
        has_api_key = bool(api_key and len(api_key) > 10)
        
        # Test connection if key exists
        connected = False
        if has_api_key:
            try:
                connected = hasattr(orchestrator, '_llm_agent') and orchestrator._llm_agent is not None
            except Exception:
                pass
        
        return {
            "connected": connected,
            "has_api_key": has_api_key,
            "model": model,
            "model_name": model_name or model,
            "provider": provider,
            "api_key_preview": f"...{api_key[-4:]}" if has_api_key else None
        }
    
    # ============================================
    # Model Configuration API
    # ============================================
    
    @app.get("/api/models")
    async def get_models():
        """Get all model configurations"""
        default_model = config_manager.get_default_model()
        # Sanitize models to remove API keys
        models = []
        for m in config_manager.get_models():
            sanitized = {k: v for k, v in m.items() if k != 'api_key'}
            sanitized['has_api_key'] = bool(m.get('api_key'))
            models.append(sanitized)
        return {
            "models": models,
            "default": default_model.get("id") if default_model else None
        }
    
    @app.post("/api/models")
    async def add_model(request: Request):
        """Add a new model configuration"""
        try:
            data = await request.json()
            model = config_manager.add_model(data)
            return {"success": True, "model": model}
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            logger.exception("Failed to add model")
            raise HTTPException(500, f"Failed to add model: {str(e)}")
    
    @app.put("/api/models/{model_id}")
    async def update_model(model_id: str, request: Request):
        """Update a model configuration"""
        try:
            data = await request.json()
            model = config_manager.update_model(model_id, data)
            if model:
                return {"success": True, "model": model}
            raise HTTPException(404, "Model not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed to update model")
            raise HTTPException(500, f"Failed to update model: {str(e)}")
    
    @app.delete("/api/models/{model_id}")
    async def delete_model(model_id: str):
        """Delete a model configuration"""
        try:
            if config_manager.delete_model(model_id):
                return {"success": True}
            raise HTTPException(404, "Model not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed to delete model")
            raise HTTPException(500, f"Failed to delete model: {str(e)}")
    
    @app.post("/api/models/{model_id}/set-default")
    async def set_default_model(model_id: str):
        """Set a model as default"""
        try:
            model = config_manager.update_model(model_id, {"is_default": True})
            if model:
                return {"success": True, "model": model}
            raise HTTPException(404, "Model not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed to set default model")
            raise HTTPException(500, f"Failed to set default model: {str(e)}")
    
    @app.post("/api/config/reload")
    async def reload_config():
        """Reload configuration from file"""
        try:
            config = config_manager.reload()
            return {"success": True, "config": config}
        except Exception as e:
            logger.exception("Failed to reload config")
            raise HTTPException(500, f"Failed to reload config: {str(e)}")
    
    @app.get("/api/models/runtime-status")
    async def get_runtime_model_status():
        """获取运行时模型状态（包括每个 Agent 类型的当前模型和可用模型）"""
        try:
            from joinflow_agent.model_manager import get_model_manager
            manager = get_model_manager()
            status = manager.get_status()
            return {
                "success": True,
                "data": status
            }
        except Exception as e:
            logger.exception("Failed to get runtime model status")
            return {
                "success": False,
                "message": str(e)
            }
    
    @app.post("/api/restart")
    async def restart_server():
        """Restart the server (schedules restart in 1 second)"""
        import threading
        
        def delayed_restart():
            import time
            time.sleep(1)
            logger.info("Restarting server...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        
        threading.Thread(target=delayed_restart, daemon=True).start()
        return {"success": True, "message": "Server will restart in 1 second"}
    
    # ============================================
    # Chat Endpoint
    # ============================================
    
    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
        start_time = datetime.now()
        
        # Get or create session
        session = None
        if session_manager:
            session = session_manager.get_or_create_session(
                session_id=request.session_id,
                user_id=request.user_id
            )
        
        # Execute task
        result = orchestrator.execute(request.message)
        
        # Update session
        if session and session_manager:
            session.add_message("user", request.message)
            session.add_message("assistant", result.output)
            session.total_tokens += result.tokens_used
            session_manager.update_session(session)
        
        end_time = datetime.now()
        
        # Extract steps from result
        steps = []
        if result.data and result.data.get("steps"):
            steps = result.data["steps"]
        
        return ChatResponse(
            message=result.output,
            session_id=session.id if session else str(uuid.uuid4()),
            tokens_used=result.tokens_used,
            execution_time_ms=(end_time - start_time).total_seconds() * 1000,
            steps=steps
        )
    
    # ============================================
    # Task Execution Endpoints
    # ============================================
    
    @app.post("/task/execute")
    async def execute_task(request: TaskExecuteRequest, background_tasks: BackgroundTasks):
        """Start task execution with progress tracking"""
        
        # Create task
        task = task_manager.create_task(
            task_id=request.task_id,
            description=request.description,
            priority=request.priority,
            mode=request.mode
        )
        
        # Start execution in background with user-selected agents
        background_tasks.add_task(
            run_task_execution,
            task_manager,
            orchestrator,
            request.task_id,
            request.description,
            request.agents  # 传递用户选择的 agents
        )
        
        return {"task_id": task.id, "status": "started"}
    
    @app.get("/task/{task_id}")
    async def get_task(task_id: str):
        """Get task status"""
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(404, "Task not found")
        return task.to_dict()
    
    @app.get("/task/{task_id}/stream")
    async def task_stream(task_id: str):
        """Stream task progress via SSE"""
        
        async def event_generator():
            queue = await task_manager.subscribe(task_id)
            
            try:
                # Send initial state
                task = task_manager.get_task(task_id)
                if task:
                    yield f"data: {json.dumps(task.to_dict())}\n\n"
                
                # Stream updates
                while True:
                    try:
                        data = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield f"data: {json.dumps(data)}\n\n"
                        
                        # Check if task is done
                        if data.get("status") in ["completed", "failed", "cancelled"]:
                            break
                    except asyncio.TimeoutError:
                        # Send keepalive
                        yield f": keepalive\n\n"
            finally:
                task_manager.unsubscribe(task_id, queue)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    @app.delete("/task/{task_id}")
    async def cancel_task(task_id: str):
        """Cancel a task"""
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(404, "Task not found")
        
        task_manager.update_task(
            task_id,
            status=TaskStatus.CANCELLED,
            completed_at=datetime.now()
        )
        
        return {"status": "cancelled", "task_id": task_id}
    
    # Register subscription APIs
    try:
        from .subscription import register_subscription_routes
        register_subscription_routes(app)
        logger.info("✅ Subscription APIs loaded")
    except Exception as e:
        logger.warning(f"Subscription APIs not available: {e}")
    
    # Register Local OS APIs
    try:
        from .local_os_api import router as local_os_router
        app.include_router(local_os_router)
        logger.info("✅ Local OS APIs loaded")
    except Exception as e:
        logger.warning(f"Local OS APIs not available: {e}")
    
    # Register Enhanced Browser APIs
    try:
        from .browser_api import router as browser_router
        app.include_router(browser_router)
        logger.info("✅ Enhanced Browser APIs loaded")
    except Exception as e:
        logger.warning(f"Enhanced Browser APIs not available: {e}")
    
    # Register extended APIs
    try:
        from .api_extensions import register_extended_apis
        register_extended_apis(app, config_manager)
        logger.info("Extended APIs loaded")
    except Exception as e:
        logger.warning(f"Extended APIs not available: {e}")
    
    # Register new feature APIs (Memory, MCP, Checkpoint, Suggestions, Multimodal)
    try:
        register_new_feature_apis(app)
        logger.info("New feature APIs loaded (Memory, MCP, Checkpoint, Suggestions, Multimodal)")
    except Exception as e:
        logger.warning(f"New feature APIs not available: {e}")
    
    return app, task_queue


# ============================================
# Task Execution Logic
# ============================================

async def run_task_execution(
    task_manager: TaskManager,
    orchestrator,
    task_id: str,
    description: str,
    selected_agents: List[str] = None
):
    """Execute a task with step-by-step progress tracking
    
    Args:
        task_manager: Task manager instance
        orchestrator: Orchestrator instance
        task_id: Task ID
        description: Task description
        selected_agents: User-selected agents (optional)
    """
    
    try:
        # Update task status
        task_manager.update_task(
            task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now()
        )
        
        # Analyze and create steps with user-selected agents
        steps = analyze_task(description, selected_agents)
        for step in steps:
            task_manager.add_step(task_id, step)
        
        task = task_manager.get_task(task_id)
        total_steps = len(task.steps)
        
        # Execute each step
        for i, step in enumerate(task.steps):
            # Update current step
            task_manager.update_task(task_id, current_step=i)
            task_manager.update_step(
                task_id, i,
                status=StepStatus.RUNNING,
                started_at=datetime.now()
            )
            
            # Execute step
            try:
                output = await execute_step(orchestrator, step)
                
                task_manager.update_step(
                    task_id, i,
                    status=StepStatus.COMPLETED,
                    output=output,
                    completed_at=datetime.now()
                )
            except Exception as e:
                task_manager.update_step(
                    task_id, i,
                    status=StepStatus.FAILED,
                    error=str(e),
                    completed_at=datetime.now()
                )
                raise
            
            # Update progress
            progress = int(((i + 1) / total_steps) * 100)
            task_manager.update_task(task_id, progress=progress)
        
        # Get final result
        result = orchestrator.execute(description)
        
        # Mark as completed
        task_manager.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            result=result.output,
            completed_at=datetime.now()
        )
        
    except Exception as e:
        logger.exception(f"Task execution failed: {task_id}")
        task_manager.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error=str(e),
            completed_at=datetime.now()
        )


def analyze_task(description: str, selected_agents: List[str] = None) -> List[TaskStep]:
    """Analyze task and create execution steps
    
    Args:
        description: Task description
        selected_agents: User-selected agents (optional). If provided, respect user's choice.
    """
    steps = []
    desc_lower = description.lower()
    selected_agents = selected_agents or []
    
    # 如果用户只选择了 llm（大模型），则使用纯 LLM 模式
    is_llm_only_mode = len(selected_agents) == 1 and 'llm' in selected_agents
    # 如果用户只选择了 os（系统），则使用系统操作模式
    is_os_only_mode = len(selected_agents) == 1 and 'os' in selected_agents
    # 如果用户明确选择了 agents
    has_user_selected_agents = len(selected_agents) > 0
    
    # 检测是否是"打开应用+写内容+保存"类型的复合任务
    is_write_and_save_task = (
        ('记事本' in desc_lower or 'notepad' in desc_lower) and 
        ('写' in desc_lower or '小说' in desc_lower or '编辑' in desc_lower) and
        ('保存' in desc_lower or '桌面' in desc_lower)
    )
    
    # 如果是纯 LLM 模式
    if is_llm_only_mode:
        steps.append(TaskStep(
            id=str(uuid.uuid4())[:8],
            description="使用大模型理解并执行任务",
            agent="llm"
        ))
        return steps
    
    # 如果是系统操作模式，或者是写入保存类任务且选择了 os
    if is_os_only_mode or (is_write_and_save_task and 'os' in selected_agents):
        # 对于写入保存任务，创建更详细的步骤
        if is_write_and_save_task:
            steps.append(TaskStep(
                id=str(uuid.uuid4())[:8],
                description="使用大模型生成内容，打开记事本并保存文件到桌面",
                agent="os"
            ))
        else:
            steps.append(TaskStep(
                id=str(uuid.uuid4())[:8],
                description="执行本机系统操作（打开应用、文件操作等）",
                agent="os"
            ))
        
        # 如果同时选择了 LLM，添加总结步骤
        if 'llm' in selected_agents:
            steps.append(TaskStep(
                id=str(uuid.uuid4())[:8],
                description="总结任务执行结果",
                agent="llm"
            ))
        return steps
    
    # 如果用户选择了特定的 agents
    if has_user_selected_agents:
        # 对于写入保存类任务，优先使用 OS agent
        if is_write_and_save_task and ('os' in selected_agents or 'llm' in selected_agents):
            steps.append(TaskStep(
                id=str(uuid.uuid4())[:8],
                description="使用大模型生成内容，打开记事本并保存文件到桌面",
                agent="os"
            ))
            if 'llm' in selected_agents:
                steps.append(TaskStep(
                    id=str(uuid.uuid4())[:8],
                    description="总结任务执行结果",
                    agent="llm"
                ))
            return steps
        
        if 'browser' in selected_agents:
            steps.append(TaskStep(
                id=str(uuid.uuid4())[:8],
                description="使用浏览器执行网页相关操作",
                agent="browser"
            ))
        if 'code' in selected_agents:
            steps.append(TaskStep(
                id=str(uuid.uuid4())[:8],
                description="生成并执行代码",
                agent="code"
            ))
        if 'os' in selected_agents:
            steps.append(TaskStep(
                id=str(uuid.uuid4())[:8],
                description="执行本机系统操作",
                agent="os"
            ))
        if 'data' in selected_agents:
            steps.append(TaskStep(
                id=str(uuid.uuid4())[:8],
                description="处理和分析数据",
                agent="data"
            ))
        if 'vision' in selected_agents:
            steps.append(TaskStep(
                id=str(uuid.uuid4())[:8],
                description="分析图像内容",
                agent="vision"
            ))
        # 添加 LLM 总结
        if 'llm' in selected_agents or len(steps) > 0:
            steps.append(TaskStep(
                id=str(uuid.uuid4())[:8],
                description="分析和总结结果",
                agent="llm"
            ))
        return steps
    
    # 自动模式：根据关键词判断
    if any(kw in desc_lower for kw in ['搜索', 'search', '新闻', '网页', 'web']):
        steps.append(TaskStep(
            id=str(uuid.uuid4())[:8],
            description="搜索相关信息",
            agent="browser"
        ))
    
    if any(kw in desc_lower for kw in ['代码', 'code', 'python', '脚本', 'script', '编程']):
        steps.append(TaskStep(
            id=str(uuid.uuid4())[:8],
            description="生成代码实现",
            agent="code"
        ))
    
    # 本机操作关键词
    if any(kw in desc_lower for kw in ['打开', '记事本', '计算器', '画图', 'notepad', 'calc', '应用', '程序', '桌面', '保存到']):
        steps.append(TaskStep(
            id=str(uuid.uuid4())[:8],
            description="执行本机应用和系统操作",
            agent="os"
        ))
    
    if any(kw in desc_lower for kw in ['文件', '目录', 'file', 'folder', '读取']):
        steps.append(TaskStep(
            id=str(uuid.uuid4())[:8],
            description="执行文件操作",
            agent="os"
        ))
    
    if any(kw in desc_lower for kw in ['数据', '分析', 'data', 'analyze', '图表', '统计']):
        steps.append(TaskStep(
            id=str(uuid.uuid4())[:8],
            description="处理和分析数据",
            agent="data"
        ))
    
    if any(kw in desc_lower for kw in ['图片', '图像', 'image', '识别', '视觉']):
        steps.append(TaskStep(
            id=str(uuid.uuid4())[:8],
            description="分析图像内容",
            agent="vision"
        ))
    
    # Always add LLM for reasoning/summarizing
    steps.append(TaskStep(
        id=str(uuid.uuid4())[:8],
        description="分析和总结结果",
        agent="llm"
    ))
    
    return steps


async def execute_step(orchestrator, step: TaskStep) -> str:
    """Execute a single step using appropriate agent"""
    
    agent_type = step.agent.lower() if step.agent else "llm"
    description = step.description
    
    try:
        # 浏览器 Agent - 使用增强版
        if agent_type == "browser":
            from joinflow_agent.browser_enhanced import EnhancedBrowserAgent
            agent = EnhancedBrowserAgent(headless=True)
            
            try:
                # 根据任务描述判断操作类型
                if "搜索" in description or "search" in description.lower():
                    # 提取搜索关键词
                    import re
                    search_match = re.search(r'搜索[：:\s]*(.+)|search[:\s]+(.+)', description, re.IGNORECASE)
                    query = search_match.group(1) or search_match.group(2) if search_match else description
                    result = await agent.search_and_analyze(query, num_results=2)
                    return f"搜索完成: {result.get('final_summary', '')[:500]}"
                    
                elif "http" in description or "www" in description:
                    # 导航到 URL
                    import re
                    url_match = re.search(r'https?://[^\s<>"]+', description)
                    if url_match:
                        page_data = await agent.navigate(url_match.group())
                        analysis = await agent.analyze_page(extract_type="summary")
                        return f"页面分析: {analysis.get('analysis', '')[:500]}"
                    
                else:
                    # 通用浏览器任务
                    result = await agent.execute_task(description)
                    return f"任务完成: {str(result.get('results', []))[:500]}"
                    
            finally:
                await agent.close()
        
        # 系统 Agent
        elif agent_type == "os":
            from .local_os_api import local_intent_parser
            import subprocess
            import platform
            
            intent = local_intent_parser(description)
            outputs = []
            
            for cmd in intent.get('commands', [])[:3]:
                try:
                    if platform.system() == "Windows":
                        result = subprocess.run(
                            cmd, shell=True, capture_output=True, timeout=30,
                            encoding='utf-8', errors='replace'
                        )
                    else:
                        result = subprocess.run(
                            cmd, shell=True, capture_output=True, timeout=30,
                            text=True
                        )
                    outputs.append(result.stdout[:200] if result.stdout else "")
                except Exception as e:
                    outputs.append(f"Error: {e}")
            
            return f"系统操作完成: {intent.get('intent', '')} - {' '.join(outputs)[:300]}"
        
        # LLM Agent
        elif agent_type == "llm":
            from joinflow_agent.model_manager import get_model_manager, AgentType
            
            manager = get_model_manager()
            result = manager.call_llm_sync(
                AgentType.LLM,
                messages=[{"role": "user", "content": description}],
                max_tokens=1000,
                temperature=0.7
            )
            return result[:500] if result else "LLM 处理完成"
        
        # 代码 Agent
        elif agent_type == "code":
            return f"代码步骤完成: {description}"
        
        # 数据 Agent
        elif agent_type == "data":
            return f"数据处理完成: {description}"
        
        # 视觉 Agent
        elif agent_type == "vision":
            return f"视觉分析完成: {description}"
        
        # 默认
        else:
            await asyncio.sleep(1.0)
            return f"步骤 '{description}' 完成"
            
    except Exception as e:
        logger.error(f"Step execution error: {e}")
        return f"步骤执行失败: {str(e)[:100]}"


# ============================================
# New Feature APIs - 新功能API
# ============================================

def register_new_feature_apis(app):
    """注册新功能API端点"""
    
    # ========================
    # 长期记忆系统 API
    # ========================
    
    @app.post("/api/memory/store")
    async def store_memory(request: Request):
        """存储记忆"""
        try:
            from joinflow_memory.long_term_memory import get_memory_store, Memory, MemoryType, MemoryPriority
            
            data = await request.json()
            store = get_memory_store()
            
            memory = Memory(
                user_id=data.get('user_id', 'default'),
                memory_type=MemoryType(data.get('type', 'knowledge')),
                key=data.get('key', ''),
                content=data.get('content', ''),
                summary=data.get('summary', ''),
                tags=data.get('tags', []),
                priority=MemoryPriority(data.get('priority', 'medium'))
            )
            
            memory_id = store.store(memory)
            return {"success": True, "memory_id": memory_id}
            
        except Exception as e:
            logger.error(f"Memory store error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/memory/recall")
    async def recall_memory(
        query: str = "",
        user_id: str = "default",
        memory_type: str = None,
        limit: int = 10
    ):
        """检索记忆"""
        try:
            from joinflow_memory.long_term_memory import get_memory_store, MemoryType
            
            store = get_memory_store()
            
            mt = MemoryType(memory_type) if memory_type else None
            memories = store.recall(
                query=query or None,
                user_id=user_id,
                memory_type=mt,
                limit=limit
            )
            
            return {
                "success": True,
                "memories": [m.to_dict() for m in memories],
                "count": len(memories)
            }
            
        except Exception as e:
            logger.error(f"Memory recall error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/memory/context")
    async def get_memory_context(query: str, user_id: str = "default"):
        """获取相关上下文"""
        try:
            from joinflow_memory.long_term_memory import get_memory_store
            
            store = get_memory_store()
            context = store.get_relevant_context(query, user_id)
            
            return {"success": True, "context": context}
            
        except Exception as e:
            logger.error(f"Memory context error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/memory/stats")
    async def get_memory_stats(user_id: str = "default"):
        """获取记忆统计"""
        try:
            from joinflow_memory.long_term_memory import get_memory_store
            
            store = get_memory_store()
            stats = store.get_statistics(user_id)
            
            return {"success": True, "stats": stats}
            
        except Exception as e:
            logger.error(f"Memory stats error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.delete("/api/memory/{memory_id}")
    async def delete_memory(memory_id: str):
        """删除记忆"""
        try:
            from joinflow_memory.long_term_memory import get_memory_store
            
            store = get_memory_store()
            deleted = store.delete(memory_id)
            
            return {"success": deleted}
            
        except Exception as e:
            logger.error(f"Memory delete error: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================
    # MCP协议 API
    # ========================
    
    @app.get("/api/mcp/tools")
    async def list_mcp_tools():
        """列出MCP工具"""
        try:
            from joinflow_core.mcp_server import get_mcp_server
            
            server = get_mcp_server()
            tools = [tool.to_mcp_format() for tool in server.tools.values()]
            
            return {"success": True, "tools": tools}
            
        except Exception as e:
            logger.error(f"MCP tools error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/mcp/call")
    async def call_mcp_tool(request: Request):
        """调用MCP工具"""
        try:
            from joinflow_core.mcp_server import get_mcp_server
            
            data = await request.json()
            server = get_mcp_server()
            
            result = await server.handle_message({
                "method": "tools/call",
                "params": {
                    "name": data.get("tool"),
                    "arguments": data.get("arguments", {})
                },
                "id": 1
            })
            
            return result
            
        except Exception as e:
            logger.error(f"MCP call error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/mcp/servers")
    async def list_mcp_servers():
        """列出MCP服务器"""
        try:
            from joinflow_core.mcp_client import get_mcp_client
            
            client = get_mcp_client()
            servers = [s.to_dict() for s in client.list_servers()]
            
            return {"success": True, "servers": servers}
            
        except Exception as e:
            logger.error(f"MCP servers error: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================
    # 检查点/断点续传 API
    # ========================
    
    @app.get("/api/checkpoints")
    async def list_checkpoints(user_id: str = "default", status: str = None):
        """列出检查点"""
        try:
            from joinflow_core.checkpoint import get_checkpoint_manager, CheckpointStatus
            
            manager = get_checkpoint_manager()
            
            cp_status = CheckpointStatus(status) if status else None
            checkpoints = manager.list_checkpoints(user_id=user_id, status=cp_status)
            
            return {
                "success": True,
                "checkpoints": [cp.to_dict() for cp in checkpoints],
                "count": len(checkpoints)
            }
            
        except Exception as e:
            logger.error(f"Checkpoints list error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/checkpoints/resumable")
    async def get_resumable_checkpoints(user_id: str = "default"):
        """获取可恢复的检查点"""
        try:
            from joinflow_core.checkpoint import get_checkpoint_manager
            
            manager = get_checkpoint_manager()
            checkpoints = manager.get_resumable(user_id)
            
            return {
                "success": True,
                "checkpoints": [cp.to_dict() for cp in checkpoints],
                "count": len(checkpoints)
            }
            
        except Exception as e:
            logger.error(f"Resumable checkpoints error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/checkpoints/{task_id}")
    async def get_checkpoint(task_id: str):
        """获取检查点详情"""
        try:
            from joinflow_core.checkpoint import get_checkpoint_manager
            
            manager = get_checkpoint_manager()
            checkpoint = manager.load(task_id)
            
            if checkpoint:
                return {"success": True, "checkpoint": checkpoint.to_dict()}
            return {"success": False, "error": "Checkpoint not found"}
            
        except Exception as e:
            logger.error(f"Checkpoint get error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/checkpoints/{task_id}/pause")
    async def pause_checkpoint(task_id: str):
        """暂停任务"""
        try:
            from joinflow_core.checkpoint import get_checkpoint_manager
            
            manager = get_checkpoint_manager()
            success = manager.pause_task(task_id)
            
            return {"success": success}
            
        except Exception as e:
            logger.error(f"Checkpoint pause error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/checkpoints/{task_id}/resume")
    async def resume_checkpoint(task_id: str):
        """恢复任务"""
        try:
            from joinflow_core.checkpoint import get_checkpoint_manager
            
            manager = get_checkpoint_manager()
            checkpoint = manager.resume_task(task_id)
            
            if checkpoint:
                return {"success": True, "checkpoint": checkpoint.to_dict()}
            return {"success": False, "error": "Cannot resume task"}
            
        except Exception as e:
            logger.error(f"Checkpoint resume error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.delete("/api/checkpoints/{task_id}")
    async def delete_checkpoint(task_id: str):
        """删除检查点"""
        try:
            from joinflow_core.checkpoint import get_checkpoint_manager
            
            manager = get_checkpoint_manager()
            deleted = manager.delete(task_id)
            
            return {"success": deleted}
            
        except Exception as e:
            logger.error(f"Checkpoint delete error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/checkpoints/stats")
    async def get_checkpoint_stats(user_id: str = None):
        """获取检查点统计"""
        try:
            from joinflow_core.checkpoint import get_checkpoint_manager
            
            manager = get_checkpoint_manager()
            stats = manager.get_statistics(user_id)
            
            return {"success": True, "stats": stats}
            
        except Exception as e:
            logger.error(f"Checkpoint stats error: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================
    # 智能建议 API
    # ========================
    
    @app.get("/api/suggestions")
    async def get_suggestions(
        trigger: str = "idle",
        input_text: str = "",
        user_id: str = "default"
    ):
        """获取建议"""
        try:
            from joinflow_core.suggestion import get_suggestion_engine, SuggestionTrigger
            
            engine = get_suggestion_engine()
            
            context = {
                'trigger': trigger,
                'input': input_text,
                'user_id': user_id
            }
            
            suggestions = engine.get_suggestions(context)
            
            return {
                "success": True,
                "suggestions": [s.to_dict() for s in suggestions]
            }
            
        except Exception as e:
            logger.error(f"Suggestions error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/suggestions/input")
    async def get_input_suggestions(input_text: str, user_id: str = "default"):
        """获取输入建议"""
        try:
            from joinflow_core.suggestion import get_suggestion_engine
            
            engine = get_suggestion_engine()
            suggestions = engine.get_input_suggestions(input_text, user_id)
            
            return {
                "success": True,
                "suggestions": [s.to_dict() for s in suggestions]
            }
            
        except Exception as e:
            logger.error(f"Input suggestions error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/suggestions/feedback")
    async def suggestion_feedback(request: Request):
        """记录建议反馈"""
        try:
            from joinflow_core.suggestion import get_suggestion_engine
            
            data = await request.json()
            engine = get_suggestion_engine()
            
            engine.record_feedback(
                suggestion_id=data.get('suggestion_id'),
                accepted=data.get('accepted', False),
                user_id=data.get('user_id', 'default')
            )
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Suggestion feedback error: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================
    # 多模态 API
    # ========================
    
    @app.post("/api/multimodal/image/analyze")
    async def analyze_image(request: Request):
        """分析图像"""
        try:
            from joinflow_agent.multimodal.image import ImageProcessor
            
            data = await request.json()
            processor = ImageProcessor()
            
            result = processor.analyze(
                image=data.get('image'),  # base64 or path
                prompt=data.get('prompt', '请详细描述这张图片的内容')
            )
            
            return {"success": True, "result": result.to_dict()}
            
        except Exception as e:
            logger.error(f"Image analyze error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/multimodal/image/ocr")
    async def image_ocr(request: Request):
        """图像OCR"""
        try:
            from joinflow_agent.multimodal.image import ImageProcessor
            
            data = await request.json()
            processor = ImageProcessor()
            
            text = processor.extract_text(
                image=data.get('image'),
                language=data.get('language', 'auto')
            )
            
            return {"success": True, "text": text}
            
        except Exception as e:
            logger.error(f"Image OCR error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/multimodal/audio/transcribe")
    async def transcribe_audio(request: Request):
        """语音转文字"""
        try:
            from joinflow_agent.multimodal.audio import AudioProcessor
            
            data = await request.json()
            processor = AudioProcessor()
            
            result = processor.transcribe(
                audio=data.get('audio'),  # base64 or path
                language=data.get('language')
            )
            
            return {"success": True, "result": result.to_dict()}
            
        except Exception as e:
            logger.error(f"Audio transcribe error: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/multimodal/audio/synthesize")
    async def synthesize_speech(request: Request):
        """文字转语音"""
        try:
            from joinflow_agent.multimodal.audio import AudioProcessor
            
            data = await request.json()
            processor = AudioProcessor()
            
            result = processor.synthesize(
                text=data.get('text'),
                voice=data.get('voice', 'alloy'),
                speed=data.get('speed', 1.0)
            )
            
            return {
                "success": True,
                "audio_base64": result.to_base64(),
                "format": result.format
            }
            
        except Exception as e:
            logger.error(f"Audio synthesize error: {e}")
            return {"success": False, "error": str(e)}
    
    logger.info("New feature APIs registered")


# ============================================
# Server Runner
# ============================================

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the web server"""
    if not HAS_FASTAPI:
        print("FastAPI not installed. Install with:")
        print("   pip install fastapi uvicorn jinja2")
        return
    
    print("\n")
    print("=" * 60)
    print("  JoinFlow Web UI - Workflow Edition")
    print("=" * 60)
    print(f"  Open browser: http://localhost:{port}")
    print(f"  API Docs: http://localhost:{port}/docs")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print("\n")
    
    app, task_queue = create_web_app()
    
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    finally:
        pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="JoinFlow Web Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port to listen")
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port)
