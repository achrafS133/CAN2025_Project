import api from "./api";

export interface AlertRequest {
  message: string;
  severity: "info" | "warning" | "critical";
  channels: string[];
  incident_id?: string;
}

export interface AlertResponse {
  alert_id: string;
  status: string;
  sent_to: string[];
  failed: string[];
  timestamp: string;
}

export interface AlertHistory {
  total: number;
  alerts: Array<{
    id: string;
    message: string;
    severity: string;
    channels: string[];
    status: string;
    sent_at: string;
  }>;
}

export interface CostStats {
  daily_cost: number;
  monthly_cost: number;
  total_api_calls: number;
  by_provider: Record<string, number>;
  last_updated: string;
}

export interface CostByProvider {
  provider: string;
  model: string;
  calls: number;
  total_cost: number;
  average_cost_per_call: number;
}

export interface BudgetStatus {
  monthly_budget: number;
  current_spent: number;
  remaining: number;
  percentage_used: number;
  projected_end_of_month: number;
  alert_threshold_reached: boolean;
}

export const alertsService = {
  async sendAlert(request: AlertRequest): Promise<AlertResponse> {
    const response = await api.post<AlertResponse>(
      "/api/v1/alerts/send",
      request
    );
    return response.data;
  },

  async sendThreatAlert(
    threatType: string,
    location: string,
    severity: string
  ): Promise<AlertResponse> {
    const response = await api.post<AlertResponse>("/api/v1/alerts/threat", {
      threat_type: threatType,
      location,
      severity,
    });
    return response.data;
  },

  async sendCrowdAlert(
    location: string,
    crowdSize: number,
    sentiment: string
  ): Promise<AlertResponse> {
    const response = await api.post<AlertResponse>("/api/v1/alerts/crowd", {
      location,
      crowd_size: crowdSize,
      sentiment,
    });
    return response.data;
  },

  async getHistory(limit: number = 50): Promise<AlertHistory> {
    const response = await api.get<AlertHistory>("/api/v1/alerts/history", {
      params: { limit },
    });
    return response.data;
  },

  async getCostStats(): Promise<CostStats> {
    const response = await api.get<CostStats>("/api/v1/alerts/costs");
    return response.data;
  },

  async getCostsByProvider(): Promise<CostByProvider[]> {
    const response = await api.get<CostByProvider[]>(
      "/api/v1/alerts/costs/by-provider"
    );
    return response.data;
  },

  async getBudgetStatus(): Promise<BudgetStatus> {
    const response = await api.get<BudgetStatus>("/api/v1/alerts/costs/budget");
    return response.data;
  },

  async resetCosts(): Promise<void> {
    await api.delete("/api/v1/alerts/costs/reset");
  },
};

export default alertsService;
