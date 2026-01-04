"""
Alerts and Cost Tracking Routes
Handles multi-channel alerts and API cost monitoring
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime, timedelta

from api.v1.routes.auth import get_current_active_user, User
from core.logger import app_logger, audit_logger

# Import integrations and cost tracking
try:
    from services.integrations import AlertRouter

    alert_router = AlertRouter()
except ImportError:
    alert_router = None
    app_logger.warning("integrations_module_not_available")

try:
    from cost_tracker import CostTracker

    cost_tracker = CostTracker()
except ImportError:
    cost_tracker = None
    app_logger.warning("cost_tracker_module_not_available")

router = APIRouter()


# Models
class AlertRequest(BaseModel):
    title: str
    message: str
    severity: str = "medium"  # low, medium, high, critical
    channels: List[str] = ["slack"]  # slack, discord, whatsapp
    metadata: Optional[Dict] = None


class AlertResponse(BaseModel):
    alert_id: str
    status: str
    channels_sent: List[str]
    timestamp: datetime


class ThreatAlert(BaseModel):
    threat_type: str
    confidence: float
    location: str
    image_url: Optional[str] = None


class CrowdAlert(BaseModel):
    location: str
    crowd_density: int
    threshold: int
    severity: str


class CostStats(BaseModel):
    daily_cost: float
    monthly_cost: float
    by_provider: Dict[str, float]
    total_calls: int
    average_cost_per_call: float


class CostByProvider(BaseModel):
    provider: str
    total_cost: float
    total_calls: int
    average_cost: float


class BudgetStatus(BaseModel):
    daily_budget: float
    monthly_budget: float
    daily_spent: float
    monthly_spent: float
    daily_remaining: float
    monthly_remaining: float
    should_alert: bool
    should_downgrade: bool


# Alert Routes
@router.post("/send", response_model=AlertResponse)
async def send_alert(
    alert: AlertRequest, current_user: User = Depends(get_current_active_user)
):
    """
    Send alert through multiple channels

    Supports: Slack, Discord, WhatsApp
    Severities: low, medium, high, critical
    """
    if not alert_router:
        raise HTTPException(status_code=503, detail="Alert system not available")

    try:
        app_logger.info(
            "alert_send_request",
            user=current_user.username,
            severity=alert.severity,
            channels=alert.channels,
        )

        # Send through selected channels
        sent_channels = []
        for channel in alert.channels:
            try:
                result = alert_router.send_multi_channel_alert(
                    title=alert.title,
                    message=alert.message,
                    severity=alert.severity,
                    channels=[channel],
                )
                if result:
                    sent_channels.append(channel)
            except Exception as e:
                app_logger.error(f"{channel}_alert_failed", error=str(e))

        # Generate alert ID
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Audit log
        audit_logger.log_alert_sent(
            alert_type=alert.severity,
            recipient=", ".join(alert.channels),
            user_id=current_user.username,
        )

        return AlertResponse(
            alert_id=alert_id,
            status="sent" if sent_channels else "failed",
            channels_sent=sent_channels,
            timestamp=datetime.now(),
        )

    except Exception as e:
        app_logger.error("send_alert_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")


@router.post("/threat")
async def send_threat_alert(
    threat: ThreatAlert, current_user: User = Depends(get_current_active_user)
):
    """
    Send threat-specific alert

    Automatically formats and sends to configured channels
    """
    if not alert_router:
        raise HTTPException(status_code=503, detail="Alert system not available")

    try:
        # Send threat alert
        result = alert_router.slack.send_threat_detected_alert(
            threat_type=threat.threat_type,
            confidence=threat.confidence,
            location=threat.location,
            image_url=threat.image_url,
        )

        # Also send to Discord
        alert_router.discord.send_threat_detected_alert(
            threat_type=threat.threat_type,
            confidence=threat.confidence,
            location=threat.location,
            image_url=threat.image_url,
        )

        app_logger.info(
            "threat_alert_sent",
            threat_type=threat.threat_type,
            location=threat.location,
        )

        return {
            "message": "Threat alert sent",
            "threat_type": threat.threat_type,
            "channels": ["slack", "discord"],
        }

    except Exception as e:
        app_logger.error("threat_alert_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to send threat alert: {str(e)}"
        )


@router.post("/crowd")
async def send_crowd_alert(
    crowd: CrowdAlert, current_user: User = Depends(get_current_active_user)
):
    """
    Send crowd density alert

    Triggered when crowd density exceeds threshold
    """
    if not alert_router:
        raise HTTPException(status_code=503, detail="Alert system not available")

    try:
        # Send crowd density alert
        alert_router.slack.send_crowd_density_alert(
            location=crowd.location,
            current_density=crowd.crowd_density,
            threshold=crowd.threshold,
        )

        alert_router.discord.send_crowd_density_alert(
            location=crowd.location,
            current_density=crowd.crowd_density,
            threshold=crowd.threshold,
        )

        app_logger.info(
            "crowd_alert_sent", location=crowd.location, density=crowd.crowd_density
        )

        return {
            "message": "Crowd alert sent",
            "location": crowd.location,
            "channels": ["slack", "discord"],
        }

    except Exception as e:
        app_logger.error("crowd_alert_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to send crowd alert: {str(e)}"
        )


@router.get("/history")
async def get_alert_history(
    limit: int = 50,
    severity: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get alert history

    Query Parameters:
    - limit: Maximum number of alerts (default: 50)
    - severity: Filter by severity (low, medium, high, critical)
    """
    # TODO: Implement database query
    app_logger.info("alert_history_request", user=current_user.username)

    return {"total": 0, "alerts": []}


# Cost Tracking Routes
@router.get("/costs", response_model=CostStats)
async def get_cost_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get API cost statistics

    Returns daily and monthly costs by provider
    """
    if not cost_tracker:
        raise HTTPException(status_code=503, detail="Cost tracker not available")

    try:
        daily_cost = cost_tracker.get_daily_cost()
        monthly_cost = cost_tracker.get_monthly_cost()
        by_provider = cost_tracker.get_cost_by_provider()

        # Calculate total calls
        total_calls = sum(
            len(cost_tracker.calls.get(provider, []))
            for provider in ["openai", "gemini", "claude"]
        )
        avg_cost = (monthly_cost / total_calls) if total_calls > 0 else 0

        app_logger.info("cost_stats_retrieved", user=current_user.username)

        return CostStats(
            daily_cost=daily_cost,
            monthly_cost=monthly_cost,
            by_provider=by_provider,
            total_calls=total_calls,
            average_cost_per_call=avg_cost,
        )

    except Exception as e:
        app_logger.error("cost_stats_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get cost stats: {str(e)}"
        )


@router.get("/costs/by-provider", response_model=List[CostByProvider])
async def get_costs_by_provider(current_user: User = Depends(get_current_active_user)):
    """
    Get detailed cost breakdown by provider
    """
    if not cost_tracker:
        raise HTTPException(status_code=503, detail="Cost tracker not available")

    try:
        by_provider = cost_tracker.get_cost_by_provider()

        result = []
        for provider, total_cost in by_provider.items():
            calls = cost_tracker.calls.get(provider, [])
            result.append(
                CostByProvider(
                    provider=provider,
                    total_cost=total_cost,
                    total_calls=len(calls),
                    average_cost=total_cost / len(calls) if calls else 0,
                )
            )

        return result

    except Exception as e:
        app_logger.error("cost_by_provider_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get costs by provider: {str(e)}"
        )


@router.get("/costs/budget", response_model=BudgetStatus)
async def get_budget_status(current_user: User = Depends(get_current_active_user)):
    """
    Get budget status and recommendations

    Returns spending vs budget and whether to downgrade model
    """
    if not cost_tracker:
        raise HTTPException(status_code=503, detail="Cost tracker not available")

    try:
        daily_cost = cost_tracker.get_daily_cost()
        monthly_cost = cost_tracker.get_monthly_cost()

        # Get budget limits from config
        daily_budget = 10.0  # $10/day default
        monthly_budget = 300.0  # $300/month default

        should_downgrade = cost_tracker.should_downgrade_model()

        return BudgetStatus(
            daily_budget=daily_budget,
            monthly_budget=monthly_budget,
            daily_spent=daily_cost,
            monthly_spent=monthly_cost,
            daily_remaining=daily_budget - daily_cost,
            monthly_remaining=monthly_budget - monthly_cost,
            should_alert=monthly_cost >= (monthly_budget * 0.8),
            should_downgrade=should_downgrade,
        )

    except Exception as e:
        app_logger.error("budget_status_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get budget status: {str(e)}"
        )


@router.delete("/costs/reset")
async def reset_cost_tracking(current_user: User = Depends(get_current_active_user)):
    """
    Reset cost tracking data

    WARNING: This will clear all cost history
    """
    if not cost_tracker:
        raise HTTPException(status_code=503, detail="Cost tracker not available")

    try:
        # Clear calls
        cost_tracker.calls = {"openai": [], "gemini": [], "claude": []}
        cost_tracker.save_to_file()

        app_logger.info("cost_tracking_reset", user=current_user.username)
        audit_logger.log_system_event(
            "cost_tracking_reset", user_id=current_user.username
        )

        return {"message": "Cost tracking data reset successfully"}

    except Exception as e:
        app_logger.error("cost_reset_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to reset cost tracking: {str(e)}"
        )
