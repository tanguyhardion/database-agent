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
  async sendMessage(
    messages: Message[]
  ): Promise<string> {
    // Check if we should use offline mode (demo mode)
    if (this.isOfflineMode) {
      return this.getDemoResponse(messages);
    }

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
      // Fall back to offline mode if connection fails
      if (error instanceof TypeError && error.message.includes("fetch")) {
        console.log("Backend not available, switching to demo mode");
        this.isOfflineMode = true;
        return this.getDemoResponse(messages);
      }
      throw error;
    }
  }

  private getDemoResponse(
    messages: Message[]  ): string {
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

    return response;
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
