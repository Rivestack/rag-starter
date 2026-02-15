<script setup lang="ts">
interface Props {
  modelValue?: number
  max?: number
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 0,
  max: 100,
})

const percentage = computed(() => Math.min(100, Math.max(0, (props.modelValue / props.max) * 100)))
</script>

<template>
  <div class="relative h-2 w-full overflow-hidden rounded-full bg-primary/20">
    <div
      class="h-full bg-primary transition-all duration-500 ease-out rounded-full"
      :style="{ width: `${percentage}%` }"
    />
  </div>
</template>
