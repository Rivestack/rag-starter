<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Moon, Sun, Monitor, Check } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

type Theme = 'system' | 'light' | 'dark'

const theme = ref<Theme>('system')
const systemDark = ref(false)
let mediaQuery: MediaQueryList | null = null

function getEffectiveDark(): boolean {
  if (theme.value === 'dark') return true
  if (theme.value === 'light') return false
  return systemDark.value
}

function applyTheme() {
  const dark = getEffectiveDark()
  if (dark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

function setTheme(value: Theme) {
  theme.value = value
  localStorage.setItem('theme', value)
  applyTheme()
}

function handleSystemChange(e: MediaQueryListEvent) {
  systemDark.value = e.matches
  if (theme.value === 'system') applyTheme()
}

onMounted(() => {
  const stored = localStorage.getItem('theme') as Theme | null
  if (stored === 'dark' || stored === 'light' || stored === 'system') {
    theme.value = stored
  }
  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  systemDark.value = mediaQuery.matches
  mediaQuery.addEventListener('change', handleSystemChange)
  applyTheme()
})

onUnmounted(() => {
  mediaQuery?.removeEventListener('change', handleSystemChange)
})

watch(theme, () => applyTheme())

function triggerIcon() {
  if (theme.value === 'system') {
    return systemDark.value ? Moon : Sun
  }
  return theme.value === 'dark' ? Moon : Sun
}
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="ghost" size="icon" title="Theme">
        <component :is="triggerIcon()" class="h-5 w-5" />
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end">
      <DropdownMenuItem @click="setTheme('light')" class="cursor-pointer">
        <Sun class="mr-2 h-4 w-4" />
        Light
        <Check v-if="theme === 'light'" class="ml-auto h-4 w-4" />
      </DropdownMenuItem>
      <DropdownMenuItem @click="setTheme('dark')" class="cursor-pointer">
        <Moon class="mr-2 h-4 w-4" />
        Dark
        <Check v-if="theme === 'dark'" class="ml-auto h-4 w-4" />
      </DropdownMenuItem>
      <DropdownMenuItem @click="setTheme('system')" class="cursor-pointer">
        <Monitor class="mr-2 h-4 w-4" />
        System
        <Check v-if="theme === 'system'" class="ml-auto h-4 w-4" />
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
