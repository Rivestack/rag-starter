<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { ExternalLink, User, ArrowUp, Calendar, MessageSquare, Zap } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import SearchBox from '@/components/SearchBox.vue'
import type { StoryDetail, RelatedStory } from '@/types'

const API_BASE = (window as any).env?.VITE_API_BASE || import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const route = useRoute()
const story = ref<StoryDetail | null>(null)
const related = ref<RelatedStory[]>([])
const relatedTimeMs = ref(0)
const chunksSearched = ref(0)
const isLoading = ref(true)
const notFound = ref(false)
const searchQuery = ref('')

const slug = computed(() => route.params.slug as string)
const hnUrl = computed(() => story.value ? `https://news.ycombinator.com/item?id=${story.value.hn_id}` : '')
const comments = computed(() => story.value?.chunks.filter(c => c.chunk_type === 'comment') ?? [])
const storyTextChunk = computed(() => story.value?.chunks.find(c => c.chunk_type === 'story_text'))

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
}

function hostname(url: string) {
  try { return new globalThis.URL(url).hostname } catch { return url }
}

function decodeHtml(text: string) {
  const el = document.createElement('textarea')
  el.innerHTML = text
  return el.value
}

async function fetchStory() {
  isLoading.value = true
  notFound.value = false

  try {
    const storyRes = await fetch(`${API_BASE}/api/stories/${slug.value}`)
    if (!storyRes.ok) {
      notFound.value = true
      return
    }
    story.value = await storyRes.json()
    document.title = `${story.value!.title} — Ask HN | Rivestack`
  } catch {
    notFound.value = true
  } finally {
    isLoading.value = false
  }

  // Fetch related stories independently — never block page render
  try {
    const relatedRes = await fetch(`${API_BASE}/api/stories/${slug.value}/related`)
    if (relatedRes.ok) {
      const data = await relatedRes.json()
      related.value = data.results ?? []
      relatedTimeMs.value = data.query_time_ms ?? 0
      chunksSearched.value = data.chunks_searched ?? 0
    }
  } catch {
    related.value = []
  }
}

function handleSearch() {
  const q = searchQuery.value.trim()
  if (q) {
    window.location.href = `/?q=${encodeURIComponent(q)}`
  }
}

onMounted(fetchStory)
</script>

<template>
  <!-- Loading -->
  <div v-if="isLoading" class="w-full flex flex-col gap-4">
    <Skeleton class="h-8 w-3/4" />
    <Skeleton class="h-4 w-1/2" />
    <Skeleton class="h-32 w-full mt-4" />
    <Skeleton class="h-24 w-full" />
    <Skeleton class="h-24 w-full" />
  </div>

  <!-- Not Found -->
  <div v-else-if="notFound" class="flex flex-col items-center py-16 text-center">
    <p class="text-lg font-semibold">Story not found</p>
    <p class="text-sm text-muted-foreground mt-2">This story may have been removed or the URL is incorrect.</p>
    <RouterLink to="/" class="text-sm text-primary hover:underline mt-4">Back to search</RouterLink>
  </div>

  <!-- Story -->
  <article v-else-if="story" class="w-full">
    <!-- Story Header -->
    <header class="mb-6">
      <h1 class="text-2xl font-bold tracking-tight leading-snug">{{ story.title }}</h1>
      <div class="flex flex-wrap items-center gap-3 mt-3 text-sm text-muted-foreground">
        <span class="flex items-center gap-1">
          <User class="h-3.5 w-3.5" />
          {{ story.author }}
        </span>
        <span class="flex items-center gap-1">
          <ArrowUp class="h-3.5 w-3.5" />
          {{ story.score }} points
        </span>
        <span class="flex items-center gap-1">
          <MessageSquare class="h-3.5 w-3.5" />
          {{ story.num_comments }} comments
        </span>
        <span class="flex items-center gap-1">
          <Calendar class="h-3.5 w-3.5" />
          {{ formatDate(story.created_at) }}
        </span>
      </div>
      <div class="flex items-center gap-3 mt-3">
        <a
          v-if="story.url"
          :href="story.url"
          target="_blank"
          rel="noopener"
          class="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <ExternalLink class="h-3.5 w-3.5" />
          {{ hostname(story.url) }}
        </a>
        <a
          :href="hnUrl"
          target="_blank"
          rel="noopener"
          class="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          View on Hacker News
        </a>
      </div>
    </header>

    <!-- Story Text (Ask HN / Show HN) -->
    <Card v-if="storyTextChunk" class="mb-6">
      <CardContent class="pt-5">
        <p class="text-sm leading-relaxed whitespace-pre-line">{{ decodeHtml(storyTextChunk.content) }}</p>
      </CardContent>
    </Card>

    <!-- Discussion Highlights -->
    <section v-if="comments.length > 0" class="mb-8">
      <h2 class="text-lg font-semibold mb-3">Discussion Highlights</h2>
      <div class="flex flex-col gap-0 divide-y">
        <div v-for="(chunk, i) in comments" :key="i" class="py-3 first:pt-0">
          <p v-if="chunk.author" class="text-xs font-medium text-muted-foreground mb-1">{{ chunk.author }}</p>
          <p class="text-sm leading-relaxed text-foreground">{{ decodeHtml(chunk.content) }}</p>
        </div>
      </div>
    </section>

    <!-- Related Stories -->
    <section v-if="related.length > 0" class="mb-8">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-lg font-semibold">Related Discussions</h2>
        <Badge v-if="relatedTimeMs > 0" variant="secondary" class="text-[10px] tabular-nums gap-1">
          <Zap class="h-3 w-3" />
          {{ relatedTimeMs.toFixed(0) }}ms across {{ chunksSearched.toLocaleString() }} embeddings
        </Badge>
      </div>
      <div class="flex flex-col gap-2">
        <RouterLink
          v-for="r in related"
          :key="r.slug"
          :to="{ name: 'story', params: { slug: r.slug } }"
          class="flex items-start justify-between gap-3 rounded-lg border p-3 hover:bg-accent transition-colors"
        >
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium leading-snug line-clamp-2">{{ r.title }}</p>
            <div class="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
              <span>{{ r.author }}</span>
              <span>{{ r.score }} pts</span>
              <span>{{ formatDate(r.created_at) }}</span>
            </div>
          </div>
          <Badge variant="outline" class="text-[10px] tabular-nums shrink-0">
            {{ (r.similarity_score * 100).toFixed(0) }}%
          </Badge>
        </RouterLink>
      </div>
    </section>

    <!-- Search Box -->
    <section class="border-t pt-6">
      <p class="text-sm text-muted-foreground mb-3">Find similar discussions</p>
      <SearchBox v-model="searchQuery" :is-searching="false" @search="handleSearch" />
    </section>

    <!-- Footer CTA -->
    <div class="text-center text-xs text-muted-foreground mt-8 pb-4">
      Semantic search powered by
      <a href="https://rivestack.io" target="_blank" class="font-semibold text-foreground hover:text-primary">Rivestack pgvector</a>
    </div>
  </article>
</template>
