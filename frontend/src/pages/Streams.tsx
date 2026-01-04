import { useState, useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { streamsService, type StreamInfo } from "@/services";
import {
  Video,
  Play,
  StopCircle,
  Plus,
  Trash2,
  AlertCircle,
  XCircle,
} from "lucide-react";

// Component for real webcam video
function WebcamPreview({ streamId }: { streamId: string }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const videoElement = videoRef.current;

    const startCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: false,
        });
        streamRef.current = mediaStream;
        if (videoElement) {
          videoElement.srcObject = mediaStream;
        }
      } catch (err) {
        console.error("Camera access error:", err);
        setError("Camera access denied or unavailable");
      }
    };

    startCamera();

    return () => {
      // Stop all tracks when component unmounts
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => {
          track.stop();
          console.log("Camera track stopped:", track.label);
        });
        streamRef.current = null;
      }
      // Clear video element
      if (videoElement) {
        videoElement.srcObject = null;
      }
    };
  }, [streamId]);

  if (error) {
    return (
      <div className="aspect-video bg-black rounded-lg flex items-center justify-center">
        <div className="text-center text-white">
          <Video className="h-12 w-12 mx-auto mb-2 text-red-500" />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <video
      ref={videoRef}
      autoPlay
      playsInline
      muted
      className="aspect-video bg-black rounded-lg w-full object-cover"
    />
  );
}

export function Streams() {
  const [streams, setStreams] = useState<StreamInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [streamErrors, setStreamErrors] = useState<Record<string, string>>({});
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newStream, setNewStream] = useState({
    name: "",
    source: "",
    enable_detection: true,
    detection_interval: 30,
  });

  useEffect(() => {
    loadStreams();
  }, []);

  const loadStreams = async () => {
    try {
      setLoading(true);
      const data = await streamsService.listStreams();
      setStreams(data);
      setError(null);
    } catch (err) {
      setError("Failed to load streams");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartStream = async (streamId: string, source: string) => {
    try {
      // Clear any previous error for this stream
      setStreamErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[streamId];
        return newErrors;
      });

      await streamsService.startStream(streamId);
      await loadStreams();

      // If source is not "0" (laptop camera), show a warning that RTSP streams are simulated
      if (source !== "0" && !source.startsWith("rtsp://")) {
        setStreamErrors((prev) => ({
          ...prev,
          [streamId]: "Stream source not available. Using simulation mode.",
        }));
      }
    } catch (err) {
      console.error("Failed to start stream:", err);
      setStreamErrors((prev) => ({
        ...prev,
        [streamId]:
          "Failed to start stream. The source may be unavailable or invalid.",
      }));
    }
  };

  const handleStopStream = async (streamId: string) => {
    try {
      await streamsService.stopStream(streamId);
      // Clear any error for this stream
      setStreamErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[streamId];
        return newErrors;
      });
      await loadStreams();
    } catch (err) {
      console.error("Failed to stop stream:", err);
    }
  };

  const clearStreamError = (streamId: string) => {
    setStreamErrors((prev) => {
      const newErrors = { ...prev };
      delete newErrors[streamId];
      return newErrors;
    });
  };

  const handleDeleteStream = async (streamId: string) => {
    if (!confirm("Are you sure you want to delete this stream?")) return;

    try {
      await streamsService.deleteStream(streamId);
      await loadStreams();
    } catch (err) {
      console.error("Failed to delete stream:", err);
    }
  };

  const handleAddStream = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await streamsService.createStream(newStream);
      setShowAddDialog(false);
      setNewStream({
        name: "",
        source: "",
        enable_detection: true,
        detection_interval: 30,
      });
      await loadStreams();
    } catch (err) {
      console.error("Failed to add stream:", err);
      alert("Failed to add stream. Please check your input.");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "text-green-500";
      case "inactive":
        return "text-gray-500";
      case "error":
        return "text-destructive";
      default:
        return "text-muted-foreground";
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading streams...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{error}</p>
            <Button onClick={loadStreams} className="mt-4">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Video Streams</h1>
          <p className="text-muted-foreground mt-2">
            Live camera feeds and recordings
          </p>
        </div>
        <Button onClick={() => setShowAddDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Stream
        </Button>
      </div>

      {/* Add Stream Dialog */}
      {showAddDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add New Stream</CardTitle>
              <CardDescription>
                Configure a new video stream source
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddStream} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Stream Name
                  </label>
                  <input
                    type="text"
                    required
                    value={newStream.name}
                    onChange={(e) =>
                      setNewStream({ ...newStream, name: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="e.g., Main Entrance Camera"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Source URL
                  </label>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      required
                      value={newStream.source}
                      onChange={(e) =>
                        setNewStream({ ...newStream, source: e.target.value })
                      }
                      className="flex-1 px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                      placeholder="rtsp://192.168.1.100/stream"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() =>
                        setNewStream({
                          ...newStream,
                          name: newStream.name || "Laptop Camera",
                          source: "0",
                        })
                      }
                      className="whitespace-nowrap"
                    >
                      Use Laptop Camera
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Supports RTSP, RTMP, or USB camera (e.g., 0 for /dev/video0)
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="enable_detection"
                    checked={newStream.enable_detection}
                    onChange={(e) =>
                      setNewStream({
                        ...newStream,
                        enable_detection: e.target.checked,
                      })
                    }
                    className="rounded border-input bg-background h-4 w-4 accent-primary"
                  />
                  <label htmlFor="enable_detection" className="text-sm">
                    Enable threat detection
                  </label>
                </div>

                {newStream.enable_detection && (
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Detection Interval (seconds)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="300"
                      value={newStream.detection_interval}
                      onChange={(e) =>
                        setNewStream({
                          ...newStream,
                          detection_interval: parseInt(e.target.value),
                        })
                      }
                      className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                  </div>
                )}

                <div className="flex gap-2 pt-4">
                  <Button type="submit" className="flex-1">
                    Add Stream
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowAddDialog(false)}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Streams</CardTitle>
            <Video className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{streams.length}</div>
            <p className="text-xs text-muted-foreground">Configured</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <Play className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {streams.filter((s) => s.status === "active").length}
            </div>
            <p className="text-xs text-muted-foreground">Streaming now</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Inactive</CardTitle>
            <StopCircle className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {streams.filter((s) => s.status !== "active").length}
            </div>
            <p className="text-xs text-muted-foreground">Offline</p>
          </CardContent>
        </Card>
      </div>

      {streams.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Video className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground text-center">
              No video streams configured yet.
              <br />
              Click "Add Stream" to get started.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {streams.map((stream) => (
            <Card key={stream.stream_id}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>{stream.name}</span>
                  <span
                    className={`text-sm font-normal ${getStatusColor(
                      stream.status
                    )}`}
                  >
                    {stream.status}
                  </span>
                </CardTitle>
                <CardDescription>{stream.source}</CardDescription>
              </CardHeader>
              <CardContent>
                {/* Video Preview - Real webcam for source "0" */}
                {stream.status === "active" && (
                  <div className="mb-4">
                    {stream.source === "0" ? (
                      <WebcamPreview
                        key={`${stream.stream_id}-${stream.started_at}`}
                        streamId={stream.stream_id}
                      />
                    ) : (
                      <div className="aspect-video bg-black rounded-lg flex items-center justify-center">
                        <div className="text-center text-white">
                          <Video className="h-12 w-12 mx-auto mb-2 animate-pulse" />
                          <p className="text-sm">Live Stream Active</p>
                          <p className="text-xs text-gray-400 mt-1">
                            {stream.name}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Stream Error Message */}
                {streamErrors[stream.stream_id] && (
                  <div className="mb-4 p-3 bg-destructive/10 border border-destructive rounded-lg flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm text-destructive">
                        {streamErrors[stream.stream_id]}
                      </p>
                    </div>
                    <button
                      onClick={() => clearStreamError(stream.stream_id)}
                      className="text-destructive hover:text-destructive/80"
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  </div>
                )}

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">FPS:</span>
                    <span className="font-medium">{stream.fps}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Resolution:</span>
                    <span className="font-medium">{stream.resolution}</span>
                  </div>
                  {stream.started_at && (
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Started:</span>
                      <span className="font-medium">
                        {new Date(stream.started_at).toLocaleTimeString(
                          "en-GB",
                          {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                            hour12: false,
                          }
                        )}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  {stream.status === "active" ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleStopStream(stream.stream_id)}
                    >
                      <StopCircle className="h-4 w-4 mr-2" />
                      Stop
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() =>
                        handleStartStream(stream.stream_id, stream.source)
                      }
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Start
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeleteStream(stream.stream_id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
