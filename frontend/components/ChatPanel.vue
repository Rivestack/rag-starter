<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { Send, Loader2, MessageSquare } from 'lucide-vue-next'
import type { ChatMessage, SourceChunk } from '~/types'

const props = defineProps<{
  messages: ChatMessage[]
  isLoading: boolean
  activeSourceId: string | null
  documentName: string
}>()

const emit = defineEmits<{
  sendMessage: [message: string]
  sourceClick: [source: SourceChunk]
}>()

const inputText = ref('')
const messagesContainer = ref<HTMLElement>()
const inputRef = ref<HTMLTextAreaElement>()

function send() {
  const text = inputText.value.trim()
  if (!text || props.isLoading) return
  emit('sendMessage', text)
  inputText.value = ''
  nextTick(() => {
    if (inputRef.value) inputRef.value.style.height = 'auto'
  })
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function autoResize(e: Event) {
  const target = e.target as HTMLTextAreaElement
  target.style.height = 'auto'
  target.style.height = Math.min(target.scrollHeight, 120) + 'px'
}

// Scroll to bottom when new messages arrive
watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  },
)
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Messages -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto">
      <!-- Empty state -->
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full p-8 text-center">
        <div class="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
          <MessageSquare class="w-7 h-7 text-primary" />
        </div>
        <h3 class="text-lg font-medium mb-1">Ask about your PDF</h3>
        <p class="text-sm text-muted-foreground max-w-[280px]">
          Ask any question about <strong>{{ documentName }}</strong> and get answers with highlighted sources.
        </p>
        <div class="flex flex-col gap-2 mt-6 w-full max-w-[280px]">
          <button
            class="text-left text-sm px-3 py-2 rounded-lg border hover:bg-muted transition-colors"
            @click="emit('sendMessage', 'What is this document about?')"
          >
            What is this document about?
          </button>
          <button
            class="text-left text-sm px-3 py-2 rounded-lg border hover:bg-muted transition-colors"
            @click="emit('sendMessage', 'Summarize the key points')"
          >
            Summarize the key points
          </button>
        </div>
      </div>

      <!-- Message list -->
      <div v-else class="divide-y">
        <ChatMessage
          v-for="msg in messages"
          :key="msg.id"
          :message="msg"
          :active-source-id="activeSourceId"
          @source-click="(s) => emit('sourceClick', s)"
        />

        <!-- Loading indicator -->
        <div v-if="isLoading" class="flex gap-3 px-4 py-3 bg-muted/40">
          <div class="w-7 h-7 rounded-full bg-secondary flex items-center justify-center shrink-0">
            <Loader2 class="w-3.5 h-3.5 animate-spin" />
          </div>
          <div class="flex items-center">
            <span class="text-sm text-muted-foreground">Thinking...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="border-t p-3 bg-white">
      <div class="flex items-end gap-2">
        <textarea
          ref="inputRef"
          v-model="inputText"
          placeholder="Ask a question about this PDF..."
          class="flex-1 resize-none rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[40px] max-h-[120px]"
          rows="1"
          @keydown="handleKeydown"
          @input="autoResize"
        />
        <Button
          size="icon"
          :disabled="!inputText.trim() || isLoading"
          @click="send"
        >
          <Send class="w-4 h-4" />
        </Button>
      </div>
    </div>
  </div>
</template>
