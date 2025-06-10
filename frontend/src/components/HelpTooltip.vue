<template>
  <div class="help-tooltip" :class="{ 'help-tooltip--visible': isVisible }">
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
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: #6b7280;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background-color: rgba(0, 0, 0, 0.05);
    color: #374151;
  }
}

.help-content {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  min-width: 200px;

  h3 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: #111827;
  }
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  
  span {
    color: #6b7280;
  }
}

kbd {
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  padding: 2px 4px;
  font-family: inherit;
  font-size: 10px;
  color: #374151;
}
</style>
