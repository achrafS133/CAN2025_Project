"""
Settings Routes
Handles system configuration and user preferences
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from api.v1.routes.auth import get_current_active_user, User
from core.logger import app_logger

router = APIRouter()

# In-memory settings storage (would be database in production)
user_settings_store = {}


class NotificationSettings(BaseModel):
    enable_notifications: bool = True
    email_alerts: bool = True
    sms_alerts: bool = False
    slack_integration: bool = True
    discord_integration: bool = False


class DetectionSettings(BaseModel):
    auto_detection: bool = True
    confidence_threshold: int = 75
    detection_interval: int = 30
    max_concurrent_streams: int = 4


class AppearanceSettings(BaseModel):
    dark_mode: bool = True
    compact_view: bool = False
    show_confidence_scores: bool = True


class DataSettings(BaseModel):
    retention_days: int = 90
    auto_archive: bool = True
    export_format: str = "csv"


class SystemSettings(BaseModel):
    notifications: NotificationSettings = NotificationSettings()
    detection: DetectionSettings = DetectionSettings()
    appearance: AppearanceSettings = AppearanceSettings()
    data: DataSettings = DataSettings()
    last_updated: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    notifications: Optional[NotificationSettings] = None
    detection: Optional[DetectionSettings] = None
    appearance: Optional[AppearanceSettings] = None
    data: Optional[DataSettings] = None


# Default settings
DEFAULT_SETTINGS = SystemSettings(
    notifications=NotificationSettings(),
    detection=DetectionSettings(),
    appearance=AppearanceSettings(),
    data=DataSettings(),
)


@router.get("/", response_model=SystemSettings)
async def get_settings(current_user: User = Depends(get_current_active_user)):
    """
    Get current system settings for the user
    """
    try:
        user_id = current_user.username

        # Get user settings or return defaults
        if user_id in user_settings_store:
            settings = user_settings_store[user_id]
        else:
            settings = DEFAULT_SETTINGS.model_copy()
            settings.last_updated = datetime.now().isoformat()

        app_logger.info("settings_retrieved", user=user_id)
        return settings

    except Exception as e:
        app_logger.error("settings_get_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


@router.put("/", response_model=SystemSettings)
async def update_settings(
    request: SettingsUpdateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update system settings
    """
    try:
        user_id = current_user.username

        # Get existing settings or create new
        if user_id in user_settings_store:
            current_settings = user_settings_store[user_id]
        else:
            current_settings = DEFAULT_SETTINGS.model_copy()

        # Update only provided fields
        if request.notifications:
            current_settings.notifications = request.notifications
        if request.detection:
            current_settings.detection = request.detection
        if request.appearance:
            current_settings.appearance = request.appearance
        if request.data:
            current_settings.data = request.data

        current_settings.last_updated = datetime.now().isoformat()

        # Store updated settings
        user_settings_store[user_id] = current_settings

        app_logger.info("settings_updated", user=user_id)

        return current_settings

    except Exception as e:
        app_logger.error("settings_update_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to update settings: {str(e)}"
        )


@router.post("/reset", response_model=SystemSettings)
async def reset_settings(current_user: User = Depends(get_current_active_user)):
    """
    Reset settings to defaults
    """
    try:
        user_id = current_user.username

        # Reset to defaults
        default = DEFAULT_SETTINGS.model_copy()
        default.last_updated = datetime.now().isoformat()
        user_settings_store[user_id] = default

        app_logger.info("settings_reset", user=user_id)

        return default

    except Exception as e:
        app_logger.error("settings_reset_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to reset settings: {str(e)}"
        )


@router.delete("/data")
async def clear_all_data(current_user: User = Depends(get_current_active_user)):
    """
    Clear all user data (threat history, alerts, etc.)
    WARNING: This action cannot be undone
    """
    try:
        user_id = current_user.username

        # In a real implementation, this would clear database records
        app_logger.warning("user_data_cleared", user=user_id)

        return {
            "message": "All data cleared successfully",
            "user": user_id,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        app_logger.error("data_clear_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")
