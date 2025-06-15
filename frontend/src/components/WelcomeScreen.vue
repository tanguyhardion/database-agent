<template>
  <div class="welcome-screen">
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
import { MessageSquare, Database } from "lucide-vue-next";
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
</style>
