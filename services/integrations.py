"""
Multi-Channel Alert Integration System
Supports Slack, Discord, WhatsApp, and Smart Watch notifications
"""

import requests
from typing import Optional, Dict, Any
from datetime import datetime

from core.config import settings
from core.logger import app_logger, audit_logger


class SlackIntegration:
    """Send alerts to Slack channels"""

    def __init__(self):
        self.webhook_url = settings.integrations.slack_webhook_url
        self.channel = settings.integrations.slack_channel

    def send_alert(
        self,
        message: str,
        severity: str = "warning",
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send alert to Slack

        Args:
            message: Alert message
            severity: info, warning, critical
            details: Additional context

        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            app_logger.warning("slack_webhook_not_configured")
            return False

        # Color coding
        colors = {"info": "#36a64f", "warning": "#ff9900", "critical": "#ff0000"}

        payload = {
            "channel": self.channel,
            "username": "CAN 2025 Guardian",
            "icon_emoji": ":shield:",
            "attachments": [
                {
                    "color": colors.get(severity, "#cccccc"),
                    "title": f"🚨 Security Alert - {severity.upper()}",
                    "text": message,
                    "fields": [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in (details or {}).items()
                    ],
                    "footer": "CAN 2025 Guardian SOC",
                    "ts": int(datetime.now().timestamp()),
                }
            ],
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=5)

            if response.status_code == 200:
                app_logger.info("slack_alert_sent", severity=severity)
                audit_logger.log_alert_sent(
                    alert_type=severity,
                    channel="slack",
                    recipient=self.channel,
                    message=message,
                    status="sent",
                )
                return True
            else:
                app_logger.error("slack_alert_failed", status_code=response.status_code)
                return False

        except Exception as e:
            app_logger.error("slack_alert_exception", error=str(e))
            return False


class DiscordIntegration:
    """Send alerts to Discord channels"""

    def __init__(self):
        self.webhook_url = settings.integrations.discord_webhook_url

    def send_alert(
        self,
        message: str,
        severity: str = "warning",
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send alert to Discord"""
        if not self.webhook_url:
            app_logger.warning("discord_webhook_not_configured")
            return False

        # Color coding
        colors = {
            "info": 3447003,  # Blue
            "warning": 16776960,  # Orange
            "critical": 15158332,  # Red
        }

        embed = {
            "title": f"🚨 Security Alert - {severity.upper()}",
            "description": message,
            "color": colors.get(severity, 10070709),
            "fields": [
                {"name": k, "value": str(v), "inline": True}
                for k, v in (details or {}).items()
            ],
            "footer": {"text": "CAN 2025 Guardian SOC"},
            "timestamp": datetime.utcnow().isoformat(),
        }

        payload = {
            "username": "CAN 2025 Guardian",
            "avatar_url": "https://example.com/shield-icon.png",
            "embeds": [embed],
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=5)

            if response.status_code in [200, 204]:
                app_logger.info("discord_alert_sent", severity=severity)
                audit_logger.log_alert_sent(
                    alert_type=severity,
                    channel="discord",
                    recipient="webhook",
                    message=message,
                    status="sent",
                )
                return True
            else:
                app_logger.error(
                    "discord_alert_failed", status_code=response.status_code
                )
                return False

        except Exception as e:
            app_logger.error("discord_alert_exception", error=str(e))
            return False


class WhatsAppIntegration:
    """Send alerts via WhatsApp Business API"""

    def __init__(self):
        self.enabled = settings.integrations.whatsapp_enabled
        self.api_key = settings.integrations.whatsapp_api_key

    def send_alert(self, phone_number: str, message: str) -> bool:
        """
        Send alert via WhatsApp

        Note: Requires WhatsApp Business API account
        """
        if not self.enabled or not self.api_key:
            app_logger.warning("whatsapp_not_configured")
            return False

        # This is a placeholder - actual implementation depends on provider
        # (Twilio, MessageBird, etc.)

        app_logger.info("whatsapp_alert_placeholder", phone=phone_number)
        return False


class AlertRouter:
    """Routes alerts to appropriate channels"""

    def __init__(self):
        self.slack = SlackIntegration()
        self.discord = DiscordIntegration()
        self.whatsapp = WhatsAppIntegration()

    def send_multi_channel_alert(
        self,
        message: str,
        severity: str = "warning",
        details: Optional[Dict[str, Any]] = None,
        channels: list = ["slack", "discord"],
    ):
        """
        Send alert to multiple channels

        Args:
            message: Alert message
            severity: info, warning, critical
            details: Additional context
            channels: List of channels to notify
        """
        results = {}

        if "slack" in channels:
            results["slack"] = self.slack.send_alert(message, severity, details)

        if "discord" in channels:
            results["discord"] = self.discord.send_alert(message, severity, details)

        if "whatsapp" in channels:
            results["whatsapp"] = False  # Placeholder

        app_logger.info("multi_channel_alert_sent", results=results)
        return results

    def send_threat_detected_alert(
        self,
        threat_type: str,
        location: str,
        confidence: float,
        image_path: Optional[str] = None,
    ):
        """Send threat detection alert"""
        message = (
            f"⚠️ **Threat Detected**\n\n"
            f"Type: {threat_type}\n"
            f"Location: {location}\n"
            f"Confidence: {confidence:.1%}"
        )

        details = {
            "Threat Type": threat_type,
            "Location": location,
            "Confidence": f"{confidence:.1%}",
            "Time": datetime.now().strftime("%H:%M:%S"),
        }

        if image_path:
            details["Evidence"] = image_path

        self.send_multi_channel_alert(
            message=message, severity="critical", details=details
        )

    def send_crowd_density_alert(self, location: str, count: int, capacity: int):
        """Send crowd density warning"""
        density_percent = (count / capacity) * 100

        message = (
            f"👥 **High Crowd Density Alert**\n\n"
            f"Location: {location}\n"
            f"Count: {count}/{capacity}\n"
            f"Density: {density_percent:.0f}%"
        )

        details = {
            "Location": location,
            "People Count": count,
            "Capacity": capacity,
            "Density": f"{density_percent:.0f}%",
        }

        severity = "critical" if density_percent > 90 else "warning"

        self.send_multi_channel_alert(
            message=message, severity=severity, details=details
        )


# Global alert router instance
alert_router = AlertRouter()
