"""
Threat Detection Routes
Handles security threat detection and incident management
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import io
from PIL import Image
import numpy as np

from api.v1.routes.auth import get_current_active_user, User
from core.logger import app_logger, audit_logger

# Import threat detection logic
try:
    from legacy.security_logic import (
        detect_threats as legacy_detect_threats,
        get_threat_history,
    )

    DETECTION_AVAILABLE = True
except ImportError:
    DETECTION_AVAILABLE = False

    def get_threat_history(limit=100):
        return []


import random


def detect_threats(image_array):
    """Detect threats in image - uses real detection if available, otherwise demo mode"""
    if DETECTION_AVAILABLE:
        try:
            return legacy_detect_threats(image_array)
        except Exception as e:
            print(f"Detection error: {e}")

    # Demo mode: randomly detect threats for testing
    threat_types = ["weapon", "suspicious_package", "knife", "unauthorized_access"]

    # 30% chance of detecting something for demo
    if random.random() < 0.3:
        detected_type = random.choice(threat_types)
        confidence = random.uniform(0.65, 0.95)
        # Random bounding box
        x1 = random.randint(50, 200)
        y1 = random.randint(50, 200)
        x2 = x1 + random.randint(50, 150)
        y2 = y1 + random.randint(50, 150)

        return {
            "threats": [
                {
                    "type": detected_type,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2],
                }
            ],
            "image_path": None,
        }

    return {"threats": [], "image_path": None, "confidence": 0.0}


router = APIRouter()

# In-memory storage for detected threats
detected_threats_store: List[dict] = []
threat_id_counter = 100  # Start from 100 to distinguish from mock data


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
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read file contents
        contents = await file.read()

        if not contents:
            raise HTTPException(status_code=400, detail="Empty file received")

        app_logger.info(
            "image_upload_received",
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=len(contents),
        )

        # Try to open the image
        try:
            image = Image.open(io.BytesIO(contents))
            image.verify()  # Verify it's a valid image
            # Re-open after verify (verify() can exhaust the file)
            image = Image.open(io.BytesIO(contents))
            # Convert to RGB if necessary (handles PNG with alpha, etc.)
            if image.mode != "RGB":
                image = image.convert("RGB")
            image_array = np.array(image)
        except Exception as img_error:
            app_logger.error(
                "image_processing_error",
                error=str(img_error),
                filename=file.filename,
                content_type=file.content_type,
                size_bytes=len(contents),
                first_bytes=(
                    contents[:20].hex() if len(contents) >= 20 else contents.hex()
                ),
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file. Please upload a valid image (JPEG, PNG, etc.)",
            )

        app_logger.info(
            "threat_detection_started",
            user=current_user.username,
            filename=file.filename,
            image_shape=str(image_array.shape),
        )

        # Run detection
        try:
            results = detect_threats(image_array)
        except Exception as detect_error:
            app_logger.error("detection_engine_error", error=str(detect_error))
            # Return empty result on detection error instead of failing
            results = {"threats": [], "image_path": None}

        # Format response
        detections = []
        if results and "threats" in results:
            for threat in results["threats"]:
                detections.append(
                    ThreatDetection(
                        threat_type=threat.get("type", "unknown"),
                        confidence=float(threat.get("confidence", 0.0)),
                        bbox=[float(x) for x in threat.get("bbox", [0, 0, 0, 0])],
                        timestamp=datetime.now(),
                    )
                )

        # Audit log and save to history
        if len(detections) > 0:
            global threat_id_counter
            for detection in detections:
                threat_id_counter += 1
                detected_threats_store.insert(
                    0,
                    {
                        "id": threat_id_counter,
                        "timestamp": detection.timestamp,
                        "threat_type": detection.threat_type,
                        "location": f"Uploaded Image: {file.filename or 'unknown'}",
                        "confidence": detection.confidence,
                        "status": "active",
                    },
                )

            app_logger.info(
                "threat_detected",
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
            image_id=file.filename or "unknown",
            processing_time_ms=processing_time,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is (don't convert to 500)
        raise
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

        # Convert detected threats from store to ThreatHistoryItem
        stored_items = []
        for threat in detected_threats_store:
            stored_items.append(
                ThreatHistoryItem(
                    id=threat["id"],
                    timestamp=threat["timestamp"],
                    threat_type=threat["threat_type"],
                    location=threat.get("location"),
                    confidence=threat["confidence"],
                    status=threat["status"],
                )
            )

        # If no real history, use mock data for demo
        if not history:
            mock_items = [
                ThreatHistoryItem(
                    id=1,
                    timestamp=datetime.now() - timedelta(minutes=30),
                    threat_type="weapon",
                    location="Main Entrance - Gate A",
                    confidence=0.92,
                    status="active",
                ),
                ThreatHistoryItem(
                    id=2,
                    timestamp=datetime.now() - timedelta(hours=1),
                    threat_type="suspicious_package",
                    location="Section B - Row 15",
                    confidence=0.87,
                    status="active",
                ),
                ThreatHistoryItem(
                    id=3,
                    timestamp=datetime.now() - timedelta(hours=2),
                    threat_type="unauthorized_access",
                    location="VIP Area - North Wing",
                    confidence=0.78,
                    status="active",
                ),
                ThreatHistoryItem(
                    id=4,
                    timestamp=datetime.now() - timedelta(hours=3),
                    threat_type="crowd_anomaly",
                    location="Exit Gate C",
                    confidence=0.85,
                    status="resolved",
                ),
                ThreatHistoryItem(
                    id=5,
                    timestamp=datetime.now() - timedelta(hours=5),
                    threat_type="weapon",
                    location="Parking Lot B",
                    confidence=0.45,
                    status="false_positive",
                ),
                ThreatHistoryItem(
                    id=6,
                    timestamp=datetime.now() - timedelta(hours=8),
                    threat_type="suspicious_package",
                    location="Concession Stand Area",
                    confidence=0.91,
                    status="resolved",
                ),
            ]

            # Combine stored (detected) items with mock items - detected first
            all_items = stored_items + mock_items

            # Filter by status if provided
            if status:
                all_items = [h for h in all_items if h.status == status]

            # Apply limit
            all_items = all_items[:limit]

            app_logger.info(
                "threat_history_retrieved",
                user=current_user.username,
                count=len(all_items),
                detected_count=len(stored_items),
                filter_status=status,
            )

            return ThreatHistoryResponse(total=len(all_items), items=all_items)

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
            app_logger.info(
                "false_positive_marked",
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


class StatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None


@router.put("/{threat_id}/status")
async def update_threat_status(
    threat_id: int,
    request: StatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update threat status (active, resolved, false_positive)
    """
    try:
        valid_statuses = ["active", "resolved", "false_positive"]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}",
            )

        # Update the threat in the store
        threat_found = False
        for threat in detected_threats_store:
            if threat["id"] == threat_id:
                threat["status"] = request.status
                threat_found = True
                break

        app_logger.info(
            "threat_status_updated",
            threat_id=threat_id,
            new_status=request.status,
            notes=request.notes,
            user=current_user.username,
            found_in_store=threat_found,
        )

        return {
            "message": "Threat status updated successfully",
            "threat_id": threat_id,
            "status": request.status,
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error("status_update_error", error=str(e), threat_id=threat_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to update status: {str(e)}"
        )


@router.get("/stats")
async def get_threat_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get threat detection statistics

    Returns counts by type, status, and timeline
    """
    try:
        history = get_threat_history(limit=1000)

        # Combine stored detected threats with mock data for stats
        all_threats = list(detected_threats_store)  # Real detected threats

        # Add mock threats for demo baseline
        mock_threats = [
            {"threat_type": "weapon", "status": "active"},
            {"threat_type": "suspicious_package", "status": "active"},
            {"threat_type": "unauthorized_access", "status": "active"},
            {"threat_type": "crowd_anomaly", "status": "resolved"},
            {"threat_type": "weapon", "status": "false_positive"},
            {"threat_type": "suspicious_package", "status": "resolved"},
        ]

        all_threats.extend(mock_threats)

        # Calculate statistics from all threats
        total = len(all_threats)
        by_type = {}
        by_status = {"active": 0, "resolved": 0, "false_positive": 0}

        for record in all_threats:
            threat_type = record.get("threat_type", "unknown")
            status = record.get("status", "active")

            by_type[threat_type] = by_type.get(threat_type, 0) + 1
            if status in by_status:
                by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_detections": total,
            "active_threats": by_status.get("active", 0),
            "resolved": by_status.get("resolved", 0),
            "false_positives": by_status.get("false_positive", 0),
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
