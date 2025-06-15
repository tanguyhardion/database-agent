<template>
  <div class="message" :class="`message--${message.role}`">
    <div class="message__avatar">
      <div v-if="message.role === 'user'" class="avatar avatar--user">
        <User :size="16" />
      </div>
      <div v-else class="avatar avatar--assistant">
        <Bot :size="16" />
      </div>
    </div>
    
    <div class="message__content">
      <div v-if="!message.isEditing" class="message__text">
        <div v-if="message.isStreaming" class="streaming">
          <div v-html="formattedContent"></div>
          <span class="cursor">|</span>
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
      
      <div v-if="!message.isEditing && !message.isStreaming" class="message__actions">
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
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  transition: background-color 0.2s;

  &--user {
    background-color: rgba(16, 163, 127, 0.1);
  }

  &--assistant {
    background-color: rgba(52, 53, 65, 0.05);
  }
}

.message__avatar {
  flex-shrink: 0;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;

  &--user {
    background-color: #10a37f;
  }

  &--assistant {
    background-color: #6366f1;
  }
}

.message__content {
  flex: 1;
  min-width: 0;
}

.message__text {
  line-height: 1.6;
  word-wrap: break-word;
  white-space: pre-wrap; /* Preserve whitespace and line breaks */

  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin: 16px 0 8px 0;
    font-weight: 600;
  }

  :deep(p) {
    margin: 0; 
  }

  :deep(pre) {
    background-color: #f4f4f4;
    border-radius: 4px;
    padding: 12px;
    overflow-x: auto;
    margin: 8px 0;
  }

  :deep(code) {
    background-color: #f4f4f4;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
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
    margin: 12px 0;
    font-size: 14px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border-radius: 6px;
    overflow: hidden;
  }

  :deep(th), :deep(td) {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
  }

  :deep(th) {
    background-color: #f8f9fa;
    font-weight: 600;
    color: #374151;
    border-bottom: 2px solid #d1d5db;
  }

  :deep(tbody tr) {
    transition: background-color 0.15s ease;
    
    &:nth-child(even) {
      background-color: #fafafa;
    }
  }

  :deep(tbody tr:last-child td) {
    border-bottom: none;
  }

  // Responsive table wrapper
  :deep(.table-wrapper) {
    overflow-x: auto;
    margin: 12px 0;
    border-radius: 6px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
}

.streaming {
  display: flex;
  align-items: flex-end;
  gap: 2px;
}

.cursor {
  animation: blink 1s infinite;
  font-weight: bold;
  color: #10a37f;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.message__edit {
  .edit-textarea {
    width: 100%;
    min-height: 80px;
    padding: 8px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-family: inherit;
    font-size: inherit;
    resize: vertical;
    outline: none;

    &:focus {
      border-color: #10a37f;
      box-shadow: 0 0 0 1px #10a37f;
    }
  }

  .edit-actions {
    display: flex;
    gap: 8px;
    margin-top: 8px;
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
  padding: 4px;
  border: none;
  background: none;
  border-radius: 4px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;

  &:hover {
    background-color: rgba(0, 0, 0, 0.1);
    color: #374151;
  }

  &--danger:hover {
    background-color: rgba(239, 68, 68, 0.1);
    color: #dc2626;
  }
}

.btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;

  &--sm {
    padding: 4px 8px;
    font-size: 12px;
  }

  &--primary {
    background-color: #10a37f;
    color: white;

    &:hover {
      background-color: #0d8f6e;
    }
  }

  &--secondary {
    background-color: #f3f4f6;
    color: #374151;

    &:hover {
      background-color: #e5e7eb;
    }
  }
}
</style>
