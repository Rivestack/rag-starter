import { ref } from 'vue'
import type { ChatMessage, SourceChunk } from '~/types'

export function useChat() {
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)

  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  async function sendMessage(documentId: string, content: string) {
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    }
    messages.value.push(userMsg)
    isLoading.value = true

    try {
      const response = await $fetch<{
        answer: string
        sources: SourceChunk[]
        model: string
      }>(`${apiBase}/api/chat`, {
        method: 'POST',
        body: {
          document_id: documentId,
          message: content,
          conversation_history: messages.value
            .slice(-10)
            .map((m) => ({ role: m.role, content: m.content })),
        },
      })

      messages.value.push({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      })
    } catch (e: any) {
      messages.value.push({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Sorry, an error occurred: ${e.message || 'Unknown error'}`,
        timestamp: new Date(),
      })
    } finally {
      isLoading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
  }

  return { messages, isLoading, sendMessage, clearMessages }
}
