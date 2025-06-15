<template>
  <div class="chat-header">
    <div class="chat-header-left">
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
  'retry-connection': [];
}>();
</script>

<style lang="scss" scoped>
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
</style>
