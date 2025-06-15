<template>
  <div class="help-tooltip">
    <button @click="toggleVisible" class="help-button" title="Keyboard shortcuts">
      <HelpCircle :size="16" />
    </button>
    
    <div v-if="isVisible" class="help-content">
      <h3>Keyboard Shortcuts</h3>
      <div class="shortcut-list">
        <div class="shortcut-item">
          <kbd>Ctrl</kbd> + <kbd>N</kbd>
          <span>New chat</span>
        </div>
        <div class="shortcut-item">
          <kbd>Esc</kbd>
          <span>Focus message input</span>
        </div>
        <div class="shortcut-item">
          <kbd>Enter</kbd>
          <span>Send message</span>
        </div>
        <div class="shortcut-item">
          <kbd>Shift</kbd> + <kbd>Enter</kbd>
          <span>New line</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { HelpCircle } from 'lucide-vue-next'
import { onClickOutside } from '@vueuse/core'

const isVisible = ref(false)
const helpRef = ref()

const toggleVisible = () => {
  isVisible.value = !isVisible.value
}

onClickOutside(helpRef, () => {
  isVisible.value = false
})
</script>

<style scoped lang="scss">
.help-tooltip {
  position: relative;
}

.help-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255, 255, 255, 0.8);
  color: var(--color-gray-500);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);

  &:hover {
    background: var(--color-white);
    color: var(--color-gray-700);
    transform: scale(1.05);
    box-shadow: var(--shadow-md);
  }
}

.help-content {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 12px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(226, 232, 240, 0.5);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  z-index: 1000;
  min-width: 240px;

  h3 {
    margin: 0 0 16px 0;
    font-size: 16px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--color-gray-800) 0%, var(--color-gray-600) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  padding: 8px 12px;
  background: rgba(248, 250, 252, 0.8);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(226, 232, 240, 0.3);
  
  span {
    color: var(--color-gray-600);
    font-weight: 500;
  }
}

kbd {
  background: linear-gradient(135deg, var(--color-gray-100) 0%, var(--color-gray-50) 100%);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-sm);
  padding: 3px 6px;
  font-family: inherit;
  font-size: 11px;
  color: var(--color-gray-700);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}
</style>
