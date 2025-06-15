<template>
  <div class="message" :class="`message--${message.role}`">
    <div class="message__avatar">
      <div v-if="message.role === 'user'" class="avatar avatar--user">
        <User :size="16" />
      </div>
      <div v-else class="avatar avatar--assistant">
        <Bot :size="16" />
      </div>
    </div>      <div class="message__content">
      <div v-if="!message.isEditing" class="message__text">
        <div v-if="message.isLoading" class="loading-indicator">
          <div class="loading-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
        <div v-else v-html="formattedContent"></div>
      </div>
      
      <div v-else class="message__edit">
        <textarea
          ref="editTextarea"
          v-model="editContent"
          @keydown.enter.meta="saveEdit"
          @keydown.enter.ctrl="saveEdit"
          @keydown.escape="cancelEdit"
          class="edit-textarea"
          rows="3"
        ></textarea>
        <div class="edit-actions">
          <button @click="saveEdit" class="btn btn--primary btn--sm">Save</button>
          <button @click="cancelEdit" class="btn btn--secondary btn--sm">Cancel</button>
        </div>
      </div>
      
      <div v-if="!message.isEditing && !message.isLoading" class="message__actions">
        <button
          v-if="message.role === 'user'"
          @click="startEdit"
          class="action-btn"
          title="Edit message"
        >
          <Edit2 :size="14" />
        </button>
        <button
          @click="copyMessage"
          class="action-btn"
          title="Copy message"
        >
          <Copy :size="14" />
        </button>
        <button
          @click="deleteMessage"
          class="action-btn action-btn--danger"
          title="Delete message"
        >
          <Trash2 :size="14" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { User, Bot, Edit2, Copy, Trash2 } from 'lucide-vue-next'
import { marked } from 'marked'
import type { Message } from '@/stores/chat'

interface Props {
  message: Message
}

interface Emits {
  (e: 'edit', messageId: string, content: string): void
  (e: 'delete', messageId: string): void
  (e: 'start-edit', messageId: string): void
  (e: 'cancel-edit', messageId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const editTextarea = ref<HTMLTextAreaElement>()
const editContent = ref('')

const formattedContent = computed(() => {
  if (props.message.role === 'assistant') {
    // Parse markdown for assistant messages with proper line break handling
    const htmlContent = marked(props.message.content, { 
      breaks: true,
      gfm: true // GitHub Flavored Markdown includes table support
    }) as string
    
    // Wrap tables in a responsive container
    return htmlContent
      .replace(/<table>/g, '<div class="table-wrapper"><table>')
      .replace(/<\/table>/g, '</table></div>')
  }
  // Plain text for user messages - convert newlines to <br> tags
  return props.message.content.replace(/\n/g, '<br>')
})

const startEdit = () => {
  editContent.value = props.message.content
  emit('start-edit', props.message.id)
  nextTick(() => {
    editTextarea.value?.focus()
  })
}

const saveEdit = () => {
  emit('edit', props.message.id, editContent.value)
}

const cancelEdit = () => {
  emit('cancel-edit', props.message.id)
  editContent.value = ''
}

const copyMessage = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
  } catch (err) {
    console.error('Failed to copy message:', err)
  }
}

const deleteMessage = () => {
  emit('delete', props.message.id)
}
</script>

<style scoped lang="scss">
.message {
  display: flex;
  gap: 16px;
  padding: 24px;
  border-radius: var(--radius-2xl);
  margin-bottom: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  &--user {
    background: rgba(102, 126, 234, 0.1);
    border: 1px solid rgba(102, 126, 234, 0.2);
    margin-left: 10%;
    
    @media (max-width: 768px) {
      margin-left: 5%;
    }
  }

  &--assistant {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(226, 232, 240, 0.5);
    margin-right: 10%;
    box-shadow: var(--shadow-md);
    
    @media (max-width: 768px) {
      margin-right: 5%;
    }
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
  }
}

.message__avatar {
  flex-shrink: 0;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: var(--shadow-md);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  &--user {
    background: var(--color-primary);
  }

  &--assistant {
    background: var(--color-secondary);
  }

  &:hover {
    transform: scale(1.05);
    box-shadow: var(--shadow-lg);
  }
}

.message__content {
  flex: 1;
  min-width: 0;
}

.message__text {
  line-height: 1.3;
  word-wrap: break-word;

  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin: 12px 0 6px 0;
    font-weight: 600;
  }

  :deep(p) {
    margin: 4px 0; 
  }  :deep(pre) {
    background: var(--color-gray-100);
    border: 1px solid var(--color-gray-200);
    border-radius: var(--radius-lg);
    padding: 16px;
    overflow-x: auto;
    margin: 12px 0;
    box-shadow: var(--shadow-sm);
  }

  :deep(code) {
    background: var(--color-gray-100);
    padding: 4px 8px;
    border-radius: var(--radius-sm);
    font-family: var(--font-mono);
    font-size: 0.875em;
    border: 1px solid var(--color-gray-200);
  }

  :deep(pre code) {
    background-color: transparent;
    padding: 0;
  }

  :deep(ul), :deep(ol) {
    margin: 8px 0;
    padding-left: 20px;
  }

  :deep(blockquote) {
    border-left: 4px solid #e5e5e5;
    margin: 8px 0;
    padding-left: 16px;
    color: #666;
  }
  // Table styling for Markdown tables
  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    font-size: 14px;
    box-shadow: var(--shadow-lg);
    border-radius: var(--radius-lg);
    overflow: hidden;
    background: var(--color-white);
  }

  :deep(th), :deep(td) {
    padding: 16px 20px;
    text-align: left;
    border-bottom: 1px solid var(--color-gray-200);
    vertical-align: top;
  }
  :deep(th) {
    background: var(--color-gray-100);
    font-weight: 600;
    color: var(--color-gray-700);
    border-bottom: 2px solid var(--color-gray-300);
  }

  :deep(tbody tr) {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    
    &:nth-child(even) {
      background: var(--color-gray-50);
    }

    &:hover {
      background: var(--color-primary-light);
      transform: scale(1.005);
    }
  }

  :deep(tbody tr:last-child td) {
    border-bottom: none;
  }

  // Responsive table wrapper
  :deep(.table-wrapper) {
    overflow-x: auto;
    margin: 16px 0;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
  }
}

.message__edit {
  .edit-textarea {
    width: 100%;
    min-height: 100px;
    padding: 16px;
    border: 2px solid var(--color-gray-200);
    border-radius: var(--radius-lg);
    font-family: inherit;
    font-size: inherit;
    resize: vertical;
    outline: none;
    background: var(--color-white);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 4px var(--color-primary-light);
      transform: scale(1.01);
    }
  }

  .edit-actions {
    display: flex;
    gap: 12px;
    margin-top: 12px;
  }
}

.message__actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s;

  .message:hover & {
    opacity: 1;
  }
}

.action-btn {
  padding: 8px;
  border: none;
  background: rgba(255, 255, 255, 0.8);
  border-radius: var(--radius-lg);
  cursor: pointer;
  color: var(--color-gray-500);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);

  &:hover {
    background: var(--color-white);
    color: var(--color-gray-700);
    transform: scale(1.1);
    box-shadow: var(--shadow-md);
  }
  &--danger:hover {
    background: var(--color-error);
    color: var(--color-white);  }
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  color: var(--color-gray-600);
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.dot {
  width: 8px;
  height: 8px;
  background: var(--color-primary);
  border-radius: 50%;
  animation: loading-bounce 1.4s infinite ease-in-out;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

.loading-text {
  font-size: 14px;
  font-style: italic;
}

@keyframes loading-bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.btn {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &--primary {
    background: var(--color-primary);
    color: var(--color-white);

    &:hover {
      background: var(--color-primary-dark);
    }
  }

  &--secondary {
    background: var(--color-gray-200);
    color: var(--color-gray-700);

    &:hover {
      background: var(--color-gray-300);
    }
  }

  &--sm {
    padding: 6px 12px;
    font-size: 12px;
  }
}
</style>
