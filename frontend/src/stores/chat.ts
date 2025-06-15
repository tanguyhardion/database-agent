import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isEditing?: boolean
  isLoading?: boolean
}

export interface Chat {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}

export const useChatStore = defineStore('chat', () => {
  const chats = ref<Chat[]>([])
  const currentChatId = ref<string | null>(null)
  
  // Load data from localStorage on initialization
  const loadFromStorage = () => {
    try {
      const savedChats = localStorage.getItem('nl-sql-chats')
      const savedCurrentChatId = localStorage.getItem('nl-sql-current-chat-id')
      
      if (savedChats) {
        const parsedChats = JSON.parse(savedChats)
        // Convert date strings back to Date objects
        chats.value = parsedChats.map((chat: any) => ({
          ...chat,
          createdAt: new Date(chat.createdAt),
          updatedAt: new Date(chat.updatedAt),
          messages: chat.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
        }))
      }
      
      if (savedCurrentChatId) {
        currentChatId.value = savedCurrentChatId
      }
    } catch (error) {
      console.error('Error loading chats from storage:', error)
    }
  }

  // Save data to localStorage
  const saveToStorage = () => {
    try {
      localStorage.setItem('nl-sql-chats', JSON.stringify(chats.value))
      localStorage.setItem('nl-sql-current-chat-id', currentChatId.value || '')
    } catch (error) {
      console.error('Error saving chats to storage:', error)
    }
  }

  const currentChat = computed(() => 
    chats.value.find(chat => chat.id === currentChatId.value)
  )

  const generateId = () => Math.random().toString(36).substring(2) + Date.now().toString(36)

  const createNewChat = () => {
    const newChat: Chat = {
      id: generateId(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    }
    
    chats.value.unshift(newChat)
    currentChatId.value = newChat.id
    saveToStorage()
    return newChat
  }

  const selectChat = (chatId: string) => {
    currentChatId.value = chatId
    saveToStorage()
  }

  const deleteChat = (chatId: string) => {
    const index = chats.value.findIndex(chat => chat.id === chatId)
    if (index !== -1) {
      chats.value.splice(index, 1)
      
      if (currentChatId.value === chatId) {
        currentChatId.value = chats.value.length > 0 ? chats.value[0].id : null
        if (chats.value.length === 0) {
          createNewChat()
        }
      }
      saveToStorage()
    }
  }

  const addMessage = (chatId: string, message: Omit<Message, 'id' | 'timestamp'>) => {
    const chat = chats.value.find(c => c.id === chatId)
    if (!chat) return

    const newMessage: Message = {
      ...message,
      id: generateId(),
      timestamp: new Date()
    }

    chat.messages.push(newMessage)
    chat.updatedAt = new Date()

    // Update chat title if it's the first user message
    if (chat.messages.length === 1 && message.role === 'user') {
      chat.title = message.content.slice(0, 50) + (message.content.length > 50 ? '...' : '')
    }

    saveToStorage()
    return newMessage
  }

  const updateMessage = (chatId: string, messageId: string, content: string) => {
    const chat = chats.value.find(c => c.id === chatId)
    if (!chat) return

    const message = chat.messages.find(m => m.id === messageId)
    if (message) {
      message.content = content
      message.isEditing = false
      chat.updatedAt = new Date()
      saveToStorage()
    }
  }

  const deleteMessage = (chatId: string, messageId: string) => {
    const chat = chats.value.find(c => c.id === chatId)
    if (!chat) return

    const index = chat.messages.findIndex(m => m.id === messageId)
    if (index !== -1) {
      chat.messages.splice(index, 1)
      chat.updatedAt = new Date()
      saveToStorage()
    }
  }

  const startMessageEditing = (chatId: string, messageId: string) => {
    const chat = chats.value.find(c => c.id === chatId)
    if (!chat) return

    const message = chat.messages.find(m => m.id === messageId)
    if (message) {
      message.isEditing = true
    }
  }
  const cancelMessageEditing = (chatId: string, messageId: string) => {
    const chat = chats.value.find(c => c.id === chatId)
    if (!chat) return

    const message = chat.messages.find(m => m.id === messageId)
    if (message) {
      message.isEditing = false
    }
  }

  const addLoadingMessage = (chatId: string) => {
    const chat = chats.value.find(c => c.id === chatId)
    if (!chat) return null

    const loadingMessage: Message = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true
    }

    chat.messages.push(loadingMessage)
    chat.updatedAt = new Date()
    saveToStorage()
    return loadingMessage
  }

  const updateLoadingMessage = (chatId: string, messageId: string, content: string) => {
    const chat = chats.value.find(c => c.id === chatId)
    if (!chat) return

    const message = chat.messages.find(m => m.id === messageId)
    if (message) {
      message.content = content
      message.isLoading = false
      chat.updatedAt = new Date()
      saveToStorage()
    }
  }

  const removeLoadingMessage = (chatId: string, messageId: string) => {
    const chat = chats.value.find(c => c.id === chatId)
    if (!chat) return

    const index = chat.messages.findIndex(m => m.id === messageId)
    if (index !== -1) {
      chat.messages.splice(index, 1)
      chat.updatedAt = new Date()
      saveToStorage()
    }
  }// Load data on initialization
  loadFromStorage()

  // Initialize with a default chat if no chats exist
  if (chats.value.length === 0) {
    createNewChat()
  }  return {
    chats,
    currentChatId,
    currentChat,
    loadFromStorage,
    saveToStorage,
    createNewChat,
    selectChat,
    deleteChat,
    addMessage,
    updateMessage,
    deleteMessage,
    startMessageEditing,
    cancelMessageEditing,
    addLoadingMessage,
    updateLoadingMessage,
    removeLoadingMessage
  }
})
