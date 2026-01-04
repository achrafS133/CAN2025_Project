import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import {
  alertsService,
  type AlertHistory,
  type BudgetStatus,
} from "@/services";
import { Bell, DollarSign, AlertCircle, TrendingUp } from "lucide-react";

export function Alerts() {
  const [history, setHistory] = useState<AlertHistory | null>(null);
  const [budget, setBudget] = useState<BudgetStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load both with individual error handling
      const historyPromise = alertsService.getHistory(50).catch(() => ({
        alerts: [],
        total: 0,
      }));

      const budgetPromise = alertsService.getBudgetStatus().catch(() => ({
        monthly_budget: 300.0,
        current_spent: 0,
        remaining: 300.0,
        percentage_used: 0,
        projected_end_of_month: 0,
        alert_threshold_reached: false,
      }));

      const [historyData, budgetData] = await Promise.all([
        historyPromise,
        budgetPromise,
      ]);

      setHistory(historyData);
      setBudget(budgetData);
    } catch (err) {
      console.error("Failed to load alerts data:", err);
      setError("Failed to load some data. Showing cached information.");
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "text-destructive";
      case "warning":
        return "text-yellow-500";
      case "info":
        return "text-blue-500";
      default:
        return "text-muted-foreground";
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading alerts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <Card className="border-yellow-500">
          <CardHeader>
            <CardTitle className="text-yellow-600">
              Limited Data Available
            </CardTitle>
            <CardDescription>
              Some services are unavailable. Showing cached or default data.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm mb-4">{error}</p>
            <Button onClick={loadData}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!history || !budget) {
    return (
      <div className="p-8">
        <Card>
          <CardHeader>
            <CardTitle>No Data Available</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Unable to load alerts data.</p>
            <Button onClick={loadData} className="mt-4">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Alert Configuration</h1>
        <p className="text-muted-foreground mt-2">
          Manage alerts, notifications and AI cost tracking
        </p>
      </div>

      {budget && (
        <div className="grid gap-4 md:grid-cols-4 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Monthly Budget
              </CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {budget.monthly_budget.toFixed(2)} DH
              </div>
              <p className="text-xs text-muted-foreground">AI API costs</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Current Spent
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {budget?.current_spent?.toFixed(2) ?? "0.00"} DH
              </div>
              <p className="text-xs text-muted-foreground">This month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Remaining</CardTitle>
              <DollarSign className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {budget?.remaining?.toFixed(2) ?? "0.00"} DH
              </div>
              <p className="text-xs text-muted-foreground">
                {budget?.percentage_used?.toFixed(1) ?? "0.0"}% used
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Projected</CardTitle>
              <AlertCircle
                className={`h-4 w-4 ${
                  budget.alert_threshold_reached
                    ? "text-destructive"
                    : "text-muted-foreground"
                }`}
              />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {budget.projected_end_of_month.toFixed(2)} DH
              </div>
              <p className="text-xs text-muted-foreground">End of month</p>
            </CardContent>
          </Card>
        </div>
      )}

      {history && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Alert History</span>
              <Bell className="h-4 w-4 text-muted-foreground" />
            </CardTitle>
            <CardDescription>
              Recent alerts sent to various channels
            </CardDescription>
          </CardHeader>
          <CardContent>
            {history.alerts.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No alerts sent yet
              </div>
            ) : (
              <div className="space-y-4">
                {history.alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-start justify-between border-b pb-4 last:border-0"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <AlertCircle
                          className={`h-4 w-4 ${getSeverityColor(
                            alert.severity
                          )}`}
                        />
                        <span className="font-medium">{alert.message}</span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>
                          {new Date(alert.sent_at).toLocaleString("en-GB", {
                            day: "2-digit",
                            month: "2-digit",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                            hour12: false,
                          })}
                        </span>
                        <span>Channels: {alert.channels.join(", ")}</span>
                        <span
                          className={
                            alert.status === "sent"
                              ? "text-green-500"
                              : "text-destructive"
                          }
                        >
                          {alert.status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
