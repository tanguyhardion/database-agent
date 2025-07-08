<template>
  <div class="chat-app">
    <ChatSidebar ref="sidebarRef" />
    <div class="chat-main">
      <WelcomeScreen
        v-if="!currentChat"
        :connection-status="connectionStatus"
        :connection-message="connectionMessage"
        :is-offline-mode="isOfflineMode"
        @create-chat="createNewChat"
        @create-table-demo="createTableDemo"
        @retry-connection="testConnection"
        @toggle-sidebar="toggleSidebar"
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
        @retry="handleMessageRetry"
        @retry-connection="testConnection"
        @toggle-sidebar="toggleSidebar"
        @create-new-chat="createNewChat"
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from "vue";
import { useChatStore } from "@/stores/chat";
import { useStorage } from "@vueuse/core";
import { chatService } from "@/services/chat";
import ChatSidebar from "@/components/ChatSidebar.vue";
import WelcomeScreen from "@/components/WelcomeScreen.vue";
import ChatContainer from "@/components/ChatContainer.vue";

const chatStore = useChatStore();
const isCollapsed = useStorage("sidebar-collapsed", false);
const chatContainerRef = ref<InstanceType<typeof ChatContainer>>();
const sidebarRef = ref<InstanceType<typeof ChatSidebar>>();
const isOfflineMode = ref(false);
const connectionStatus = ref<
  "unknown" | "checking" | "connected" | "disconnected"
>("unknown");
const connectionMessage = ref("");
const connectionCheckInterval = ref<number | null>(null);

const currentChat = computed(() => chatStore.currentChat);

const toggleSidebar = () => {
  sidebarRef.value?.toggle();
};

const createNewChat = () => {
  // If there's already an empty chat, don't create a new one
  if (currentChat.value && currentChat.value.messages.length === 0) {
    return;
  }
  chatStore.createNewChat();

  // Auto-close menu after creating new chat
  isCollapsed.value = true;

  // Let the input handle its own focus - no need to manually focus
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

  // Add loading message for AI response
  const loadingMessage = chatStore.addLoadingMessage(currentChat.value.id);
  if (!loadingMessage) return;

  // Scroll to bottom
  scrollToBottom();
  // Set loading state
  chatContainerRef.value?.setLoading(true);
  try {
    // Send message and get response
    const response = await chatService.sendMessage(
      currentChat.value.messages
        .slice(0, -1)
        .filter((m) => !m.isLoading)
        .concat([userMessage])
    );

    // Update the loading message with the actual response
    chatStore.updateLoadingMessage(
      currentChat.value.id,
      loadingMessage.id,
      response
    );

    // Update offline mode status
    isOfflineMode.value = connectionStatus.value !== "connected";
    connectionStatus.value = chatService.getConnectionStatus();
    if (isOfflineMode.value) {
      connectionMessage.value = "Not connected";
    } else {
      connectionMessage.value = "Connected to backend";
    }
  } catch (error) {
    console.error("Error sending message:", error);
    // Remove loading message and add error message
    chatStore.removeLoadingMessage(currentChat.value.id, loadingMessage.id);
    chatStore.addMessage(currentChat.value.id, {
      role: "assistant",
      content:
        "Sorry, I encountered an error while processing your request. Please try again.",
    });
  } finally {
    chatContainerRef.value?.setLoading(false);
    scrollToBottom();
    // Ensure input focus is restored after message processing
    nextTick(() => {
      chatContainerRef.value?.focus();
    });
  }
};
const handleMessageEdit = async (messageId: string, content: string) => {
  if (!currentChat.value) return;

  // Find the index of the message to edit BEFORE updating it
  const messageIndex = currentChat.value.messages.findIndex(
    (m) => m.id === messageId
  );
  if (messageIndex === -1) return;

  const editedMessage = currentChat.value.messages[messageIndex];

  // Update the message content
  chatStore.updateMessage(currentChat.value.id, messageId, content);

  // If the edited message is a user message, regenerate the assistant response
  if (editedMessage.role === "user") {
    // Remove all messages after the edited message (including assistant responses)
    const messagesToKeep = currentChat.value.messages.slice(
      0,
      messageIndex + 1
    );

    // Update the chat to only include messages up to and including the edited message
    const chat = chatStore.chats.find((c) => c.id === currentChat.value!.id);
    if (chat) {
      chat.messages = messagesToKeep;
      chat.updatedAt = new Date();
      chatStore.saveToStorage();
    }

    // Add loading message for AI response
    const loadingMessage = chatStore.addLoadingMessage(currentChat.value.id);
    if (!loadingMessage) return;

    // Scroll to bottom
    scrollToBottom();
    // Set loading state
    chatContainerRef.value?.setLoading(true);

    try {
      // Send updated conversation and get new response
      const response = await chatService.sendMessage(
        messagesToKeep.filter((m) => !m.isLoading)
      );

      // Update the loading message with the actual response
      chatStore.updateLoadingMessage(
        currentChat.value.id,
        loadingMessage.id,
        response
      );

      // Update offline mode status
      isOfflineMode.value = connectionStatus.value !== "connected";
      connectionStatus.value = chatService.getConnectionStatus();
      if (isOfflineMode.value) {
        connectionMessage.value = "Not connected";
      } else {
        connectionMessage.value = "Connected to backend";
      }
    } catch (error) {
      console.error("Error regenerating response:", error);
      // Remove loading message and add error message
      chatStore.removeLoadingMessage(currentChat.value.id, loadingMessage.id);
      chatStore.addMessage(currentChat.value.id, {
        role: "assistant",
        content:
          "Sorry, I encountered an error while processing your request. Please try again.",
      });
    } finally {
      chatContainerRef.value?.setLoading(false);
      scrollToBottom();
      // Ensure input focus is restored after message editing
      nextTick(() => {
        chatContainerRef.value?.focus();
      });
    }
  }
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
const handleMessageRetry = async (messageId: string) => {
  if (!currentChat.value) return;

  // Find the index of the message to retry
  const messageIndex = currentChat.value.messages.findIndex(
    (m) => m.id === messageId
  );
  if (messageIndex === -1) return;

  const messageToRetry = currentChat.value.messages[messageIndex];

  // Only allow retry for user messages
  if (messageToRetry.role !== "user") return;

  // Remove all messages after the user message (including assistant responses)
  const messagesToKeep = currentChat.value.messages.slice(
    0,
    messageIndex + 1
  );

  // Update the chat to only include messages up to and including the user message
  const chat = chatStore.chats.find((c) => c.id === currentChat.value!.id);
  if (chat) {
    chat.messages = messagesToKeep;
    chat.updatedAt = new Date();
    chatStore.saveToStorage();
  }

  // Add loading message for AI response
  const loadingMessage = chatStore.addLoadingMessage(currentChat.value.id);
  if (!loadingMessage) return;

  // Scroll to bottom
  scrollToBottom();
  // Set loading state
  chatContainerRef.value?.setLoading(true);

  try {
    // Send conversation up to the retried message and get new response
    const response = await chatService.sendMessage(
      messagesToKeep.filter((m) => !m.isLoading)
    );

    // Update the loading message with the actual response
    chatStore.updateLoadingMessage(
      currentChat.value.id,
      loadingMessage.id,
      response
    );

    // Update offline mode status
    isOfflineMode.value = connectionStatus.value !== "connected";
    connectionStatus.value = chatService.getConnectionStatus();
    if (isOfflineMode.value) {
      connectionMessage.value = "Not connected";
    } else {
      connectionMessage.value = "Connected to backend";
    }
  } catch (error) {
    console.error("Error retrying message:", error);
    // Remove loading message and add error message
    chatStore.removeLoadingMessage(currentChat.value.id, loadingMessage.id);
    chatStore.addMessage(currentChat.value.id, {
      role: "assistant",
      content:
        "Sorry, I encountered an error while processing your request. Please try again.",
    });
  } finally {
    chatContainerRef.value?.setLoading(false);
    scrollToBottom();
    // Ensure input focus is restored after retry
    nextTick(() => {
      chatContainerRef.value?.focus();
    });
  }
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
    connectionMessage.value = "Disconnected";
  }
};

// Check if device is mobile
const isMobile = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  );
};

// Keyboard shortcuts
const handleKeydown = (e: KeyboardEvent) => {
  // Skip keyboard shortcuts on mobile devices
  if (isMobile()) return;

  // Ctrl/Cmd + Shift + K: New chat
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "k") {
    e.preventDefault();
    createNewChat();
  }
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
  // Set up periodic connection check (every 5 seconds)
  connectionCheckInterval.value = setInterval(() => {
    // Only check if we're currently in offline mode
    if (isOfflineMode.value) {
      testConnection();
    }
  }, 5000);
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
  background: var(--color-gray-50);
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
  }

  @media (max-width: 992px) {
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

  @media (max-width: 992px) {
    width: 100%;
  }
}
</style>
