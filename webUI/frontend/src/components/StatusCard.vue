<template>
    <div class="bg-gray-900/50 p-2 rounded border transition-all duration-300 flex flex-col items-center justify-center text-center h-16"
         :class="active ? 'border-cyan-500/50 bg-cyan-900/20 shadow-[0_0_10px_rgba(6,182,212,0.1)]' : 'border-gray-700 opacity-60'">
        <div class="text-[10px] text-gray-500 uppercase">{{ label }}</div>
        <div class="w-2 h-2 rounded-full mt-1 mb-1" :class="active ? 'bg-cyan-400 shadow-[0_0_5px_cyan] animate-pulse' : 'bg-gray-600'"></div>
        <div v-if="value" class="text-xs font-mono font-bold text-white">{{ value }}</div>
    </div>
</template>

<script setup>
defineProps({
    label: String,
    active: Boolean,
    value: String,
    sub: String
})
</script>
