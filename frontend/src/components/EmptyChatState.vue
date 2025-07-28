<template>
  <div class="empty-chat-centered">
    <div class="greeting-content">
      <Database :size="48" class="empty-chat__icon" />
      <h3>Ask. Analyze. Act.</h3>
      <p>
        Ask me anything about your business. I’ll handle the data side.
      </p>
    </div>
    <div class="centered-chat-input">
      <div class="chat-input-minimal">
        <ChatInput ref="chatInputRef" @send="$emit('send', $event)" />
      </div>
      <div class="example-questions-inline">
        <button
          v-for="example in exampleQuestions"
          :key="example"
          @click="$emit('send', example)"
          class="example-btn-small"
        >
          {{ example }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { Database } from "lucide-vue-next";
import ChatInput from "./ChatInput.vue";

const chatInputRef = ref<InstanceType<typeof ChatInput>>();

const exampleQuestions = [
  "What data categories are available?",
  "How many properties are in the USA?",
  "What is the average lease term?",
];

defineEmits<{
  send: [message: string];
}>();

defineExpose({
  focus: () => {
    nextTick(() => {
      chatInputRef.value?.focus();
    });
  },
  setLoading: (loading: boolean) => chatInputRef.value?.setLoading(loading)
});
</script>

<style lang="scss" scoped>
.empty-chat-centered {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 32px;
  gap: 24px;
  min-height: 0;

  @media (max-width: 992px) {
    padding: 16px;
    gap: 16px;
  }
}

.greeting-content {
  text-align: center;
  max-width: 600px;
  h3 {
    font-size: 28px;
    font-weight: 700;
    color: var(--color-gray-800);
    margin-bottom: 12px;

    @media (max-width: 992px) {
      font-size: 24px;
    }
  }

  p {
    font-size: 18px;
    color: var(--color-gray-600);
    line-height: 1.7;
    margin-bottom: 0;
    font-weight: 400;

    @media (max-width: 992px) {
      font-size: 16px;
    }
  }
}

.empty-chat__icon {
  color: var(--color-primary);
  margin: 0 auto 24px;
  opacity: 0.7;
}

.centered-chat-input {
  width: 100%;
  max-width: 800px;
  z-index: 10;
}

.chat-input-minimal {
  :deep(.chat-input) {
    padding: 0;
    background: transparent;
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    border-top: none;
  }

  :deep(.input-container) {
    box-shadow: var(--shadow-lg);
    border: 2px solid var(--color-gray-200);

    &:focus-within {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1), var(--shadow-xl);
    }
  }

  :deep(.input-footer) {
    margin-top: 8px;
  }
}

.example-questions-inline {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;

  @media (max-width: 992px) {
    gap: 6px;
    margin-top: 12px;
  }
}

.example-btn-small {
  padding: 8px 16px;
  background: var(--color-white);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-full);
  font-size: 13px;
  color: var(--color-gray-700);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  white-space: nowrap;

  &:hover {
    border-color: var(--color-primary);
    background: var(--color-primary-light);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }

  @media (max-width: 992px) {
    padding: 6px 12px;
    font-size: 12px;
  }
}
</style>
