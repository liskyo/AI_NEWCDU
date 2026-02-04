<script setup>
import axios from 'axios'
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ArrowPathIcon, PlayIcon, PauseIcon, PresentationChartLineIcon, BeakerIcon, SignalIcon } from '@heroicons/vue/24/solid'

// State
const isSimMode = ref(false) // Toggle between Real API and Local Sim
const isPaused = ref(false)
const updateInterval = ref(null)
const selectedMetric = ref('temp') // 'temp', 'pressure', 'flow'
const timeRange = ref('1h') // '1h', '24h' (simulated)

// Mock Data Storage
const historyData = ref([])
const maxPoints = 60

// Simulated Data Generator (Sine Wave for Test)
const generateNextPoint = () => {
    const now = new Date()
    const t = now.getTime()
    
    // Smooth Sine Waves for Sim Mode
    const baseTemp = 25 + Math.sin(t / 2000) * 5 // Faster oscillation
    const basePressure = 2.5 + Math.cos(t / 2000) * 1.0
    const baseFlow = 45 + Math.sin(t / 1500) * 10

    return {
        timestamp: t,
        timeLabel: now.toLocaleTimeString(),
        temp_in: baseTemp + (Math.random() - 0.5),
        temp_out: baseTemp + 5 + (Math.random() - 0.5),
        pressure_in: basePressure + (Math.random() * 0.1),
        pressure_out: basePressure - 0.5 + (Math.random() * 0.1),
        flow: baseFlow + (Math.random())
    }
}

// Real Data Fetcher
const fetchRealData = async () => {
    try {
        // Attempt to fetch from Engineer Mode endpoint or Status logic
        const response = await axios.get('/get_data_engineerMode') // Using standard endpoint
        const val = response.data?.value || {}
        
        // Map backend keys to our chart keys
        // Assuming keys: temp_clntSply(T1), temp_clntRtn(T2), etc.
        // Fallback to 0 if undefined to prevent NaN
        return {
            timestamp: new Date().getTime(),
            timeLabel: new Date().toLocaleTimeString(),
            temp_in: val.temp_clntSply || 0,
            temp_out: val.temp_clntRtn || 0,
            pressure_in: val.prsr_clntSply || 0,
            pressure_out: val.prsr_clntRtn || 0,
            flow: val.flow_clnt || 0
        }
    } catch (e) {
        console.warn("API Error, falling back to last point or zero")
        return {
             timestamp: new Date().getTime(),
             timeLabel: new Date().toLocaleTimeString(),
             temp_in: 0, temp_out: 0, pressure_in: 0, pressure_out: 0, flow: 0
        }
    }
}

// Initialize Mock History
// This function is no longer needed as history is reset on source toggle and populated by updateChart
// const initHistory = () => {
//     const data = []
//     const now = new Date().getTime()
//     for (let i = maxPoints; i >= 0; i--) {
//         const t = now - (i * 1000) // 1 sec interval for demo
//         data.push({
//             timestamp: t,
//             timeLabel: new Date(t).toLocaleTimeString(),
//             temp_in: 25 + Math.random(),
//             temp_out: 30 + Math.random(),
//             pressure_in: 2.5 + Math.random() * 0.1,
//             pressure_out: 2.0 + Math.random() * 0.1,
//             flow: 45 + Math.random() * 2
//         })
//     }
//     historyData.value = data
// }

// Chart Dimensions
const chartWidth = 800
const chartHeight = 300
const padding = 40

// Scale Calculation
const scale = computed(() => {
    if (historyData.value.length === 0) return { min: 0, max: 100, range: 100 }
    
    let key1, key2
    if (selectedMetric.value === 'temp') { key1 = 'temp_in'; key2 = 'temp_out' }
    else if (selectedMetric.value === 'pressure') { key1 = 'pressure_in'; key2 = 'pressure_out' }
    else { key1 = 'flow'; key2 = 'flow' }

    const values = historyData.value.flatMap(d => [d[key1], d[key2]])
    let min = Math.min(...values)
    let max = Math.max(...values)
    
    // Add padding to range
    const range = max - min || 1
    min = min - range * 0.1
    max = max + range * 0.1
    
    return { min, max, range: max - min }
})

// Computed Paths
const getPath = (key) => {
    if (historyData.value.length < 2) return ''
    const { min, range } = scale.value

    const points = historyData.value.map((d, i) => {
        const x = padding + (i / (maxPoints)) * (chartWidth - 2 * padding)
        const y = chartHeight - padding - ((d[key] - min) / range) * (chartHeight - 2 * padding)
        return `${x},${y}`
    }).join(' ')

    return points
}

// Ticks
const yTicks = computed(() => {
    const { min, range } = scale.value
    const ticks = []
    const count = 5
    for (let i = 0; i <= count; i++) {
        const value = min + (range * i) / count
        const y = chartHeight - padding - (i / count) * (chartHeight - 2 * padding)
        ticks.push({ y, value: value.toFixed(1) })
    }
    return ticks
})

// Actions
const setMetric = (metric) => {
    selectedMetric.value = metric
}

const updateChart = async () => {
    let newPoint
    if (isSimMode.value) {
        newPoint = generateNextPoint()
    } else {
        newPoint = await fetchRealData()
    }
    
    historyData.value.push(newPoint)
    if (historyData.value.length > maxPoints) {
        historyData.value.shift()
    }
}

const toggleSource = () => {
    isSimMode.value = !isSimMode.value
    // Reset history when switching modes to avoid jumpy graphs
    historyData.value = [] 
}

const togglePause = () => {
    isPaused.value = !isPaused.value
}

const startUpdates = () => {
    if (updateInterval.value) clearInterval(updateInterval.value)
    updateInterval.value = setInterval(() => {
        if (!isPaused.value) updateChart()
    }, 1000)
}

const stopUpdates = () => {
    if (updateInterval.value) clearInterval(updateInterval.value)
}

onMounted(() => {
    // initHistory() // Removed as history is now dynamically populated
    startUpdates()
})

onUnmounted(() => {
    stopUpdates()
})
</script>

<template>
    <div class="min-h-screen bg-gray-900 text-cyan-400 p-6 font-mono pb-20 overflow-hidden relative">
         <!-- Background Grid -->
         <div class="fixed inset-0 bg-[linear-gradient(rgba(17,24,39,0.9),rgba(17,24,39,0.9)),url('/grid.png')] pointer-events-none opacity-20 z-0"></div>

         <div class="relative z-10 max-w-6xl mx-auto">
             <!-- Header -->
            <header class="relative z-50 flex justify-between items-center mb-8 border-b border-cyan-800 pb-4">
               <!-- ... Header content remains same ... -->
               <div>
                    <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 flex items-center">
                        <PresentationChartLineIcon class="w-8 h-8 mr-3" />
                         TREND ANALYSIS
                    </h1>
                     <p class="text-xs text-gray-400 mt-1 uppercase tracking-widest">Historical Data Visualization System</p>
                </div>
                
                <div class="flex items-center space-x-4">
                     <!-- Metric Selector -->
                    <div class="flex bg-gray-800 rounded p-1 border border-gray-700 shadow-lg relative z-50">
                        <button type="button" @click="setMetric('temp')" :class="selectedMetric === 'temp' ? 'bg-cyan-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-gray-700'" class="px-4 py-1.5 rounded text-xs font-bold uppercase transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/50">Temperature</button>
                        <button type="button" @click="setMetric('pressure')" :class="selectedMetric === 'pressure' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-gray-700'" class="px-4 py-1.5 rounded text-xs font-bold uppercase transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50">Pressure</button>
                        <button type="button" @click="setMetric('flow')" :class="selectedMetric === 'flow' ? 'bg-green-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-gray-700'" class="px-4 py-1.5 rounded text-xs font-bold uppercase transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-green-500/50">Flow</button>
                    </div>

                    <!-- Controls -->
                    <div class="flex items-center space-x-3">
                         <!-- Source Toggle -->
                        <button type="button" @click="toggleSource" 
                                :class="isSimMode ? 'border-yellow-500 text-yellow-500 bg-yellow-900/10' : 'border-green-500 text-green-500 bg-green-900/10'"
                                class="flex items-center px-4 py-2 border rounded text-xs font-bold uppercase tracking-wider transition-all hover:bg-gray-800 z-50 relative">
                            <component :is="isSimMode ? BeakerIcon : SignalIcon" class="w-4 h-4 mr-2" />
                            {{ isSimMode ? 'TEST SIM' : 'LIVE DATA' }}
                        </button>

                         <!-- Pause Toggle -->
                        <button type="button" @click="togglePause" 
                                :class="isPaused ? 'border-gray-500 text-gray-500' : 'border-cyan-500 text-cyan-400 bg-cyan-900/10'"
                                class="flex items-center px-4 py-2 border rounded text-xs font-bold uppercase tracking-wider transition-all hover:bg-gray-800 z-50 relative">
                            <component :is="isPaused ? PlayIcon : PauseIcon" class="w-4 h-4 mr-2" />
                            {{ isPaused ? 'RESUME' : 'RUNNING' }}
                        </button>
                    </div>
                </div>
            </header>

            <!-- Chart Container -->
            <div class="bg-gray-800/50 border border-gray-700 rounded-lg p-6 backdrop-blur-sm shadow-xl relative overflow-hidden">
                <!-- SVG Chart -->
                 <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="w-full h-auto drop-shadow-[0_0_10px_rgba(6,182,212,0.3)]">
                    
                    <!-- Grid Lines & Ticks -->
                    <g v-for="(tick, i) in yTicks" :key="i">
                         <line 
                              :x1="padding" :y1="tick.y"
                              :x2="chartWidth - padding" :y2="tick.y"
                              stroke="#374151" stroke-width="1" stroke-dasharray="4" />
                         <text :x="padding - 10" :y="tick.y + 4" 
                               fill="#9CA3AF" text-anchor="end" font-size="10" font-family="monospace">
                             {{ tick.value }}
                         </text>
                    </g>

                    <!-- Axes -->
                    <line :x1="padding" :y1="chartHeight - padding" :x2="chartWidth - padding" :y2="chartHeight - padding" stroke="#9CA3AF" stroke-width="2" />
                    <line :x1="padding" :y1="padding" :x2="padding" :y2="chartHeight - padding" stroke="#9CA3AF" stroke-width="2" />

                    <!-- Paths -->
                    <template v-if="selectedMetric === 'temp'">
                         <!-- Temp In -->
                        <polyline :points="getPath('temp_in')" fill="none" stroke="#22d3ee" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="transition-all duration-300" />
                         <!-- Temp Out -->
                        <polyline :points="getPath('temp_out')" fill="none" stroke="#f472b6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="transition-all duration-300" />
                    </template>
                    
                     <template v-if="selectedMetric === 'pressure'">
                         <!-- Pressure In -->
                        <polyline :points="getPath('pressure_in')" fill="none" stroke="#60a5fa" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
                         <!-- Pressure Out -->
                        <polyline :points="getPath('pressure_out')" fill="none" stroke="#818cf8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
                    </template>

                     <template v-if="selectedMetric === 'flow'">
                         <!-- Flow -->
                        <polyline :points="getPath('flow')" fill="none" stroke="#34d399" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
                    </template>

                </svg>

                <!-- Legend -->
                 <div class="absolute top-6 right-6 flex flex-col space-y-2 bg-gray-900/80 p-3 rounded border border-gray-700">
                     <template v-if="selectedMetric === 'temp'">
                        <div class="flex items-center text-xs text-cyan-400 font-bold"><span class="w-3 h-3 bg-cyan-400 rounded-full mr-2"></span> Supply Temp (T1)</div>
                        <div class="flex items-center text-xs text-pink-400 font-bold"><span class="w-3 h-3 bg-pink-400 rounded-full mr-2"></span> Return Temp (T2)</div>
                     </template>
                     <template v-if="selectedMetric === 'pressure'">
                        <div class="flex items-center text-xs text-blue-400 font-bold"><span class="w-3 h-3 bg-blue-400 rounded-full mr-2"></span> Supply Pressure (P1)</div>
                        <div class="flex items-center text-xs text-indigo-400 font-bold"><span class="w-3 h-3 bg-indigo-400 rounded-full mr-2"></span> Return Pressure (P2)</div>
                     </template>
                      <template v-if="selectedMetric === 'flow'">
                        <div class="flex items-center text-xs text-green-400 font-bold"><span class="w-3 h-3 bg-green-400 rounded-full mr-2"></span> Flow Rate (F1)</div>
                     </template>
                 </div>
            </div>

            <!-- Stats/Summary Below Chart -->
             <div class="grid grid-cols-3 gap-6 mt-6">
                <div class="bg-gray-800/50 p-4 rounded border border-gray-700">
                    <div class="text-xs text-gray-500 uppercase">Current Value</div>
                    <div class="text-2xl font-mono text-white mt-1">
                        {{ selectedMetric === 'temp' ? historyData[historyData.length-1]?.temp_in.toFixed(1) + ' °C' : (selectedMetric === 'pressure' ? historyData[historyData.length-1]?.pressure_in.toFixed(1) + ' bar' : historyData[historyData.length-1]?.flow.toFixed(1) + ' LPM') }}
                    </div>
                </div>
                 <div class="bg-gray-800/50 p-4 rounded border border-gray-700">
                    <div class="text-xs text-gray-500 uppercase">Peak (Last Hour)</div>
                    <div class="text-2xl font-mono text-yellow-400 mt-1">
                         --
                    </div>
                </div>
                 <div class="bg-gray-800/50 p-4 rounded border border-gray-700">
                    <div class="text-xs text-gray-500 uppercase">Average trend</div>
                     <div class="text-2xl font-mono text-green-400 mt-1 flex items-center">
                         <span class="mr-2">↗</span> Stable
                    </div>
                </div>
            </div>

         </div>
    </div>
</template>
