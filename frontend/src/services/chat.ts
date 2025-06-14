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
  private isOfflineMode = false;
  private connectionStatus:
    | "unknown"
    | "checking"
    | "connected"
    | "disconnected" = "unknown";

  async *streamChat(
    messages: Message[]
  ): AsyncGenerator<string, void, unknown> {    // Check if we should use offline mode (demo mode)
    if (this.isOfflineMode) {
      yield* this.getDemoResponse(messages);
      return;
    }// Transform messages to the expected format
    const transformedMessages = messages.map((msg) => ({
      role: msg.role,
      content:
        msg.role === "user"
          ? [{ type: "text", text: msg.content }]
          : [{ type: "text", text: msg.content }],
    }));    const requestBody: ChatRequest = {
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
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body");
      }
      const decoder = new TextDecoder();
      let buffer = "";
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            if (line.trim() === "") continue;
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") {
                return;
              }
              try {
                const parsed = JSON.parse(data);
                if (parsed.type === "text-delta" && parsed.textDelta) {
                  yield parsed.textDelta;
                }
              } catch (e) {
                // Skip invalid JSON
                console.warn("Invalid JSON in stream:", data);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error("Error in streamChat:", error);
      // Fall back to offline mode if connection fails
      if (error instanceof TypeError && error.message.includes("fetch")) {        console.log("Backend not available, switching to demo mode");
        this.isOfflineMode = true;
        yield* this.getDemoResponse(messages);
        return;
      }
      throw error;
    }
  }  private async *getDemoResponse(
    messages: Message[]
  ): AsyncGenerator<string, void, unknown> {
    const lastMessage = messages[messages.length - 1];
    const userQuery = lastMessage?.content.toLowerCase() || "";
    let response = "";
    
    if (userQuery.includes("table") || userQuery.includes("schema")) {
      response = `I found information about the available data structures in your database.
Based on your query, I can see several data categories including:
- Company information
- Entity records  
- Transaction data
- Sales records
The database contains structured information across multiple data domains.
*Note: This is demo mode. Connect to the backend for real database queries.*`;
    } else if (userQuery.includes("count") || userQuery.includes("how many")) {
      response = `I've analyzed the data for your count request.
**Result:** 1,247 records found.
The count was successfully calculated based on your criteria.
*Note: This is demo mode. Connect to the backend for real database queries.*`;
    } else if (userQuery.includes("sample") || userQuery.includes("example")) {
      response = `Here are some sample results from your query:
| ID | Name | Category | Value |
|-----|------|----------|--------|
| 1 | Acme Corp | Technology | 50,000,000 |
| 2 | Global Inc | Manufacturing | 75,000,000 |
| 3 | StartupXYZ | Software | 2,500,000 |
This gives you an overview of the data structure and typical values.
*Note: This is demo mode. Connect to the backend for real database queries.*`;
    } else {
      response = `I understand you're asking: "${lastMessage?.content}"
I'm analyzing your request and will:
1. 🔍 Examine the relevant data sources
2. 📊 Process the information to find what you need  
3. 🛠️ Generate the appropriate results
4. ✅ Present the findings in a clear format
*Note: This is demo mode. Start the backend server to connect to your actual database for real-time queries.*
To get started with live data, ensure your backend server is running on http://localhost:8000`;
    }

    // Simulate streaming by yielding chunks
    const words = response.split(" ");
    for (let i = 0; i < words.length; i++) {
      await new Promise((resolve) =>
        setTimeout(resolve, 50 + Math.random() * 100)
      );
      yield words[i] + (i < words.length - 1 ? " " : "");
    }
  }
  setOfflineMode(offline: boolean) {
    this.isOfflineMode = offline;
  }  isInOfflineMode(): boolean {
    return this.isOfflineMode;
  }
  async testConnection(): Promise<{ isConnected: boolean; status: string }> {
    this.connectionStatus = "checking";
    try {
      // Simple health check - attempt to fetch the base URL or a health endpoint
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: "OPTIONS", // Use OPTIONS for a lightweight check
        headers: {
          "Content-Type": "application/json",
        },
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (response.ok || response.status === 405) {
        // 405 Method Not Allowed is also OK for OPTIONS
        this.isOfflineMode = false;
        this.connectionStatus = "connected";
        return { isConnected: true, status: "Connected to backend" };
      } else {
        this.isOfflineMode = true;
        this.connectionStatus = "disconnected";
        return { isConnected: false, status: "Backend responded with error" };
      }
    } catch (error) {
      this.isOfflineMode = true;
      this.connectionStatus = "disconnected";
      if (error instanceof DOMException && error.name === "AbortError") {
        return { isConnected: false, status: "Connection timeout" };
      } else if (
        error instanceof TypeError &&
        error.message.includes("fetch")
      ) {
        return { isConnected: false, status: "Backend not available" };
      } else {
        return { isConnected: false, status: "Connection failed" };
      }
    }
  }
  getConnectionStatus(): "unknown" | "checking" | "connected" | "disconnected" {
    return this.connectionStatus;
  }
}
export const chatService = new ChatService();
