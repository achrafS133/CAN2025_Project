"""
Comprehensive Logging Framework
Handles application logs and audit trails
"""

import logging
import structlog
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging(log_level: str = "INFO") -> structlog.BoundLogger:
    """
    Setup structured logging with both file and console output

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level),
        handlers=[
            logging.FileHandler(
                LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
            ),
            logging.StreamHandler(),
        ],
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


class AuditLogger:
    """
    Audit logger for tracking user actions and system events
    Compliant with security standards for forensic analysis
    """

    def __init__(self):
        self.audit_file = LOG_DIR / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        self.logger = logging.getLogger("audit")

        # Separate handler for audit logs
        handler = logging.FileHandler(self.audit_file)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        action: str = "",
        resource: str = "",
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ):
        """
        Log an audit event

        Args:
            event_type: Type of event (login, api_call, threat_detected, etc.)
            user_id: User identifier
            action: Action performed
            resource: Resource accessed
            status: success, failure, error
            details: Additional event details
            ip_address: Client IP address
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "status": status,
            "ip_address": ip_address,
            "details": details or {},
        }

        self.logger.info(json.dumps(audit_entry))

    def log_threat_detection(
        self,
        threat_type: str,
        confidence: float,
        location: str,
        image_path: Optional[str] = None,
        action_taken: str = "alert_sent",
    ):
        """Log threat detection event"""
        self.log_event(
            event_type="threat_detection",
            action="detect_threat",
            resource=threat_type,
            status="detected",
            details={
                "confidence": confidence,
                "location": location,
                "image_path": image_path,
                "action_taken": action_taken,
            },
        )

    def log_api_call(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        cost_usd: float,
        response_time_ms: float,
        status: str = "success",
    ):
        """Log AI API call for cost tracking"""
        self.log_event(
            event_type="api_call",
            action="ai_inference",
            resource=f"{provider}/{model}",
            status=status,
            details={
                "tokens_used": tokens_used,
                "cost_usd": cost_usd,
                "response_time_ms": response_time_ms,
            },
        )

    def log_user_query(
        self, user_id: str, query: str, model_used: str, response_length: int
    ):
        """Log user chat query"""
        self.log_event(
            event_type="user_query",
            user_id=user_id,
            action="chat_query",
            resource=model_used,
            status="success",
            details={"query_length": len(query), "response_length": response_length},
        )

    def log_alert_sent(
        self,
        alert_type: str,
        channel: str,
        recipient: str,
        message: str,
        status: str = "sent",
    ):
        """Log alert notifications"""
        self.log_event(
            event_type="alert_sent",
            action="send_alert",
            resource=channel,
            status=status,
            details={
                "alert_type": alert_type,
                "recipient": recipient,
                "message_preview": message[:100],
            },
        )

    def log_false_positive(
        self,
        threat_id: str,
        original_classification: str,
        corrected_by: str,
        feedback: str,
    ):
        """Log false positive feedback for model improvement"""
        self.log_event(
            event_type="false_positive_feedback",
            user_id=corrected_by,
            action="mark_false_positive",
            resource=threat_id,
            status="recorded",
            details={
                "original_classification": original_classification,
                "feedback": feedback,
            },
        )

    def log_system_event(
        self,
        event_name: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log system-level events"""
        self.log_event(
            event_type="system_event",
            action=event_name,
            resource="system",
            status=severity,
            details={"message": message, **(details or {})},
        )


class PerformanceLogger:
    """Logger for tracking performance metrics"""

    def __init__(self):
        self.perf_file = (
            LOG_DIR / f"performance_{datetime.now().strftime('%Y%m%d')}.log"
        )
        self.logger = logging.getLogger("performance")

        handler = logging.FileHandler(self.perf_file)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        context: Optional[Dict[str, Any]] = None,
    ):
        """Log a performance metric"""
        metric_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "metric": metric_name,
            "value": value,
            "unit": unit,
            "context": context or {},
        }

        self.logger.info(json.dumps(metric_entry))


# Global logger instances
app_logger = setup_logging()
audit_logger = AuditLogger()
perf_logger = PerformanceLogger()
