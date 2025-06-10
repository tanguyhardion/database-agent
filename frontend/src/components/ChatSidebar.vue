<template>
  <div class="sidebar" :class="{ 'sidebar--collapsed': isCollapsed }">
    <div class="sidebar__header">
      <button @click="toggleSidebar" class="sidebar__toggle">
        <Menu :size="20" />
      </button>
        <button
        v-if="!isCollapsed"
        @click="createNewChat"
        class="new-chat-btn"
        :disabled="isCreatingChat"
      >
        <Plus v-if="!isCreatingChat" :size="16" />
        <div v-else class="spinner"></div>
        New Chat
      </button>
    </div>

    <div v-if="!isCollapsed" class="sidebar__content">
      <div class="chat-list">
        <div
          v-for="chat in chats"
          :key="chat.id"
          class="chat-item"
          :class="{ 'chat-item--active': chat.id === currentChatId }"
          @click="selectChat(chat.id)"
        >
          <div class="chat-item__content">
            <div class="chat-item__title">{{ chat.title }}</div>
            <div class="chat-item__meta">
              <span class="chat-item__time">
                {{ formatTime(chat.updatedAt) }}
              </span>
              <span class="chat-item__count">
                {{ chat.messages.length }} messages
              </span>
            </div>
          </div>
          
          <div class="chat-item__actions">
            <button
              @click.stop="deleteChat(chat.id)"
              class="chat-item__delete"
              title="Delete chat"
            >
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
      </div>

      <div v-if="chats.length === 0" class="empty-state">
        <MessageSquare :size="48" class="empty-state__icon" />
        <h3 class="empty-state__title">No chats yet</h3>
        <p class="empty-state__description">
          Start a conversation by creating a new chat
        </p>
      </div>
    </div>

    <div v-if="!isCollapsed" class="sidebar__footer">      <div class="app-info">
        <h4>Business Data Chat</h4>
        <p>Ask questions about your data in natural language</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Menu, Plus, Trash2, MessageSquare } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { useStorage } from '@vueuse/core'

const chatStore = useChatStore()
const isCollapsed = useStorage('sidebar-collapsed', false)
const isCreatingChat = ref(false)

const chats = computed(() => chatStore.chats)
const currentChatId = computed(() => chatStore.currentChatId)

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const createNewChat = () => {
  isCreatingChat.value = true
  chatStore.createNewChat()
  // Reset after a short delay for visual feedback
  setTimeout(() => {
    isCreatingChat.value = false
  }, 500)
}

const selectChat = (chatId: string) => {
  chatStore.selectChat(chatId)
}

const deleteChat = (chatId: string) => {
  if (confirm('Are you sure you want to delete this chat?')) {
    chatStore.deleteChat(chatId)
  }
}

const formatTime = (date: Date) => {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7) {
    return `${diffDays} days ago`
  } else {
    return date.toLocaleDateString()
  }
}
</script>

<style scoped lang="scss">
.sidebar {
  width: 280px;
  height: 100vh;
  background-color: #111827;
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;

  &--collapsed {
    width: 64px;
  }

  @media (max-width: 768px) {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1000;
    transform: translateX(-100%);
    
    &--collapsed {
      width: 280px;
      transform: translateX(0);
    }
  }
}

.sidebar__header {
  padding: 16px;
  border-bottom: 1px solid #374151;
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar__toggle {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: background-color 0.2s;

  &:hover {
    background-color: #374151;
  }
}

.new-chat-btn {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background-color: #10a37f;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;

  &:hover:not(:disabled) {
    background-color: #0d8f6e;
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.sidebar__content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}

.chat-list {
  padding: 0 16px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #374151;
  }

  &--active {
    background-color: #10a37f;

    &:hover {
      background-color: #0d8f6e;
    }
  }
}

.chat-item__content {
  flex: 1;
  min-width: 0;
}

.chat-item__title {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-item__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #9ca3af;

  .chat-item--active & {
    color: #ffffff;
  }
}

.chat-item__time {
  white-space: nowrap;
}

.chat-item__count {
  white-space: nowrap;
}

.chat-item__actions {
  opacity: 0;
  transition: opacity 0.2s;

  .chat-item:hover & {
    opacity: 1;
  }

  .chat-item--active & {
    opacity: 1;
  }
}

.chat-item__delete {
  background: none;
  border: none;
  color: #ef4444;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;

  &:hover {
    background-color: rgba(239, 68, 68, 0.1);
  }
}

.empty-state {
  text-align: center;
  padding: 48px 32px;
  color: #9ca3af;
}

.empty-state__icon {
  margin: 0 auto 16px;
  opacity: 0.5;
}

.empty-state__title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #d1d5db;
}

.empty-state__description {
  font-size: 14px;
  line-height: 1.5;
}

.sidebar__footer {
  padding: 16px;
  border-top: 1px solid #374151;
}

.app-info {
  h4 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
    color: #10a37f;
  }

  p {
    font-size: 12px;
    color: #9ca3af;
    line-height: 1.4;
  }
}

/* Scrollbar styling */
.sidebar__content::-webkit-scrollbar {
  width: 6px;
}

.sidebar__content::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar__content::-webkit-scrollbar-thumb {
  background: #374151;
  border-radius: 3px;
}

.sidebar__content::-webkit-scrollbar-thumb:hover {
  background: #4b5563;
}
</style>
