#!/usr/bin/env python3
"""
JoinFlow Subscription System
============================

Manages subscription plans, user subscriptions, and billing.
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class PricingPlan:
    """定价计划"""
    id: str
    name: str
    name_zh: str
    type: PlanType
    price_monthly: float
    price_yearly: float
    currency: str = "CNY"
    features: List[str] = field(default_factory=list)
    features_zh: List[str] = field(default_factory=list)
    limits: Dict[str, Any] = field(default_factory=dict)
    is_popular: bool = False
    is_enterprise: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "name_zh": self.name_zh,
            "type": self.type.value,
            "price_monthly": self.price_monthly,
            "price_yearly": self.price_yearly,
            "currency": self.currency,
            "features": self.features,
            "features_zh": self.features_zh,
            "limits": self.limits,
            "is_popular": self.is_popular,
            "is_enterprise": self.is_enterprise
        }


@dataclass
class Subscription:
    """用户订阅"""
    id: str
    user_id: str
    plan_id: str
    plan_type: PlanType
    billing_cycle: BillingCycle
    status: str  # active, cancelled, expired, trial
    start_date: datetime
    end_date: datetime
    trial_end: Optional[datetime] = None
    auto_renew: bool = True
    payment_method: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "plan_type": self.plan_type.value,
            "billing_cycle": self.billing_cycle.value,
            "status": self.status,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "trial_end": self.trial_end.isoformat() if self.trial_end else None,
            "auto_renew": self.auto_renew,
            "payment_method": self.payment_method,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# 默认定价计划
DEFAULT_PLANS = [
    PricingPlan(
        id="free",
        name="Free",
        name_zh="免费版",
        type=PlanType.FREE,
        price_monthly=0,
        price_yearly=0,
        features=[
            "5 tasks per day",
            "Basic Browser Agent",
            "Basic LLM Agent",
            "Community support",
            "All export formats"
        ],
        features_zh=[
            "每日 5 个任务",
            "基础浏览器 Agent",
            "基础 LLM Agent",
            "社区支持",
            "所有导出格式"
        ],
        limits={
            "tasks_per_day": 5,
            "agents": ["browser", "llm"],
            "export_formats": ["markdown", "html", "json", "pdf", "excel", "pptx"],
            "knowledge_base_docs": 10,
            "parallel_tasks": 1
        }
    ),
    PricingPlan(
        id="pro",
        name="Pro",
        name_zh="专业版",
        type=PlanType.PRO,
        price_monthly=99,
        price_yearly=999,
        is_popular=True,
        features=[
            "Unlimited tasks",
            "All 6 Agents",
            "Priority execution",
            "Email support",
            "All export formats",
            "Knowledge base (100 docs)",
            "API access",
            "Custom workflows"
        ],
        features_zh=[
            "无限任务",
            "全部 6 个 Agent",
            "优先执行",
            "邮件支持",
            "所有导出格式",
            "知识库 (100 文档)",
            "API 访问",
            "自定义工作流"
        ],
        limits={
            "tasks_per_day": -1,  # unlimited
            "agents": ["browser", "llm", "os", "code", "data", "vision"],
            "export_formats": ["markdown", "html", "json", "pdf", "excel"],
            "knowledge_base_docs": 100,
            "parallel_tasks": 3
        }
    ),
    PricingPlan(
        id="team",
        name="Team",
        name_zh="团队版",
        type=PlanType.TEAM,
        price_monthly=299,
        price_yearly=2999,
        features=[
            "Everything in Pro",
            "Up to 10 team members",
            "Team collaboration",
            "Shared workflows",
            "Priority support",
            "Knowledge base (1000 docs)",
            "Advanced analytics",
            "Custom integrations"
        ],
        features_zh=[
            "专业版全部功能",
            "最多 10 名团队成员",
            "团队协作",
            "共享工作流",
            "优先支持",
            "知识库 (1000 文档)",
            "高级分析",
            "自定义集成"
        ],
        limits={
            "tasks_per_day": -1,
            "agents": ["browser", "llm", "os", "code", "data", "vision"],
            "export_formats": ["markdown", "html", "json", "pdf", "excel", "pptx"],
            "knowledge_base_docs": 1000,
            "parallel_tasks": 5,
            "team_members": 10
        }
    ),
    PricingPlan(
        id="enterprise",
        name="Enterprise",
        name_zh="企业版",
        type=PlanType.ENTERPRISE,
        price_monthly=0,  # Custom pricing
        price_yearly=0,
        is_enterprise=True,
        features=[
            "Everything in Team",
            "Unlimited team members",
            "SSO/SAML",
            "Dedicated support",
            "SLA guarantee",
            "On-premise deployment",
            "Custom development",
            "Training & onboarding"
        ],
        features_zh=[
            "团队版全部功能",
            "无限团队成员",
            "SSO/SAML 单点登录",
            "专属支持",
            "SLA 保证",
            "私有化部署",
            "定制开发",
            "培训与入门指导"
        ],
        limits={
            "tasks_per_day": -1,
            "agents": ["browser", "llm", "os", "code", "data", "vision"],
            "export_formats": ["markdown", "html", "json", "pdf", "excel", "pptx", "custom"],
            "knowledge_base_docs": -1,
            "parallel_tasks": -1,
            "team_members": -1
        }
    )
]


class SubscriptionManager:
    """订阅管理器"""
    
    def __init__(self, storage_path: str = "./subscriptions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.subscriptions_file = self.storage_path / "subscriptions.json"
        self.plans = {p.id: p for p in DEFAULT_PLANS}
        self._subscriptions: Dict[str, Subscription] = {}
        self._load_subscriptions()
    
    def _load_subscriptions(self):
        """加载订阅数据"""
        if self.subscriptions_file.exists():
            try:
                with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for sub_data in data.get("subscriptions", []):
                        sub = self._dict_to_subscription(sub_data)
                        self._subscriptions[sub.user_id] = sub
            except Exception as e:
                logger.error(f"Failed to load subscriptions: {e}")
    
    def _save_subscriptions(self):
        """保存订阅数据"""
        try:
            data = {
                "subscriptions": [s.to_dict() for s in self._subscriptions.values()]
            }
            with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save subscriptions: {e}")
    
    def _dict_to_subscription(self, data: Dict) -> Subscription:
        """字典转订阅对象"""
        return Subscription(
            id=data["id"],
            user_id=data["user_id"],
            plan_id=data["plan_id"],
            plan_type=PlanType(data["plan_type"]),
            billing_cycle=BillingCycle(data["billing_cycle"]),
            status=data["status"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]),
            trial_end=datetime.fromisoformat(data["trial_end"]) if data.get("trial_end") else None,
            auto_renew=data.get("auto_renew", True),
            payment_method=data.get("payment_method"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )
    
    def get_plans(self) -> List[Dict]:
        """获取所有定价计划"""
        return [p.to_dict() for p in self.plans.values()]
    
    def get_plan(self, plan_id: str) -> Optional[Dict]:
        """获取单个定价计划"""
        plan = self.plans.get(plan_id)
        return plan.to_dict() if plan else None
    
    def get_subscription(self, user_id: str) -> Optional[Dict]:
        """获取用户订阅"""
        sub = self._subscriptions.get(user_id)
        if sub:
            # 检查是否过期
            if sub.status == "active" and sub.end_date < datetime.now():
                sub.status = "expired"
                sub.updated_at = datetime.now()
                self._save_subscriptions()
            return sub.to_dict()
        # 返回默认免费计划
        return {
            "plan_id": "free",
            "plan_type": "free",
            "status": "active",
            "limits": self.plans["free"].limits
        }
    
    def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        billing_cycle: str = "monthly",
        trial_days: int = 0
    ) -> Dict:
        """创建订阅"""
        plan = self.plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        now = datetime.now()
        
        if billing_cycle == "yearly":
            end_date = now + timedelta(days=365)
            cycle = BillingCycle.YEARLY
        else:
            end_date = now + timedelta(days=30)
            cycle = BillingCycle.MONTHLY
        
        trial_end = None
        status = "active"
        if trial_days > 0:
            trial_end = now + timedelta(days=trial_days)
            status = "trial"
        
        subscription = Subscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            plan_id=plan_id,
            plan_type=plan.type,
            billing_cycle=cycle,
            status=status,
            start_date=now,
            end_date=end_date,
            trial_end=trial_end,
            auto_renew=True
        )
        
        self._subscriptions[user_id] = subscription
        self._save_subscriptions()
        
        return subscription.to_dict()
    
    def cancel_subscription(self, user_id: str) -> bool:
        """取消订阅"""
        sub = self._subscriptions.get(user_id)
        if sub:
            sub.status = "cancelled"
            sub.auto_renew = False
            sub.updated_at = datetime.now()
            self._save_subscriptions()
            return True
        return False
    
    def update_subscription(self, user_id: str, updates: Dict) -> Optional[Dict]:
        """更新订阅"""
        sub = self._subscriptions.get(user_id)
        if sub:
            if "auto_renew" in updates:
                sub.auto_renew = updates["auto_renew"]
            if "payment_method" in updates:
                sub.payment_method = updates["payment_method"]
            sub.updated_at = datetime.now()
            self._save_subscriptions()
            return sub.to_dict()
        return None
    
    def check_feature_access(self, user_id: str, feature: str) -> bool:
        """检查功能访问权限"""
        sub_data = self.get_subscription(user_id)
        plan_id = sub_data.get("plan_id", "free")
        plan = self.plans.get(plan_id)
        
        if not plan:
            return False
        
        limits = plan.limits
        
        # 检查各种限制
        if feature == "unlimited_tasks":
            return limits.get("tasks_per_day", 0) == -1
        elif feature.startswith("agent_"):
            agent_name = feature.replace("agent_", "")
            return agent_name in limits.get("agents", [])
        elif feature.startswith("export_"):
            format_name = feature.replace("export_", "")
            return format_name in limits.get("export_formats", [])
        
        return True
    
    def get_usage_limits(self, user_id: str) -> Dict:
        """获取使用限制"""
        sub_data = self.get_subscription(user_id)
        plan_id = sub_data.get("plan_id", "free")
        plan = self.plans.get(plan_id)
        
        if plan:
            return plan.limits
        return self.plans["free"].limits


# 全局订阅管理器
subscription_manager = SubscriptionManager()


def register_subscription_routes(app, prefix: str = "/api"):
    """注册订阅相关路由"""
    from fastapi import HTTPException, Request
    from fastapi.responses import JSONResponse
    
    @app.get(f"{prefix}/pricing")
    async def get_pricing_plans():
        """获取所有定价计划"""
        plans = subscription_manager.get_plans()
        return {
            "plans": plans,
            "currency": "CNY",
            "currency_symbol": "¥"
        }
    
    @app.get(f"{prefix}/pricing/{{plan_id}}")
    async def get_pricing_plan(plan_id: str):
        """获取单个定价计划"""
        plan = subscription_manager.get_plan(plan_id)
        if not plan:
            raise HTTPException(404, "Plan not found")
        return plan
    
    @app.get(f"{prefix}/subscription")
    async def get_current_subscription(request: Request):
        """获取当前用户订阅状态"""
        # 从请求中获取用户ID（这里简化处理，实际应从认证中获取）
        user_id = request.headers.get("X-User-ID", "default")
        subscription = subscription_manager.get_subscription(user_id)
        plan = subscription_manager.get_plan(subscription.get("plan_id", "free"))
        return {
            "subscription": subscription,
            "plan": plan,
            "limits": subscription_manager.get_usage_limits(user_id)
        }
    
    @app.post(f"{prefix}/subscription/create")
    async def create_subscription(request: Request):
        """创建订阅"""
        try:
            data = await request.json()
            user_id = request.headers.get("X-User-ID", "default")
            
            subscription = subscription_manager.create_subscription(
                user_id=user_id,
                plan_id=data.get("plan_id", "pro"),
                billing_cycle=data.get("billing_cycle", "monthly"),
                trial_days=data.get("trial_days", 0)
            )
            
            return {"success": True, "subscription": subscription}
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            logger.exception("Failed to create subscription")
            raise HTTPException(500, f"Failed to create subscription: {str(e)}")
    
    @app.post(f"{prefix}/subscription/cancel")
    async def cancel_subscription(request: Request):
        """取消订阅"""
        user_id = request.headers.get("X-User-ID", "default")
        success = subscription_manager.cancel_subscription(user_id)
        if success:
            return {"success": True, "message": "Subscription cancelled"}
        raise HTTPException(404, "No active subscription found")
    
    @app.put(f"{prefix}/subscription")
    async def update_subscription(request: Request):
        """更新订阅设置"""
        try:
            data = await request.json()
            user_id = request.headers.get("X-User-ID", "default")
            
            subscription = subscription_manager.update_subscription(user_id, data)
            if subscription:
                return {"success": True, "subscription": subscription}
            raise HTTPException(404, "No subscription found")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed to update subscription")
            raise HTTPException(500, f"Failed to update subscription: {str(e)}")
    
    @app.get(f"{prefix}/subscription/check-access")
    async def check_feature_access(request: Request, feature: str):
        """检查功能访问权限"""
        user_id = request.headers.get("X-User-ID", "default")
        has_access = subscription_manager.check_feature_access(user_id, feature)
        return {
            "feature": feature,
            "has_access": has_access
        }
    
    logger.info("Subscription routes registered")

