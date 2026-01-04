"""
Video Streaming Routes
Handles live camera feeds and multi-camera management
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import base64
import cv2
import asyncio

from api.v1.routes.auth import get_current_active_user, User
from core.logger import app_logger

# Import video stream logic
try:
    from services.video_stream import VideoStream, MultiCameraManager, create_multi_view

    camera_manager = MultiCameraManager()
except ImportError:
    camera_manager = None
    app_logger.warning("video_stream_module_not_available")

router = APIRouter()


# Models
class StreamInfo(BaseModel):
    stream_id: str
    name: str
    url: str
    status: str  # active, stopped, error
    fps: int
    resolution: str
    protocol: str  # rtsp, rtmp, usb


class StreamStats(BaseModel):
    stream_id: str
    frames_processed: int
    current_fps: float
    dropped_frames: int
    uptime_seconds: float


class AddStreamRequest(BaseModel):
    name: str
    url: str
    fps: int = 30
    buffer_size: int = 30


class MultiViewRequest(BaseModel):
    stream_ids: List[str]
    layout: str = "2x2"  # 2x2, 3x3, 1+3


# Routes
@router.get("/", response_model=List[StreamInfo])
async def get_all_streams(current_user: User = Depends(get_current_active_user)):
    """
    Get list of all camera streams

    Returns information about active and configured streams
    """
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")

    try:
        stats = camera_manager.get_stats()

        streams = []
        for stream_id, stream_stats in stats.items():
            # Extract stream info
            stream = camera_manager.streams.get(stream_id)
            if stream:
                streams.append(
                    StreamInfo(
                        stream_id=stream_id,
                        name=stream_stats.get("name", stream_id),
                        url=stream_stats.get("url", "unknown"),
                        status=(
                            "active"
                            if stream_stats.get("running", False)
                            else "stopped"
                        ),
                        fps=stream_stats.get("fps", 0),
                        resolution=stream_stats.get("resolution", "unknown"),
                        protocol=stream_stats.get("protocol", "unknown"),
                    )
                )

        app_logger.info(
            "streams_listed", user=current_user.username, count=len(streams)
        )

        return streams

    except Exception as e:
        app_logger.error("list_streams_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list streams: {str(e)}")


@router.post("/", status_code=201)
async def add_stream(
    request: AddStreamRequest, current_user: User = Depends(get_current_active_user)
):
    """
    Add new camera stream

    Supports RTSP, RTMP, and USB camera URLs
    """
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")

    try:
        # Check if max streams reached
        if len(camera_manager.streams) >= 4:
            raise HTTPException(status_code=400, detail="Maximum 4 streams allowed")

        app_logger.info(
            "adding_stream",
            user=current_user.username,
            name=request.name,
            url=request.url,
        )

        # Add stream
        stream_id = camera_manager.add_stream(
            url=request.url,
            name=request.name,
            fps=request.fps,
            buffer_size=request.buffer_size,
        )

        return {
            "message": "Stream added successfully",
            "stream_id": stream_id,
            "name": request.name,
        }

    except Exception as e:
        app_logger.error("add_stream_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to add stream: {str(e)}")


@router.delete("/{stream_id}")
async def remove_stream(
    stream_id: str, current_user: User = Depends(get_current_active_user)
):
    """
    Remove camera stream

    Stops the stream and removes it from active streams
    """
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")

    try:
        camera_manager.remove_stream(stream_id)

        app_logger.info(
            "stream_removed", user=current_user.username, stream_id=stream_id
        )

        return {"message": "Stream removed successfully", "stream_id": stream_id}

    except Exception as e:
        app_logger.error("remove_stream_error", error=str(e), stream_id=stream_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to remove stream: {str(e)}"
        )


@router.get("/{stream_id}/stats", response_model=StreamStats)
async def get_stream_stats(
    stream_id: str, current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed statistics for a specific stream
    """
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")

    try:
        stream = camera_manager.streams.get(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")

        stats = camera_manager.get_stats().get(stream_id, {})

        return StreamStats(
            stream_id=stream_id,
            frames_processed=stats.get("frames_processed", 0),
            current_fps=stats.get("fps", 0.0),
            dropped_frames=stats.get("dropped_frames", 0),
            uptime_seconds=stats.get("uptime_seconds", 0.0),
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error("stream_stats_error", error=str(e), stream_id=stream_id)
        raise HTTPException(
            status_code=500, detail=f"Failed to get stream stats: {str(e)}"
        )


@router.post("/multi-view")
async def get_multi_view(
    request: MultiViewRequest, current_user: User = Depends(get_current_active_user)
):
    """
    Create multi-camera view grid

    Combines multiple streams into a single grid layout
    """
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")

    try:
        # Validate stream IDs
        for stream_id in request.stream_ids:
            if stream_id not in camera_manager.streams:
                raise HTTPException(
                    status_code=404, detail=f"Stream {stream_id} not found"
                )

        # Create multi-view
        multi_view_frame = create_multi_view(camera_manager, request.stream_ids)

        if multi_view_frame is None:
            raise HTTPException(status_code=500, detail="Failed to create multi-view")

        # Encode frame to base64 for JSON response
        _, buffer = cv2.imencode(".jpg", multi_view_frame)
        frame_base64 = base64.b64encode(buffer).decode("utf-8")

        return {
            "layout": request.layout,
            "streams": request.stream_ids,
            "frame": frame_base64,
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error("multi_view_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to create multi-view: {str(e)}"
        )


@router.websocket("/{stream_id}")
async def stream_websocket(websocket: WebSocket, stream_id: str):
    """
    WebSocket endpoint for real-time video streaming

    Sends frames as base64-encoded JPEG images
    """
    await websocket.accept()

    if not camera_manager:
        await websocket.send_json({"error": "Camera manager not available"})
        await websocket.close()
        return

    try:
        # Get stream
        stream = camera_manager.streams.get(stream_id)
        if not stream:
            await websocket.send_json({"error": f"Stream {stream_id} not found"})
            await websocket.close()
            return

        app_logger.info("websocket_stream_started", stream_id=stream_id)

        # Send initial info
        await websocket.send_json(
            {"status": "connected", "stream_id": stream_id, "fps": stream.fps}
        )

        # Stream frames
        while True:
            try:
                # Get frame from stream
                frame = camera_manager.get_frame(stream_id)

                if frame is not None:
                    # Encode frame to JPEG
                    _, buffer = cv2.imencode(
                        ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
                    )
                    frame_base64 = base64.b64encode(buffer).decode("utf-8")

                    # Send frame
                    await websocket.send_json(
                        {
                            "type": "frame",
                            "stream_id": stream_id,
                            "timestamp": datetime.now().isoformat(),
                            "data": frame_base64,
                        }
                    )

                # Control frame rate
                await asyncio.sleep(1.0 / stream.fps)

            except WebSocketDisconnect:
                app_logger.info("websocket_stream_disconnected", stream_id=stream_id)
                break
            except Exception as e:
                app_logger.error(
                    "websocket_stream_error", error=str(e), stream_id=stream_id
                )
                await websocket.send_json({"error": str(e)})
                break

    except Exception as e:
        app_logger.error("websocket_connection_error", error=str(e))
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.post("/{stream_id}/start")
async def start_stream(
    stream_id: str, current_user: User = Depends(get_current_active_user)
):
    """
    Start a stopped stream
    """
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")

    try:
        stream = camera_manager.streams.get(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")

        stream.start()
        app_logger.info(
            "stream_started", stream_id=stream_id, user=current_user.username
        )

        return {"message": "Stream started", "stream_id": stream_id}

    except Exception as e:
        app_logger.error("start_stream_error", error=str(e), stream_id=stream_id)
        raise HTTPException(status_code=500, detail=f"Failed to start stream: {str(e)}")


@router.post("/{stream_id}/stop")
async def stop_stream(
    stream_id: str, current_user: User = Depends(get_current_active_user)
):
    """
    Stop a running stream
    """
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")

    try:
        stream = camera_manager.streams.get(stream_id)
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")

        stream.stop()
        app_logger.info(
            "stream_stopped", stream_id=stream_id, user=current_user.username
        )

        return {"message": "Stream stopped", "stream_id": stream_id}

    except Exception as e:
        app_logger.error("stop_stream_error", error=str(e), stream_id=stream_id)
        raise HTTPException(status_code=500, detail=f"Failed to stop stream: {str(e)}")
