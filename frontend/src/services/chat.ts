// Modified chat.ts service
import type { Message } from "@/stores/chat";
export interface ChatRequest {
  system?: string;
  tools?: any[];
  messages: Array<{
    role: string;
    content: string | Array<{ type: string; text: string }>;
  }>;
}
export class ChatService {
  private baseUrl = "http://localhost:8000";
  private connectionStatus:
    | "unknown"
    | "checking"
    | "connected"
    | "disconnected" = "unknown";

  async sendMessage(messages: Message[]): Promise<string> {
    // Transform messages to the expected format
    const transformedMessages = messages.map((msg) => ({
      role: msg.role,
      content:
        msg.role === "user"
          ? [{ type: "text", text: msg.content }]
          : [{ type: "text", text: msg.content }],
    }));

    const requestBody: ChatRequest = {
      system: "You are a helpful assistant for SQL queries.",
      tools: [],
      messages: transformedMessages,
    };

    try {
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      if (result.type === "error") {
        throw new Error(result.content);
      }
      return result.content;
    } catch (error) {
      console.error("Error in sendMessage:", error);
      // If backend is not available, return not connected message
      return "<i>Server unavailable</i>";
    }
  }

  async testConnection(): Promise<{ isConnected: boolean; status: string }> {
    this.connectionStatus = "checking";
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: "OPTIONS",
        headers: {
          "Content-Type": "application/json",
        },
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (response.ok || response.status === 405) {
        this.connectionStatus = "connected";
        return { isConnected: true, status: "Connected to backend" };
      } else {
        this.connectionStatus = "disconnected";
        return { isConnected: false, status: "Not connected" };
      }
    } catch (error) {
      this.connectionStatus = "disconnected";
      return { isConnected: false, status: "Not connected" };
    }
  }

  async getPromptMode(): Promise<string> {
    try {
      const response = await fetch(`${this.baseUrl}/api/prompt-mode`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      return result.mode;
    } catch (error) {
      console.error("Error getting prompt mode:", error);
      return "technical"; // Default fallback
    }
  }

  async setPromptMode(mode: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/prompt-mode`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mode }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return true;
    } catch (error) {
      console.error("Error setting prompt mode:", error);
      return false;
    }
  }

  getConnectionStatus(): "unknown" | "checking" | "connected" | "disconnected" {
    return this.connectionStatus;
  }
}

export const chatService = new ChatService();
