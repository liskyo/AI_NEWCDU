<template>
    <div class="min-h-screen bg-gray-900 text-cyan-400 p-6 font-mono selection:bg-cyan-900 selection:text-white relative overflow-y-auto pb-20">
        <!-- Background Grid Effect -->
        <div class="absolute inset-0 bg-[linear-gradient(rgba(17,24,39,0.9),rgba(17,24,39,0.9)),url('/grid.png')] pointer-events-none opacity-20"></div>

        <!-- Header -->
        <header class="relative z-10 mb-8 flex justify-between items-center border-b border-cyan-800 pb-4">
            <div>
                <h1 class="text-3xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">SYSTEM STATUS</h1>
                <p class="text-xs text-gray-400 mt-1 flex items-center">
                    <span class="w-2 h-2 rounded-full mr-2" :class="loading ? 'bg-yellow-500 animate-pulse' : (error ? 'bg-red-500' : 'bg-green-500')"></span>
                    {{ loading ? 'SYNCING...' : (error ? 'CONNECTION ERROR' : 'OPERATIONAL') }}
                </p>
            </div>
            <div class="flex items-center space-x-4">
                <button @click="toggleTestMode" 
                    :class="isTestMode ? 'text-yellow-400 border-yellow-400 bg-yellow-400/10' : 'text-gray-500 border-gray-600 hover:text-cyan-400 hover:border-cyan-400'"
                    class="px-3 py-1 border rounded text-xs transition-colors uppercase tracking-widest">
                    {{ isTestMode ? 'TEST MODE: ON' : 'LIVE DATA' }}
                </button>
            </div>
        </header>

        <!-- Error Banner -->
        <div v-if="error" class="relative z-10 mb-6 bg-red-900/20 border border-red-500/50 p-4 rounded text-red-400 flex items-center animate-pulse">
            <svg class="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            {{ error }}
        </div>

        <!-- Main Content -->
        <div class="relative z-10 space-y-6">

            <!-- Top Section: System Diagram -->
            <div class="w-full relative group">
                <!-- Tech Frame Borders -->
                <div class="absolute inset-0 border border-cyan-500/30 rounded-lg pointer-events-none"></div>
                <!-- Corner Accents -->
                <div class="absolute top-0 left-0 w-4 h-4 border-l-2 border-t-2 border-cyan-500 rounded-tl pointer-events-none"></div>
                <div class="absolute top-0 right-0 w-4 h-4 border-r-2 border-t-2 border-cyan-500 rounded-tr pointer-events-none"></div>
                <div class="absolute bottom-0 left-0 w-4 h-4 border-l-2 border-b-2 border-cyan-500 rounded-bl pointer-events-none"></div>
                <div class="absolute bottom-0 right-0 w-4 h-4 border-r-2 border-b-2 border-cyan-500 rounded-br pointer-events-none"></div>
                <!-- Glow Effect -->
                <div class="absolute -inset-[1px] bg-gradient-to-r from-cyan-500/10 via-transparent to-cyan-500/10 rounded-lg blur-sm opacity-50 pointer-events-none"></div>
                
                <div class="bg-gray-900/80 border border-gray-800 rounded-lg p-2 backdrop-blur-md overflow-hidden relative min-h-[400px] lg:min-h-[600px] flex items-center justify-center shadow-[inset_0_0_20px_rgba(0,0,0,0.5)]">
                    <!-- Grid Background -->
                    <div class="absolute inset-0 bg-[linear-gradient(rgba(6,182,212,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(6,182,212,0.03)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none"></div>
                    
                    <!-- Diagram Component -->
                    <SystemDiagram 
                        v-if="sensorData" 
                        :data="sensorData" 
                        class="w-full h-full relative z-10" 
                    />
                    <div v-else class="text-center relative z-10">
                        <div class="w-16 h-16 border-4 border-t-cyan-500 border-gray-700 rounded-full animate-spin mx-auto mb-4"></div>
                        <p class="text-gray-500 text-sm animate-pulse">LOADING SCHEMATICS...</p>
                    </div>
                </div>
            </div>
            
            <!-- Bottom Section: Metrics Grid -->
            <!-- Expanded Grid to 4 columns to fit more data, or dense 3 columns -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                
                <!-- Column 1: Operation & Power & Levels -->
                <div class="space-y-4">
                    <!-- Operation Status Card -->
                    <div class="relative bg-gray-900/60 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-sm overflow-hidden group hover:border-cyan-500/60 transition-colors">
                         <div class="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent"></div>
                         <h3 class="text-xs text-gray-400 uppercase tracking-widest mb-2 flex items-center">
                            <span class="w-1 h-3 bg-cyan-500 mr-2 rounded-sm"></span>
                            System Status
                         </h3>
                         <div class="text-4xl font-bold text-white tracking-widest font-mono mb-4">
                             {{ sensorData?.value?.opMod || '---' }}
                         </div>
                         <div class="space-y-2 text-xs">
                             <div class="flex justify-between items-center bg-black/40 p-2 rounded border border-gray-800">
                                 <span class="text-gray-500">Power</span>
                                 <span class="text-cyan-300 font-mono">{{ formatVal(sensorData?.value?.power) }} kW</span>
                             </div>
                             <div class="flex justify-between items-center bg-black/40 p-2 rounded border border-gray-800">
                                 <span class="text-gray-500">Avg Current</span>
                                 <span class="text-cyan-300 font-mono">{{ formatVal(sensorData?.value?.AC || sensorData?.value?.current) }} A</span>
                             </div>
                             <div class="flex justify-between items-center bg-black/40 p-2 rounded border border-gray-800">
                                 <span class="text-gray-500">Heat Capacity</span>
                                 <span class="text-cyan-300 font-mono">{{ formatVal(sensorData?.value?.heat_capacity) }} kW</span>
                             </div>
                         </div>
                    </div>

                    <!-- Liquid Levels & Power Components -->
                    <div class="relative bg-gray-900/60 border border-gray-700 rounded-lg p-5">
                         <h3 class="text-gray-400 text-xs uppercase tracking-widest mb-3">Levels & Power</h3>
                         <div class="grid grid-cols-3 gap-2 mb-2">
                             <StatusCard label="Level 1" :active="!!sensorData?.value?.level1" />
                             <StatusCard label="Level 2" :active="!!sensorData?.value?.level2" />
                             <StatusCard label="Level 3" :active="!!sensorData?.value?.level3" />
                         </div>
                         <div class="grid grid-cols-2 gap-2">
                             <StatusCard label="Pwr Sup 1" :active="!!sensorData?.value?.powerSupply1" />
                             <StatusCard label="Pwr Sup 2" :active="!!sensorData?.value?.powerSupply2" />
                         </div>
                    </div>
                </div>

                <!-- Column 2: Primary Loop (Coolant) -->
                <div class="relative bg-gray-900/60 border border-gray-700 rounded-lg p-5 group hover:border-cyan-500/30 transition-colors">
                    <div class="absolute bottom-0 right-0 w-8 h-8 border-r-2 border-b-2 border-gray-600 rounded-br group-hover:border-cyan-500/50 transition-colors pointer-events-none"></div>
                    
                    <h3 class="text-cyan-500 font-bold mb-4 uppercase text-sm flex items-center">
                        <span class="inline-block w-2 h-2 bg-cyan-500 rotate-45 mr-2"></span>
                        Primary Loop (Coolant)
                    </h3>
                    <div class="space-y-3">
                        <SensorRow label="Supply Temp (T1)" :value="sensorData?.value?.temp_clntSply" unit="°C" />
                        <SensorRow label="Split Temp (T1sp)" :value="sensorData?.value?.temp_clntSplySpr" unit="°C" class="opacity-70 text-xs" />
                        <SensorRow label="Return Temp (T2)" :value="sensorData?.value?.temp_clntRtn" unit="°C" />
                        <div class="border-t border-gray-800 my-2"></div>
                        <SensorRow label="Supply Pressure (P1)" :value="sensorData?.value?.prsr_clntSply" unit="bar" />
                        <SensorRow label="Split Pressure (P1sp)" :value="sensorData?.value?.prsr_clntSplySpr" unit="bar" class="opacity-70 text-xs" />
                        <SensorRow label="Return Pressure (P2)" :value="sensorData?.value?.prsr_clntRtn" unit="bar" />
                        <SensorRow label="Spare Pressure (P2sp)" :value="sensorData?.value?.prsr_clntRtnSpr" unit="bar" class="opacity-70 text-xs" />
                        <SensorRow label="Diff. Pressure (Pd)" :value="sensorData?.value?.prsr_diff" unit="bar" color="text-yellow-400" />
                        <div class="border-t border-gray-800 my-2"></div>
                        <SensorRow label="Flow Rate (F1)" :value="sensorData?.value?.flow_clnt" unit="LPM" />
                    </div>
                </div>

                <!-- Column 3: Secondary Loop & Valves -->
                <div class="space-y-4">
                     <!-- Secondary Loop Water (Facility) -->
                    <div class="relative bg-gray-900/60 border border-gray-700 rounded-lg p-5 group hover:border-blue-500/30 transition-colors">
                        <h3 class="text-blue-500 font-bold mb-4 uppercase text-sm flex items-center">
                             <span class="inline-block w-2 h-2 bg-blue-500 rotate-45 mr-2"></span>
                             Secondary Loop
                        </h3>
                        <div class="space-y-3">
                            <SensorRow label="Supply Temp (T4)" :value="sensorData?.value?.temp_waterIn" unit="°C" color="text-blue-300" />
                            <SensorRow label="Return Temp (T5)" :value="sensorData?.value?.temp_waterOut" unit="°C" color="text-blue-300" />
                            <SensorRow label="Inlet Pressure (P10)" :value="sensorData?.value?.prsr_wtrIn" unit="bar" color="text-blue-300" />
                            <SensorRow label="Outlet Pressure (P11)" :value="sensorData?.value?.prsr_wtrOut" unit="bar" color="text-blue-300" />
                             <SensorRow label="Flow Rate (F2)" :value="sensorData?.value?.flow_wtr" unit="LPM" color="text-blue-300" />
                        </div>
                    </div>
                    
                    <!-- Valves Status -->
                    <div class="relative bg-gray-900/60 border border-gray-700 rounded-lg p-5">
                        <h3 class="text-gray-400 text-xs uppercase tracking-widest mb-3">Valve Status (EV)</h3>
                        <div class="grid grid-cols-4 gap-2">
                             <StatusCard label="EV1" :active="!!sensorData?.value?.ev1" />
                             <StatusCard label="EV2" :active="!!sensorData?.value?.ev2" />
                             <StatusCard label="EV3" :active="!!sensorData?.value?.ev3" />
                             <StatusCard label="EV4" :active="!!sensorData?.value?.ev4" />
                        </div>
                    </div>
                </div>

                <!-- Column 4: Quality & Components & Diagnostics -->
                <div class="space-y-4">
                    <!-- Water Quality & Env -->
                    <div class="relative bg-gray-900/60 border border-gray-700 rounded-lg p-5">
                        <h3 class="text-gray-400 text-xs uppercase tracking-widest mb-4 border-b border-gray-800 pb-2">Environment & Quality</h3>
                        <div class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                             <SensorRow label="Ambient (Ta)" :value="sensorData?.value?.temp_ambient" unit="°C" />
                             <SensorRow label="Dew Point (TDp)" :value="sensorData?.value?.dewPt" unit="°C" />
                             <SensorRow label="Rel. Humidity" :value="sensorData?.value?.rltHmd" unit="%" />
                             <SensorRow label="pH Level" :value="sensorData?.value?.pH" unit="pH" color="text-green-300" />
                             <SensorRow label="Conductivity" :value="sensorData?.value?.cdct" unit="µS" color="text-yellow-300" />
                             <SensorRow label="Turbidity" :value="sensorData?.value?.tbd" unit="NRU" color="text-yellow-300" />
                        </div>
                    </div>

                    <!-- Pump & PV -->
                    <div class="relative bg-gray-900/60 border border-gray-700 rounded-lg p-5">
                        <h3 class="text-gray-400 text-xs uppercase tracking-widest mb-4">Pumps & Control</h3>
                         <div class="space-y-3">
                             <div class="flex justify-between items-center bg-black/20 p-2 rounded border border-gray-800">
                                 <span class="text-sm text-gray-400">Pump 1</span>
                                 <span class="text-cyan-300 font-mono font-bold">{{ formatVal(sensorData?.value?.inv1_freq) }}%</span>
                             </div>
                             <div class="flex justify-between items-center bg-black/20 p-2 rounded border border-gray-800">
                                 <span class="text-sm text-gray-400">Pump 2</span>
                                 <span class="text-cyan-300 font-mono font-bold">{{ formatVal(sensorData?.value?.inv2_freq) }}%</span>
                             </div>
                             <div class="flex justify-between items-center bg-black/20 p-2 rounded border border-gray-800">
                                 <span class="text-sm text-gray-400">PV Opening</span>
                                 <span class="text-cyan-300 font-mono font-bold">{{ formatVal(sensorData?.value?.WaterPV) }}%</span>
                             </div>
                        </div>
                    </div>
                    
                    <!-- Filters Detailed View -->
                     <div class="relative bg-gray-900/60 border border-gray-700 rounded-lg p-3">
                        <h3 class="text-gray-400 text-xs uppercase tracking-widest mb-2">Filter(P3-[P4~8]Max)</h3>
                        <div class="space-y-2">
                             <!-- Calculation Display -->
                            <div class="bg-black/30 rounded p-2 border border-gray-800 text-xs mb-2">
                                <div class="text-gray-500 mb-1">Pressure Drop Calculation</div>
                                <div class="flex flex-wrap items-center font-mono text-cyan-300 gap-1">
                                    <span>P3 ({{ formatVal(sensorData?.value?.prsr_fltIn) }})</span>
                                    <span class="text-gray-500">-</span>
                                    <span>Max ({{ formatVal(sensorData?.value?.prsr_fltmax) }})</span>
                                    <span class="text-gray-500">=</span>
                                    <span :class="(sensorData?.value?.prsr_fltIn - sensorData?.value?.prsr_fltmax) > 0.5 ? 'text-red-400' : 'text-green-400'">
                                        {{ ((sensorData?.value?.prsr_fltIn || 0) - (sensorData?.value?.prsr_fltmax || 0)).toFixed(1) }}
                                    </span>
                                    <span class="text-gray-500 text-[10px] ml-1">bar</span>
                                </div>
                            </div>

                            <SensorRow label="Inlet (P3)" :value="sensorData?.value?.prsr_fltIn" unit="bar" class="text-xs" />
                            <div class="grid grid-cols-2 gap-x-4 gap-y-1">
                                <SensorRow label="Flt 1 (P4)" :value="sensorData?.value?.prsr_flt1Out" unit="bar" class="text-xs opacity-80" />
                                <SensorRow label="Flt 2 (P5)" :value="sensorData?.value?.prsr_flt2Out" unit="bar" class="text-xs opacity-80" />
                                <SensorRow label="Flt 3 (P6)" :value="sensorData?.value?.prsr_flt3Out" unit="bar" class="text-xs opacity-80" />
                                <SensorRow label="Flt 4 (P7)" :value="sensorData?.value?.prsr_flt4Out" unit="bar" class="text-xs opacity-80" />
                                <SensorRow label="Flt 5 (P8)" :value="sensorData?.value?.prsr_flt5Out" unit="bar" class="text-xs opacity-80" />
                            </div>
                            <div class="border-t border-gray-800 mt-1 pt-1">
                                 <SensorRow label="Max Outlet" :value="sensorData?.value?.prsr_fltmax" unit="bar" class="text-xs font-bold" />
                            </div>
                        </div>
                    </div>
                </div>

            </div>

             <!-- Device Diagnostics Section (New) -->
            <div class="relative bg-gray-900/60 border border-gray-700 rounded-lg p-4 mt-6">
                <!-- Header -->
                 <div class="absolute top-0 left-0 w-2 h-full bg-cyan-900/50 rounded-l"></div>
                <h3 class="text-gray-400 text-sm uppercase tracking-widest mb-4 flex items-center pl-4">
                    <span class="w-2 h-2 bg-cyan-500 mr-2 rotate-45"></span>
                    Device Diagnostics
                </h3>
                
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 pl-4">
                    <div v-for="(status, name) in deviceStatuses" :key="name" class="bg-black/20 rounded p-2 border border-gray-800 flex justify-between items-center">
                        <span class="text-xs text-gray-400">{{ name }}</span>
                        <span class="text-xs font-bold px-2 py-0.5 rounded" 
                            :class="status === 'OK' || status === 'Valid' ? 'text-green-400 bg-green-900/20' : 'text-red-400 bg-red-900/20'">
                            {{ status }}
                        </span>
                    </div>
                </div>
            </div>

        </div>

        <!-- Sticky Footer Alarm Bar -->
        <div v-if="systemAlarm" class="fixed bottom-0 left-0 right-0 bg-yellow-400 text-black font-bold text-center py-1 z-50 text-sm animate-pulse tracking-wider uppercase">
            {{ systemAlarm }}
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import SystemDiagram from './SystemDiagram.vue'
import SensorRow from './SensorRow.vue'
import StatusCard from './StatusCard.vue'

// State for mock data
const isTestMode = ref(false)
const sensorData = ref(null)
const loading = ref(true)
const error = ref(null)
let pollInterval = null

const formatVal = (val) => {
    if (val === undefined || val === null) return '--'
    return Number(val).toFixed(1)
}

// Device Statuses Computed Property
const deviceStatuses = computed(() => {
    if (!sensorData.value?.value) return {}
    const d = sensorData.value.value
    return {
        'PV1': d.ev_pv1_status || 'OK',
        'EV1': d.ev1_status || 'OK',
        'EV2': d.ev2_status || 'OK',
        'EV3': d.ev3_status || 'OK',
        'EV4': d.ev4_status || 'OK',
        'Leakage': d.leakage_status || 'OK',
        'Inv1 Err': d.inv1_error || 'OK',
        'Inv2 Err': d.inv2_error || 'OK',
        'Inv1 Over': d.inv1_overload || 'OK',
        'Inv2 Over': d.inv2_overload || 'OK',
        'PLC': d.plc_status || 'Device Error', // Defaulting to error for demo matching user screenshot
        'ATS': d.ats_status || 'OFF',
        'PC1': d.pc1_status || 'OK',
        'PC2': d.pc2_status || 'OK',
    }
})

const systemAlarm = computed(() => {
    return sensorData.value?.value?.system_alarm || 'M351 PLC Communication Broken Error' // Defaulting for demo
})

// Mock Data Generator (Comprehensive)
const generateMockData = () => {
    return {
        value: {
            opMod: 'AUTO',
            power: 3.5,
            current: 12.5,
            AC: 12.6,
            heat_capacity: 45.2,
            
            // Primary
            temp_clntSply: 25.4,
            temp_clntSplySpr: 25.5,
            temp_clntRtn: 30.1,
            prsr_clntSply: 2.5,
            prsr_clntSplySpr: 2.4,
            prsr_clntRtn: 1.5,
            prsr_clntRtnSpr: 1.4,
            prsr_diff: 1.0,
            flow_clnt: 45.2,
            
            // Secondary
            temp_waterIn: 20.5,
            temp_waterOut: 35.2,
            prsr_wtrIn: 3.2,
            prsr_wtrOut: 3.0,
            flow_wtr: 50.1,
            
            // Env & Quality
            temp_ambient: 24.5,
            dewPt: 12.0,
            rltHmd: 45,
            pH: 7.2,
            cdct: 15.5,
            tbd: 0.5,
            
            // Components
            inv1_freq: 85,
            inv2_freq: 0,
            WaterPV: 62,
            level1: true,
            level2: true,
            level3: false,
            powerSupply1: true,
            powerSupply2: true,
            ev1: true,
            ev2: true,
            ev3: true,
            ev4: true,
            
            // Filters
            prsr_fltIn: 2.8,
            prsr_fltmax: 2.7,
            prsr_flt1Out: 2.7,
            prsr_flt2Out: 2.6,
            prsr_flt3Out: 2.5,
            prsr_flt4Out: 2.4,
            prsr_flt5Out: 2.3,

             // Device Status Mock
            ev_pv1_status: 'OK',
            ev1_status: 'OK',
            ev2_status: 'OK',
            ev3_status: 'OK',
            ev4_status: 'OK',
            leakage_status: 'OK',
            inv1_error: 'OK',
            inv2_error: 'OK',
            inv1_overload: 'OK',
            inv2_overload: 'OK',
            plc_status: 'Device Error',
            ats_status: 'OFF',
            pc1_status: 'OK',
            pc2_status: 'OK',
            system_alarm: 'M351 PLC Communication Broken Error'
        }
    }
}

const fetchData = async () => {
    if (isTestMode.value) return
    try {
        const response = await axios.get('/api/status') 
        sensorData.value = response.data
        error.value = null
    } catch (err) {
        if (!sensorData.value) error.value = "CONNECTION LOST"
    } finally {
        loading.value = false
    }
}

const toggleTestMode = () => {
    isTestMode.value = !isTestMode.value
    if (isTestMode.value) {
        sensorData.value = generateMockData()
        if (pollInterval) clearInterval(pollInterval)
        pollInterval = setInterval(() => {
            sensorData.value = generateMockData()
        }, 1000)
    } else {
        if (pollInterval) clearInterval(pollInterval)
        fetchData()
        pollInterval = setInterval(fetchData, 2000)
    }
}

onMounted(() => {
    fetchData()
    // Start with fetch
    pollInterval = setInterval(fetchData, 2000)
})

onUnmounted(() => {
    clearInterval(pollInterval)
})
</script>

<style scoped>
/* Custom styles if needed */
</style>
