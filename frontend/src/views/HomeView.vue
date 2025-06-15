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
          <button
            @click="createTableDemo"
            class="welcome-btn welcome-btn--secondary"
          >
            <Database :size="20" />
            View Table Demo
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
        <div
          v-if="currentChat.messages.length === 0"
          class="empty-chat-centered"
        >
          <div class="greeting-content">
            <Database :size="48" class="empty-chat__icon" />
            <h3>Start asking questions</h3>
            <p>
              Ask me anything about your business data and I'll provide the
              insights you need.
            </p>
          </div>
          <div class="centered-chat-input">
            <div class="chat-input-minimal">
              <ChatInput ref="chatInput" @send="sendMessage" />
            </div>
            <div class="example-questions-inline">
              <button
                v-for="example in exampleQuestions"
                :key="example"
                @click="sendMessage(example)"
                class="example-btn-small"
              >
                {{ example }}
              </button>
            </div>
          </div>
        </div>
        <div v-else class="chat-with-messages">
          <div ref="messagesContainer" class="messages-container">
            <div class="messages-list">
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
  chatInput.value?.setLoading(true);
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
    if (
      messagesContainer.value &&
      currentChat.value &&
      currentChat.value.messages.length > 0
    ) {
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
.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  position: relative;
}

.welcome-content {
  text-align: center;
  max-width: 600px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: var(--radius-2xl);
  padding: 48px;
  box-shadow: var(--shadow-xl);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 32px 64px -12px rgba(0, 0, 0, 0.25);
  }
}

.welcome-title {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(
    135deg,
    var(--color-primary) 0%,
    var(--color-secondary) 100%
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 20px;
  letter-spacing: -0.02em;
}

.welcome-description {
  font-size: 18px;
  color: var(--color-gray-600);
  line-height: 1.7;
  margin-bottom: 32px;
  font-weight: 400;
}
.welcome-connection-status {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}
.welcome-status-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: var(--radius-full);
  font-size: 14px;
  font-weight: 600;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.2);

  &--connected {
    background: linear-gradient(
      135deg,
      var(--color-secondary-light) 0%,
      rgba(209, 250, 229, 0.8) 100%
    );
    color: var(--color-secondary-dark);

    .status-dot {
      background: var(--color-secondary);
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
    }
  }

  &--demo {
    background: linear-gradient(
      135deg,
      rgba(254, 243, 199, 0.9) 0%,
      rgba(253, 230, 138, 0.8) 100%
    );
    color: var(--color-warning);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    .status-dot {
      background: var(--color-warning);
      box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
    }

    &:hover {
      background: linear-gradient(
        135deg,
        rgba(253, 230, 138, 0.95) 0%,
        rgba(252, 211, 77, 0.8) 100%
      );
      transform: scale(1.02);
    }
  }

  &--checking {
    background: linear-gradient(
      135deg,
      rgba(224, 242, 254, 0.9) 0%,
      rgba(186, 230, 253, 0.8) 100%
    );
    color: var(--color-info);

    .status-dot {
      background: var(--color-info);
      box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
    }
  }
}

.welcome-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 16px 32px;
  background: linear-gradient(
    135deg,
    var(--color-primary) 0%,
    var(--color-primary-dark) 100%
  );
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-xl);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin: 8px;
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.2),
      transparent
    );
    transition: left 0.5s;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);

    &::before {
      left: 100%;
    }
  }

  &:active {
    transform: translateY(0);
  }

  &--secondary {
    background: linear-gradient(
      135deg,
      var(--color-white) 0%,
      var(--color-gray-50) 100%
    );
    color: var(--color-gray-700);
    border: 2px solid var(--color-gray-200);

    &:hover {
      background: linear-gradient(
        135deg,
        var(--color-gray-50) 0%,
        var(--color-gray-100) 100%
      );
      border-color: var(--color-primary);
    }
  }
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.chat-with-messages {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.empty-chat-centered {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 32px;
  gap: 24px;
  min-height: 0;

  @media (max-width: 768px) {
    padding: 16px;
    gap: 16px;
  }
}

.greeting-content {
  text-align: center;
  max-width: 600px;

  h3 {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(
      135deg,
      var(--color-gray-800) 0%,
      var(--color-gray-600) 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 12px;

    @media (max-width: 768px) {
      font-size: 24px;
    }
  }

  p {
    font-size: 18px;
    color: var(--color-gray-600);
    line-height: 1.7;
    margin-bottom: 0;
    font-weight: 400;

    @media (max-width: 768px) {
      font-size: 16px;
    }
  }
}

.empty-chat__icon {
  color: var(--color-primary);
  margin: 0 auto 24px;
  opacity: 0.7;
}

.centered-chat-input {
  width: 100%;
  max-width: 800px;
  z-index: 10;
}

.chat-input-minimal {
  :deep(.chat-input) {
    padding: 0;
    background: transparent;
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    border-top: none;
  }

  :deep(.input-container) {
    box-shadow: var(--shadow-lg);
    border: 2px solid var(--color-gray-200);

    &:focus-within {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1), var(--shadow-xl);
    }
  }

  :deep(.input-footer) {
    margin-top: 8px;
  }
}

.example-questions-inline {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;

  @media (max-width: 768px) {
    gap: 6px;
    margin-top: 12px;
  }
}

.example-btn-small {
  padding: 8px 16px;
  background: linear-gradient(
    135deg,
    var(--color-white) 0%,
    var(--color-gray-50) 100%
  );
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-full);
  font-size: 13px;
  color: var(--color-gray-700);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  white-space: nowrap;

  &:hover {
    border-color: var(--color-primary);
    background: linear-gradient(
      135deg,
      var(--color-primary-light) 0%,
      rgba(224, 231, 255, 0.3) 100%
    );
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }

  @media (max-width: 768px) {
    padding: 6px 12px;
    font-size: 12px;
  }
}
.chat-header {
  padding: 24px 32px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(248, 250, 252, 0.9) 100%
  );
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow-sm);
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 20px;
  min-width: 0;
  flex: 1;
}

.chat-title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(
    135deg,
    var(--color-gray-800) 0%,
    var(--color-gray-600) 100%
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-meta {
  font-size: 14px;
  color: var(--color-gray-500);
  font-weight: 500;
  background: rgba(156, 163, 175, 0.1);
  padding: 4px 12px;
  border-radius: var(--radius-full);
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
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 600;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.2);

  &--connected {
    background: linear-gradient(
      135deg,
      var(--color-secondary-light) 0%,
      rgba(209, 250, 229, 0.8) 100%
    );
    color: var(--color-secondary-dark);

    .status-dot {
      background: var(--color-secondary);
      box-shadow: 0 0 6px rgba(16, 185, 129, 0.4);
    }
  }

  &--demo {
    background: linear-gradient(
      135deg,
      rgba(254, 243, 199, 0.9) 0%,
      rgba(253, 230, 138, 0.8) 100%
    );
    color: var(--color-warning);

    .status-dot {
      background: var(--color-warning);
      box-shadow: 0 0 6px rgba(245, 158, 11, 0.4);
    }

    &:hover {
      background: linear-gradient(
        135deg,
        rgba(253, 230, 138, 0.95) 0%,
        rgba(252, 211, 77, 0.8) 100%
      );
      transform: scale(1.02);
    }
  }

  &--checking {
    background: linear-gradient(
      135deg,
      rgba(224, 242, 254, 0.9) 0%,
      rgba(186, 230, 253, 0.8) 100%
    );
    color: var(--color-info);

    .status-dot {
      background: var(--color-info);
      box-shadow: 0 0 6px rgba(59, 130, 246, 0.4);
    }
  }
}

.retry-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: inherit;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: var(--radius-sm);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: scale(1.1);
  }
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
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
  padding: 24px 0;
  position: relative;
}

.messages-list {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 24px;
  @media (max-width: 768px) {
    padding: 0 16px;
  }
}

/* Scrollbar styling */
.messages-container::-webkit-scrollbar {
  width: 10px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background: var(--color-gray-300);
  border-radius: var(--radius-full);
  border: 2px solid transparent;
  background-clip: content-box;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: var(--color-gray-400);
  background-clip: content-box;
}
</style>
