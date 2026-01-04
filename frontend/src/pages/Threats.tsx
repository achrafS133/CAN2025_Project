import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import {
  AlertTriangle,
  Shield,
  Clock,
  Upload,
  CheckCircle,
  XCircle,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useState, useEffect, useRef } from "react";
import {
  threatsService,
  type ThreatHistoryItem,
  type ThreatStats,
} from "@/services";

export function Threats() {
  const [threats, setThreats] = useState<ThreatHistoryItem[]>([]);
  const [stats, setStats] = useState<ThreatStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [historyData, statsData] = await Promise.all([
        threatsService.getHistory(100),
        threatsService.getStats(),
      ]);
      setThreats(historyData.items);
      setStats(statsData);
      setError(null);
    } catch (err) {
      setError("Failed to load threat data");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setUploadError(null);
      const result = await threatsService.detectThreat(file);

      if (result.threats_detected > 0) {
        alert(
          `⚠️ ${
            result.threats_detected
          } threat(s) detected!\n\nTypes: ${result.detections
            .map((d) => d.threat_type)
            .join(", ")}\n\nCheck the threat history for details.`
        );
        await loadData();
      } else {
        alert("✅ No threats detected in the image. The area appears safe.");
      }
    } catch (err: unknown) {
      console.error("Upload failed:", err);
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setUploadError(
        `Failed to analyze image: ${errorMessage}. The threat detection service may be temporarily unavailable.`
      );
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleMarkResolved = async (threatId: number) => {
    try {
      setActionLoading(threatId);
      await threatsService.updateStatus(
        threatId,
        "resolved",
        "Handled by security team"
      );
      // Update local state immediately for better UX
      setThreats((prev) =>
        prev.map((t) => (t.id === threatId ? { ...t, status: "resolved" } : t))
      );
      // Refresh stats
      const statsData = await threatsService.getStats();
      setStats(statsData);
    } catch (err) {
      console.error("Failed to mark as resolved:", err);
      alert("Failed to update threat status. Please try again.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleMarkFalsePositive = async (threatId: number) => {
    try {
      setActionLoading(threatId);
      await threatsService.markFalsePositive(
        threatId,
        "Marked as false positive by operator"
      );
      // Update local state immediately
      setThreats((prev) =>
        prev.map((t) =>
          t.id === threatId ? { ...t, status: "false_positive" } : t
        )
      );
      // Refresh stats
      const statsData = await threatsService.getStats();
      setStats(statsData);
    } catch (err) {
      console.error("Failed to mark as false positive:", err);
      alert("Failed to update threat status. Please try again.");
    } finally {
      setActionLoading(null);
    }
  };

  const getSeverityColor = (confidence: number) => {
    if (confidence > 0.8) return "text-destructive";
    if (confidence > 0.5) return "text-yellow-500";
    return "text-blue-500";
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return "bg-destructive text-destructive-foreground";
      case "resolved":
        return "bg-green-500 text-white";
      case "false_positive":
        return "bg-gray-500 text-white";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading threats...</p>
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
            <Button onClick={loadData} className="mt-4">
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
          <h1 className="text-3xl font-bold">Threat Detection</h1>
          <p className="text-muted-foreground">
            Real-time security threats and anomaly detection
          </p>
        </div>
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Upload className="h-4 w-4 mr-2" />
            )}
            {uploading ? "Analyzing..." : "Upload Image"}
          </Button>
        </div>
      </div>

      {/* Upload Error Message */}
      {uploadError && (
        <div className="mb-6 p-4 bg-destructive/10 border border-destructive rounded-lg flex items-start gap-3">
          <XCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium text-destructive">
              Image Analysis Failed
            </p>
            <p className="text-sm text-destructive/80 mt-1">{uploadError}</p>
          </div>
          <button
            onClick={() => setUploadError(null)}
            className="text-destructive hover:text-destructive/80"
          >
            <XCircle className="h-4 w-4" />
          </button>
        </div>
      )}

      {stats && (
        <div className="grid gap-4 md:grid-cols-3 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Active Threats
              </CardTitle>
              <AlertTriangle className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_threats}</div>
              <p className="text-xs text-muted-foreground">
                Require immediate attention
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Detections
              </CardTitle>
              <Shield className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_detections}</div>
              <p className="text-xs text-muted-foreground">All time</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Resolved</CardTitle>
              <Clock className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.resolved}</div>
              <p className="text-xs text-muted-foreground">
                Successfully handled
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {threats.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Shield className="h-12 w-12 text-green-500 mb-4" />
            <p className="text-muted-foreground text-center">
              No threats detected yet.
              <br />
              Upload an image to start threat detection.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {threats.map((threat) => (
            <Card key={threat.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle
                        className={`h-5 w-5 ${getSeverityColor(
                          threat.confidence
                        )}`}
                      />
                      {threat.threat_type.toUpperCase()} Detected
                    </CardTitle>
                    <CardDescription className="mt-2">
                      {threat.location || "Unknown location"} •{" "}
                      {new Date(threat.timestamp).toLocaleString("en-GB", {
                        day: "2-digit",
                        month: "2-digit",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        hour12: false,
                      })}{" "}
                      • Confidence: {(threat.confidence * 100).toFixed(1)}%
                    </CardDescription>
                  </div>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${getStatusBadge(
                      threat.status
                    )}`}
                  >
                    {threat.status}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  {threat.status === "active" && (
                    <>
                      <Button
                        size="sm"
                        onClick={() => handleMarkResolved(threat.id)}
                        disabled={actionLoading === threat.id}
                      >
                        {actionLoading === threat.id ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <CheckCircle className="h-4 w-4 mr-2" />
                        )}
                        Mark Resolved
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleMarkFalsePositive(threat.id)}
                        disabled={actionLoading === threat.id}
                      >
                        <XCircle className="h-4 w-4 mr-2" />
                        False Positive
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
