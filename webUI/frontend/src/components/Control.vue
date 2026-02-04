<template>
    <div class="min-h-screen bg-gray-900 text-cyan-400 p-6 font-mono selection:bg-cyan-900 selection:text-white">
        <!-- Header -->
        <header class="mb-8 flex justify-between items-center border-b border-cyan-800 pb-4">
            <div>
                <h1 class="text-3xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">CONTROL CENTER</h1>
                <p class="text-xs text-gray-400 mt-1">SYSTEM STATUS: <span :class="connectionStatus === 'Connected' ? 'text-green-500' : 'text-red-500'">{{ connectionStatus }}</span></p>
            </div>
            <div class="flex items-center space-x-4">
                 <div class="px-4 py-2 border border-red-500/50 rounded bg-red-900/10 flex items-center space-x-3 shadow-[0_0_10px_rgba(239,68,68,0.2)]">
                     <span class="text-red-400 font-bold text-sm">ERROR RESET</span>
                     <button @click="resetError" class="px-3 py-1 bg-red-600 hover:bg-red-500 text-white text-xs rounded transition-colors uppercase tracking-widest">
                         RESET
                     </button>
                 </div>
            </div>
        </header>

        <!-- Main Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            <!-- LEFT COLUMN: Mode Selection & Control -->
            <div class="lg:col-span-8 space-y-6">
                
                <!-- Mode Selection Panel -->
                <div class="bg-gray-800/50 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-sm relative overflow-hidden group hover:border-cyan-500/60 transition-colors">
                    <div class="absolute top-0 right-0 w-20 h-20 bg-cyan-500/5 rounded-bl-full -mr-10 -mt-10 pointer-events-none"></div>
                    
                    <h2 class="text-xl font-semibold mb-6 flex items-center text-cyan-300">
                        <span class="w-2 h-2 bg-cyan-400 rounded-full mr-3 animate-pulse"></span>
                        MODE SELECTION
                    </h2>

                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                        <button 
                            v-for="mode in ['Auto', 'Manual', 'Stop', 'Engineer']" 
                            :key="mode"
                            @click="selectedMode = mode.toLowerCase()"
                            :class="[
                                'py-4 px-2 rounded border transition-all duration-300 relative overflow-hidden',
                                selectedMode === mode.toLowerCase() 
                                    ? 'bg-cyan-900/40 border-cyan-400 text-cyan-300 shadow-[0_0_15px_rgba(34,211,238,0.3)]' 
                                    : 'bg-gray-900/50 border-gray-700 text-gray-500 hover:border-gray-500 hover:text-gray-300'
                            ]"
                        >
                            <span class="relative z-10 font-bold tracking-widest">{{ mode.toUpperCase() }}</span>
                            <div v-if="selectedMode === mode.toLowerCase()" class="absolute inset-0 bg-cyan-400/5 scanline"></div>
                        </button>
                    </div>

                    <!-- Dynamic Settings Area -->
                    <div class="p-6 bg-gray-900/80 rounded border border-gray-700 min-h-[300px]">
                        
                        <!-- AUTO MODE CONFIG -->
                        <div v-if="selectedMode === 'auto'" class="space-y-6 animate-fade-in">
                            <h3 class="text-gray-400 text-sm uppercase tracking-widest border-b border-gray-700 pb-2 mb-4">Auto Configuration</h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div class="space-y-2">
                                    <label class="text-sm text-cyan-600 font-semibold">Target Coolant Temp (°C)</label>
                                    <input type="number" v-model.number="autoSettings.temp" 
                                           class="w-full bg-gray-800 text-white border border-gray-600 rounded p-3 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all text-lg font-mono placeholder-gray-600">
                                </div>
                                <div class="space-y-2">
                                    <label class="text-sm text-cyan-600 font-semibold">Target Coolant Pressure (KPa)</label>
                                    <input type="number" v-model.number="autoSettings.pressure" 
                                           class="w-full bg-gray-800 text-white border border-gray-600 rounded p-3 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all text-lg font-mono">
                                </div>
                            </div>
                        </div>

                         <!-- MANUAL MODE CONFIG -->
                        <div v-else-if="selectedMode === 'manual'" class="space-y-6 animate-fade-in">
                            <h3 class="text-gray-400 text-sm uppercase tracking-widest border-b border-gray-700 pb-2 mb-4">Manual Override</h3>
                             <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div class="space-y-2">
                                    <label class="text-sm text-yellow-600 font-semibold">Pump 1 Speed (%)</label>
                                    <input type="number" v-model.number="manualSettings.pump1" 
                                           class="w-full bg-gray-800 text-white border border-gray-600 rounded p-3 focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 outline-none transition-all text-lg font-mono">
                                </div>
                                <div class="space-y-2">
                                    <label class="text-sm text-yellow-600 font-semibold">Pump 2 Speed (%)</label>
                                    <input type="number" v-model.number="manualSettings.pump2" 
                                           class="w-full bg-gray-800 text-white border border-gray-600 rounded p-3 focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 outline-none transition-all text-lg font-mono">
                                </div>
                                <div class="space-y-2 md:col-span-2">
                                    <label class="text-sm text-blue-500 font-semibold">Proportional Valve (PV1) Opening (%)</label>
                                    <input type="number" v-model.number="manualSettings.waterPV" 
                                           class="w-full bg-gray-800 text-white border border-gray-600 rounded p-3 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all text-lg font-mono text-center">
                                </div>
                            </div>
                        </div>

                         <!-- STOP MODE CONFIG -->
                        <div v-else-if="selectedMode === 'stop'" class="flex flex-col items-center justify-center h-full text-center space-y-4 animate-fade-in text-gray-500">
                            <svg class="w-16 h-16 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            <span class="text-lg">System Halted</span>
                            <div class="w-full max-w-md mt-6 border-t border-gray-800 pt-6">
                                <h4 class="text-xs uppercase tracking-widest text-cyan-800 mb-4">Inverter Maintenance Switches</h4>
                                <div class="flex justify-center space-x-8">
                                    <label class="flex items-center space-x-3 cursor-pointer group">
                                         <input type="checkbox" v-model="inverterSwitches.inv1" class="form-checkbox bg-gray-900 border-gray-600 text-cyan-600 rounded focus:ring-offset-gray-900 focus:ring-cyan-500">
                                         <span class="group-hover:text-cyan-400 transition-colors">Inverter 1</span>
                                    </label>
                                    <label class="flex items-center space-x-3 cursor-pointer group">
                                         <input type="checkbox" v-model="inverterSwitches.inv2" class="form-checkbox bg-gray-900 border-gray-600 text-cyan-600 rounded focus:ring-offset-gray-900 focus:ring-cyan-500">
                                         <span class="group-hover:text-cyan-400 transition-colors">Inverter 2</span>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <!-- ENGINEER MODE MESSAGE -->
                        <div v-else class="flex items-center justify-center h-full text-center text-purple-400 animate-fade-in">
                            <div>
                                <h3 class="text-lg font-bold">ENGINEER MODE ACTIVE</h3>
                                <p class="text-sm opacity-70">Please consult the Engineer Tab for advanced settings.</p>
                            </div>
                        </div>

                    </div>

                    <!-- Action Bar -->
                    <div class="mt-6 flex justify-end space-x-4">
                         <button @click="fetchData" class="px-6 py-3 border border-gray-600 text-gray-400 rounded hover:bg-gray-800 hover:text-white transition-colors uppercase text-sm tracking-wider">
                            Reload
                        </button>
                        <button @click="applyMode" class="px-8 py-3 bg-cyan-700/80 hover:bg-cyan-600 text-white rounded shadow-[0_0_20px_rgba(6,182,212,0.4)] transition-all uppercase font-bold tracking-wider flex items-center">
                            <span class="mr-2">EXECUTE</span>
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                        </button>
                    </div>

                </div>
            </div>

            <!-- RIGHT COLUMN: Status & Maintenance -->
            <div class="lg:col-span-4 space-y-6">
                
                <!-- System Status Summary -->
                 <div class="bg-gray-800/50 border border-gray-700 rounded-lg p-6 backdrop-blur-sm">
                    <h3 class="text-gray-400 text-xs uppercase tracking-widest mb-4">Live Diagnostics</h3>
                    <div class="space-y-4">
                        <div class="flex justify-between items-center border-b border-gray-700 pb-2">
                            <span class="text-gray-400">Current Mode</span>
                            <span class="font-bold text-cyan-300">{{ controlData?.value?.resultMode || '---' }}</span>
                        </div>
                        <div class="flex justify-between items-center border-b border-gray-700 pb-2">
                             <span class="text-gray-400">System Time</span>
                             <span class="font-mono text-xs">{{ systemTime }}</span>
                        </div>
                         <!-- Add more mini-stats here -->
                    </div>
                 </div>

                <!-- Maintenance Panel -- NEW SECTION -->
                <div class="bg-gray-800/50 border border-gray-700 rounded-lg p-6 backdrop-blur-sm space-y-8">
                     <h3 class="text-cyan-500 font-bold border-l-4 border-cyan-500 pl-3 uppercase tracking-widest">Maintenance</h3>
                     
                     <!-- Running Times -->
                     <div>
                        <h4 class="text-xs text-gray-400 uppercase mb-3 flex justify-between items-center">
                            <span>Component Runtime (Hrs)</span>
                            <button @click="resetRunTimes" class="text-[10px] text-red-500 hover:text-red-400 border border-red-900/50 bg-red-900/20 px-2 py-0.5 rounded">RESET ALL</button>
                        </h4>
                        <div class="grid grid-cols-2 gap-3 text-xs">
                             <div class="bg-gray-900 p-2 rounded border border-gray-700 flex justify-between">
                                 <span class="text-gray-500">Pump 1</span>
                                 <span class="text-white font-mono">{{ controlData?.text?.Pump1_run_time || 0 }}</span>
                             </div>
                             <div class="bg-gray-900 p-2 rounded border border-gray-700 flex justify-between">
                                 <span class="text-gray-500">Pump 2</span>
                                 <span class="text-white font-mono">{{ controlData?.text?.Pump2_run_time || 0 }}</span>
                             </div>
                             <div v-for="i in 5" :key="i" class="bg-gray-900 p-2 rounded border border-gray-700 flex justify-between">
                                 <span class="text-gray-500">Filter {{i}}</span>
                                 <span class="text-white font-mono">{{ controlData?.filter?.[`f${i}`] || 0 }}</span>
                             </div>
                        </div>
                     </div>

                     <!-- Firmware Update -->
                     <div class="space-y-2">
                         <h4 class="text-xs text-gray-400 uppercase">System Firmware</h4>
                         <div class="flex space-x-2">
                             <label class="flex-1 cursor-pointer">
                                 <div class="w-full bg-gray-900 border border-dashed border-gray-600 rounded px-3 py-2 text-xs text-center text-gray-400 hover:border-cyan-500 hover:text-cyan-500 transition-colors truncate">
                                     {{ selectedFirmware ? selectedFirmware.name : 'Select .zip File' }}
                                 </div>
                                 <input type="file" class="hidden" accept=".zip" @change="handleFileSelect">
                             </label>
                             <button @click="uploadFirmware" :disabled="!selectedFirmware || uploading" class="px-3 bg-cyan-700 disabled:bg-gray-700 text-white text-xs rounded uppercase font-bold">
                                 {{ uploading ? '...' : 'Update' }}
                             </button>
                         </div>
                     </div>

                     <!-- Export / Import / Reboot -->
                     <div class="grid grid-cols-2 gap-3 pt-4 border-t border-gray-700">
                         <button @click="exportSettings" class="py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs">Export Config</button>
                         <button @click="importSettings" class="py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs">Import Config</button>
                         <button @click="rebootSystem" class="col-span-2 py-2 bg-red-900/30 border border-red-900 hover:bg-red-800/40 text-red-400 rounded text-xs font-bold tracking-widest mt-2">
                             REBOOT SYSTEM
                         </button>
                     </div>

                </div>

            </div>
        </div>

        <div v-if="loading" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
            <div class="text-cyan-400 text-lg font-bold animate-pulse">ESTABLISHING UPLINK...</div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const controlData = ref(null)
const loading = ref(true)
const connectionStatus = ref('Connecting...')
const selectedMode = ref('stop')
const systemTime = ref('')
const uploading = ref(false)
const selectedFirmware = ref(null)

// Mode Settings Models
const autoSettings = ref({ temp: 25, pressure: 200 })
const manualSettings = ref({ pump1: 0, pump2: 0, waterPV: 0 })
const inverterSwitches = ref({ inv1: false, inv2: false })

let timer = null
let clockTimer = null

const fetchData = async () => {
    try {
        const response = await axios.get('/get_data_control')
        controlData.value = response.data
        connectionStatus.value = 'Connected'
        
        // Initial populate if needed (only on first load to prevent overwriting user input)
        // Note: Real implementation might sync this differently
    } catch (err) {
        console.error("Fetch control failed", err)
        connectionStatus.value = 'Offline'
    } finally {
        loading.value = false
    }
}

const updateClock = () => {
    const now = new Date()
    systemTime.value = now.toLocaleTimeString()
}

// Actions
const applyMode = async () => {
    try {
        const payload = {
            value: selectedMode.value, 
            force_change_mode: false,
            // Mapping to backend expected structure
            input: {
                selectMode: selectedMode.value, 
                temp: autoSettings.value.temp,
                prsr: autoSettings.value.pressure,
                p1: manualSettings.value.pump1,
                p2: manualSettings.value.pump2,
                water_pv: manualSettings.value.waterPV,
                // Passing placeholders for others if needed
                currentMode: controlData.value?.value?.resultMode || ''
            }
        }
        loading.value = true
        await axios.post('/set_operation_mode', payload)
        alert('COMMAND EXECUTED')
        fetchData()
    } catch (err) {
        alert('EXECUTION FAILED: ' + (err.response?.data?.message || err.message))
    } finally {
        loading.value = false
    }
}

const resetError = async () => {
    // Mock or implement if API exists
    alert('Reset signal sent (Mock)')
}

const handleFileSelect = (event) => {
    selectedFirmware.value = event.target.files[0]
}

const uploadFirmware = async () => {
    if (!selectedFirmware.value) return
    
    const formData = new FormData()
    formData.append('file', selectedFirmware.value)
    
    uploading.value = true
    try {
        await axios.post('/api/v1/1.3MW/upload_zip', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
        alert('FIRMWARE UPLOAD SUCCESSFUL. SYSTEM RESTARTING...')
    } catch (err) {
        alert('UPLOAD FAILED: ' + (err.response?.data?.message || err.message))
    } finally {
        uploading.value = false
        selectedFirmware.value = null
    }
}

const resetRunTimes = () => {
    // Missing backend API
    alert('Reset Run Times: Feature requires backend implementation.')
}

const exportSettings = () => {
     // Missing backend API
    alert('Export Config: Feature requires backend implementation.')
}

const importSettings = () => {
     // Missing backend API
    alert('Import Config: Feature requires backend implementation.')
}

const rebootSystem = () => {
    if(confirm('SYSTEM REBOOT INITIATED. CONFIRM?')) {
        // Missing backend API
        alert('Reboot command sent (Mock).')
    }
}

onMounted(() => {
    fetchData()
    updateClock()
    timer = setInterval(fetchData, 5000)
    clockTimer = setInterval(updateClock, 1000)
})

onUnmounted(() => {
    clearInterval(timer)
    clearInterval(clockTimer)
})
</script>

<style scoped>
.scanline {
    background: linear-gradient(
        to bottom,
        transparent 50%,
        rgba(34, 211, 238, 0.1) 51%,
        transparent 52%
    );
    background-size: 100% 4px;
    animation: scan 1s linear infinite;
    pointer-events: none;
}

@keyframes scan {
    0% { background-position: 0 0; }
    100% { background-position: 0 100%; }
}

@keyframes fade-in {
    from { opacity: 0; transform: translateY(5px); }
    to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
    animation: fade-in 0.3s ease-out forwards;
}
</style>
