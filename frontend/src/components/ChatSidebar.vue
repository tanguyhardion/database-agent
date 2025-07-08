<template>
  <!-- Mobile overlay -->
  <div 
    v-if="!isCollapsed" 
    class="sidebar-overlay" 
    @click="toggleSidebar"
  ></div>
  
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

    <div v-if="!isCollapsed" class="sidebar__footer">
      <div class="app-info">
        <h4>Business Data Chat</h4>
        <p>Ask questions about your data in natural language</p>
      </div>
      <div class="sidebar__logo">
        <img src="/logo.png" alt="Company Logo" class="sidebar-logo-full" />
      </div>
    </div>
    <div v-else class="sidebar__footer--collapsed">
      <div class="sidebar__logo-collapsed">
        <img src="/logo_short.png" alt="Logo Short" class="sidebar-logo-short" />
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
const currentChat = computed(() => chatStore.currentChat)

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const shouldAutoCloseSidebar = () => window.innerWidth < 992

const createNewChat = () => {
  // If there's already an empty chat, don't create a new one
  if (currentChat.value && currentChat.value.messages.length === 0) {
    return;
  }
  isCreatingChat.value = true
  chatStore.createNewChat()
  
  // Auto-close menu after creating new chat if viewport < 992px
  if (shouldAutoCloseSidebar()) {
    isCollapsed.value = true
  }
  
  // Reset after a short delay for visual feedback
  setTimeout(() => {
    isCreatingChat.value = false
  }, 500)
}

const selectChat = (chatId: string) => {
  chatStore.selectChat(chatId)
  
  // Auto-close menu after selecting chat if viewport < 992px
  if (shouldAutoCloseSidebar()) {
    isCollapsed.value = true
  }
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

// Expose the toggle function for parent components
defineExpose({
  toggle: toggleSidebar
})
</script>

<style scoped lang="scss">
.sidebar {
  width: 280px;
  height: 100vh;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(71, 85, 105, 0.3);
  color: var(--color-white);
  display: flex;
  flex-direction: column;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-xl);
  overflow: hidden;

  &--collapsed {
    width: 64px;
  }
  @media (max-width: 992px) {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1000;
    width: 280px;
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    &:not(.sidebar--collapsed) {
      transform: translateX(0);
    }
  }
}

.sidebar__header {
  padding: 20px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  .sidebar--collapsed & {
    justify-content: center;
    padding: 20px 12px;
  }
}

.sidebar__toggle {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: var(--color-white);
  cursor: pointer;
  padding: 12px;
  border-radius: var(--radius-lg);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
    box-shadow: var(--shadow-md);
  }

  &:active {
    transform: scale(0.95);
  }
}

.new-chat-btn {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;  padding: 14px 20px;
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-xl);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-lg);
  white-space: nowrap;
  min-width: 0;

  .sidebar--collapsed & {
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease-in-out;
  }  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
    background: var(--color-primary-dark);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    transform: none;
  }

  .spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid var(--color-white);
    border-radius: var(--radius-full);
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
  transition: opacity 0.2s ease-in-out;
  min-width: 280px;

  .sidebar--collapsed & {
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease-in-out;
  }
}

.chat-list {
  padding: 0 16px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  margin-bottom: 8px;
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);

  &:hover {
    background: rgba(255, 255, 255, 0.15);
    box-shadow: var(--shadow-md);
  }  &--active {
    background: var(--color-primary);
    box-shadow: var(--shadow-lg);
    border: 1px solid rgba(255, 255, 255, 0.2);

    &:hover {
      background: var(--color-primary-dark);
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

  @media (max-width: 992px) {
    display: none;
  }
}

.chat-item__actions {
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  .chat-item:hover & {
    opacity: 1;
  }

  .chat-item--active & {
    opacity: 1;
  }
}

.chat-item__delete {
  background: transparent;
  border: none;
  color: var(--color-gray-200);
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-lg);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  &:hover {
    background: var(--color-error);
    color: var(--color-white);
    transform: scale(1.1);
    box-shadow: var(--shadow-md);
  }

  &:active {
    transform: scale(0.95);
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
  border-top: 1px solid rgba(71, 85, 105, 0.3);
  transition: opacity 0.2s ease-in-out;
  min-width: 280px;

  .sidebar--collapsed & {
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease-in-out;
  }
}

.app-info {  h4 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
    color: var(--color-primary);
  }

  p {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.4;
    font-weight: 400;
  }
}

.sidebar__logo {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  margin-top: 16px;
  img.sidebar-logo-full {
    max-width: 120px;
    max-height: 48px;
    width: auto;
    height: auto;
    filter: drop-shadow(0 2px 8px rgba(0,0,0,0.15));
  }
}
.sidebar__footer--collapsed {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  padding-bottom: 16px;
}
.sidebar__logo-collapsed {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  width: 100%;
  img.sidebar-logo-short {
    max-width: 36px;
    max-height: 36px;
    width: auto;
    height: auto;
    filter: drop-shadow(0 2px 8px rgba(0,0,0,0.15));
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

.sidebar-overlay {
  display: none;
  
  @media (max-width: 992px) {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
    opacity: 0;
    animation: fadeIn 0.3s ease-out forwards;
  }
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}
</style>
