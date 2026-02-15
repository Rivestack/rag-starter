<script setup lang="ts">
import { cn } from '~/lib/utils'
</script>

<template>
  <div :class="cn('rounded-xl border bg-card text-card-foreground shadow', $attrs.class as string)">
    <slot />
  </div>
</template>
