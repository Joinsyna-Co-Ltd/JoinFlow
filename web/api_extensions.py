"""
JoinFlow API Extensions
=======================

Extended API endpoints for:
- Knowledge Base management
- Qdrant service monitoring
- Token usage statistics
- File exports
"""

import os
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ==========================================
# Request/Response Models
# ==========================================

class KnowledgeUploadResponse(BaseModel):
    success: bool
    document_id: str
    filename: str
    collection: str
    status: str
    message: str


class QdrantHealthResponse(BaseModel):
    status: str
    url: str
    connected: bool
    available: bool
    in_memory_mode: bool
    collections: Dict[str, Any]
    token_usage: Dict[str, Any]


class TokenStatsResponse(BaseModel):
    session_start: str
    duration_minutes: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cached_queries: int
    cache_hits: int
    cache_hit_rate: str
    tokens_saved: int
    savings_percent: str
    estimated_cost_usd: str
    estimated_savings_usd: str


class ExportRequest(BaseModel):
    task_id: str
    format: str  # markdown, html, json, pdf, excel, ppt
    include_steps: bool = True
    include_metadata: bool = True


# ==========================================
# API Extension Registration
# ==========================================

def register_extended_apis(app, config_manager):
    """Register extended API endpoints"""
    
    # Get or create services
    qdrant_service = None
    kb_manager = None
    
    try:
        from joinflow_core.qdrant_service import get_qdrant_service
        qdrant_service = get_qdrant_service()
        logger.info("Qdrant service initialized for API")
    except Exception as e:
        logger.warning(f"Qdrant service not available: {e}")
    
    try:
        from joinflow_rag.knowledge_base import KnowledgeBaseManager
        
        # Get vector store and embedder from qdrant service
        vector_store = None
        embedder = None
        
        if qdrant_service and qdrant_service.is_available:
            from joinflow_index.qdrant_store import QdrantVectorStore
            from joinflow_index.config import QdrantConfig
            
            vector_store = QdrantVectorStore(
                QdrantConfig(
                    collection=qdrant_service.config.knowledge_collection,
                    vector_dim=qdrant_service.config.vector_dim,
                    url=qdrant_service.config.url
                ),
                client=qdrant_service.client
            )
            embedder = qdrant_service.get_embedder()
        
        kb_manager = KnowledgeBaseManager(
            storage_path="./knowledge_base",
            vector_store=vector_store,
            embedder=embedder
        )
        logger.info("Knowledge base manager initialized")
    except Exception as e:
        logger.warning(f"Knowledge base manager not available: {e}")
    
    # ==========================================
    # Qdrant Service APIs
    # ==========================================
    
    @app.get("/api/qdrant/health")
    async def qdrant_health():
        """Get Qdrant service health status"""
        if not qdrant_service:
            return {
                "status": "not_configured",
                "url": os.environ.get("QDRANT_URL", "http://localhost:6333"),
                "connected": False,
                "available": False,
                "in_memory_mode": False,
                "collections": {},
                "token_usage": {},
                "error": "Qdrant service not initialized"
            }
        
        return qdrant_service.health_check(force=True)
    
    @app.post("/api/qdrant/reconnect")
    async def qdrant_reconnect():
        """Attempt to reconnect to Qdrant server"""
        if not qdrant_service:
            raise HTTPException(503, "Qdrant service not configured")
        
        success = qdrant_service.reconnect()
        return {
            "success": success,
            "status": qdrant_service.status.value,
            "connected": qdrant_service.is_connected
        }
    
    @app.get("/api/qdrant/collections")
    async def list_collections():
        """List all Qdrant collections"""
        if not qdrant_service or not qdrant_service.is_available:
            raise HTTPException(503, "Qdrant not available")
        
        try:
            collections = qdrant_service.client.get_collections().collections
            return {
                "collections": [
                    {"name": c.name}
                    for c in collections
                ]
            }
        except Exception as e:
            raise HTTPException(500, str(e))
    
    # ==========================================
    # Token Usage & Cache APIs
    # ==========================================
    
    @app.get("/api/tokens/stats")
    async def get_token_stats():
        """Get token usage statistics"""
        if not qdrant_service:
            return {
                "error": "Token tracking not available",
                "message": "Qdrant service required for token tracking"
            }
        
        return qdrant_service.get_token_stats()
    
    @app.post("/api/tokens/reset")
    async def reset_token_stats():
        """Reset token usage statistics"""
        if not qdrant_service:
            raise HTTPException(503, "Token tracking not available")
        
        qdrant_service.reset_token_stats()
        return {"success": True, "message": "Token statistics reset"}
    
    @app.get("/api/cache/stats")
    async def get_cache_stats():
        """Get LLM response cache statistics"""
        if not qdrant_service or not qdrant_service.is_available:
            return {
                "enabled": False,
                "entries": 0,
                "message": "Cache not available"
            }
        
        try:
            # Get cache collection info
            info = qdrant_service.client.get_collection(
                qdrant_service.config.cache_collection
            )
            
            token_stats = qdrant_service.get_token_stats()
            
            return {
                "enabled": qdrant_service.config.cache_enabled,
                "collection": qdrant_service.config.cache_collection,
                "entries": info.points_count,
                "vectors_count": info.vectors_count,
                "similarity_threshold": qdrant_service.config.cache_similarity_threshold,
                "ttl_hours": qdrant_service.config.cache_ttl_hours,
                "cache_hits": token_stats.get("cache_hits", 0),
                "hit_rate": token_stats.get("cache_hit_rate", "0%"),
                "tokens_saved": token_stats.get("tokens_saved", 0),
                "savings_usd": token_stats.get("estimated_savings_usd", "$0.00")
            }
        except Exception as e:
            return {
                "enabled": qdrant_service.config.cache_enabled,
                "entries": 0,
                "error": str(e)
            }
    
    @app.post("/api/cache/clear")
    async def clear_cache(older_than_days: int = None):
        """Clear LLM response cache"""
        if not qdrant_service:
            raise HTTPException(503, "Cache not available")
        
        cleared = qdrant_service.clear_cache(older_than_days)
        return {
            "success": True,
            "cleared_entries": cleared,
            "message": f"Cleared {cleared} cache entries"
        }
    
    # ==========================================
    # Knowledge Base APIs
    # ==========================================
    
    @app.get("/api/knowledge/collections")
    async def list_kb_collections():
        """List knowledge base collections"""
        if not kb_manager:
            return {"collections": [], "error": "Knowledge base not configured"}
        
        collections = kb_manager.list_collections()
        return {
            "collections": [c.to_dict() for c in collections]
        }
    
    @app.post("/api/knowledge/collections")
    async def create_kb_collection(request: Request):
        """Create a new knowledge base collection"""
        if not kb_manager:
            raise HTTPException(503, "Knowledge base not configured")
        
        data = await request.json()
        
        from joinflow_rag.knowledge_base import Collection
        
        collection = Collection(
            name=data.get("name", ""),
            description=data.get("description", ""),
            chunk_size=data.get("chunk_size", 500),
            chunk_overlap=data.get("chunk_overlap", 50)
        )
        
        result = kb_manager.create_collection(collection)
        return {"success": True, "collection": result.to_dict()}
    
    @app.get("/api/knowledge/documents")
    async def list_documents(
        collection: str = None,
        status: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        """List documents in knowledge base"""
        if not kb_manager:
            return {"documents": [], "total": 0, "error": "Knowledge base not configured"}
        
        from joinflow_rag.knowledge_base import DocumentStatus
        
        status_enum = None
        if status:
            try:
                status_enum = DocumentStatus(status)
            except ValueError:
                pass
        
        docs, total = kb_manager.list_documents(
            collection=collection,
            status=status_enum,
            limit=limit,
            offset=offset
        )
        
        return {
            "documents": [d.to_dict() for d in docs],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    @app.post("/api/knowledge/upload")
    async def upload_document(
        file: UploadFile = File(...),
        collection: str = Form("default"),
        tags: str = Form("")
    ):
        """Upload a document to knowledge base"""
        if not kb_manager:
            raise HTTPException(503, "Knowledge base not configured")
        
        try:
            content = await file.read()
            tags_list = [t.strip() for t in tags.split(",") if t.strip()]
            
            doc = kb_manager.add_document(
                file_content=content,
                filename=file.filename,
                collection=collection,
                tags=tags_list
            )
            
            # Process document in background
            kb_manager.process_document(doc.id)
            
            return KnowledgeUploadResponse(
                success=True,
                document_id=doc.id,
                filename=file.filename,
                collection=collection,
                status=doc.status.value,
                message="Document uploaded and indexed successfully"
            )
            
        except Exception as e:
            logger.exception("Upload failed")
            raise HTTPException(500, f"Upload failed: {str(e)}")
    
    @app.post("/api/knowledge/text")
    async def add_text_document(request: Request):
        """Add text content directly to knowledge base"""
        if not kb_manager:
            raise HTTPException(503, "Knowledge base not configured")
        
        data = await request.json()
        
        doc = kb_manager.add_text_document(
            content=data.get("content", ""),
            name=data.get("name", f"text_{uuid.uuid4().hex[:8]}"),
            collection=data.get("collection", "default"),
            tags=data.get("tags", [])
        )
        
        kb_manager.process_document(doc.id)
        
        return {
            "success": True,
            "document_id": doc.id,
            "status": doc.status.value
        }
    
    @app.delete("/api/knowledge/documents/{doc_id}")
    async def delete_document(doc_id: str):
        """Delete a document from knowledge base"""
        if not kb_manager:
            raise HTTPException(503, "Knowledge base not configured")
        
        success = kb_manager.delete_document(doc_id)
        if not success:
            raise HTTPException(404, "Document not found")
        
        return {"success": True, "message": "Document deleted"}
    
    @app.get("/api/knowledge/search")
    async def search_knowledge(
        query: str,
        collection: str = None,
        top_k: int = 10
    ):
        """Search the knowledge base"""
        if not kb_manager:
            return {"results": [], "error": "Knowledge base not configured"}
        
        results = kb_manager.search_documents(
            query=query,
            collection=collection,
            top_k=top_k
        )
        
        return {"query": query, "results": results}
    
    @app.get("/api/knowledge/stats")
    async def get_kb_stats():
        """Get knowledge base statistics"""
        if not kb_manager:
            return {"error": "Knowledge base not configured"}
        
        return kb_manager.get_statistics()
    
    # ==========================================
    # Export APIs
    # ==========================================
    
    @app.post("/api/export/{format}")
    async def export_task_result(format: str, request: Request):
        """Export task result in various formats"""
        data = await request.json()
        
        task_id = data.get("task_id", "")
        description = data.get("description", "")
        result = data.get("result", "")
        steps = data.get("steps", [])
        metadata = data.get("metadata", {})
        
        try:
            if format == "markdown":
                from joinflow_core.exporter import MarkdownExporter
                content = MarkdownExporter.export_task_result(
                    task_id, description, result, steps, metadata
                )
                return StreamingResponse(
                    iter([content]),
                    media_type="text/markdown",
                    headers={"Content-Disposition": f"attachment; filename=task_{task_id}.md"}
                )
            
            elif format == "html":
                from joinflow_core.exporter import HTMLExporter
                content = HTMLExporter.export_task_result(
                    task_id, description, result, steps, metadata
                )
                return StreamingResponse(
                    iter([content]),
                    media_type="text/html",
                    headers={"Content-Disposition": f"attachment; filename=task_{task_id}.html"}
                )
            
            elif format == "json":
                from joinflow_core.exporter import JSONExporter
                content = JSONExporter.export_task_result(
                    task_id, description, result, steps, metadata
                )
                return StreamingResponse(
                    iter([content]),
                    media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename=task_{task_id}.json"}
                )
            
            elif format == "pdf":
                from joinflow_core.exporter import PDFExporter
                if not PDFExporter.is_available():
                    raise HTTPException(501, "PDF export requires reportlab: pip install reportlab")
                
                content = PDFExporter.export_task_result(
                    task_id, description, result, steps, metadata
                )
                return StreamingResponse(
                    iter([content]),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=task_{task_id}.pdf"}
                )
            
            elif format == "excel":
                from joinflow_core.advanced_exporter import ExcelExporter
                if not ExcelExporter.is_available():
                    raise HTTPException(501, "Excel export requires openpyxl: pip install openpyxl")
                
                content = ExcelExporter.export_task_result(
                    task_id, description, result, steps, metadata
                )
                return StreamingResponse(
                    iter([content]),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=task_{task_id}.xlsx"}
                )
            
            elif format == "ppt":
                from joinflow_core.advanced_exporter import PPTExporter
                if not PPTExporter.is_available():
                    raise HTTPException(501, "PPT export requires python-pptx: pip install python-pptx")
                
                content = PPTExporter.export_task_result(
                    task_id, description, result, steps, metadata
                )
                return StreamingResponse(
                    iter([content]),
                    media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    headers={"Content-Disposition": f"attachment; filename=task_{task_id}.pptx"}
                )
            
            else:
                raise HTTPException(400, f"Unsupported format: {format}")
                
        except ImportError as e:
            raise HTTPException(501, f"Export dependency not installed: {e}")
        except Exception as e:
            logger.exception(f"Export failed for format {format}")
            raise HTTPException(500, f"Export failed: {str(e)}")
    
    # ==========================================
    # LLM Providers APIs
    # ==========================================
    
    @app.get("/api/providers")
    async def get_all_providers():
        """Get all supported LLM providers"""
        try:
            from joinflow_core.llm_providers import (
                ALL_PROVIDERS, PROVIDERS_BY_CATEGORY, ProviderCategory
            )
            
            providers_list = []
            for provider_id, provider in ALL_PROVIDERS.items():
                providers_list.append({
                    "id": provider.id,
                    "name": provider.name,
                    "category": provider.category.value,
                    "api_base": provider.api_base,
                    "api_key_env": provider.api_key_env,
                    "description": provider.description,
                    "website": provider.website,
                    "docs_url": provider.docs_url,
                    "supports_streaming": provider.supports_streaming,
                    "supports_function_calling": provider.supports_function_calling,
                    "supports_vision": provider.supports_vision,
                    "models_count": len(provider.models),
                })
            
            # Group by category
            by_category = {
                "international": [],
                "chinese": [],
                "cloud": [],
                "local": [],
            }
            
            for cat, providers in PROVIDERS_BY_CATEGORY.items():
                cat_key = cat.value
                by_category[cat_key] = [p.id for p in providers]
            
            return {
                "providers": providers_list,
                "by_category": by_category,
                "total_providers": len(providers_list)
            }
            
        except ImportError:
            # Fallback if llm_providers not available
            return {
                "providers": [],
                "by_category": {},
                "total_providers": 0,
                "error": "LLM providers module not available"
            }
    
    @app.get("/api/providers/{provider_id}")
    async def get_provider_details(provider_id: str):
        """Get detailed information about a specific provider"""
        try:
            from joinflow_core.llm_providers import get_provider
            
            provider = get_provider(provider_id)
            if not provider:
                raise HTTPException(404, f"Provider not found: {provider_id}")
            
            return {
                "id": provider.id,
                "name": provider.name,
                "category": provider.category.value,
                "api_base": provider.api_base,
                "api_key_env": provider.api_key_env,
                "description": provider.description,
                "website": provider.website,
                "docs_url": provider.docs_url,
                "pricing_url": provider.pricing_url,
                "supports_streaming": provider.supports_streaming,
                "supports_function_calling": provider.supports_function_calling,
                "supports_vision": provider.supports_vision,
                "models": provider.models,
            }
            
        except ImportError:
            raise HTTPException(503, "LLM providers module not available")
    
    @app.get("/api/providers/{provider_id}/models")
    async def get_provider_models(provider_id: str):
        """Get all models for a specific provider"""
        try:
            from joinflow_core.llm_providers import get_provider
            
            provider = get_provider(provider_id)
            if not provider:
                raise HTTPException(404, f"Provider not found: {provider_id}")
            
            return {
                "provider": provider_id,
                "provider_name": provider.name,
                "models": provider.models,
                "total": len(provider.models)
            }
            
        except ImportError:
            raise HTTPException(503, "LLM providers module not available")
    
    @app.get("/api/models/all")
    async def get_all_models():
        """Get all models from all providers"""
        try:
            from joinflow_core.llm_providers import get_all_models
            
            models = get_all_models()
            return {
                "models": models,
                "total": len(models)
            }
            
        except ImportError:
            return {"models": [], "total": 0, "error": "LLM providers module not available"}
    
    @app.get("/api/models/search")
    async def search_models(query: str):
        """Search models by name or ID"""
        try:
            from joinflow_core.llm_providers import search_models
            
            results = search_models(query)
            return {
                "query": query,
                "results": results,
                "total": len(results)
            }
            
        except ImportError:
            return {"query": query, "results": [], "total": 0}
    
    logger.info("Extended APIs registered successfully")
