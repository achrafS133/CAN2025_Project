import api from "./api";

export interface StreamInfo {
  stream_id: string;
  name: string;
  source: string;
  status: "active" | "inactive" | "error";
  fps: number;
  resolution: string;
  started_at?: string;
}

export interface StreamStats {
  stream_id: string;
  uptime_seconds: number;
  frames_processed: number;
  average_fps: number;
  detections_count: number;
  last_detection?: string;
}

export interface CreateStreamRequest {
  name: string;
  source: string;
  enable_detection: boolean;
  detection_interval: number;
}

export interface MultiViewRequest {
  stream_ids: string[];
  layout: "grid" | "pip" | "side-by-side";
}

export const streamsService = {
  async listStreams(): Promise<StreamInfo[]> {
    const response = await api.get<StreamInfo[]>("/api/v1/streams/");
    return response.data;
  },

  async createStream(request: CreateStreamRequest): Promise<StreamInfo> {
    const response = await api.post<StreamInfo>("/api/v1/streams/", request);
    return response.data;
  },

  async deleteStream(streamId: string): Promise<void> {
    await api.delete(`/api/v1/streams/${streamId}`);
  },

  async getStreamStats(streamId: string): Promise<StreamStats> {
    const response = await api.get<StreamStats>(
      `/api/v1/streams/${streamId}/stats`
    );
    return response.data;
  },

  async startStream(streamId: string): Promise<void> {
    await api.post(`/api/v1/streams/${streamId}/start`);
  },

  async stopStream(streamId: string): Promise<void> {
    await api.post(`/api/v1/streams/${streamId}/stop`);
  },

  async createMultiView(
    request: MultiViewRequest
  ): Promise<{ view_id: string }> {
    const response = await api.post<{ view_id: string }>(
      "/api/v1/streams/multi-view",
      request
    );
    return response.data;
  },

  getStreamUrl(streamId: string): string {
    const baseUrl = api.defaults.baseURL || "http://localhost:8888";
    return `${baseUrl}/api/v1/streams/${streamId}/feed`;
  },
};

export default streamsService;
