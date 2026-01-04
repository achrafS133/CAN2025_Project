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
    from services.cost_tracker import CostTracker

    cost_tracker = CostTracker()
except ImportError as e:
    cost_tracker = None
    app_logger.warning(f"cost_tracker_module_not_available: {e}")

router = APIRouter()


# Models
class AlertRequest(BaseModel):
    message: str
    severity: str = "info"  # info, warning, critical
    channels: List[str] = ["slack"]  # slack, discord, whatsapp
    incident_id: Optional[str] = None


class AlertResponse(BaseModel):
    alert_id: str
    status: str
    sent_to: List[str]
    failed: List[str]
    timestamp: str


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
    total_api_calls: int
    by_provider: Dict[str, float]
    last_updated: str


class CostByProvider(BaseModel):
    provider: str
    model: str
    calls: int
    total_cost: float
    average_cost_per_call: float


class BudgetStatus(BaseModel):
    monthly_budget: float
    current_spent: float
    remaining: float
    percentage_used: float
    projected_end_of_month: float
    alert_threshold_reached: bool


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

        failed_channels = [ch for ch in alert.channels if ch not in sent_channels]

        return AlertResponse(
            alert_id=alert_id,
            status="sent" if sent_channels else "failed",
            sent_to=sent_channels,
            failed=failed_channels,
            timestamp=datetime.now().isoformat(),
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
    app_logger.info("alert_history_request", user=current_user.username)

    # Return mock alert history for demo
    mock_alerts = [
        {
            "id": "alert_001",
            "message": "High crowd density detected at Gate B",
            "severity": "warning",
            "channels": ["slack", "discord"],
            "status": "sent",
            "sent_at": (datetime.now() - timedelta(minutes=15)).isoformat(),
        },
        {
            "id": "alert_002",
            "message": "Potential weapon detected - Main Entrance",
            "severity": "critical",
            "channels": ["slack", "discord", "whatsapp"],
            "status": "sent",
            "sent_at": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "alert_003",
            "message": "Suspicious package identified - Section C",
            "severity": "critical",
            "channels": ["slack", "discord"],
            "status": "sent",
            "sent_at": (datetime.now() - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "alert_004",
            "message": "Unauthorized access attempt at VIP area",
            "severity": "warning",
            "channels": ["slack"],
            "status": "sent",
            "sent_at": (datetime.now() - timedelta(hours=3)).isoformat(),
        },
        {
            "id": "alert_005",
            "message": "System health check completed successfully",
            "severity": "info",
            "channels": ["slack"],
            "status": "sent",
            "sent_at": (datetime.now() - timedelta(hours=5)).isoformat(),
        },
    ]

    # Filter by severity if provided
    if severity:
        mock_alerts = [a for a in mock_alerts if a["severity"] == severity]

    # Apply limit
    mock_alerts = mock_alerts[:limit]

    return {"total": len(mock_alerts), "alerts": mock_alerts}


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

        app_logger.info("cost_stats_retrieved", user=current_user.username)

        return CostStats(
            daily_cost=daily_cost,
            monthly_cost=monthly_cost,
            total_api_calls=total_calls,
            by_provider=by_provider,
            last_updated=datetime.now().isoformat(),
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
                    model=f"{provider}-default",  # TODO: Get actual model name
                    calls=len(calls),
                    total_cost=total_cost,
                    average_cost_per_call=total_cost / len(calls) if calls else 0,
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
    # Always return mock data for now since cost_tracker may not be fully functional
    monthly_budget = 300.0
    current_spent = 45.0

    return BudgetStatus(
        monthly_budget=monthly_budget,
        current_spent=current_spent,
        remaining=monthly_budget - current_spent,
        percentage_used=(current_spent / monthly_budget) * 100,
        projected_end_of_month=current_spent * (30 / 4),  # Assuming 4 days in
        alert_threshold_reached=False,
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
