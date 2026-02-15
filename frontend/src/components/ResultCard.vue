<script setup lang="ts">
import { ExternalLink, MessageSquare, User, ArrowUp, Calendar } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import type { SearchResultItem } from '@/types'

defineProps<{
  result: SearchResultItem
}>()

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function chunkLabel(type: string) {
  if (type === 'title') return 'Title'
  if (type === 'story_text') return 'Post'
  return 'Comment'
}

function truncate(text: string, max: number) {
  if (text.length <= max) return text
  return text.slice(0, max) + '...'
}
</script>

<template>
  <Card class="transition-shadow hover:shadow-md">
    <CardHeader class="pb-3">
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1 min-w-0">
          <a
            :href="result.story_hn_url"
            target="_blank"
            class="text-sm font-semibold leading-snug hover:text-primary transition-colors line-clamp-2"
          >
            {{ result.story_title }}
          </a>
          <div class="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
            <span class="flex items-center gap-1">
              <User class="h-3 w-3" />
              {{ result.story_author }}
            </span>
            <span class="flex items-center gap-1">
              <ArrowUp class="h-3 w-3" />
              {{ result.story_score }}
            </span>
            <span class="flex items-center gap-1">
              <Calendar class="h-3 w-3" />
              {{ formatDate(result.story_date) }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-1.5 shrink-0">
          <Badge variant="secondary" class="text-[10px]">
            {{ chunkLabel(result.chunk_type) }}
          </Badge>
          <Badge variant="outline" class="text-[10px] tabular-nums">
            {{ (result.similarity_score * 100).toFixed(0) }}%
          </Badge>
        </div>
      </div>
    </CardHeader>
    <CardContent class="pt-0">
      <p class="text-sm text-muted-foreground leading-relaxed">
        <template v-if="result.chunk_type === 'comment' && result.comment_author">
          <span class="font-medium text-foreground">{{ result.comment_author }}:</span>
          {{ ' ' }}
        </template>
        {{ truncate(result.matched_content, 300) }}
      </p>
      <div class="flex items-center gap-2 mt-3" v-if="result.story_url">
        <a
          :href="result.story_url"
          target="_blank"
          class="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          <ExternalLink class="h-3 w-3" />
          {{ new URL(result.story_url).hostname }}
        </a>
      </div>
    </CardContent>
  </Card>
</template>
