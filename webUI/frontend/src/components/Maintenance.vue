<script setup>
import { ref } from 'vue'
import { WrenchScrewdriverIcon, ArchiveBoxIcon, CheckBadgeIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/solid'

const parts = ref([
    { id: 1, name: 'Main Pump 1', type: 'pump', hours: 4520, maxHours: 10000, status: 'good' },
    { id: 2, name: 'Main Pump 2', type: 'pump', hours: 120, maxHours: 10000, status: 'good' },
    { id: 3, name: 'Fine Filter Cartridge', type: 'filter', hours: 680, maxHours: 1000, status: 'warning' },
    { id: 4, name: 'Coolant Fluid', type: 'fluid', hours: 4520, maxHours: 8000, status: 'good' },
    { id: 5, name: 'Solenoid Valve Set', type: 'valve', hours: 8500, maxHours: 20000, status: 'good' },
])

const logs = ref([
    { date: '2025-10-12', action: 'Filter Replacement', text: 'Replaced P3 filter cartridge.' },
    { date: '2025-08-01', action: 'System Check', text: 'Annual maintenance check passed.' },
])

const getHealthPercent = (current, max) => {
    return Math.max(0, 100 - (current / max) * 100)
}

const getStatusColor = (percent) => {
    if (percent > 50) return 'text-green-500 stroke-green-500'
    if (percent > 20) return 'text-yellow-500 stroke-yellow-500'
    return 'text-red-500 stroke-red-500'
}

const resetPart = (id) => {
    if(confirm('Confirm maintenance action complete? This will reset the counter.')) {
        const part = parts.value.find(p => p.id === id)
        if(part) {
            part.hours = 0
            alert(`${part.name} maintenance recorded.`)
        }
    }
}
</script>

<template>
    <div class="min-h-screen bg-gray-900 text-cyan-400 p-6 font-mono pb-20">
        <div class="fixed inset-0 bg-[linear-gradient(rgba(17,24,39,0.95),rgba(17,24,39,0.95)),url('/grid.png')] pointer-events-none opacity-20 z-0"></div>

        <div class="relative z-10 max-w-6xl mx-auto space-y-8">
            <!-- Header -->
             <header class="flex justify-between items-center border-b border-cyan-800 pb-4">
                 <div>
                    <h1 class="text-3xl font-bold tracking-wider flex items-center text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-500">
                        <WrenchScrewdriverIcon class="w-8 h-8 mr-3 text-orange-500" />
                        MAINTENANCE CENTER
                    </h1>
                    <p class="text-xs text-gray-400 mt-1 uppercase tracking-widest">Component Lifecycle & Health Monitoring</p>
                 </div>
                 <div class="bg-gray-800 border border-gray-700 px-4 py-2 rounded flex items-center space-x-2">
                     <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                     <span class="text-xs font-bold text-gray-300">SYSTEM HEALTHY</span>
                 </div>
             </header>

             <!-- Grid of Parts -->
             <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                 
                 <div v-for="part in parts" :key="part.id" class="bg-gray-800/40 border border-gray-700 hover:border-orange-500/50 transition-colors rounded-lg p-6 relative overflow-hidden group">
                     <!-- Background Progress Circle (Simple CSS Conic Gradient could be used, using SVG for control) -->
                     
                     <div class="flex justify-between items-start mb-4">
                         <div>
                             <h3 class="font-bold text-gray-200">{{ part.name }}</h3>
                             <p class="text-xs text-gray-500 uppercase">{{ part.type }}</p>
                         </div>
                         <div class="text-right">
                             <div class="text-2xl font-bold" :class="getStatusColor(getHealthPercent(part.hours, part.maxHours))">
                                 {{ getHealthPercent(part.hours, part.maxHours).toFixed(0) }}%
                             </div>
                             <div class="text-[10px] text-gray-500 uppercase">Health</div>
                         </div>
                     </div>

                     <!-- Bar -->
                     <div class="w-full bg-gray-900 rounded-full h-2 mb-4 overflow-hidden">
                         <div class="h-full transition-all duration-1000" 
                              :class="getStatusColor(getHealthPercent(part.hours, part.maxHours)).replace('text-', 'bg-').replace('stroke-', '')"
                              :style="{ width: getHealthPercent(part.hours, part.maxHours) + '%' }">
                         </div>
                     </div>

                     <div class="flex justify-between items-center text-xs text-gray-400 mb-6">
                         <span>Run: {{ part.hours }} hrs</span>
                         <span>Max: {{ part.maxHours }} hrs</span>
                     </div>

                     <button @click="resetPart(part.id)" class="w-full py-2 border border-gray-600 rounded text-xs font-bold uppercase hover:bg-orange-500 hover:text-white hover:border-orange-500 transition-all">
                         Record Maintenance
                     </button>
                    
                    <div v-if="getHealthPercent(part.hours, part.maxHours) < 30" class="absolute top-0 right-0 p-2">
                        <ExclamationTriangleIcon class="w-5 h-5 text-red-500 animate-bounce" />
                    </div>
                 </div>

             </div>

             <!-- Logs Section -->
             <div class="bg-gray-800/40 border border-gray-700 rounded-lg p-6">
                 <h2 class="text-xl font-bold text-gray-300 mb-4 flex items-center">
                     <ArchiveBoxIcon class="w-6 h-6 mr-2 text-gray-500" />
                     Service History
                 </h2>
                 <div class="space-y-2">
                     <div v-for="(log, idx) in logs" :key="idx" class="flex items-start space-x-4 p-3 bg-gray-900/50 rounded border border-gray-800 hover:border-gray-600 transition-colors">
                         <div class="text-xs text-cyan-500 font-mono whitespace-nowrap pt-0.5">{{ log.date }}</div>
                         <div>
                             <div class="text-sm font-bold text-gray-200">{{ log.action }}</div>
                             <div class="text-xs text-gray-500">{{ log.text }}</div>
                         </div>
                         <div class="ml-auto">
                             <CheckBadgeIcon class="w-5 h-5 text-green-800" />
                         </div>
                     </div>
                 </div>
             </div>

        </div>
    </div>
</template>
