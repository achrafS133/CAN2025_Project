"""
Threat Detection Routes
Handles security threat detection and incident management
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import io
from PIL import Image
import numpy as np

from api.v1.routes.auth import get_current_active_user, User
from core.logger import app_logger, audit_logger

# Import threat detection logic
try:
    from legacy.security_logic import detect_threats, get_threat_history
except ImportError:
    # Fallback if module not available
    def detect_threats(image_array):
        return {"threats": [], "image_path": None, "confidence": 0.0}

    def get_threat_history(limit=100):
        return []


router = APIRouter()


# Models
class ThreatDetection(BaseModel):
    threat_type: str
    confidence: float
    bbox: List[float]
    timestamp: datetime


class ThreatDetectionResponse(BaseModel):
    status: str
    threats_detected: int
    detections: List[ThreatDetection]
    image_id: Optional[str] = None
    processing_time_ms: float


class ThreatHistoryItem(BaseModel):
    id: int
    timestamp: datetime
    threat_type: str
    location: Optional[str] = None
    confidence: float
    status: str  # active, resolved, false_positive


class ThreatHistoryResponse(BaseModel):
    total: int
    items: List[ThreatHistoryItem]


class FeedbackRequest(BaseModel):
    is_false_positive: bool
    notes: Optional[str] = None


# Routes
@router.post("/detect", response_model=ThreatDetectionResponse)
async def detect_threat(
    file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)
):
    """
    Detect threats in uploaded image using YOLOv8

    Supports: weapons, suspicious packages, unauthorized access
    """
    start_time = datetime.now()

    # Validate file
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image_array = np.array(image)

        app_logger.info(
            "threat_detection_started",
            user=current_user.username,
            filename=file.filename,
            image_shape=image_array.shape,
        )

        # Run detection
        results = detect_threats(image_array)

        # Format response
        detections = []
        if results and "threats" in results:
            for threat in results["threats"]:
                detections.append(
                    ThreatDetection(
                        threat_type=threat.get("type", "unknown"),
                        confidence=threat.get("confidence", 0.0),
                        bbox=threat.get("bbox", [0, 0, 0, 0]),
                        timestamp=datetime.now(),
                    )
                )

        # Audit log
        if len(detections) > 0:
            audit_logger.log_threat_detection(
                threat_type=detections[0].threat_type,
                confidence=detections[0].confidence,
                location="uploaded_image",
                user_id=current_user.username,
            )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return ThreatDetectionResponse(
            status="success" if len(detections) > 0 else "no_threats",
            threats_detected=len(detections),
            detections=detections,
            image_id=file.filename,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        app_logger.error(
            "threat_detection_error", error=str(e), user=current_user.username
        )
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.get("/history", response_model=ThreatHistoryResponse)
async def get_threats_history(
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get threat detection history

    Query Parameters:
    - limit: Maximum number of records (default: 100)
    - status: Filter by status (active, resolved, false_positive)
    """
    try:
        # Get history from database
        history = get_threat_history(limit=limit)

        # Filter by status if provided
        if status:
            history = [h for h in history if h.get("status") == status]

        # Format response
        items = []
        for record in history:
            items.append(
                ThreatHistoryItem(
                    id=record.get("id", 0),
                    timestamp=record.get("timestamp", datetime.now()),
                    threat_type=record.get("threat_type", "unknown"),
                    location=record.get("location"),
                    confidence=record.get("confidence", 0.0),
                    status=record.get("status", "active"),
                )
            )

        app_logger.info(
            "threat_history_retrieved",
            user=current_user.username,
            count=len(items),
            filter_status=status,
        )

        return ThreatHistoryResponse(total=len(items), items=items)

    except Exception as e:
        app_logger.error("threat_history_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve history: {str(e)}"
        )


@router.post("/{threat_id}/feedback")
async def submit_feedback(
    threat_id: int,
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit feedback for a threat detection (mark as false positive)
    """
    try:
        # Log feedback
        if feedback.is_false_positive:
            audit_logger.log_false_positive(
                threat_id=threat_id,
                reason=feedback.notes or "User marked as false positive",
                user_id=current_user.username,
            )
            status = "false_positive"
        else:
            status = "confirmed"

        app_logger.info(
            "threat_feedback_submitted",
            threat_id=threat_id,
            status=status,
            user=current_user.username,
        )

        # TODO: Update database with feedback

        return {
            "message": "Feedback submitted successfully",
            "threat_id": threat_id,
            "status": status,
        }

    except Exception as e:
        app_logger.error("feedback_submission_error", error=str(e), threat_id=threat_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/stats")
async def get_threat_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get threat detection statistics

    Returns counts by type, status, and timeline
    """
    try:
        history = get_threat_history(limit=1000)

        # Calculate statistics
        total = len(history)
        by_type = {}
        by_status = {"active": 0, "resolved": 0, "false_positive": 0}

        for record in history:
            threat_type = record.get("threat_type", "unknown")
            status = record.get("status", "active")

            by_type[threat_type] = by_type.get(threat_type, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_detections": total,
            "by_type": by_type,
            "by_status": by_status,
            "false_positive_rate": (
                (by_status["false_positive"] / total * 100) if total > 0 else 0
            ),
        }

    except Exception as e:
        app_logger.error("threat_stats_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )
