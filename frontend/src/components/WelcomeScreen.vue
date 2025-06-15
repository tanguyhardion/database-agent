<template>
  <div class="welcome-screen">
    <button 
      class="mobile-menu-btn"
      @click="$emit('toggle-sidebar')"
      aria-label="Toggle menu"
    >
      <Menu :size="20" />
    </button>
    <div class="welcome-content">
      <h1 class="welcome-title">Welcome to Business Data Chat</h1>
      <p class="welcome-description">
        Ask questions about your business data in natural language and get
        insights instantly.
      </p>
      <!-- Connection status in welcome screen -->
      <div class="welcome-connection-status">
        <ConnectionStatus 
          :status="connectionStatus"
          :message="connectionMessage"
          :is-offline="isOfflineMode"
          size="large"
          @retry="$emit('retry-connection')"
        />
      </div>
      <button @click="$emit('create-chat')" class="welcome-btn">
        <MessageSquare :size="20" />
        Start New Chat
      </button>
      <button
        @click="$emit('create-table-demo')"
        class="welcome-btn welcome-btn--secondary"
      >
        <Database :size="20" />
        View Table Demo
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { MessageSquare, Database, Menu } from "lucide-vue-next";
import ConnectionStatus from "./ConnectionStatus.vue";

interface Props {
  connectionStatus: "unknown" | "checking" | "connected" | "disconnected";
  connectionMessage: string;
  isOfflineMode: boolean;
}

defineProps<Props>();

defineEmits<{
  'create-chat': [];
  'create-table-demo': [];
  'retry-connection': [];
  'toggle-sidebar': [];
}>();
</script>

<style lang="scss" scoped>
.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  position: relative;
}

.mobile-menu-btn {
  display: none;
  position: absolute;
  top: 24px;
  left: 24px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(226, 232, 240, 0.5);
  color: var(--color-gray-600);
  cursor: pointer;
  padding: 12px;
  border-radius: var(--radius-lg);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-md);
  z-index: 10;

  @media (max-width: 768px) {
    display: flex;
  }

  &:hover {
    background: rgba(255, 255, 255, 1);
    color: var(--color-gray-800);
    transform: scale(1.05);
  }

  &:active {
    transform: scale(0.95);
  }
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

  @media (max-width: 768px) {
    padding: 32px 24px;
    margin: 0 16px;
    max-width: none;
  }

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 32px 64px -12px rgba(0, 0, 0, 0.25);
  }
}

.welcome-title {
  font-size: 36px;
  font-weight: 700;
  color: var(--color-gray-800);
  margin-bottom: 16px;
  line-height: 1.2;
  letter-spacing: -0.02em;

  @media (max-width: 768px) {
    font-size: 28px;
  }
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

.welcome-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;  padding: 16px 32px;
  background: var(--color-primary);
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

  @media (max-width: 768px) {
    width: 100%;
    margin: 6px 0;
    padding: 14px 24px;
    font-size: 15px;
  }

  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;    background: rgba(255, 255, 255, 0.2);
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
    background: var(--color-white);
    color: var(--color-gray-700);
    border: 2px solid var(--color-gray-200);

    &:hover {
      background: var(--color-gray-50);
      border-color: var(--color-primary);
    }
  }
}
</style>
