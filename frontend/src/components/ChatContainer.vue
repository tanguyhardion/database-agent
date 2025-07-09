<template>
  <div class="chat-container">    <ChatHeader
      class="chat-header"
      :title="chat.title"
      :message-count="chat.messages.length"
      :connection-status="connectionStatus"
      :connection-message="connectionMessage"
      :is-offline-mode="isOfflineMode"
      @retry-connection="$emit('retry-connection')"
      @toggle-sidebar="$emit('toggle-sidebar')"
      @create-new-chat="$emit('create-new-chat')"
    />

    <EmptyChatState
      v-if="chat.messages.length === 0"
      ref="emptyChatRef"
      @send="$emit('send', $event)"
    />

    <div v-else class="chat-with-messages">
      <div ref="messagesContainer" class="messages-container">
        <div class="messages-list">
          <MessageComponent
            class="message"
            v-for="message in chat.messages"
            :key="message.id"
            :message="message"
            @edit="(messageId, content) => $emit('edit', messageId, content)"
            @delete="$emit('delete', message.id)"
            @start-edit="$emit('start-edit', message.id)"
            @cancel-edit="$emit('cancel-edit', message.id)"
            @retry="$emit('retry', message.id)"
          />
        </div>
      </div>
      
      <!-- Scroll to bottom button - positioned relative to chat-with-messages but above chat input -->
      <Transition name="scroll-button">
        <button
          v-if="showScrollButton"
          class="scroll-to-bottom-button"
          @click="scrollToBottom"
          aria-label="Scroll to bottom"
        >
          <ArrowDown :size="16" />
        </button>
      </Transition>
      
      <ChatInput ref="chatInputRef" @send="$emit('send', $event)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted, onUnmounted } from "vue";
import type { Chat } from "@/stores/chat";
import ChatHeader from "./ChatHeader.vue";
import EmptyChatState from "./EmptyChatState.vue";
import MessageComponent from "./MessageComponent.vue";
import ChatInput from "./ChatInput.vue";
import { ArrowDown } from "lucide-vue-next";

interface Props {
  chat: Chat;
  connectionStatus: "unknown" | "checking" | "connected" | "disconnected";
  connectionMessage: string;
  isOfflineMode: boolean;
}

const props = defineProps<Props>();

const messagesContainer = ref<HTMLElement>();
const chatInputRef = ref<InstanceType<typeof ChatInput>>();
const emptyChatRef = ref<InstanceType<typeof EmptyChatState>>();
const showScrollButton = ref(false);

// Function to check if scrolled to bottom
const checkScrollPosition = () => {
  if (!messagesContainer.value) return;
  
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value;
  const threshold = 100; // Show button when more than 100px from bottom
  const isNearBottom = scrollTop + clientHeight >= scrollHeight - threshold;
  
  showScrollButton.value = !isNearBottom && props.chat.messages.length > 0;
};

// Function to scroll to bottom
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: 'smooth'
    });
  }
};

// Setup scroll listener
onMounted(() => {
  if (messagesContainer.value) {
    messagesContainer.value.addEventListener('scroll', checkScrollPosition);
  }
});

onUnmounted(() => {
  if (messagesContainer.value) {
    messagesContainer.value.removeEventListener('scroll', checkScrollPosition);
  }
});

// Watch for transition from empty state to messages view
watch(
  () => props.chat.messages.length,
  (newLength, oldLength) => {
    // If we just added the first message (transition from 0 to 1+)
    if (oldLength === 0 && newLength > 0) {
      // Wait for the UI to transition and then focus the new ChatInput
      nextTick(() => {
        setTimeout(() => {
          if (chatInputRef.value) {
            chatInputRef.value.focus();
          }
        }, 100); // Small delay to ensure the transition is complete
      });
    }
    
    // Check scroll position when messages change
    nextTick(() => {
      checkScrollPosition();
    });
  }
);

defineEmits<{
  send: [message: string];
  edit: [messageId: string, content: string];
  delete: [messageId: string];
  "start-edit": [messageId: string];
  "cancel-edit": [messageId: string];
  retry: [messageId: string];
  "retry-connection": [];
  "toggle-sidebar": [];
  "create-new-chat": [];
}>();

defineExpose({
  focus: () => {
    nextTick(() => {
      if (emptyChatRef.value) {
        emptyChatRef.value.focus();
      } else if (chatInputRef.value) {
        chatInputRef.value.focus();
      }
    });
  },
  setLoading: (loading: boolean) => {
    if (emptyChatRef.value) {
      emptyChatRef.value.setLoading(loading);
    } else if (chatInputRef.value) {
      chatInputRef.value.setLoading(loading);
    }
    
    // Additional focus management when loading is finished
    if (!loading) {
      nextTick(() => {
        if (chatInputRef.value) {
          chatInputRef.value.focus();
        } else if (emptyChatRef.value) {
          emptyChatRef.value.focus();
        }
      });
    }
  },
  scrollToBottom: () => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  },
});
</script>

<style lang="scss" scoped>
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
  position: relative; /* Add position relative for absolute positioning of scroll button */
}

.chat-header {
  position: sticky;
  top: 0;
  z-index: 10;
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
  @media (max-width: 992px) {
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

/* Scroll to bottom button */
.scroll-to-bottom-button {
  position: absolute;
  bottom: 150px; /* Position just above the chat input */
  left: 50%; /* Center horizontally */
  transform: translateX(-50%); /* Adjust for centering */
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.2s ease;
  z-index: 5;

  &:hover {
    background: var(--color-primary-dark);
    transform: translateX(-50%) translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  }

  &:active {
    transform: translateX(-50%) translateY(0);
  }

  @media (max-width: 992px) {
    bottom: 110px; /* Adjust for mobile */
    width: 40px;
    height: 40px;
  }
}

/* Scroll button transition */
.scroll-button-enter-active,
.scroll-button-leave-active {
  transition: all 0.3s ease;
}

.scroll-button-enter-from,
.scroll-button-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px) scale(0.8);
}

.scroll-button-enter-to,
.scroll-button-leave-from {
  opacity: 1;
  transform: translateX(-50%) translateY(0) scale(1);
}
</style>
