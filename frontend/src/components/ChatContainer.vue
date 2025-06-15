<template>
  <div class="chat-container">
    <ChatHeader
      class="chat-header"
      :title="chat.title"
      :message-count="chat.messages.length"
      :connection-status="connectionStatus"
      :connection-message="connectionMessage"
      :is-offline-mode="isOfflineMode"
      @retry-connection="$emit('retry-connection')"
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
            @edit="$emit('edit', message.id, $event)"
            @delete="$emit('delete', message.id)"
            @start-edit="$emit('start-edit', message.id)"
            @cancel-edit="$emit('cancel-edit', message.id)"
          />
        </div>
      </div>
      <ChatInput ref="chatInputRef" @send="$emit('send', $event)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { Chat } from "@/stores/chat";
import ChatHeader from "./ChatHeader.vue";
import EmptyChatState from "./EmptyChatState.vue";
import MessageComponent from "./MessageComponent.vue";
import ChatInput from "./ChatInput.vue";

interface Props {
  chat: Chat;
  connectionStatus: "unknown" | "checking" | "connected" | "disconnected";
  connectionMessage: string;
  isOfflineMode: boolean;
}

defineProps<Props>();

const messagesContainer = ref<HTMLElement>();
const chatInputRef = ref<InstanceType<typeof ChatInput>>();
const emptyChatRef = ref<InstanceType<typeof EmptyChatState>>();

defineEmits<{
  send: [message: string];
  edit: [messageId: string, content: string];
  delete: [messageId: string];
  "start-edit": [messageId: string];
  "cancel-edit": [messageId: string];
  "retry-connection": [];
}>();

defineExpose({
  focus: () => {
    if (emptyChatRef.value) {
      emptyChatRef.value.focus();
    } else if (chatInputRef.value) {
      chatInputRef.value.focus();
    }
  },
  setLoading: (loading: boolean) => {
    if (emptyChatRef.value) {
      emptyChatRef.value.setLoading(loading);
    } else if (chatInputRef.value) {
      chatInputRef.value.setLoading(loading);
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
