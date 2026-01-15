"""API接口模块"""
from .server import create_app, OSAssistantAPI
from .routes import register_routes

__all__ = ["create_app", "OSAssistantAPI", "register_routes"]

