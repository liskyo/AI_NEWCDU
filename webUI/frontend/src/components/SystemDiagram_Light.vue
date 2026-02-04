<script setup>
import { computed } from 'vue'

const props = defineProps({
    data: { type: Object, default: () => ({}) },
    units: { type: Object, default: () => ({}) }
})

const getIconPath = (name) => {
    return `/img/diagram/${name}`
}

const sensors = [
    // === 1. Status & Tank (Top) ===
    // Tank1: Ls(Left), Ps(Top Right), Ts(Bottom Right) 
    // Coords adjusted: Ls(Up-Right), Ps(Right), Ts(Right)
    { key: 'level_tank', label: 'Ls', icon: '冷卻液液位.png', x: 32.4, y: 11, layout: 'row-val-icon', unit: '%' }, 
    { key: 'prsr_tank', label: 'Ps', icon: '氣壓P.png', x: 47.7, y: 9.9, layout: 'row-icon-val', unit: 'bar' },
    { key: 'temp_tank', label: 'Ts', icon: '冷卻液溫度T.png', x: 47.2, y: 20.5, layout: 'row-icon-val', unit: '°C' },

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
        title: props.data?.error?.PLC ? 'PLC Connection : Error' : 'PLC connection : OK',
        statusColor: isError ? 'text-red-500' : 'text-green-600', 
        statusDot: isError ? 'text-red-500' : 'text-green-600',
        pcBox: 'Main'
    }
})
</script>

<template>
    <div class="relative w-full aspect-[2/1] bg-white rounded-xl shadow-lg border-[6px] border-gray-300 overflow-hidden select-none"
         style="container-type: inline-size;">
        
        <!-- === Background Image (CDU底圖.png) === -->
        <img :src="getIconPath('CDU底圖.png')" class="absolute inset-0 w-full h-full object-contain" />

        <!-- === Status Info Box === -->
        <div class="absolute top-[2%] left-[2%] z-20 bg-white/95 rounded-[1cqw] p-[1cqw] shadow-md border border-gray-300 w-[22%] font-mono leading-tight">
             <div class="flex flex-col space-y-[0.5cqw]">
                <div class="font-bold text-gray-700 text-[1.1cqw]">PLC connection : <span :class="getStatusBox.statusColor" class="font-extrabold">{{ getStatusBox.title.split(': ')[1] }}</span></div>
                <div class="font-bold text-gray-700 text-[1.1cqw]">CDU Status : <span class="text-green-600">●</span></div>
                <div class="font-bold text-gray-700 text-[1.1cqw]">Operation Mode : <span class="text-yellow-600 font-bold bg-yellow-50 px-[0.5cqw] rounded border border-yellow-200">{{ getStatusBox.mode }}</span></div>
                <div class="font-bold text-gray-700 text-[1.1cqw]">PC Box : <span class="text-green-700 font-bold">{{ getStatusBox.pcBox }}</span></div>
             </div>
        </div>


        <!-- Grouping Sections (Background Boxes) -->
        <div v-for="sec in sections" :key="sec.label"
             class="absolute border-2 border-dashed border-gray-300 rounded-lg pointer-events-none z-0"
             :class="sec.class"
             :style="{ left: sec.x + '%', top: sec.y + '%', width: sec.w + '%', height: sec.h + '%' }">
             <div class="absolute -top-[1.2cqw] left-2 text-[0.9cqw] font-bold text-gray-400 bg-white px-1 uppercase tracking-wider">
                {{ sec.label }}
             </div>
        </div>

        <!-- Icons Overlay -->
         <div v-for="s in sensors" :key="s.key" 
             class="absolute flex flex-col items-center transform -translate-x-1/2 -translate-y-1/2 group z-10"
             :style="{ left: s.x + '%', top: s.y + '%' }">
             
            <!-- === Standard Vertical Layout (Default) === -->
            <!-- Label -> Icon -> Value -->
            <template v-if="!s.layout || s.layout === 'vertical'">
                 <!-- Icon (Dynamic Size) -->
                 <div class="relative aspect-square flex items-center justify-center" 
                      :class="s.sizeClass || 'w-[2.5cqw]'">
                    <img :src="getIconPath(s.icon)" class="w-full h-full object-contain drop-shadow-sm transition-transform hover:scale-110" />
                </div>
                 <!-- Label (Dynamic Font Size) -->
                 <div class="absolute -top-[1cqw] font-bold text-gray-800 uppercase whitespace-nowrap drop-shadow-md" 
                      :class="s.labelSizeClass || 'text-[0.8cqw]'">{{ s.label }}</div>
                <div class="mt-[0.2cqw] px-[0.3cqw] py-[0.1cqw] bg-yellow-100 hover:bg-white border border-yellow-200 rounded-[0.3cqw] text-[1cqw] font-mono font-bold text-gray-800 min-w-[2.5cqw] text-center shadow-sm">
                     {{ getValue(s.key) }} <span v-if="s.unit" class="text-[0.7em] text-gray-600">{{ s.unit }}</span>
                </div>
            </template>

            <!-- === Ambient Layout: Label -> Icon -> Value === -->
            <template v-else-if="s.layout === 'row-label-icon-val'">
                <div class="flex items-center space-x-[0.5cqw] whitespace-nowrap">
                     <span class="text-[0.9cqw] font-bold text-gray-800 uppercase drop-shadow-sm text-right min-w-[2cqw]">{{ s.label }}</span>
                     <div class="relative w-[2.5cqw] aspect-square flex items-center justify-center">
                        <img :src="getIconPath(s.icon)" class="w-full h-full object-contain drop-shadow-sm transition-transform hover:scale-110" />
                    </div>
                    <div class="px-[0.3cqw] py-[0.1cqw] bg-yellow-100 hover:bg-white border border-yellow-200 rounded-[0.3cqw] text-[1cqw] font-mono font-bold text-gray-800 min-w-[3cqw] text-center shadow-sm">
                         {{ getValue(s.key) }} <span v-if="s.unit" class="text-[0.7em] text-gray-600">{{ s.unit }}</span>
                    </div>
                </div>
            </template>

            <!-- === Tank Ls Layout: Value -> Icon (With Label Below) === -->
            <template v-else-if="s.layout === 'row-val-icon'">
                <div class="flex items-center space-x-[0.3cqw] whitespace-nowrap">
                    <!-- Value (Left) -->
                    <div class="px-[0.3cqw] py-[0.1cqw] bg-yellow-100 hover:bg-white border border-yellow-200 rounded-[0.3cqw] text-[1cqw] font-mono font-bold text-gray-800 min-w-[3cqw] text-center shadow-sm">
                         {{ getValue(s.key) }} <span v-if="s.unit" class="text-[0.7em] text-gray-600">{{ s.unit }}</span>
                    </div>
                    <!-- Icon (Right) -->
                     <div class="relative w-[2.5cqw] aspect-square flex items-center justify-center">
                        <img :src="getIconPath(s.icon)" class="w-full h-full object-contain drop-shadow-sm transition-transform hover:scale-110" />
                        <!-- Label Below -->
                        <div class="absolute -bottom-[1cqw] text-[0.8cqw] font-bold text-gray-800 uppercase whitespace-nowrap drop-shadow-md">{{ s.label }}</div>
                    </div>
                </div>
            </template>

            <!-- === Tank Ps/Ts Layout: Icon -> Value (With Label Below) === -->
            <template v-else-if="s.layout === 'row-icon-val'">
                <div class="flex items-center space-x-[0.3cqw] whitespace-nowrap">
                    <!-- Icon (Left) -->
                     <div class="relative w-[2.5cqw] aspect-square flex items-center justify-center">
                        <img :src="getIconPath(s.icon)" class="w-full h-full object-contain drop-shadow-sm transition-transform hover:scale-110" />
                        <!-- Label Below -->
                        <div class="absolute -bottom-[1cqw] text-[0.8cqw] font-bold text-gray-800 uppercase whitespace-nowrap drop-shadow-md">{{ s.label }}</div>
                    </div>
                    <!-- Value (Right) -->
                    <div class="px-[0.3cqw] py-[0.1cqw] bg-yellow-100 hover:bg-white border border-yellow-200 rounded-[0.3cqw] text-[1cqw] font-mono font-bold text-gray-800 min-w-[3cqw] text-center shadow-sm">
                         {{ getValue(s.key) }} <span v-if="s.unit" class="text-[0.7em] text-gray-600">{{ s.unit }}</span>
                    </div>
                </div>
            </template>

        </div>
        
    </div>
</template>
