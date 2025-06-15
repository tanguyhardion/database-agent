<template>
  <div class="chat-input">
    <div class="input-container">
      <textarea
        ref="inputRef"
        v-model="inputMessage"        @keydown.enter.exact.prevent="handleSubmit"
        @keydown.enter.shift="addNewLine"
        @input="handleInput"
        placeholder="Send a message..."
        class="message-input"
        rows="1"
        :disabled="isLoading"
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
    
    <div class="input-footer">
      <span class="input-hint">
        Press <kbd>Enter</kbd> to send, <kbd>Shift + Enter</kbd> for new line
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { Send } from 'lucide-vue-next'

interface Emits {
  (e: 'send', message: string): void
}

const emit = defineEmits<Emits>()

const inputRef = ref<HTMLTextAreaElement>()
const inputMessage = ref('')
const isLoading = ref(false)

const canSend = computed(() => 
  inputMessage.value.trim().length > 0 && !isLoading.value
)

const handleInput = () => {
  // Auto-resize textarea
  const textarea = inputRef.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
  }
}

const handleSubmit = () => {
  if (!canSend.value) return
  
  const message = inputMessage.value.trim()
  if (message) {
    emit('send', message)
    inputMessage.value = ''
    
    // Reset textarea height
    nextTick(() => {
      if (inputRef.value) {
        inputRef.value.style.height = 'auto'
      }
    })
  }
}

const addNewLine = (event: KeyboardEvent) => {
  // Let the default behavior happen (cursor moves to next line)
  // without adding extra newline characters
  nextTick(() => {
    handleInput()
  })
}

const setLoading = (loading: boolean) => {
  isLoading.value = loading
}

const focus = () => {
  inputRef.value?.focus()
}

defineExpose({
  setLoading,
  focus
})
</script>

<style scoped lang="scss">
.chat-input {
  padding: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.8) 100%);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(226, 232, 240, 0.5);
}

.input-container {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  max-width: 768px;
  margin: 0 auto;
  padding: 8px;
  background: var(--color-white);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-xl);
  border: 1px solid rgba(226, 232, 240, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:focus-within {
    transform: translateY(-2px);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
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

  &:disabled {
    background-color: var(--color-gray-50);
    cursor: not-allowed;
    opacity: 0.6;
  }

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
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
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
    background: linear-gradient(135deg, var(--color-primary-dark) 0%, #4c51bf 100%);
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

.input-footer {
  text-align: center;
  margin-top: 12px;
}

.input-hint {
  font-size: 13px;
  color: var(--color-gray-500);
  font-weight: 400;
}

kbd {
  background: linear-gradient(135deg, var(--color-gray-100) 0%, var(--color-gray-50) 100%);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-sm);
  padding: 2px 6px;
  font-family: inherit;
  font-size: 11px;
  font-weight: 500;
  box-shadow: var(--shadow-sm);
}
</style>
