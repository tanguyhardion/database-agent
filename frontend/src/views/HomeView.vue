<template>
  <div class="chat-app">
    <ChatSidebar />
    <div class="chat-main">
      <WelcomeScreen
        v-if="!currentChat"
        :connection-status="connectionStatus"
        :connection-message="connectionMessage"
        :is-offline-mode="isOfflineMode"
        @create-chat="createNewChat"
        @create-table-demo="createTableDemo"
        @retry-connection="testConnection"
      />
      <ChatContainer
        v-else
        ref="chatContainerRef"
        :chat="currentChat"
        :connection-status="connectionStatus"
        :connection-message="connectionMessage"
        :is-offline-mode="isOfflineMode"
        @send="sendMessage"
        @edit="handleMessageEdit"
        @delete="handleMessageDelete"
        @start-edit="handleStartEdit"
        @cancel-edit="handleCancelEdit"
        @retry-connection="testConnection"
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from "vue";
import { useChatStore } from "@/stores/chat";
import { chatService } from "@/services/chat";
import ChatSidebar from "@/components/ChatSidebar.vue";
import WelcomeScreen from "@/components/WelcomeScreen.vue";
import ChatContainer from "@/components/ChatContainer.vue";

const chatStore = useChatStore();
const chatContainerRef = ref<InstanceType<typeof ChatContainer>>();
const isOfflineMode = ref(false);
const connectionStatus = ref<
  "unknown" | "checking" | "connected" | "disconnected"
>("unknown");
const connectionMessage = ref("");
const connectionCheckInterval = ref<number | null>(null);

const currentChat = computed(() => chatStore.currentChat);

const createNewChat = () => {
  chatStore.createNewChat();
  nextTick(() => {
    chatContainerRef.value?.focus();
  });
};

const createTableDemo = () => {
  chatStore.createNewChat();
  if (!currentChat.value) return;

  // Add user message asking for data
  chatStore.addMessage(currentChat.value.id, {
    role: "user",
    content: "Show me a sample data table",
  });

  // Add assistant response with a sample table
  const tableContent = `Here's a sample data table showing sales performance:

| Product | Sales ($) | Units Sold | Growth (%) |
|---------|-----------|------------|------------|
| Product A | 125,000 | 450 | +15.2% |
| Product B | 89,500 | 320 | +8.7% |
| Product C | 156,000 | 612 | +22.1% |
| Product D | 74,200 | 185 | -3.4% |
| Product E | 203,800 | 890 | +31.5% |

**Key Insights:**
- Product E shows the highest growth at 31.5%
- Product D is the only product with negative growth
- Total revenue across all products: $648,500

You can also ask me to:
- Filter the data by specific criteria
- Show different time periods
- Export data in various formats
- Create visualizations from the data`;

  chatStore.addMessage(currentChat.value.id, {
    role: "assistant",
    content: tableContent,
  });

  nextTick(() => {
    scrollToBottom();
  });
};
const sendMessage = async (content: string) => {
  if (!currentChat.value) {
    createNewChat();
    if (!currentChat.value) return;
  }
  // Add user message
  const userMessage = chatStore.addMessage(currentChat.value.id, {
    role: "user",
    content,
  });
  if (!userMessage) return;
  // Scroll to bottom
  scrollToBottom();
  // Set loading state
  chatContainerRef.value?.setLoading(true);
  try {
    // Add assistant message with streaming
    const assistantMessage = chatStore.addMessage(currentChat.value.id, {
      role: "assistant",
      content: "",
      isStreaming: true,
    });
    if (!assistantMessage) return; // Stream response
    const stream = chatService.streamChat(
      currentChat.value.messages.slice(0, -1).concat([userMessage])
    );
    for await (const chunk of stream) {
      chatStore.streamMessage(currentChat.value.id, assistantMessage.id, chunk);
      scrollToBottom();
    }
    // Update offline mode status
    isOfflineMode.value = chatService.isInOfflineMode();
    connectionStatus.value = chatService.getConnectionStatus();
    if (isOfflineMode.value) {
      connectionMessage.value = "Demo mode - backend not available";
    } else {
      connectionMessage.value = "Connected to backend";
    }
    // Finish streaming
    chatStore.finishStreaming(currentChat.value.id, assistantMessage.id);
  } catch (error) {
    console.error("Error sending message:", error);
    // Add error message
    chatStore.addMessage(currentChat.value.id, {
      role: "assistant",
      content:
        "Sorry, I encountered an error while processing your request. Please try again.",
    });  } finally {
    chatContainerRef.value?.setLoading(false);
    scrollToBottom();
    // Refocus the chat input after sending a message
    nextTick(() => {
      chatContainerRef.value?.focus();
    });
  }
};
const handleMessageEdit = (messageId: string, content: string) => {
  if (!currentChat.value) return;
  chatStore.updateMessage(currentChat.value.id, messageId, content);
};
const handleMessageDelete = (messageId: string) => {
  if (!currentChat.value) return;
  if (confirm("Are you sure you want to delete this message?")) {
    chatStore.deleteMessage(currentChat.value.id, messageId);
  }
};
const handleStartEdit = (messageId: string) => {
  if (!currentChat.value) return;
  chatStore.startMessageEditing(currentChat.value.id, messageId);
};
const handleCancelEdit = (messageId: string) => {
  if (!currentChat.value) return;
  chatStore.cancelMessageEditing(currentChat.value.id, messageId);
};
const scrollToBottom = () => {
  nextTick(() => {
    chatContainerRef.value?.scrollToBottom();
  });
};
// Test backend connection
const testConnection = async () => {
  connectionStatus.value = "checking";
  try {
    const result = await chatService.testConnection();
    connectionStatus.value = chatService.getConnectionStatus();
    isOfflineMode.value = !result.isConnected;
    connectionMessage.value = result.status;
    console.log(
      result.isConnected
        ? "Backend connected successfully"
        : `Backend connection failed: ${result.status}`
    );
  } catch (error) {
    console.error("Error testing connection:", error);
    connectionStatus.value = "disconnected";
    isOfflineMode.value = true;
    connectionMessage.value = "Connection test failed";
  }
};
// Keyboard shortcuts
const handleKeydown = (e: KeyboardEvent) => {
  // Ctrl/Cmd + N: New chat
  if ((e.ctrlKey || e.metaKey) && e.key === "n") {
    e.preventDefault();
    createNewChat();  }
  // Escape: Focus input
  if (e.key === "Escape") {
    e.preventDefault();
    chatContainerRef.value?.focus();
  }
};
onMounted(() => {
  document.addEventListener("keydown", handleKeydown);
  // Test connection immediately when app loads
  testConnection();
  // Set up periodic connection check (every 30 seconds)
  connectionCheckInterval.value = setInterval(() => {
    // Only check if we're currently in offline mode
    if (isOfflineMode.value) {
      testConnection();
    }
  }, 30000);
  // Focus input on mount
  nextTick(() => {
    chatContainerRef.value?.focus();
  });
});
onUnmounted(() => {
  document.removeEventListener("keydown", handleKeydown);
  // Clean up interval
  if (connectionCheckInterval.value) {
    clearInterval(connectionCheckInterval.value);
    connectionCheckInterval.value = null;
  }
});
// Watch for new messages and scroll to bottom
watch(
  () => currentChat.value?.messages.length,
  () => {
    scrollToBottom();
  }
);
// Focus input when chat changes
watch(
  () => currentChat.value?.id,
  () => {
    nextTick(() => {
      chatContainerRef.value?.focus();
    });
  }
);
</script>
<style lang="scss" scoped>
.chat-app {
  display: flex;
  height: 100vh;
  background: linear-gradient(
    135deg,
    var(--color-gray-50) 0%,
    var(--color-primary-light) 100%
  );
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23667eea' fill-opacity='0.03'%3E%3Ccircle cx='30' cy='30' r='4'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")
      repeat;
    pointer-events: none;
  }

  @media (max-width: 768px) {
    flex-direction: column;
  }
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}
</style>
