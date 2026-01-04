import api from "./api";

export interface DashboardStats {
  total_incidents: number;
  active_alerts: number;
  resolved_incidents: number;
  average_response_time_minutes: number;
  threat_level: "low" | "medium" | "high" | "critical";
  daily_incidents: Array<{
    date: string;
    count: number;
  }>;
  incidents_by_type: Record<string, number>;
}

export interface Anomaly {
  timestamp: string;
  metric: string;
  value: number;
  expected_value: number;
  severity: "low" | "medium" | "high";
  description: string;
}

export interface AnomalyResponse {
  detected: number;
  anomalies: Anomaly[];
  recommendation: string;
}

export interface TrendResponse {
  period: string;
  metrics: Array<{
    timestamp: string;
    incidents: number;
    threats: number;
    response_time: number;
  }>;
  predictions: Array<{
    timestamp: string;
    predicted_incidents: number;
    confidence: number;
  }>;
}

export interface HeatmapData {
  zones: Array<{
    zone_id: string;
    zone_name: string;
    incident_count: number;
    severity_score: number;
    coordinates: {
      lat: number;
      lng: number;
    };
  }>;
  timestamp: string;
}

export interface ExportRequest {
  start_date: string;
  end_date: string;
  format: "csv" | "excel" | "pdf";
  include_images: boolean;
}

export interface ComparativeAnalysis {
  current_period: {
    start_date: string;
    end_date: string;
    total_incidents: number;
    average_response_time: number;
  };
  previous_period: {
    start_date: string;
    end_date: string;
    total_incidents: number;
    average_response_time: number;
  };
  changes: {
    incidents_change_percent: number;
    response_time_change_percent: number;
    trend: "improving" | "declining" | "stable";
  };
}

export interface PredictionData {
  timestamp: string;
  predicted_incidents: number;
  confidence: number;
  factors: string[];
}

export interface PredictionResponse {
  predictions: PredictionData[];
  overall_trend: "increasing" | "decreasing" | "stable";
  confidence: number;
  recommendations: string[];
}

export const analyticsService = {
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>(
      "/api/v1/analytics/dashboard"
    );
    return response.data;
  },

  async detectAnomalies(days: number = 7): Promise<AnomalyResponse> {
    const response = await api.get<AnomalyResponse>(
      "/api/v1/analytics/anomalies",
      {
        params: { days },
      }
    );
    return response.data;
  },

  async getTrends(period: string = "7d"): Promise<TrendResponse> {
    const response = await api.get<TrendResponse>("/api/v1/analytics/trends", {
      params: { period },
    });
    return response.data;
  },

  async getHeatmap(date?: string): Promise<HeatmapData> {
    const response = await api.get<HeatmapData>("/api/v1/analytics/heatmap", {
      params: { date },
    });
    return response.data;
  },

  async exportData(request: ExportRequest): Promise<Blob> {
    const response = await api.post<Blob>("/api/v1/analytics/export", request, {
      responseType: "blob",
    });
    return response.data;
  },

  async getComparativeAnalysis(
    currentStart: string,
    currentEnd: string,
    previousStart: string,
    previousEnd: string
  ): Promise<ComparativeAnalysis> {
    const response = await api.get<ComparativeAnalysis>(
      "/api/v1/analytics/comparative",
      {
        params: {
          current_start: currentStart,
          current_end: currentEnd,
          previous_start: previousStart,
          previous_end: previousEnd,
        },
      }
    );
    return response.data;
  },

  async getPredictions(days: number = 7): Promise<PredictionResponse> {
    const response = await api.get<PredictionResponse>(
      "/api/v1/analytics/predictions",
      {
        params: { days },
      }
    );
    return response.data;
  },
};

export default analyticsService;
