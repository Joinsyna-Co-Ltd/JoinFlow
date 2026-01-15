"""
Web API Service
===============

FastAPI-based REST API for the agent system:
- Task execution endpoints
- Session management
- Real-time progress (SSE)
- WebSocket support
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Optional, Dict, List
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

# Check for FastAPI
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    logger.warning("FastAPI not installed. Install with: pip install fastapi uvicorn")


if HAS_FASTAPI:
    
    # -------------------------
    # Request/Response Models
    # -------------------------
    
    class ChatRequest(BaseModel):
        """Chat request model"""
        message: str = Field(..., description="User message")
        session_id: Optional[str] = Field(None, description="Session ID for context")
        user_id: str = Field("default", description="User identifier")
        stream: bool = Field(False, description="Enable streaming response")
        
    class ChatResponse(BaseModel):
        """Chat response model"""
        message: str
        session_id: str
        task_id: Optional[str] = None
        tokens_used: int = 0
        execution_time_ms: float = 0
        steps: List[dict] = []
    
    class TaskRequest(BaseModel):
        """Task execution request"""
        task: str = Field(..., description="Task description")
        user_id: str = Field("default")
        session_id: Optional[str] = None
        priority: int = Field(2, ge=1, le=4, description="Priority 1-4")
        async_execution: bool = Field(False, description="Execute asynchronously")
    
    class TaskResponse(BaseModel):
        """Task response model"""
        task_id: str
        status: str
        result: Optional[str] = None
        error: Optional[str] = None
        progress: float = 0
        created_at: str
        completed_at: Optional[str] = None
    
    class SessionRequest(BaseModel):
        """Session creation request"""
        user_id: str = Field("default")
        system_prompt: Optional[str] = None
        metadata: Optional[dict] = None
    
    class KnowledgeRequest(BaseModel):
        """Knowledge base query request"""
        query: str = Field(..., description="Search query")
        top_k: int = Field(5, ge=1, le=20)
        min_score: float = Field(0.3, ge=0, le=1)
    
    class DocumentRequest(BaseModel):
        """Document indexing request"""
        documents: List[str] = Field(..., description="Documents to index")
        metadata: Optional[List[dict]] = None
        collection: str = Field("default")
    
    
    # -------------------------
    # API Application
    # -------------------------
    
    def create_api(
        orchestrator: Any = None,
        session_manager: Any = None,
        task_queue: Any = None
    ) -> FastAPI:
        """
        Create FastAPI application with all endpoints.
        
        Args:
            orchestrator: Orchestrator instance
            session_manager: SessionManager instance  
            task_queue: TaskQueue instance
            
        Returns:
            Configured FastAPI application
        """
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info("Starting JoinFlow API...")
            if task_queue:
                task_queue.start()
            yield
            # Shutdown
            logger.info("Shutting down JoinFlow API...")
            if task_queue:
                task_queue.stop()
        
        app = FastAPI(
            title="JoinFlow Agent API",
            description="Multi-Agent RAG System API",
            version="0.2.0",
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
        
        # -------------------------
        # Health & Info
        # -------------------------
        
        @app.get("/")
        async def root():
            return {
                "name": "JoinFlow Agent API",
                "version": "0.2.0",
                "status": "running"
            }
        
        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            }
        
        @app.get("/info")
        async def info():
            info_data = {
                "agents": ["browser", "llm", "os", "code", "data", "vision"],
                "features": [
                    "multi-agent-orchestration",
                    "rag-retrieval",
                    "browser-automation",
                    "code-execution",
                    "data-processing",
                    "vision-understanding"
                ]
            }
            
            if task_queue:
                info_data["queue_stats"] = task_queue.get_stats()
            if session_manager:
                info_data["session_stats"] = session_manager.get_stats()
            
            return info_data
        
        # -------------------------
        # Chat Endpoints
        # -------------------------
        
        @app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
            """
            Send a message to the agent system.
            """
            if not orchestrator:
                raise HTTPException(500, "Orchestrator not configured")
            
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
            
            return ChatResponse(
                message=result.output,
                session_id=session.id if session else str(uuid.uuid4()),
                tokens_used=result.tokens_used,
                execution_time_ms=(end_time - start_time).total_seconds() * 1000,
                steps=result.data.get("steps", []) if result.data else []
            )
        
        @app.post("/chat/stream")
        async def chat_stream(request: ChatRequest):
            """
            Stream chat response using Server-Sent Events.
            """
            if not orchestrator:
                raise HTTPException(500, "Orchestrator not configured")
            
            async def generate():
                # Initial event
                yield f"data: {json.dumps({'type': 'start', 'message': 'Processing...'})}\n\n"
                
                # Execute (this would ideally be async with progress callbacks)
                result = orchestrator.execute(request.message)
                
                # Send result
                yield f"data: {json.dumps({'type': 'result', 'message': result.output})}\n\n"
                
                # Final event
                yield f"data: {json.dumps({'type': 'end', 'tokens': result.tokens_used})}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        
        # -------------------------
        # Task Endpoints
        # -------------------------
        
        @app.post("/task", response_model=TaskResponse)
        async def submit_task(request: TaskRequest):
            """
            Submit a task for execution.
            """
            if request.async_execution:
                if not task_queue:
                    raise HTTPException(500, "Task queue not configured")
                
                from .task_queue import TaskPriority
                
                task = task_queue.submit(
                    orchestrator.execute,
                    request.task,
                    name=request.task[:50],
                    priority=TaskPriority(request.priority),
                    user_id=request.user_id,
                    session_id=request.session_id
                )
                
                return TaskResponse(
                    task_id=task.id,
                    status=task.status.value,
                    progress=task.progress,
                    created_at=task.created_at.isoformat()
                )
            else:
                # Synchronous execution
                result = orchestrator.execute(request.task)
                
                return TaskResponse(
                    task_id=str(uuid.uuid4()),
                    status="completed" if result.status.value == "success" else "failed",
                    result=result.output,
                    error=result.error,
                    progress=100,
                    created_at=datetime.now().isoformat(),
                    completed_at=datetime.now().isoformat()
                )
        
        @app.get("/task/{task_id}", response_model=TaskResponse)
        async def get_task(task_id: str):
            """
            Get task status by ID.
            """
            if not task_queue:
                raise HTTPException(500, "Task queue not configured")
            
            task = task_queue.get_task(task_id)
            if not task:
                raise HTTPException(404, f"Task not found: {task_id}")
            
            return TaskResponse(
                task_id=task.id,
                status=task.status.value,
                result=str(task.result) if task.result else None,
                error=task.error,
                progress=task.progress,
                created_at=task.created_at.isoformat(),
                completed_at=task.completed_at.isoformat() if task.completed_at else None
            )
        
        @app.delete("/task/{task_id}")
        async def cancel_task(task_id: str):
            """
            Cancel a pending or running task.
            """
            if not task_queue:
                raise HTTPException(500, "Task queue not configured")
            
            success = task_queue.cancel_task(task_id)
            if not success:
                raise HTTPException(400, "Task cannot be cancelled")
            
            return {"status": "cancelled", "task_id": task_id}
        
        @app.get("/task/{task_id}/stream")
        async def task_progress_stream(task_id: str):
            """
            Stream task progress updates.
            """
            if not task_queue:
                raise HTTPException(500, "Task queue not configured")
            
            async def generate():
                while True:
                    task = task_queue.get_task(task_id)
                    if not task:
                        yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                        break
                    
                    yield f"data: {json.dumps(task.to_dict())}\n\n"
                    
                    if task.status.value in ("completed", "failed", "cancelled"):
                        break
                    
                    await asyncio.sleep(0.5)
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        
        # -------------------------
        # Session Endpoints
        # -------------------------
        
        @app.post("/session")
        async def create_session(request: SessionRequest):
            """
            Create a new session.
            """
            if not session_manager:
                raise HTTPException(500, "Session manager not configured")
            
            session = session_manager.create_session(
                user_id=request.user_id,
                system_prompt=request.system_prompt,
                metadata=request.metadata
            )
            
            return {"session_id": session.id, "user_id": session.user_id}
        
        @app.get("/session/{session_id}")
        async def get_session(session_id: str):
            """
            Get session details.
            """
            if not session_manager:
                raise HTTPException(500, "Session manager not configured")
            
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(404, f"Session not found: {session_id}")
            
            return session.to_dict()
        
        @app.delete("/session/{session_id}")
        async def delete_session(session_id: str):
            """
            Delete a session.
            """
            if not session_manager:
                raise HTTPException(500, "Session manager not configured")
            
            success = session_manager.delete_session(session_id)
            if not success:
                raise HTTPException(404, f"Session not found: {session_id}")
            
            return {"status": "deleted", "session_id": session_id}
        
        @app.get("/session/{session_id}/messages")
        async def get_session_messages(session_id: str, limit: int = 50):
            """
            Get session messages.
            """
            if not session_manager:
                raise HTTPException(500, "Session manager not configured")
            
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(404, f"Session not found: {session_id}")
            
            messages = session.get_messages(limit)
            return {"messages": [m.to_dict() for m in messages]}
        
        # -------------------------
        # Knowledge Base Endpoints
        # -------------------------
        
        @app.post("/knowledge/query")
        async def query_knowledge(request: KnowledgeRequest):
            """
            Query the knowledge base.
            """
            if not orchestrator or not orchestrator._rag_engine:
                raise HTTPException(500, "RAG engine not configured")
            
            from joinflow_rag.policies import RetrievalPolicy
            
            policy = RetrievalPolicy(
                top_k=request.top_k,
                min_score=request.min_score
            )
            
            response = orchestrator._rag_engine.query(request.query, policy=policy)
            
            return {
                "answer": response.answer,
                "context": [
                    {"doc_id": c.doc_id, "score": c.score, "content": c.content}
                    for c in response.context
                ]
            }
        
        @app.post("/knowledge/index")
        async def index_documents(request: DocumentRequest):
            """
            Index documents into knowledge base.
            """
            if not orchestrator or not orchestrator._rag_engine:
                raise HTTPException(500, "RAG engine not configured")
            
            # This would need proper document embedding
            # For now, return placeholder
            return {
                "status": "indexed",
                "document_count": len(request.documents),
                "collection": request.collection
            }
        
        # -------------------------
        # Agent Endpoints
        # -------------------------
        
        @app.post("/agent/browser")
        async def browser_agent(task: str):
            """
            Execute browser agent task.
            """
            if not orchestrator:
                raise HTTPException(500, "Orchestrator not configured")
            
            result = orchestrator._browser_agent.execute(task)
            return {
                "output": result.output,
                "success": result.status.value == "success"
            }
        
        @app.post("/agent/code")
        async def code_agent(code: str, language: str = "python"):
            """
            Execute code in sandbox.
            """
            from .code_executor import CodeExecutorAgent
            
            executor = CodeExecutorAgent()
            
            if language == "python":
                exec_result = executor._sandbox.execute_python(code)
            elif language in ("shell", "bash"):
                exec_result = executor._sandbox.execute_shell(code)
            else:
                raise HTTPException(400, f"Unsupported language: {language}")
            
            return {
                "success": exec_result.success,
                "output": exec_result.output,
                "error": exec_result.error,
                "execution_time_ms": exec_result.execution_time_ms
            }
        
        @app.post("/agent/data")
        async def data_agent(task: str):
            """
            Execute data processing task.
            """
            from .data_agent import DataProcessingAgent
            
            agent = DataProcessingAgent()
            result = agent.execute(task)
            
            return {
                "output": result.output,
                "data": result.data,
                "success": result.status.value == "success"
            }
        
        return app
    
    
    def run_api(
        orchestrator: Any = None,
        session_manager: Any = None,
        task_queue: Any = None,
        host: str = "0.0.0.0",
        port: int = 8000
    ) -> None:
        """
        Run the API server.
        
        Args:
            orchestrator: Orchestrator instance
            session_manager: SessionManager instance
            task_queue: TaskQueue instance
            host: Host to bind to
            port: Port to listen on
        """
        import uvicorn
        
        app = create_api(orchestrator, session_manager, task_queue)
        uvicorn.run(app, host=host, port=port)


else:
    # Stub when FastAPI not available
    def create_api(*args, **kwargs):
        raise ImportError("FastAPI not installed. Install with: pip install fastapi uvicorn")
    
    def run_api(*args, **kwargs):
        raise ImportError("FastAPI not installed. Install with: pip install fastapi uvicorn")

