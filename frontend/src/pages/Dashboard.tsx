import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Shield, AlertTriangle, CheckCircle, Activity } from "lucide-react";
import { useState, useEffect } from "react";
import { analyticsService, type DashboardStats } from "@/services";

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await analyticsService.getDashboardStats();
      setStats(data);
      setError(null);
    } catch (err) {
      console.error("Failed to load dashboard stats:", err);
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <p className="text-destructive mb-4">
            {error || "No data available"}
          </p>
          <button
            onClick={loadStats}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case "critical":
        return "text-destructive";
      case "high":
        return "text-orange-500";
      case "medium":
        return "text-yellow-500";
      default:
        return "text-green-500";
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Security Operations Center - CAN 2025 Guardian
        </p>
      </div>

      {stats && (
        <>
          <div className="grid gap-4 md:grid-cols-4 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Total Incidents
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-destructive" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.total_incidents}
                </div>
                <p className="text-xs text-muted-foreground">All time</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Active Alerts
                </CardTitle>
                <Activity className="h-4 w-4 text-orange-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.active_alerts}</div>
                <p className="text-xs text-muted-foreground">
                  Require attention
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Resolved</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.resolved_incidents}
                </div>
                <p className="text-xs text-muted-foreground">This period</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Threat Level
                </CardTitle>
                <Shield
                  className={`h-4 w-4 ${getThreatLevelColor(
                    stats.threat_level || "low"
                  )}`}
                />
              </CardHeader>
              <CardContent>
                <div
                  className={`text-2xl font-bold ${getThreatLevelColor(
                    stats.threat_level || "low"
                  )}`}
                >
                  {(stats.threat_level || "low").toUpperCase()}
                </div>
                <p className="text-xs text-muted-foreground">Current status</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2 mb-8">
            <Card>
              <CardHeader>
                <CardTitle>Incidents by Type</CardTitle>
                <CardDescription>
                  Distribution of detected threats
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(stats.incidents_by_type || {}).length > 0 ? (
                    Object.entries(stats.incidents_by_type || {}).map(
                      ([type, count]) => (
                        <div
                          key={type}
                          className="flex items-center justify-between"
                        >
                          <span className="text-sm font-medium capitalize">
                            {type}
                          </span>
                          <span className="text-2xl font-bold">{count}</span>
                        </div>
                      )
                    )
                  ) : (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      No incidents recorded yet
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Response Time</CardTitle>
                <CardDescription>
                  Average incident response time
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">
                  {stats.average_response_time_minutes}
                  <span className="text-lg text-muted-foreground">min</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Quick response ensures safety
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Daily Incident Trend</CardTitle>
              <CardDescription>Incidents over the last days</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {(stats.daily_incidents || []).length > 0 ? (
                  (stats.daily_incidents || []).slice(-7).map((day) => (
                    <div
                      key={day.date}
                      className="flex items-center justify-between"
                    >
                      <span className="text-sm">{day.date}</span>
                      <div className="flex items-center gap-2">
                        <div
                          className="h-2 bg-primary rounded"
                          style={{
                            width: `${Math.min(day.count * 10, 200)}px`,
                          }}
                        ></div>
                        <span className="text-sm font-medium w-8 text-right">
                          {day.count}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No daily incident data available
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
