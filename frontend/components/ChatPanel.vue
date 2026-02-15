<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { Send, Loader2, MessageSquare, Sparkles } from 'lucide-vue-next'
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
  <div class="flex flex-col h-full bg-white">
    <!-- Header -->
    <div class="h-12 border-b flex items-center px-4 gap-2 shrink-0">
      <MessageSquare class="w-4 h-4 text-primary" />
      <span class="text-sm font-semibold">Chat</span>
      <span class="text-xs text-muted-foreground truncate">{{ documentName }}</span>
    </div>

    <!-- Messages -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto">
      <!-- Empty state -->
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full p-8 text-center">
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/10 to-purple-100 flex items-center justify-center mb-5">
          <Sparkles class="w-7 h-7 text-primary" />
        </div>
        <h3 class="text-lg font-semibold mb-1">Ask about your PDF</h3>
        <p class="text-sm text-muted-foreground max-w-[280px] mb-6">
          Get AI-powered answers with source highlights from <strong class="text-foreground">{{ documentName }}</strong>
        </p>
        <div class="flex flex-col gap-2 w-full max-w-[300px]">
          <button
            class="text-left text-sm px-4 py-2.5 rounded-xl border hover:bg-primary/5 hover:border-primary/20 hover:text-primary transition-all duration-200 font-medium"
            @click="emit('sendMessage', 'What is this document about?')"
          >
            What is this document about?
          </button>
          <button
            class="text-left text-sm px-4 py-2.5 rounded-xl border hover:bg-primary/5 hover:border-primary/20 hover:text-primary transition-all duration-200 font-medium"
            @click="emit('sendMessage', 'Summarize the key points')"
          >
            Summarize the key points
          </button>
          <button
            class="text-left text-sm px-4 py-2.5 rounded-xl border hover:bg-primary/5 hover:border-primary/20 hover:text-primary transition-all duration-200 font-medium"
            @click="emit('sendMessage', 'What are the main conclusions?')"
          >
            What are the main conclusions?
          </button>
        </div>
      </div>

      <!-- Message list -->
      <div v-else>
        <ChatMessage
          v-for="msg in messages"
          :key="msg.id"
          :message="msg"
          :active-source-id="activeSourceId"
          @source-click="(s) => emit('sourceClick', s)"
        />

        <!-- Loading indicator -->
        <div v-if="isLoading" class="flex gap-3 px-5 py-4">
          <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-primary/10 to-purple-100 flex items-center justify-center shrink-0">
            <Loader2 class="w-4 h-4 text-primary animate-spin" />
          </div>
          <div class="flex items-center">
            <div class="flex gap-1">
              <span class="w-2 h-2 rounded-full bg-primary/40 animate-bounce [animation-delay:0ms]" />
              <span class="w-2 h-2 rounded-full bg-primary/40 animate-bounce [animation-delay:150ms]" />
              <span class="w-2 h-2 rounded-full bg-primary/40 animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="border-t p-4">
      <div class="flex items-end gap-2">
        <textarea
          ref="inputRef"
          v-model="inputText"
          placeholder="Ask a question about this PDF..."
          class="flex-1 resize-none rounded-xl border bg-muted/30 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40 min-h-[44px] max-h-[120px] transition-all duration-200 placeholder:text-muted-foreground/60"
          rows="1"
          @keydown="handleKeydown"
          @input="autoResize"
        />
        <Button
          size="icon"
          :disabled="!inputText.trim() || isLoading"
          class="rounded-xl h-[44px] w-[44px] shadow-sm shadow-primary/25"
          @click="send"
        >
          <Send class="w-4 h-4" />
        </Button>
      </div>
    </div>
  </div>
</template>
