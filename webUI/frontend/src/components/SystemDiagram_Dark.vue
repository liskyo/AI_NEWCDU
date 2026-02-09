<script setup>
import { computed } from 'vue'

const props = defineProps({
    data: { type: Object, default: () => ({}) },
    units: { type: Object, default: () => ({}) }
})

const getIconPath = (name) => {
    return `/img/diagram/${name}`
}

// Dynamic Style for Thermometers
const getIconStyle = (key, value) => {
    if (!key.toLowerCase().includes('temp') && !key.toLowerCase().includes('t5') && !key.toLowerCase().includes('t4')) return {}
    
    // Parse value
    const val = parseFloat(value)
    if (isNaN(val)) return {}

    // Color Logic: Blue < 20, Green 20-40, Red > 40
    if (val > 40) {
        return { filter: 'sepia(1) saturate(5) hue-rotate(-50deg)' } // Red-ish
    } else if (val < 20) {
        return { filter: 'sepia(1) saturate(5) hue-rotate(180deg)' } // Blue-ish
    } else {
        return { filter: 'sepia(1) saturate(2) hue-rotate(50deg)' } // Green-ish
    }
}

const sensors = [
    // === 1. Status & Tank (Top) ===
    // Tank1: Ls(Left), Ps(Top Right), Ts(Bottom Right) 
    // Coords adjusted: Ls(Up-Right), Ps(Right), Ts(Right)
    { key: 'level_tank', label: 'Ls', icon: 'icon_level.png', x: 32.4, y: 11, layout: 'row-val-icon', unit: '%' }, 
    { key: 'prsr_tank', label: 'Ps', icon: 'icon_pressure.png', x: 47.7, y: 9.9, layout: 'row-icon-val', unit: 'bar' },
    { key: 'temp_tank', label: 'Ts', icon: 'icon_temp.png', x: 47.2, y: 20.5, layout: 'row-icon-val', unit: '°C' },

    // Ambient (Top Far Right - Horizontal Label-Icon-Value)
    { key: 'dewPt', label: 'T Dp', icon: '露點溫度T_Dp.png', x: 86, y: 8, layout: 'row-label-icon-val', unit: '°C' },
    { key: 'rltHmd', label: 'RH', icon: '相對溼度RH.png', x: 86, y: 15, layout: 'row-label-icon-val', unit: '%' }, 
    { key: 'temp_ambient', label: 'Ta', icon: '溫度計T.png', x: 86, y: 22, layout: 'row-label-icon-val', unit: '°C' }, 

    // Water Quality (Top Right)
    { key: 'pH', label: 'PH', icon: 'PH值.png', x: 60, y: 22, unit: 'pH' },
    { key: 'cdct', label: 'CON', icon: '電導率CON.png', x: 66, y: 22, unit: 'µS' },
    { key: 'tbd', label: 'Tur', icon: '濁度Tur.png', x: 72, y: 22, unit: 'NRU' },

    // === 2. Facility Water (Left Side - Blue/Red Lines) ===
    // Supply (Blue Top)
    // T4 -> 60% Size (1.5cqw)
    { key: 'temp_waterIn', label: 'T4', icon: '設施水溫度T.png', x: 25, y: 48, sizeClass: 'w-[1.5cqw]', unit: '°C' },
    { key: 'WaterPV', label: 'PV1', icon: '比例閥PV.png', x:31, y: 48, unit: '%' },
    { key: 'prsr_wtrIn', label: 'P10', icon: '設施水水壓P.png', x: 37, y: 48, unit: 'bar' },

    // Return (Red Bottom)
    // T5 -> 60% Size (1.5cqw)
    { key: 'prsr_wtrOut', label: 'P11', icon: '設施水水壓P.png', x: 37, y: 76, unit: 'bar' },
    { key: 'temp_waterOut', label: 'T5', icon: '設施水溫度T.png', x: 31, y: 76, sizeClass: 'w-[1.5cqw]', unit: '°C' },
    { key: 'flow_wtr', label: 'F2', icon: '設施水流量F.png', x: 25, y: 76, unit: 'LPM' },

    // === 3. Coolant Loop (Right Side) ===
    // Supply Line (Blue)
    { key: 'flow_clnt', label: 'F1', icon: '冷卻液流量F.png', x: 49, y: 48, unit: 'LPM' },
    { key: 'prsr_fltIn', label: 'P3', icon: '冷卻液水壓P.png', x: 55, y: 48, unit: 'bar' }, // Before Loop

    // Filter Loop (Interior Sensors)
    { key: 'prsr_fltmax', label: 'P4~P8 Max', icon: '氣壓P.png', x: 63, y: 48, unit: 'bar' }, 
    // User Request: Font 50% (0.4cqw)
    { key: 'prsr_flt1Out', label: 'Filter(P3-[P4~8]Max)', icon: '氣壓P.png', x: 70, y: 48, labelSizeClass: 'text-[0.6cqw]', unit: 'bar' }, 

    // Main Output
    // T1 -> 60% Size (1.5cqw)
    { key: 'prsr_clntSply', label: 'P1', icon: '冷卻液水壓P.png', x: 79, y: 39, unit: 'bar' },
    { key: 'temp_clntSply', label: 'T1', icon: '冷卻液溫度T.png', x: 85, y: 39, sizeClass: 'w-[1.5cqw]', unit: '°C' },

    // Return Line (Red)
    // T2 -> 60% Size (1.5cqw)
    { key: 'prsr_clntRtn', label: 'P2', icon: '冷卻液水壓P.png', x: 74, y: 76, unit: 'bar' }, 
    { key: 'temp_clntRtn', label: 'T2', icon: '冷卻液溫度T.png', x: 84, y: 76, sizeClass: 'w-[1.5cqw]', unit: '°C' },

    // Pump Matrix (Bottom Right)
    // Top Row
    { key: 'ev4', label: 'EV4', icon: '電動閥.png', x: 56, y: 72 },
    { key: 'inv1_freq', label: 'PUMP1', icon: '泵浦P.png', x: 60, y: 72, unit: '%' },
    { key: 'ev3', label: 'EV3', icon: '電動閥.png', x: 64, y: 72 },

    // Bottom Row
    { key: 'ev2', label: 'EV2', icon: '電動閥.png', x: 56, y: 92 },
    { key: 'inv2_freq', label: 'PUMP2', icon: '泵浦P.png', x: 60, y: 92, unit: '%' },
    { key: 'ev1', label: 'EV1', icon: '電動閥.png', x: 64, y: 92 },
    { key: 'ev1', label: 'EV1', icon: '電動閥.png', x: 64, y: 92 },
]

const sections = [
    // Environment
    { label: 'Environment', x: 80, y: 3, w: 15, h: 26 },
    // Tank 1
    { label: 'Tank 1', x: 28, y: 5, w: 25, h: 22 },
    // Water Quality
    { label: 'Water Quality', x: 58, y: 15, w: 20, h: 15 },
]

const getValue = (key) => {
    // Custom Calculation for Pressure Drop
    if (key === 'prsr_flt1Out') {
        const p3 = props.data?.value?.prsr_fltIn
        const maxP = props.data?.value?.prsr_fltmax
        if (p3 !== undefined && maxP !== undefined && typeof p3 === 'number' && typeof maxP === 'number') {
            return (p3 - maxP).toFixed(1)
        }
        return '-'
    }

    const val = props.data?.value?.[key]
    if (val === undefined || val === null) return '-'
    if (typeof val === 'number') return val.toFixed(1)
    return val
}

const getStatusBox = computed(() => {
    const opMod = props.data?.value?.opMod || '-'
    const isError = props.data?.error?.PLC
    return {
        mode: opMod,
        title: props.data?.error?.PLC ? 'PLC : Error' : 'PLC : OK',
        statusColor: isError ? 'text-red-500' : 'text-green-400', 
        statusDot: isError ? 'text-red-500' : 'text-green-400',
        pcBox: 'Main'
    }
})
</script>

<template>
    <div class="relative w-full aspect-[2/1] bg-[#9e9e9e] rounded-xl shadow-lg border-[6px] border-gray-500 overflow-hidden select-none"
         style="container-type: inline-size;">
        
        <!-- === Background Image === -->
        <img :src="getIconPath('CDU底圖_灰.png')" class="absolute inset-0 w-full h-full object-contain mix-blend-normal" />

        <!-- === Status Info Box === -->
        <div class="absolute top-[2%] left-[2%] z-20 bg-black/40 rounded-[1cqw] p-[1cqw] shadow-md border border-gray-500 w-[22%] font-mono leading-tight backdrop-blur-sm">
             <div class="flex flex-col space-y-[0.5cqw]">
                <div class="font-bold text-white text-[1.1cqw]">PLC connection : <span :class="getStatusBox.statusColor" class="font-extrabold">{{ getStatusBox.title.split(': ')[1] }}</span></div>
                <div class="font-bold text-white text-[1.1cqw]">CDU Status : <span class="text-green-400">●</span></div>
                <div class="font-bold text-white text-[1.1cqw]">Operation Mode : <span class="text-yellow-300 font-bold bg-white/10 px-[0.5cqw] rounded border border-yellow-200/30">{{ getStatusBox.mode }}</span></div>
                <div class="font-bold text-white text-[1.1cqw]">PC Box : <span class="text-green-400 font-bold">{{ getStatusBox.pcBox }}</span></div>
             </div>
        </div>

        <!-- Grouping Sections (Background Boxes) -->
        <div v-for="sec in sections" :key="sec.label"
             class="absolute border-2 border-dashed border-gray-600 rounded-lg pointer-events-none z-0"
             :class="sec.class"
             :style="{ left: sec.x + '%', top: sec.y + '%', width: sec.w + '%', height: sec.h + '%' }">
             <div class="absolute -top-[1.2cqw] left-2 text-[0.9cqw] font-bold text-gray-500 bg-[#9e9e9e] px-1 uppercase tracking-wider">
                {{ sec.label }}
             </div>
        </div>

        <!-- === Dynamic SVG Overlay (New) === -->
        <svg class="absolute inset-0 w-full h-full pointer-events-none z-5" style="overflow: visible;">
            <defs>
                <linearGradient id="waterGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.8" />
                    <stop offset="100%" stop-color="#1d4ed8" stop-opacity="0.9" />
                </linearGradient>
            </defs>
            
            <!-- 1. Tank Water Level Animation -->
            <!-- Located at Tank 1 Section: x=28%, y=5%, w=25%, h=22% -->
            <!-- Approximated inner tank area -->
            <rect x="30%" :y="`${25 - (getValue('level_tank') > 0 ? getValue('level_tank') * 0.18 : 0)}%`" 
                  width="8%" :height="`${getValue('level_tank') > 0 ? getValue('level_tank') * 0.18 : 0}%`" 
                  fill="url(#waterGradient)" rx="4"
                  class="transition-all duration-1000 ease-in-out" />

            <!-- 2. Dynamic Pipes Flow Animation -->
            <!-- Only show if Flow > 5 LPM -->
            <g v-if="getValue('flow_clnt') > 5 || getValue('inv1_freq') > 10" class="pipe-flow">
                <!-- Supply Line (Blue) Path: Pump -> Output -->
                <path d="M 60 72 L 60 48 L 85 48" fill="none" stroke="#3b82f6" stroke-width="0.5cqw" stroke-dasharray="1 1" class="animate-flow" />
                
                <!-- Return Line (Red) Path: Input -> Tank -->
                <path d="M 85 76 L 74 76 L 74 90 L 40 90 L 40 25" fill="none" stroke="#ef4444" stroke-width="0.5cqw" stroke-dasharray="1 1" class="animate-flow-reverse" />
            </g>
        </svg>

        <!-- Icons Overlay -->
         <div v-for="s in sensors" :key="s.key" 
             class="absolute flex flex-col items-center transform -translate-x-1/2 -translate-y-1/2 group z-10"
             :style="{ left: s.x + '%', top: s.y + '%' }">
            
            <!-- Link Template to Units with Light Text Color for Dark Mode? No, this is Dark Mode file -->
            
            <!-- Standard (Icon Top, Value Bottom) -->
            <div v-if="!s.layout" class="mt-[0.2cqw] text-center bg-black/50 px-[0.4cqw] rounded backdrop-blur-[2px]">
                 <!-- Label -->
                 <div class="text-[0.7cqw] font-bold text-gray-200 whitespace-nowrap leading-none mb-[0.1cqw]">
                    {{ s.label }}
                 </div>
                 <!-- Value Box -->
                 <div class="text-[0.9cqw] font-mono font-bold text-white bg-white/10 px-[0.3cqw] py-[0.1cqw] rounded border border-white/20 shadow-sm min-w-[2.5cqw] text-center backdrop-blur-sm">
                    {{ getValue(s.key) }} <span v-if="s.unit" class="text-[0.7em] text-gray-400">{{ s.unit }}</span>
                 </div>
            </div>

            <!-- Row: Label - Icon - Value (Horizontal) -->
            <div v-else-if="s.layout === 'row-label-icon-val'" class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center space-x-[0.4cqw]">
                 <span class="text-[0.8cqw] font-bold text-white whitespace-nowrap drop-shadow-md">{{ s.label }}</span>
                 <img :src="getIconPath(s.icon)" 
                      :style="getIconStyle(s.key, getValue(s.key))"
                      class="w-[2cqw] mix-blend-normal transition-all duration-500" />
                 <span class="text-[0.9cqw] font-mono font-bold text-yellow-300 bg-black/60 px-[0.3cqw] rounded border border-white/10">
                    {{ getValue(s.key) }} <span v-if="s.unit" class="text-[0.7em] text-yellow-500">{{ s.unit }}</span>
                 </span>
            </div>

             <!-- Row: Val - Icon -->
             <div v-else-if="s.layout === 'row-val-icon'" class="absolute right-[60%] flex items-center space-x-[0.3cqw]">
                 <div class="text-[0.9cqw] font-mono font-bold text-white bg-black/50 px-[0.3cqw] rounded border border-white/20 whitespace-nowrap">
                    {{ getValue(s.key) }} <span v-if="s.unit" class="text-[0.7em] text-gray-400">{{ s.unit }}</span>
                 </div>
                 <div class="relative flex flex-col items-center">
                    <img :src="getIconPath(s.icon)" 
                         :style="getIconStyle(s.key, getValue(s.key))"
                         class="w-[2.5cqw] text-white relative z-10 mix-blend-normal transition-all duration-500" />
                    <div class="absolute -bottom-[0.8cqw] text-[0.7cqw] font-bold text-white whitespace-nowrap drop-shadow-md">{{ s.label }}</div>
                 </div>
            </div>

             <!-- Row: Icon - Val -->
            <div v-else-if="s.layout === 'row-icon-val'" class="absolute left-[60%] flex items-center space-x-[0.3cqw]">
                 <div class="relative flex flex-col items-center">
                    <img :src="getIconPath(s.icon)" 
                         :style="getIconStyle(s.key, getValue(s.key))"
                         class="w-[2.5cqw] text-white relative z-10 mix-blend-normal transition-all duration-500" />
                    <div class="absolute -bottom-[0.8cqw] text-[0.7cqw] font-bold text-white whitespace-nowrap drop-shadow-md">{{ s.label }}</div>
                 </div>
                 <div class="text-[0.9cqw] font-mono font-bold text-white bg-black/50 px-[0.3cqw] rounded border border-white/20 whitespace-nowrap">
                    {{ getValue(s.key) }} <span v-if="s.unit" class="text-[0.7em] text-gray-400">{{ s.unit }}</span>
                 </div>
            </div>

         </div>
    </div>
</template>

<style scoped>
.animate-flow {
    animation: dash 1s linear infinite;
}
.animate-flow-reverse {
    animation: dash 1s linear infinite reverse;
}

@keyframes dash {
    to {
        stroke-dashoffset: -2;
    }
}
</style>
