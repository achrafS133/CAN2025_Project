import api from "./api";

export interface ThreatDetection {
  threat_type: string;
  confidence: number;
  bbox: number[];
  timestamp: string;
}

export interface ThreatDetectionResponse {
  status: string;
  threats_detected: number;
  detections: ThreatDetection[];
  image_id?: string;
  processing_time_ms: number;
}

export interface ThreatHistoryItem {
  id: number;
  timestamp: string;
  threat_type: string;
  location?: string;
  confidence: number;
  status: string;
}

export interface ThreatHistoryResponse {
  total: number;
  items: ThreatHistoryItem[];
}

export interface ThreatStats {
  total_detections: number;
  active_threats: number;
  resolved: number;
  false_positives: number;
  by_type: Record<string, number>;
}

export const threatsService = {
  async detectThreat(file: File): Promise<ThreatDetectionResponse> {
    const formData = new FormData();
    formData.append("file", file);

    // Remove Content-Type so axios sets it with the correct multipart boundary
    const response = await api.post<ThreatDetectionResponse>(
      "/api/v1/threats/detect",
      formData,
      {
        headers: {
          "Content-Type": undefined,
        },
      }
    );

    return response.data;
  },

  async getHistory(
    limit: number = 100,
    status?: string
  ): Promise<ThreatHistoryResponse> {
    const response = await api.get<ThreatHistoryResponse>(
      "/api/v1/threats/history",
      {
        params: { limit, status },
      }
    );

    return response.data;
  },

  async getStats(): Promise<ThreatStats> {
    const response = await api.get<ThreatStats>("/api/v1/threats/stats");
    return response.data;
  },

  async updateStatus(
    threatId: number,
    status: string,
    notes?: string
  ): Promise<void> {
    await api.put(`/api/v1/threats/${threatId}/status`, {
      status,
      notes,
    });
  },

  async markFalsePositive(threatId: number, notes?: string): Promise<void> {
    await api.post(`/api/v1/threats/${threatId}/feedback`, {
      is_false_positive: true,
      notes,
    });
  },
};

export default threatsService;
