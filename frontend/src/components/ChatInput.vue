<template>
  <div class="chat-input">
    <div class="input-container">
      <textarea
        ref="inputRef"
        v-model="inputMessage"
        @keydown.enter.exact.prevent="handleSubmit"
        @keydown.enter.shift.exact="addNewLine"
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

const addNewLine = () => {
  inputMessage.value += '\n'
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
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  background-color: white;
}

.input-container {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  max-width: 768px;
  margin: 0 auto;
}

.message-input {
  flex: 1;
  min-height: 44px;
  max-height: 200px;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.4;
  resize: none;
  outline: none;
  transition: all 0.2s;

  &:focus {
    border-color: #10a37f;
    box-shadow: 0 0 0 1px #10a37f;
  }

  &:disabled {
    background-color: #f9fafb;
    cursor: not-allowed;
  }

  &::placeholder {
    color: #9ca3af;
  }
}

.send-button {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 12px;
  background-color: #10a37f;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background-color: #0d8f6e;
    transform: scale(1.02);
  }

  &:disabled {
    background-color: #d1d5db;
    cursor: not-allowed;
    transform: none;
  }

  &--loading {
    cursor: not-allowed;
  }
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.input-footer {
  text-align: center;
  margin-top: 8px;
}

.input-hint {
  font-size: 12px;
  color: #6b7280;
}

kbd {
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  padding: 1px 4px;
  font-family: inherit;
  font-size: 11px;
}
</style>
