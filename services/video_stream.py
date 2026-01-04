"""
Video Stream Processor
Supports RTSP/RTMP live camera feeds, multi-camera view
"""

import cv2
import numpy as np
from typing import Optional, List, Tuple, Dict
from threading import Thread
from queue import Queue
import time

from core.config import settings
from core.logger import app_logger, perf_logger


class VideoStream:
    """Process live video streams from RTSP/RTMP sources"""

    def __init__(self, source: str, stream_id: str, buffer_size: int = 30):
        """
        Initialize video stream

        Args:
            source: Video source (RTSP URL, RTMP URL, or camera index)
            stream_id: Unique identifier for this stream
            buffer_size: Frame buffer size
        """
        self.source = source
        self.stream_id = stream_id
        self.buffer_size = buffer_size

        self.stream = None
        self.frame_queue = Queue(maxsize=buffer_size)
        self.stopped = False
        self.thread = None

        self.fps = 0
        self.frame_count = 0
        self.width = 0
        self.height = 0

        app_logger.info("video_stream_initialized", stream_id=stream_id, source=source)

    def start(self) -> bool:
        """Start capturing from video stream"""
        try:
            self.stream = cv2.VideoCapture(self.source)

            if not self.stream.isOpened():
                app_logger.error("stream_open_failed", stream_id=self.stream_id)
                return False

            # Get stream properties
            self.fps = self.stream.get(cv2.CAP_PROP_FPS)
            self.width = int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Start capture thread
            self.stopped = False
            self.thread = Thread(target=self._capture_frames, daemon=True)
            self.thread.start()

            app_logger.info(
                "video_stream_started",
                stream_id=self.stream_id,
                fps=self.fps,
                resolution=f"{self.width}x{self.height}",
            )

            return True

        except Exception as e:
            app_logger.error(
                "video_stream_start_failed", stream_id=self.stream_id, error=str(e)
            )
            return False

    def _capture_frames(self):
        """Capture frames in background thread"""
        while not self.stopped:
            if not self.stream.isOpened():
                break

            ret, frame = self.stream.read()

            if not ret:
                app_logger.warning("frame_read_failed", stream_id=self.stream_id)
                continue

            # Add to queue (drop oldest if full)
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except:
                    pass

            self.frame_queue.put(frame)
            self.frame_count += 1

            # Sleep to match target FPS
            if settings.video_stream.processing_fps > 0:
                time.sleep(1.0 / settings.video_stream.processing_fps)

    def read(self) -> Optional[np.ndarray]:
        """
        Read next frame from stream

        Returns:
            Frame as numpy array or None if not available
        """
        if self.frame_queue.empty():
            return None

        try:
            return self.frame_queue.get_nowait()
        except:
            return None

    def stop(self):
        """Stop capturing from stream"""
        self.stopped = True

        if self.thread is not None:
            self.thread.join(timeout=2)

        if self.stream is not None:
            self.stream.release()

        app_logger.info(
            "video_stream_stopped",
            stream_id=self.stream_id,
            frames_processed=self.frame_count,
        )

    def get_stats(self) -> Dict:
        """Get stream statistics"""
        return {
            "stream_id": self.stream_id,
            "fps": self.fps,
            "resolution": f"{self.width}x{self.height}",
            "frames_processed": self.frame_count,
            "buffer_size": self.frame_queue.qsize(),
            "is_active": not self.stopped,
        }


class MultiCameraManager:
    """Manage multiple video streams simultaneously"""

    def __init__(self, max_streams: int = 4):
        """
        Initialize multi-camera manager

        Args:
            max_streams: Maximum number of concurrent streams
        """
        self.max_streams = max_streams
        self.streams: Dict[str, VideoStream] = {}

        app_logger.info("multi_camera_manager_initialized", max_streams=max_streams)

    def add_stream(self, source: str, stream_id: str) -> bool:
        """
        Add a new video stream

        Args:
            source: Video source URL or camera index
            stream_id: Unique identifier for stream

        Returns:
            True if added successfully
        """
        if len(self.streams) >= self.max_streams:
            app_logger.warning(
                "max_streams_reached", current=len(self.streams), max=self.max_streams
            )
            return False

        if stream_id in self.streams:
            app_logger.warning("stream_already_exists", stream_id=stream_id)
            return False

        stream = VideoStream(source, stream_id)
        if stream.start():
            self.streams[stream_id] = stream
            return True

        return False

    def remove_stream(self, stream_id: str) -> bool:
        """Remove and stop a video stream"""
        if stream_id not in self.streams:
            return False

        self.streams[stream_id].stop()
        del self.streams[stream_id]

        app_logger.info("stream_removed", stream_id=stream_id)
        return True

    def get_frame(self, stream_id: str) -> Optional[np.ndarray]:
        """Get latest frame from specific stream"""
        if stream_id not in self.streams:
            return None

        return self.streams[stream_id].read()

    def get_all_frames(self) -> Dict[str, np.ndarray]:
        """Get latest frame from all active streams"""
        frames = {}
        for stream_id, stream in self.streams.items():
            frame = stream.read()
            if frame is not None:
                frames[stream_id] = frame

        return frames

    def stop_all(self):
        """Stop all video streams"""
        for stream_id in list(self.streams.keys()):
            self.remove_stream(stream_id)

        app_logger.info("all_streams_stopped")

    def get_stats(self) -> List[Dict]:
        """Get statistics for all streams"""
        return [stream.get_stats() for stream in self.streams.values()]


def create_multi_view(
    frames: Dict[str, np.ndarray], grid_size: Tuple[int, int] = (2, 2)
) -> np.ndarray:
    """
    Create a grid view of multiple camera feeds

    Args:
        frames: Dictionary of stream_id -> frame
        grid_size: (rows, cols) for grid layout

    Returns:
        Combined grid image
    """
    rows, cols = grid_size

    # Get target size for each cell (use first frame's size)
    if not frames:
        return np.zeros((480, 640, 3), dtype=np.uint8)

    first_frame = next(iter(frames.values()))
    cell_height, cell_width = first_frame.shape[:2]

    # Resize to fit grid
    cell_height = cell_height // rows
    cell_width = cell_width // cols

    # Create blank grid
    grid = np.zeros((cell_height * rows, cell_width * cols, 3), dtype=np.uint8)

    # Fill grid with frames
    stream_ids = list(frames.keys())
    for idx in range(min(len(frames), rows * cols)):
        row = idx // cols
        col = idx % cols

        frame = frames[stream_ids[idx]]
        resized = cv2.resize(frame, (cell_width, cell_height))

        y_start = row * cell_height
        y_end = (row + 1) * cell_height
        x_start = col * cell_width
        x_end = (col + 1) * cell_width

        grid[y_start:y_end, x_start:x_end] = resized

        # Add stream ID label
        cv2.putText(
            grid,
            stream_ids[idx],
            (x_start + 10, y_start + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

    return grid


# Global multi-camera manager
camera_manager = MultiCameraManager(
    max_streams=settings.video_stream.max_concurrent_streams
)
