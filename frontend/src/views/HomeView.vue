<template>
  <div class="chat-app">
    <ChatSidebar />
    <div class="chat-main">
      <div v-if="!currentChat" class="welcome-screen">
        <div class="welcome-content">
          <h1 class="welcome-title">Welcome to Business Data Chat</h1>
          <p class="welcome-description">
            Ask questions about your business data in natural language and get
            insights instantly.
          </p>
          <!-- Connection status in welcome screen -->
          <div class="welcome-connection-status">
            <div
              v-if="connectionStatus === 'checking'"
              class="welcome-status-badge welcome-status-badge--checking"
            >
              <div class="status-dot status-dot--pulse"></div>
              Testing connection to backend...
            </div>
            <div
              v-else-if="isOfflineMode"
              class="welcome-status-badge welcome-status-badge--demo"
              @click="testConnection"
              style="cursor: pointer"
            >
              <div class="status-dot"></div>
              Demo Mode - {{ connectionMessage }}
              <button class="retry-btn" title="Retry connection">↻</button>
            </div>
            <div
              v-else
              class="welcome-status-badge welcome-status-badge--connected"
            >
              <div class="status-dot"></div>
              Connected to backend
            </div>
          </div>
          <button @click="createNewChat" class="welcome-btn">
            <MessageSquare :size="20" />
            Start New Chat
          </button>
        </div>
      </div>
      <div v-else class="chat-container">
        <div class="chat-header">
          <div class="chat-header-left">
            <h2 class="chat-title">{{ currentChat.title }}</h2>
            <div class="chat-meta">
              {{ currentChat.messages.length }} messages
            </div>
            <div class="setting-item">
              <label
                class="toggle-label"
                style="
                  cursor: pointer;
                  display: flex;
                  gap: 0.5rem;
                  align-items: center;
                "
              >
                <input
                  type="checkbox"
                  v-model="showQuery"
                  @change="onShowQueryToggle"
                  class="toggle-checkbox"
                />
                <span class="toggle-text">Show SQL Query</span>
              </label>
            </div>
          </div>
          <div class="connection-status">
            <HelpTooltip />
            <div
              v-if="connectionStatus === 'checking'"
              class="status-badge status-badge--checking"
              title="Testing connection to backend..."
            >
              <div class="status-dot status-dot--pulse"></div>
              Checking...
            </div>
            <div
              v-else-if="isOfflineMode"
              class="status-badge status-badge--demo"
              :title="
                connectionMessage ||
                'Demo mode - start backend for real queries'
              "
              @click="testConnection"
              style="cursor: pointer"
            >
              <div class="status-dot"></div>
              Demo Mode
              <button class="retry-btn" title="Retry connection">↻</button>
            </div>
            <div
              v-else
              class="status-badge status-badge--connected"
              :title="connectionMessage || 'Connected to backend'"
            >
              <div class="status-dot"></div>
              Connected
            </div>
          </div>
        </div>
        <div ref="messagesContainer" class="messages-container">
          <div v-if="currentChat.messages.length === 0" class="empty-chat">
            <div class="empty-chat__content">
              <Database :size="48" class="empty-chat__icon" />
              <h3>Start asking questions</h3>
              <p>
                Ask me anything about your business data and I'll provide the
                insights you need.
              </p>
              <div class="example-questions">
                <h4>Example questions:</h4>
                <button
                  v-for="example in exampleQuestions"
                  :key="example"
                  @click="sendMessage(example)"
                  class="example-btn"
                >
                  {{ example }}
                </button>
              </div>
            </div>
          </div>
          <div v-else class="messages-list">
            <MessageComponent
              class="message"
              v-for="message in currentChat.messages"
              :key="message.id"
              :message="message"
              @edit="handleMessageEdit"
              @delete="handleMessageDelete"
              @start-edit="handleStartEdit"
              @cancel-edit="handleCancelEdit"
            />
          </div>
        </div>
        <ChatInput ref="chatInput" @send="sendMessage" />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from "vue";
import { MessageSquare, Database } from "lucide-vue-next";
import { useChatStore } from "@/stores/chat";
import { chatService } from "@/services/chat";
import ChatSidebar from "@/components/ChatSidebar.vue";
import MessageComponent from "@/components/MessageComponent.vue";
import ChatInput from "@/components/ChatInput.vue";
import HelpTooltip from "@/components/HelpTooltip.vue";
const chatStore = useChatStore();
const messagesContainer = ref<HTMLElement>();
const chatInput = ref<InstanceType<typeof ChatInput>>();
const isOfflineMode = ref(false);
const connectionStatus = ref<
  "unknown" | "checking" | "connected" | "disconnected"
>("unknown");
const connectionMessage = ref("");
const connectionCheckInterval = ref<number | null>(null);
const currentChat = computed(() => chatStore.currentChat);
const showQuery = ref(chatService.getShowQuery());
const onShowQueryToggle = () => {
  chatService.setShowQuery(showQuery.value);
  console.log(`Query display ${showQuery.value ? "enabled" : "disabled"}`);
};
const exampleQuestions = [
  "How many properties are in the UK?",
  "Show me the top performing entities",
  "What data categories are available?",
  "Give me a summary of recent transactions",
];
const createNewChat = () => {
  chatStore.createNewChat();
  nextTick(() => {
    chatInput.value?.focus();
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
  chatInput.value?.setLoading(true);
  try {
    // Add assistant message with streaming
    const assistantMessage = chatStore.addMessage(currentChat.value.id, {
      role: "assistant",
      content: "",
      isStreaming: true,
    });
    if (!assistantMessage) return;
    // Stream response
    const stream = chatService.streamChat(
      currentChat.value.messages.slice(0, -1).concat([userMessage]),
      showQuery.value
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
    });
  } finally {
    chatInput.value?.setLoading(false);
    scrollToBottom();
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
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
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
    createNewChat();
  }
  // Escape: Focus input
  if (e.key === "Escape") {
    e.preventDefault();
    chatInput.value?.focus();
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
    chatInput.value?.focus();
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
      chatInput.value?.focus();
    });
  }
);
</script>
<style lang="scss" scoped>
.chat-app {
  display: flex;
  height: 100vh;
  background-color: #f9fafb;
  @media (max-width: 768px) {
    flex-direction: column;
  }
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}
.welcome-content {
  text-align: center;
  max-width: 500px;
}
.welcome-title {
  font-size: 32px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 16px;
}
.welcome-description {
  font-size: 16px;
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 24px;
}
.welcome-connection-status {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}
.welcome-status-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  &--connected {
    background-color: #dcfce7;
    color: #166534;
    .status-dot {
      background-color: #22c55e;
    }
  }
  &--demo {
    background-color: #fef3c7;
    color: #d97706;
    transition: background-color 0.2s;
    .status-dot {
      background-color: #f59e0b;
    }
    &:hover {
      background-color: #fde68a;
    }
  }
  &--checking {
    background-color: #e0f2fe;
    color: #0369a1;
    .status-dot {
      background-color: #0ea5e9;
    }
  }
}
.welcome-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background-color: #10a37f;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  &:hover {
    background-color: #0d8f6e;
  }
}
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.chat-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
  flex: 1;
}
.chat-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chat-meta {
  font-size: 14px;
  color: #6b7280;
}
.connection-status {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  &--connected {
    background-color: #dcfce7;
    color: #166534;
    .status-dot {
      background-color: #22c55e;
    }
  }
  &--demo {
    background-color: #fef3c7;
    color: #d97706;
    .status-dot {
      background-color: #f59e0b;
    }
    &:hover {
      background-color: #fde68a;
    }
  }
  &--checking {
    background-color: #e0f2fe;
    color: #0369a1;
    .status-dot {
      background-color: #0ea5e9;
    }
  }
}
.retry-btn {
  background: none;
  border: none;
  color: inherit;
  font-size: 14px;
  cursor: pointer;
  padding: 0 2px;
  border-radius: 2px;
  transition: background-color 0.2s;
  &:hover {
    background-color: rgba(0, 0, 0, 0.1);
  }
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  animation: pulse 2s infinite;
  &--pulse {
    animation: pulse 1s infinite;
  }
}
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}
.empty-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 32px;
}
.empty-chat__content {
  text-align: center;
  max-width: 500px;
}
.empty-chat__icon {
  color: #9ca3af;
  margin: 0 auto 16px;
}
.empty-chat h3 {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}
.empty-chat p {
  font-size: 16px;
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 32px;
}
.example-questions {
  h4 {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 12px;
  }
}
.example-btn {
  display: block;
  width: 100%;
  text-align: left;
  padding: 12px 16px;
  margin-bottom: 8px;
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
  &:hover {
    border-color: #10a37f;
    background-color: rgba(16, 163, 127, 0.05);
  }
}
.messages-list {
  max-width: 768px;
  margin: 0 auto;
  padding: 0 16px;
  .message {
    margin-bottom: 12px;
  }
  @media (max-width: 768px) {
    padding: 0 12px;
  }
}
/* Scrollbar styling */
.messages-container::-webkit-scrollbar {
  width: 8px;
}
.messages-container::-webkit-scrollbar-track {
  background: transparent;
}
.messages-container::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}
.messages-container::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
