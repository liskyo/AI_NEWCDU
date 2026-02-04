<template>
    <div class="flex justify-between items-center group hover:bg-white/5 p-1 rounded transition-colors cursor-default" :class="$attrs.class">
        <span class="text-gray-400 text-sm group-hover:text-gray-300 transition-colors">{{ label }}</span>
        <span class="font-mono font-bold transition-all" :class="color || 'text-cyan-300'">
            {{ formattedValue }} <span class="text-[10px] opacity-70">{{ unit }}</span>
        </span>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    label: String,
    value: [Number, String, Boolean],
    unit: String,
    color: String
})

const formattedValue = computed(() => {
    if (props.value === undefined || props.value === null) return '--'
    if (typeof props.value === 'number') return props.value.toFixed(1)
    return props.value
})
</script>
