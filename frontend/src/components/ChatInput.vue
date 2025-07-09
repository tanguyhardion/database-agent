<template>
  <div class="chat-input">
    <div class="input-container">
      <textarea
        ref="inputRef"
        v-model="inputMessage"
        @keydown="handleKeydown"
        @input="handleInput"
        :placeholder="placeholderText"
        class="message-input"
        rows="1"
      ></textarea>
      <button
        @click="handleSubmit"
        :disabled="!canSend"
        class="send-button"
        :class="{ 'send-button--loading': isLoading }"
      >
        <Send v-if="!isLoading" :size="16" />
        <div v-else class="spinner"></div>
      </button>
    </div>
    <div class="disclaimer">
      ⚠️ This chatbot is experimental and can make mistakes. Please verify
      important information. Results may be limited to a subset of available
      data. Powered by GPT-4o.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from "vue";
import { Send } from "lucide-vue-next";

interface Emits {
  (e: "send", message: string): void;
}

const emit = defineEmits<Emits>();

const inputRef = ref<HTMLTextAreaElement>();
const inputMessage = ref("");
const isLoading = ref(false);

const placeholderText = computed(() => "Send a message...");

const canSend = computed(
  () => inputMessage.value.trim().length > 0 && !isLoading.value
);

// Check if device is mobile
const isMobile = () => {
  return (
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    )
  );
};

// Handle keyboard shortcuts
const handleKeydown = (event: KeyboardEvent) => {
  // On mobile, let default behavior handle enter key
  if (isMobile()) return;

  if (event.key === "Enter") {
    if (event.shiftKey) {
      // Shift+Enter: Add new line (default behavior)
      addNewLine(event);
    } else {
      // Enter: Submit message
      event.preventDefault();
      handleSubmit();
    }
  }
};

const handleInput = () => {
  // Auto-resize textarea
  const textarea = inputRef.value;
  if (textarea) {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
  }
};

const handleSubmit = () => {
  if (!canSend.value) return;

  const message = inputMessage.value.trim();
  if (message) {
    emit("send", message);
    inputMessage.value = "";

    // Reset textarea height and immediately refocus
    nextTick(() => {
      if (inputRef.value) {
        inputRef.value.style.height = "auto";
        inputRef.value.focus(); // Refocus immediately after sending
      }
    });
  }
};

const addNewLine = (event: KeyboardEvent) => {
  nextTick(() => {
    handleInput();
  });
};

const setLoading = (loading: boolean) => {
  isLoading.value = loading;

  // When loading starts, maintain focus on the input
  if (loading) {
    nextTick(() => {
      if (inputRef.value && document.activeElement !== inputRef.value) {
        inputRef.value.focus();
      }
    });
  }

  // When loading is finished, ensure the input regains focus
  if (!loading) {
    nextTick(() => {
      if (inputRef.value) {
        inputRef.value.focus();
      }
    });
  }
};

const focus = () => {
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus();
    }
  });
};

defineExpose({
  setLoading,
  focus,
});
</script>

<style scoped lang="scss">
.chat-input {
  padding: 24px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(226, 232, 240, 0.5);
}

.input-container {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  max-width: 992px;
  margin: 0 auto;
  padding: 8px;
  background: var(--color-white);
  border-radius: var(--radius-2xl);
  border: 1px solid rgba(226, 232, 240);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:focus-within {
    transform: translateY(-2px);
    border-color: var(--color-primary);
  }
}

.message-input {
  flex: 1;
  min-height: 48px;
  max-height: 200px;
  padding: 16px 20px;
  border: none;
  border-radius: var(--radius-xl);
  font-family: inherit;
  font-size: 16px;
  line-height: 1.5;
  resize: none;
  outline: none;
  background: transparent;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  &::placeholder {
    color: var(--color-gray-400);
    font-weight: 400;
  }
}

.send-button {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border: none;
  border-radius: var(--radius-xl);
  background: var(--color-primary);
  color: var(--color-white);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-md);

  &:hover:not(:disabled) {
    transform: scale(1.05);
    box-shadow: var(--shadow-lg);
    background: var(--color-primary-dark);
  }

  &:active:not(:disabled) {
    transform: scale(0.95);
  }

  &:disabled {
    background: var(--color-gray-300);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  &--loading {
    cursor: not-allowed;
  }
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid var(--color-white);
  border-radius: var(--radius-full);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.disclaimer {
  text-align: center;
  margin-top: 12px;
  font-size: 12px;
  color: var(--color-gray-500);
  opacity: 0.8;
  font-weight: 400;
  line-height: 1.4;
  max-width: 992px;
  margin-left: auto;
  margin-right: auto;
}
</style>
