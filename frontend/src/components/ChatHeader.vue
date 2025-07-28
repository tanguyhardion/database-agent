<template>
  <div class="chat-header">
    <div class="chat-header-left">
      <button
        class="mobile-menu-btn"
        @click="$emit('toggle-sidebar')"
        aria-label="Toggle menu"
      >
        <Menu :size="20" />
      </button>

      <!-- Collapsed menu "+" button -->
      <button
        v-if="isCollapsed"
        class="collapsed-new-chat-btn"
        @click="$emit('create-new-chat')"
        aria-label="Create new chat"
        title="Create new chat"
      >
        <Plus :size="20" />
      </button>
      
      <h2 class="chat-title">{{ title }}</h2>
      <div class="chat-meta">{{ messageCount }} messages</div>
    </div>
    <div class="connection-status">
      <HelpTooltip />
      <ConnectionStatus
        :status="connectionStatus"
        :message="connectionMessage"
        :is-offline="isOfflineMode"
        @retry="$emit('retry-connection')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Menu, Plus } from "lucide-vue-next";
import { ref, onMounted, onUnmounted } from "vue";
import { useStorage } from "@vueuse/core";
import HelpTooltip from "./HelpTooltip.vue";
import ConnectionStatus from "./ConnectionStatus.vue";

interface Props {
  title: string;
  messageCount: number;
  connectionStatus: "unknown" | "checking" | "connected" | "disconnected";
  connectionMessage: string;
  isOfflineMode: boolean;
}

defineProps<Props>();

defineEmits<{
  "retry-connection": [];
  "toggle-sidebar": [];
  "create-new-chat": [];
}>();

const isCollapsed = useStorage("sidebar-collapsed", false);
</script>

<style lang="scss" scoped>
.chat-header {
  padding: 24px 32px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow-sm);

  @media (max-width: 992px) {
    padding: 16px 20px;
  }
}

.mobile-menu-btn {
  display: none;
  background: rgba(100, 116, 139, 0.1);
  border: none;
  color: var(--color-gray-600);
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-lg);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  align-items: center;
  justify-content: center;

  @media (max-width: 992px) {
    display: flex;
  }

  &:hover {
    background: rgba(100, 116, 139, 0.2);
    color: var(--color-gray-800);
  }

  &:active {
    transform: scale(0.95);
  }
}

.collapsed-new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  border: none;
  color: var(--color-white);
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-lg);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);

  &:hover {
    background: var(--color-primary-dark);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }

  &:active {
    transform: scale(0.95);
  }
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
  color: var(--color-gray-800);
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

  @media (max-width: 992px) {
    display: none;
  }
}

.cost-meta {
  font-size: 14px;
  color: var(--color-green-600);
  font-weight: 600;
  background: rgba(34, 197, 94, 0.1);
  padding: 4px 12px;
  border-radius: var(--radius-full);
}

.connection-status {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
