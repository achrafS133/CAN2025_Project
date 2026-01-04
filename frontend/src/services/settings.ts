import api from "./api";

export interface NotificationSettings {
  enable_notifications: boolean;
  email_alerts: boolean;
  sms_alerts: boolean;
  slack_integration: boolean;
  discord_integration: boolean;
}

export interface DetectionSettings {
  auto_detection: boolean;
  confidence_threshold: number;
  detection_interval: number;
  max_concurrent_streams: number;
}

export interface AppearanceSettings {
  dark_mode: boolean;
  compact_view: boolean;
  show_confidence_scores: boolean;
}

export interface DataSettings {
  retention_days: number;
  auto_archive: boolean;
  export_format: string;
}

export interface SystemSettings {
  notifications: NotificationSettings;
  detection: DetectionSettings;
  appearance: AppearanceSettings;
  data: DataSettings;
  last_updated?: string;
}

export interface SettingsUpdateRequest {
  notifications?: Partial<NotificationSettings>;
  detection?: Partial<DetectionSettings>;
  appearance?: Partial<AppearanceSettings>;
  data?: Partial<DataSettings>;
}

export const settingsService = {
  async getSettings(): Promise<SystemSettings> {
    const response = await api.get<SystemSettings>("/api/v1/settings/");
    return response.data;
  },

  async updateSettings(
    settings: SettingsUpdateRequest
  ): Promise<SystemSettings> {
    const response = await api.put<SystemSettings>(
      "/api/v1/settings/",
      settings
    );
    return response.data;
  },

  async resetSettings(): Promise<SystemSettings> {
    const response = await api.post<SystemSettings>("/api/v1/settings/reset");
    return response.data;
  },

  async clearAllData(): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(
      "/api/v1/settings/data"
    );
    return response.data;
  },
};

export default settingsService;
