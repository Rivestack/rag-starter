<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-vue-next'
import type { BboxRect } from '~/types'

const props = defineProps<{
  pdfUrl: string | null
  currentPage: number
  highlights: BboxRect[]
}>()

const emit = defineEmits<{
  'update:currentPage': [page: number]
  pagesLoaded: [count: number]
}>()

const pdfDoc = ref<any>(null)
const totalPages = ref(0)
const scale = ref(1.2)
const containerRef = ref<HTMLElement>()
const pageRefs = ref<Map<number, HTMLElement>>(new Map())
const canvasRefs = ref<Map<number, HTMLCanvasElement>>(new Map())
const isLoading = ref(false)

// Load PDF using pdfjs-dist directly
async function loadPdf(url: string) {
  isLoading.value = true
  try {
    const pdfjsLib = await import('pdfjs-dist')
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`

    const loadingTask = pdfjsLib.getDocument(url)
    pdfDoc.value = await loadingTask.promise
    totalPages.value = pdfDoc.value.numPages
    emit('pagesLoaded', totalPages.value)

    await nextTick()
    for (let i = 1; i <= totalPages.value; i++) {
      await renderPage(i)
    }
  } catch (e) {
    console.error('Failed to load PDF:', e)
  } finally {
    isLoading.value = false
  }
}

async function renderPage(pageNum: number) {
  if (!pdfDoc.value) return
  const page = await pdfDoc.value.getPage(pageNum)
  const viewport = page.getViewport({ scale: scale.value })

  const canvas = canvasRefs.value.get(pageNum)
  if (!canvas) return

  canvas.width = viewport.width
  canvas.height = viewport.height

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  await page.render({ canvasContext: ctx, viewport }).promise
}

// Scroll to page when currentPage changes
watch(
  () => props.currentPage,
  (page) => {
    const el = pageRefs.value.get(page)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  },
)

// Reload PDF when URL changes
watch(
  () => props.pdfUrl,
  (url) => {
    if (url) loadPdf(url)
  },
  { immediate: true },
)

// Re-render on scale change
watch(scale, async () => {
  if (!pdfDoc.value) return
  await nextTick()
  for (let i = 1; i <= totalPages.value; i++) {
    await renderPage(i)
  }
})

function getPageHighlights(pageNumber: number): BboxRect[] {
  return props.highlights.filter((h) => h.page === pageNumber)
}

function setPageRef(el: any, page: number) {
  if (el) pageRefs.value.set(page, el)
}

function setCanvasRef(el: any, page: number) {
  if (el) canvasRefs.value.set(page, el)
}

function prevPage() {
  if (props.currentPage > 1) emit('update:currentPage', props.currentPage - 1)
}

function nextPage() {
  if (props.currentPage < totalPages.value) emit('update:currentPage', props.currentPage + 1)
}
</script>

<template>
  <div class="flex flex-col h-full bg-muted/30">
    <!-- Toolbar -->
    <div class="h-10 border-b bg-white flex items-center justify-between px-3 shrink-0">
      <div class="flex items-center gap-1">
        <button class="p-1 rounded hover:bg-muted" @click="prevPage">
          <ChevronLeft class="w-4 h-4" />
        </button>
        <span class="text-xs text-muted-foreground min-w-[80px] text-center">
          {{ currentPage }} / {{ totalPages }}
        </span>
        <button class="p-1 rounded hover:bg-muted" @click="nextPage">
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>
      <div class="flex items-center gap-1">
        <button class="p-1 rounded hover:bg-muted" @click="scale = Math.max(0.5, scale - 0.2)">
          <ZoomOut class="w-4 h-4" />
        </button>
        <span class="text-xs text-muted-foreground min-w-[40px] text-center">
          {{ Math.round(scale * 100) }}%
        </span>
        <button class="p-1 rounded hover:bg-muted" @click="scale = Math.min(3, scale + 0.2)">
          <ZoomIn class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- PDF Pages -->
    <div ref="containerRef" class="flex-1 overflow-auto p-4">
      <div v-if="isLoading" class="flex items-center justify-center h-full">
        <div class="text-sm text-muted-foreground">Loading PDF...</div>
      </div>

      <div v-else class="flex flex-col items-center gap-4">
        <div
          v-for="page in totalPages"
          :key="page"
          :ref="(el: any) => setPageRef(el, page)"
          class="relative shadow-md bg-white"
        >
          <canvas :ref="(el: any) => setCanvasRef(el, page)" />

          <!-- Highlight overlay -->
          <div class="absolute inset-0 pointer-events-none">
            <div
              v-for="(bbox, idx) in getPageHighlights(page)"
              :key="idx"
              class="absolute rounded-sm bg-yellow-300/40 border border-yellow-400/50 animate-highlight-pulse"
              :style="{
                left: `${bbox.x0 * 100}%`,
                top: `${bbox.y0 * 100}%`,
                width: `${(bbox.x1 - bbox.x0) * 100}%`,
                height: `${(bbox.y1 - bbox.y0) * 100}%`,
              }"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
