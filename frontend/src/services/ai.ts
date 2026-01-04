import api from "./api";

export interface ChatRequest {
  query: string;
  model: string;
  context?: string[];
}

export interface ChatResponse {
  response: string;
  model: string;
  timestamp: string;
  tokens_used?: number;
  cost?: number;
}

export interface ModelInfo {
  name: string;
  provider: string;
  description: string;
  cost_per_1k_tokens: number;
  available: boolean;
}

export interface ConversationHistory {
  id: string;
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    timestamp: string;
  }>;
  model: string;
  created_at: string;
}

export const aiService = {
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>("/api/v1/ai/chat", request);
    return response.data;
  },

  async getModels(): Promise<ModelInfo[]> {
    const response = await api.get<ModelInfo[]>("/api/v1/ai/models");
    return response.data;
  },

  async streamChat(
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): Promise<void> {
    try {
      const token = localStorage.getItem("access_token");
      const wsUrl =
        api.defaults.baseURL?.replace("http", "ws") || "ws://localhost:8888";

      const ws = new WebSocket(`${wsUrl}/api/v1/ai/ws/chat?token=${token}`);

      ws.onopen = () => {
        ws.send(JSON.stringify(request));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "chunk") {
          onChunk(data.content);
        } else if (data.type === "complete") {
          onComplete();
          ws.close();
        } else if (data.type === "error") {
          onError(new Error(data.message));
          ws.close();
        }
      };

      ws.onerror = () => {
        onError(new Error("WebSocket error"));
        ws.close();
      };
    } catch (error) {
      onError(error as Error);
    }
  },

  async getConversationHistory(): Promise<ConversationHistory[]> {
    const response = await api.get<ConversationHistory[]>(
      "/api/v1/ai/conversations"
    );
    return response.data;
  },

  async clearConversation(conversationId: string): Promise<void> {
    await api.delete(`/api/v1/ai/conversations/${conversationId}`);
  },
};

export default aiService;
