<template>
  <div
    :class="[
      'status-badge',
      `status-badge--${status}`,
      { 'status-badge--large': size === 'large' }
    ]"
    :title="message || getDefaultMessage()"
    @click="handleClick"
    :style="isClickable ? 'cursor: pointer' : ''"
  >
    <div :class="['status-dot', { 'status-dot--pulse': status === 'checking' }]"></div>
    {{ getDisplayText() }}
    <button
      v-if="isOffline && isClickable"
      class="retry-btn"
      title="Retry connection"
      @click.stop="$emit('retry')"
    >
      ↻
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  status: "unknown" | "checking" | "connected" | "disconnected";
  message?: string;
  isOffline?: boolean;
  size?: "normal" | "large";
}

const props = withDefaults(defineProps<Props>(), {
  size: "normal",
  isOffline: false
});

const emit = defineEmits<{
  retry: [];
}>();

const isClickable = computed(() => props.isOffline && props.status !== 'checking');

const getDisplayText = () => {
  switch (props.status) {
    case 'checking':
      return props.size === 'large' ? 'Testing connection to backend...' : 'Checking...';
    case 'connected':
      return 'Connected';
    case 'disconnected':
    case 'unknown':
    default:
      return 'Demo Mode';
  }
};

const getDefaultMessage = () => {
  switch (props.status) {
    case 'checking':
      return 'Testing connection to backend...';
    case 'connected':
      return 'Connected to backend';
    case 'disconnected':
    case 'unknown':
    default:
      return 'Demo mode - start backend for real queries';
  }
};

const handleClick = () => {
  if (isClickable.value) {
    emit('retry');
  }
};
</script>

<style lang="scss" scoped>
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

  &--large {
    padding: 12px 20px;
    font-size: 14px;
    gap: 10px;
  }

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

    &.status-badge--large .status-dot {
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
    }
  }

  &--demo,
  &--disconnected,
  &--unknown {
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

    &.status-badge--large .status-dot {
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
      box-shadow: 0 0 6px rgba(59, 130, 246, 0.4);
    }

    &.status-badge--large .status-dot {
      box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
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
</style>
