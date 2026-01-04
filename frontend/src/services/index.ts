// Export all services from a single entry point
export { default as api } from "./api";
export { default as authService } from "./auth";
export { default as threatsService } from "./threats";
export { default as aiService } from "./ai";
export { default as analyticsService } from "./analytics";
export { default as streamsService } from "./streams";
export { default as alertsService } from "./alerts";
export { default as settingsService } from "./settings";

// Export types
export type { LoginCredentials, AuthResponse } from "./auth";
export type {
  ThreatDetection,
  ThreatDetectionResponse,
  ThreatHistoryItem,
  ThreatHistoryResponse,
  ThreatStats,
} from "./threats";
export type {
  ChatRequest,
  ChatResponse,
  ModelInfo,
  ConversationHistory,
} from "./ai";
export type {
  DashboardStats,
  Anomaly,
  AnomalyResponse,
  TrendResponse,
  HeatmapData,
  ExportRequest,
  ComparativeAnalysis,
  PredictionData,
  PredictionResponse,
} from "./analytics";
export type {
  StreamInfo,
  StreamStats,
  CreateStreamRequest,
  MultiViewRequest,
} from "./streams";
export type {
  AlertRequest,
  AlertResponse,
  AlertHistory,
  CostStats,
  CostByProvider,
  BudgetStatus,
} from "./alerts";
export type {
  NotificationSettings,
  DetectionSettings,
  AppearanceSettings,
  DataSettings,
  SystemSettings,
  SettingsUpdateRequest,
} from "./settings";
