<script setup>
import { ref, onMounted, reactive } from 'vue'
import axios from 'axios'
import { ChevronDownIcon, ChevronUpIcon, CpuChipIcon, WrenchScrewdriverIcon, AdjustmentsHorizontalIcon, ShieldCheckIcon, SignalIcon, CommandLineIcon } from '@heroicons/vue/24/solid'

const loading = ref(true)
const activeSection = ref(null)

// --- Data Models ---
// Sensor Adjust
const adjustData = ref({})
// Threshold
const thresholdData = ref({})
// PID
const pidTemp = ref({
    sample_time_temp: '', kp_temp: '', ki_time_temp: '', kd_temp: '', kd_time_temp: ''
})
const pidPressure = ref({
    sample_time_pressure: '', kp_pressure: '', ki_time_pressure: '', kd_pressure: '', kd_time_pressure: ''
})
// FW Info
const fwInfo = ref({ SN: '', Model: '', Version: '' })
const plcVersion = ref('')
// Auto Mode
const autoSetting = reactive({
    auto_water: 0,
    auto_pump: 0,
    auto_dew_point: 0
})
// Valve Setting
const valveData = reactive({
    ta_close_valve: 0,
    t1_close_valve: 0
})
// Switch Version
const switchData = reactive({
    function_switch: 'new',
    flow_switch: 'old',
    flow2_switch: 'old',
    median_switch: 'old',
    mc_switch: 'old'
})
// Screen Setting
const timeoutLight = ref(300)

// --- Configurations ---
const sensorRows = [
    { label: 'Coolant Supply Temp (T1)', id: 'Temp_ClntSply' },
    { label: 'Coolant Supply Temp (Spare) (T1 sp)', id: 'Temp_ClntSplySpr' },
    { label: 'Coolant Return Temp (T2)', id: 'Temp_ClntRtn' },
    { label: 'Facility Water Supply Temp (T4)', id: 'Temp_WaterIn' },
    { label: 'Facility Water Return Temp (T5)', id: 'Temp_WaterOut' },
    { label: 'Coolant Supply Pressure (P1)', id: 'Prsr_ClntSply' },
    { label: 'Coolant Supply Pressure (Spare) (P1 sp)', id: 'Prsr_ClntSplySpr' },
    { label: 'Coolant Return Pressure (P2)', id: 'Prsr_ClntRtn' },
    { label: 'Filter Inlet Pressure (P3)', id: 'Prsr_FltIn' },
]

// --- Initialization ---
const fetchData = async () => {
    loading.value = true
    try {
        const [engRes, verRes, timeRes] = await Promise.all([
            axios.get('/get_data_engineerMode'),
            axios.get('/read_version'),
            axios.get('/get_timeout')
        ])

        const data = engRes.data
        // Adjust
        adjustData.value = data.sensor_adjust || {}
        // Threshold
        thresholdData.value = data.thrshd || {}
        // PID
        pidTemp.value = data.pid_temp || {}
        pidPressure.value = data.pid_pressure || {}
        // Auto
        if (data.auto_setting) {
            autoSetting.auto_water = data.auto_setting.auto_water
            autoSetting.auto_pump = data.auto_setting.auto_pump
            autoSetting.auto_dew_point = data.auto_setting.auto_dew_point
        }
        // Valve
        if (data.valve) {
            valveData.ta_close_valve = data.valve.ta
            valveData.t1_close_valve = data.valve.t1
        }
        // Switch Version
        if (data.ver_switch) {
            switchData.function_switch = data.ver_switch.function_switch ? 'old' : 'new'
            switchData.flow_switch = data.ver_switch.flow_switch ? 'old' : 'new'
            switchData.flow2_switch = data.ver_switch.flow2_switch ? 'old' : 'new'
            switchData.median_switch = data.ver_switch.median_switch ? 'old' : 'new'
            switchData.mc_switch = data.ver_switch.mc_switch ? 'old' : 'new'
        }

        // FW Info
        const vData = verRes.data
        if (vData.FW_Info) {
            fwInfo.value = { 
                SN: vData.FW_Info.SN, 
                Model: vData.FW_Info.Model, 
                Version: vData.FW_Info.Version 
            }
        }
        plcVersion.value = vData.plc_version

        // Timeout
        if (timeRes.data && timeRes.data.timeoutLight) {
            timeoutLight.value = timeRes.data.timeoutLight
        }

    } catch (err) {
        console.error("Failed to load engineer data", err)
    } finally {
        loading.value = false
    }
}

// --- Demo Global Toggle ---
const isTestMode = ref(false)

const checkTestMode = async () => {
    try {
        const res = await axios.get('/api/demo_mode_status')
        isTestMode.value = res.data.demo_mode
    } catch (err) { }
}

const toggleTestMode = async () => {
    try {
        const payload = { demo_mode: !isTestMode.value }
        const res = await axios.post('/api/toggle_demo_mode', payload)
        if (res.data.success) {
            isTestMode.value = res.data.demo_mode
        }
    } catch (err) {
        console.error("Failed to toggle global demo mode", err)
    }
}

// --- Actions ---
const saveAdjust = async () => {
    try {
        await axios.post('/writeSensorAdjust', adjustData.value)
        alert('Sensor adjustment saved')
    } catch (err) { alert('Failed to save') }
}

const saveThreshold = async () => {
    try {
        await axios.post('/thrshd_set', thresholdData.value)
        alert('Thresholds saved')
    } catch (err) { alert('Failed to save') }
}

const savePID = async () => {
    try {
        const payload = {
            temp: pidTemp.value,
            pressure: pidPressure.value
        }
        await axios.post('/store_pid', payload)
        alert('PID settings saved')
    } catch (err) { alert('Failed to save PID') }
}

const saveFW = async () => {
    try {
        await axios.post('/write_version', fwInfo.value)
        alert('FW Info saved')
    } catch (err) { alert('Failed to save FW Info') }
}

const saveAuto = async () => {
    try {
        await axios.post('/auto_setting_apply', autoSetting)
        alert('Auto Mode settings saved')
    } catch (err) { alert('Failed to save Auto settings') }
}

const saveValve = async () => {
    try {
        const payload = {
            ta: valveData.ta_close_valve,
            t1: valveData.t1_close_valve
        }
        await axios.post('/set_valve_condition', payload)
        alert('Valve settings saved')
    } catch (err) { alert('Failed to save Valve settings') }
}

const saveTimeout = async () => {
    try {
        await axios.post('/set_timeout', { timeoutLight: timeoutLight.value })
        alert('Timeout saved')
    } catch (err) { alert('Failed to save Timeout') }
}

const saveSwitch = async () => {
    try {
        const payload = {
            function_switch: switchData.function_switch === 'old',
            flow_switch: switchData.flow_switch === 'old',
            flow2_switch: switchData.flow2_switch === 'old',
            median_switch: switchData.median_switch === 'old',
            mc_switch: switchData.mc_switch === 'old'
        }
        await axios.post('/version_switch', payload)
        alert('Version Switches saved')
    } catch (err) { alert('Failed to save Version Switches') }
}

const toggleSection = (section) => {
    activeSection.value = activeSection.value === section ? null : section
}

const getAdjustValue = (id, type) => adjustData.value[`${id}_${type}`] || 0
const updateAdjustValue = (id, type, val) => adjustData.value[`${id}_${type}`] = parseFloat(val)

onMounted(async () => {
    await checkTestMode()
    fetchData()
})
</script>

<template>
    <div class="min-h-screen bg-gray-900 text-cyan-400 p-6 font-mono selection:bg-cyan-900 selection:text-white pb-20">
        <!-- Background Grid Effect -->
        <div class="fixed inset-0 bg-[linear-gradient(rgba(17,24,39,0.9),rgba(17,24,39,0.9)),url('/grid.png')] pointer-events-none opacity-20 z-0"></div>

        <!-- Header -->
        <header class="relative z-10 mb-8 flex justify-between items-center border-b border-cyan-800 pb-4">
            <div>
                <h1 class="text-3xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">ENGINEER MODE</h1>
                <p class="text-xs text-gray-400 mt-1 flex items-center">
                    <span class="w-2 h-2 rounded-full mr-2" :class="loading ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'"></span>
                    ADVANCED CONFIGURATION ACCESS
                </p>
            </div>
            <div class="flex items-center space-x-4">
                <button @click="toggleTestMode" 
                        class="px-3 py-1 border text-xs rounded transition-all tracking-widest uppercase font-bold shadow-lg flex items-center"
                        :class="isTestMode ? 'bg-yellow-500 text-black border-yellow-400 shadow-yellow-500/50 hover:bg-yellow-400' : 'bg-transparent text-gray-500 border-gray-600 hover:text-gray-300 hover:border-gray-400'">
                    Test Mode: <span class="ml-1" :class="isTestMode ? 'text-black' : 'text-gray-400'">{{ isTestMode ? 'ON' : 'OFF' }}</span>
                </button>
                <button @click="fetchData" class="px-3 py-1 bg-cyan-900/40 hover:bg-cyan-800 border border-cyan-500/50 hover:border-cyan-400 text-cyan-300 text-xs rounded transition-all uppercase tracking-widest flex items-center">
                    <span class="mr-2">↻</span> Reload Data
                </button>
            </div>
        </header>

        <div v-if="loading" class="relative z-10 text-center py-20 text-cyan-500/50 animate-pulse text-xl font-bold tracking-[0.2em]">
            INITIALIZING SYSTEM PARAMETERS...
        </div>

        <div v-else class="relative z-10 space-y-4">
            
            <!-- 1. Sensor Adjustment -->
            <div class="bg-gray-800/40 border border-gray-700/50 rounded-lg overflow-hidden backdrop-blur-sm transition-all hover:border-cyan-500/30 group">
                <button @click="toggleSection('adjust')" class="w-full px-6 py-4 bg-gray-900/80 flex justify-between items-center text-left hover:bg-gray-800 transition-colors">
                    <div class="flex items-center space-x-3">
                        <AdjustmentsHorizontalIcon class="w-5 h-5 text-cyan-500" />
                        <span class="font-bold text-cyan-100 tracking-wide uppercase text-sm">Sensor Adjustment</span>
                    </div>
                    <ChevronDownIcon class="w-5 h-5 text-cyan-500 transition-transform duration-300" :class="activeSection === 'adjust' ? 'rotate-180' : ''" />
                </button>
                <div v-show="activeSection === 'adjust'" class="p-6 border-t border-gray-700/50 bg-gray-900/40">
                    <div class="overflow-x-auto mb-6 rounded border border-gray-700">
                        <table class="min-w-full divide-y divide-gray-700">
                            <thead class="bg-gray-900">
                                <tr>
                                    <th class="px-4 py-3 text-left text-xs uppercase font-bold text-gray-500 tracking-wider">Sensor Name</th>
                                    <th class="px-4 py-3 text-left text-xs uppercase font-bold text-cyan-600 tracking-wider w-32">Factor</th>
                                    <th class="px-4 py-3 text-left text-xs uppercase font-bold text-cyan-600 tracking-wider w-32">Offset</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-700 bg-gray-800/20">
                                <tr v-for="sensor in sensorRows" :key="sensor.id" class="hover:bg-cyan-900/10 transition-colors">
                                    <td class="px-4 py-2 text-xs text-gray-300 font-mono">{{ sensor.label }}</td>
                                    <td class="px-4 py-2"><input type="number" step="0.01" :value="getAdjustValue(sensor.id, 'Factor')" @input="e=>updateAdjustValue(sensor.id, 'Factor', e.target.value)" class="w-full bg-gray-900 text-cyan-300 rounded border border-gray-600 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 text-xs p-1"></td>
                                    <td class="px-4 py-2"><input type="number" step="0.01" :value="getAdjustValue(sensor.id, 'Offset')" @input="e=>updateAdjustValue(sensor.id, 'Offset', e.target.value)" class="w-full bg-gray-900 text-cyan-300 rounded border border-gray-600 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 text-xs p-1"></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="flex justify-end">
                        <button @click="saveAdjust" class="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded text-xs font-bold uppercase tracking-widest shadow-lg shadow-cyan-500/20 transition-all">Apply Calibration</button>
                    </div>
                </div>
            </div>

            <!-- 2. Threshold Setting -->
            <div class="bg-gray-800/40 border border-gray-700/50 rounded-lg overflow-hidden backdrop-blur-sm transition-all hover:border-cyan-500/30 group">
                <button @click="toggleSection('threshold')" class="w-full px-6 py-4 bg-gray-900/80 flex justify-between items-center text-left hover:bg-gray-800 transition-colors">
                    <div class="flex items-center space-x-3">
                        <ShieldCheckIcon class="w-5 h-5 text-red-400" />
                        <span class="font-bold text-cyan-100 tracking-wide uppercase text-sm">Alert Threshold Setting</span>
                    </div>
                    <ChevronDownIcon class="w-5 h-5 text-cyan-500 transition-transform duration-300" :class="activeSection === 'threshold' ? 'rotate-180' : ''" />
                </button>
                <div v-show="activeSection === 'threshold'" class="p-6 border-t border-gray-700/50 bg-gray-900/40">
                     <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                         <div v-for="sensor in sensorRows" :key="sensor.id" class="border border-gray-700 bg-gray-800/50 p-3 rounded hover:border-cyan-500/50 transition-colors">
                            <h4 class="font-bold text-xs text-cyan-300 mb-3 uppercase tracking-wider">{{ sensor.label }}</h4>
                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <label class="text-[10px] uppercase text-yellow-500 font-bold mb-1 block">Warn Limit</label>
                                    <input v-model="thresholdData[`Thr_W_${sensor.id}`]" type="number" class="w-full bg-gray-900 text-yellow-400 text-xs border border-gray-600 rounded p-1.5 focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500">
                                </div>
                                <div>
                                    <label class="text-[10px] uppercase text-red-500 font-bold mb-1 block">Alert Limit</label>
                                    <input v-model="thresholdData[`Thr_A_${sensor.id}`]" type="number" class="w-full bg-gray-900 text-red-400 text-xs border border-gray-600 rounded p-1.5 focus:border-red-500 focus:ring-1 focus:ring-red-500">
                                </div>
                            </div>
                        </div>
                     </div>
                    <div class="flex justify-end mt-6">
                        <button @click="saveThreshold" class="bg-red-600 hover:bg-red-500 text-white px-6 py-2 rounded text-xs font-bold uppercase tracking-widest shadow-lg shadow-red-500/20 transition-all">Update Thresholds</button>
                    </div>
                </div>
            </div>

            <!-- 3. PID Setting -->
            <div class="bg-gray-800/40 border border-gray-700/50 rounded-lg overflow-hidden backdrop-blur-sm transition-all hover:border-cyan-500/30 group">
                <button @click="toggleSection('pid')" class="w-full px-6 py-4 bg-gray-900/80 flex justify-between items-center text-left hover:bg-gray-800 transition-colors">
                    <div class="flex items-center space-x-3">
                        <SignalIcon class="w-5 h-5 text-green-400" />
                        <span class="font-bold text-cyan-100 tracking-wide uppercase text-sm">PID Control Params</span>
                    </div>
                    <ChevronDownIcon class="w-5 h-5 text-cyan-500 transition-transform duration-300" :class="activeSection === 'pid' ? 'rotate-180' : ''" />
                </button>
                <div v-show="activeSection === 'pid'" class="p-6 border-t border-gray-700/50 bg-gray-900/40">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <!-- Pressure PID -->
                        <div class="bg-gray-800/30 p-4 rounded border border-gray-700">
                            <h4 class="font-bold text-cyan-400 mb-4 border-b border-gray-700 pb-2 flex items-center">
                                <span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span> Pressure Loop
                            </h4>
                            <div class="space-y-3">
                                <div class="flex justify-between items-center bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                    <label class="text-xs text-gray-400 font-bold">Sample Time</label>
                                    <input v-model="pidPressure.sample_time_pressure" type="number" class="w-24 bg-gray-800 text-white border-0 rounded text-xs p-1 focus:ring-1 focus:ring-cyan-500 text-right"/>
                                </div>
                                <div class="flex justify-between items-center bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                    <label class="text-xs text-gray-400 font-bold">Proportional (KP)</label>
                                    <input v-model="pidPressure.kp_pressure" type="number" class="w-24 bg-gray-800 text-white border-0 rounded text-xs p-1 focus:ring-1 focus:ring-cyan-500 text-right"/>
                                </div>
                                <div class="flex justify-between items-center bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                    <label class="text-xs text-gray-400 font-bold">Integral Time</label>
                                    <input v-model="pidPressure.ki_time_pressure" type="number" class="w-24 bg-gray-800 text-white border-0 rounded text-xs p-1 focus:ring-1 focus:ring-cyan-500 text-right"/>
                                </div>
                                <div class="flex justify-between items-center bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                    <label class="text-xs text-gray-400 font-bold">Derivative (KD)</label>
                                    <input v-model="pidPressure.kd_pressure" type="number" class="w-24 bg-gray-800 text-white border-0 rounded text-xs p-1 focus:ring-1 focus:ring-cyan-500 text-right"/>
                                </div>
                                <div class="flex justify-between items-center bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                    <label class="text-xs text-gray-400 font-bold">Derivative Time</label>
                                    <input v-model="pidPressure.kd_time_pressure" type="number" class="w-24 bg-gray-800 text-white border-0 rounded text-xs p-1 focus:ring-1 focus:ring-cyan-500 text-right"/>
                                </div>
                            </div>
                        </div>

                        <!-- Temp PID -->
                        <div class="bg-gray-800/30 p-4 rounded border border-gray-700">
                            <h4 class="font-bold text-cyan-400 mb-4 border-b border-gray-700 pb-2 flex items-center">
                                <span class="w-2 h-2 bg-pink-500 rounded-full mr-2"></span> Temperature Loop
                            </h4>
                            <div class="space-y-3">
                                <div class="flex justify-between items-center bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                    <label class="text-xs text-gray-400 font-bold">Sample Time</label>
                                    <input v-model="pidTemp.sample_time_temp" type="number" class="w-24 bg-gray-800 text-white border-0 rounded text-xs p-1 focus:ring-1 focus:ring-cyan-500 text-right"/>
                                </div>
                                <div class="flex justify-between items-center bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                    <label class="text-xs text-gray-400 font-bold">Proportional (KP)</label>
                                    <input v-model="pidTemp.kp_temp" type="number" class="w-24 bg-gray-800 text-white border-0 rounded text-xs p-1 focus:ring-1 focus:ring-cyan-500 text-right"/>
                                </div>
                                <div class="flex justify-between items-center bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                    <label class="text-xs text-gray-400 font-bold">Integral Time</label>
                                    <input v-model="pidTemp.ki_time_temp" type="number" class="w-24 bg-gray-800 text-white border-0 rounded text-xs p-1 focus:ring-1 focus:ring-cyan-500 text-right"/>
                                </div>
                                <div class="flex justify-between items-center bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                    <label class="text-xs text-gray-400 font-bold">Derivative (KD)</label>
                                    <input v-model="pidTemp.kd_temp" type="number" class="w-24 bg-gray-800 text-white border-0 rounded text-xs p-1 focus:ring-1 focus:ring-cyan-500 text-right"/>
                                </div>
                                <div class="flex justify-between items-center bg-gray-900/50 p-2 rounded border border-gray-700/50">
                                    <label class="text-xs text-gray-400 font-bold">Derivative Time</label>
                                    <input v-model="pidTemp.kd_time_temp" type="number" class="w-24 bg-gray-800 text-white border-0 rounded text-xs p-1 focus:ring-1 focus:ring-cyan-500 text-right"/>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-end mt-4">
                        <button @click="savePID" class="bg-green-600 hover:bg-green-500 text-white px-6 py-2 rounded text-xs font-bold uppercase tracking-widest shadow-lg shadow-green-500/20 transition-all">Save PID Config</button>
                    </div>
                </div>
            </div>

            <!-- 4. FW Setting -->
            <div class="bg-gray-800/40 border border-gray-700/50 rounded-lg overflow-hidden backdrop-blur-sm transition-all hover:border-cyan-500/30 group">
                <button @click="toggleSection('fw')" class="w-full px-6 py-4 bg-gray-900/80 flex justify-between items-center text-left hover:bg-gray-800 transition-colors">
                    <div class="flex items-center space-x-3">
                        <CpuChipIcon class="w-5 h-5 text-purple-400" />
                        <span class="font-bold text-cyan-100 tracking-wide uppercase text-sm">Firmware Identification & Status</span>
                    </div>
                    <ChevronDownIcon class="w-5 h-5 text-cyan-500 transition-transform duration-300" :class="activeSection === 'fw' ? 'rotate-180' : ''" />
                </button>
                <div v-show="activeSection === 'fw'" class="p-6 border-t border-gray-700/50 bg-gray-900/40">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        
                        <!-- Writable Settings -->
                        <div class="space-y-4">
                            <h4 class="text-xs font-bold text-purple-400 uppercase tracking-widest border-b border-gray-700 pb-2 mb-4">Device Identification</h4>
                            <div class="bg-gray-800/50 p-3 rounded flex items-center border border-gray-700">
                                 <label class="w-32 text-xs font-bold text-gray-400 uppercase">Serial Number</label>
                                 <input v-model="fwInfo.SN" type="text" class="flex-1 bg-transparent border-0 border-b border-gray-600 focus:border-cyan-500 focus:ring-0 text-cyan-300 text-sm font-mono">
                            </div>
                            <div class="bg-gray-800/50 p-3 rounded flex items-center border border-gray-700">
                                 <label class="w-32 text-xs font-bold text-gray-400 uppercase">Model</label>
                                 <input v-model="fwInfo.Model" type="text" class="flex-1 bg-transparent border-0 border-b border-gray-600 focus:border-cyan-500 focus:ring-0 text-cyan-300 text-sm font-mono">
                            </div>
                            <!-- Save Button -->
                            <div class="flex justify-end pt-2">
                                <button @click="saveFW" class="bg-purple-600 hover:bg-purple-500 text-white px-6 py-2 rounded text-xs font-bold uppercase tracking-widest shadow-lg shadow-purple-500/20 transition-all">Update Info</button>
                            </div>
                        </div>

                        <!-- Read-Only Versions -->
                         <div class="space-y-4">
                            <h4 class="text-xs font-bold text-gray-400 uppercase tracking-widest border-b border-gray-700 pb-2 mb-4">Component Versions</h4>
                            <div class="grid grid-cols-1 gap-2">
                                <div class="flex justify-between items-center py-2 border-b border-gray-800 border-dashed">
                                    <span class="text-xs text-gray-500 uppercase">System Version</span>
                                    <span class="text-sm font-mono text-cyan-300">{{ fwInfo.Version || '--' }}</span>
                                </div>
                                <div class="flex justify-between items-center py-2 border-b border-gray-800 border-dashed">
                                    <span class="text-xs text-gray-500 uppercase">WebUI</span>
                                    <span class="text-sm font-mono text-gray-300">{{ fwInfo.WebUI || '--' }}</span>
                                </div>
                                <div class="flex justify-between items-center py-2 border-b border-gray-800 border-dashed">
                                    <span class="text-xs text-gray-500 uppercase">SCC_API</span>
                                    <span class="text-sm font-mono text-gray-300">{{ fwInfo.SCC_API || '--' }}</span>
                                </div>
                                <div class="flex justify-between items-center py-2 border-b border-gray-800 border-dashed">
                                    <span class="text-xs text-gray-500 uppercase">SNMP</span>
                                    <span class="text-sm font-mono text-gray-300">{{ fwInfo.SNMP || '--' }}</span>
                                </div>
                                <div class="flex justify-between items-center py-2 border-b border-gray-800 border-dashed">
                                    <span class="text-xs text-gray-500 uppercase">Redfish</span>
                                    <span class="text-sm font-mono text-gray-300">{{ fwInfo.Redfish || '--' }}</span>
                                </div>
                                <div class="flex justify-between items-center py-2 border-b border-gray-800 border-dashed">
                                    <span class="text-xs text-gray-500 uppercase">Modbus Server</span>
                                    <span class="text-sm font-mono text-gray-300">{{ fwInfo.Modbus_Server || '--' }}</span>
                                </div>
                                <div class="flex justify-between items-center py-2 border-b border-gray-800 border-dashed bg-gray-800/30 px-2 rounded">
                                    <span class="text-xs font-bold text-gray-400 uppercase">PLC Version</span>
                                    <span class="text-sm font-mono text-yellow-500">{{ plcVersion || '--' }}</span>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </div>

            <!-- 5. Switch Version -->
             <div class="bg-gray-800/40 border border-gray-700/50 rounded-lg overflow-hidden backdrop-blur-sm transition-all hover:border-cyan-500/30 group">
                <button @click="toggleSection('switch')" class="w-full px-6 py-4 bg-gray-900/80 flex justify-between items-center text-left hover:bg-gray-800 transition-colors">
                    <div class="flex items-center space-x-3">
                        <CommandLineIcon class="w-5 h-5 text-yellow-400" />
                        <span class="font-bold text-cyan-100 tracking-wide uppercase text-sm">Logic Version Control</span>
                    </div>
                    <ChevronDownIcon class="w-5 h-5 text-cyan-500 transition-transform duration-300" :class="activeSection === 'switch' ? 'rotate-180' : ''" />
                </button>
                <div v-show="activeSection === 'switch'" class="p-6 border-t border-gray-700/50 bg-gray-900/40">
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div v-for="(val, key) in switchData" :key="key" class="bg-gray-800/50 border border-gray-700 p-4 rounded hover:border-yellow-500/50 transition-colors">
                            <span class="block text-xs font-bold text-gray-400 uppercase mb-2">{{ key.replace('_', ' ') }}</span>
                            <div class="relative">
                                <select v-model="switchData[key]" class="w-full bg-gray-900 border border-gray-600 text-white text-sm rounded p-2 focus:ring-1 focus:ring-yellow-500 focus:border-yellow-500 appearance-none">
                                    <option value="old">Legacy (V1)</option>
                                    <option value="new">Modern (V2)</option>
                                </select>
                                <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-gray-500">▼</div>
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-end mt-4">
                        <button @click="saveSwitch" class="bg-yellow-600 hover:bg-yellow-500 text-white px-6 py-2 rounded text-xs font-bold uppercase tracking-widest shadow-lg shadow-yellow-500/20 transition-all">Apply Versioning</button>
                    </div>
                </div>
            </div>

             <!-- 6. Misc (Auto, Valve, Timeout) in one group -->
             <div class="bg-gray-800/40 border border-gray-700/50 rounded-lg overflow-hidden backdrop-blur-sm transition-all hover:border-cyan-500/30 group">
                <button @click="toggleSection('misc')" class="w-full px-6 py-4 bg-gray-900/80 flex justify-between items-center text-left hover:bg-gray-800 transition-colors">
                    <div class="flex items-center space-x-3">
                        <WrenchScrewdriverIcon class="w-5 h-5 text-gray-400" />
                        <span class="font-bold text-cyan-100 tracking-wide uppercase text-sm">Advanced System Parameters</span>
                    </div>
                    <ChevronDownIcon class="w-5 h-5 text-cyan-500 transition-transform duration-300" :class="activeSection === 'misc' ? 'rotate-180' : ''" />
                </button>
                <div v-show="activeSection === 'misc'" class="p-6 border-t border-gray-700/50 bg-gray-900/40 grid grid-cols-1 xl:grid-cols-3 gap-6">
                    
                    <!-- Auto -->
                    <div class="bg-gray-800/30 p-4 rounded border border-gray-700">
                        <h4 class="font-bold text-cyan-400 text-xs uppercase mb-4 py-1 border-b border-gray-700">Auto Mode Redundancy</h4>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center">
                                <label class="text-xs text-gray-400">Water Valve (%)</label>
                                <input v-model="autoSetting.auto_water" type="number" class="w-20 bg-gray-900 border border-gray-600 rounded text-xs p-1 text-white text-right">
                            </div>
                            <div class="flex justify-between items-center">
                                <label class="text-xs text-gray-400">Pump Speed (%)</label>
                                <input v-model="autoSetting.auto_pump" type="number" class="w-20 bg-gray-900 border border-gray-600 rounded text-xs p-1 text-white text-right">
                            </div>
                            <div class="flex justify-between items-center">
                                <label class="text-xs text-gray-400">Min Opening (%)</label>
                                <input v-model="autoSetting.auto_dew_point" type="number" class="w-20 bg-gray-900 border border-gray-600 rounded text-xs p-1 text-white text-right">
                            </div>
                            <button @click="saveAuto" class="w-full mt-2 bg-gray-700 hover:bg-gray-600 text-white py-1.5 rounded text-xs font-bold uppercase transition-all">Set Auto Params</button>
                        </div>
                    </div>

                    <!-- Valve -->
                     <div class="bg-gray-800/30 p-4 rounded border border-gray-700">
                        <h4 class="font-bold text-cyan-400 text-xs uppercase mb-4 py-1 border-b border-gray-700">Valve Close Conditions</h4>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center">
                                <label class="text-xs text-gray-400">Ambient T(a) &lt;</label>
                                <div class="relative"><input v-model="valveData.ta_close_valve" type="number" class="w-20 bg-gray-900 border border-gray-600 rounded text-xs p-1 text-white text-right"><span class="absolute right-6 top-1 text-gray-500 text-[10px]">°C</span></div>
                            </div>
                            <div class="flex justify-between items-center">
                                <label class="text-xs text-gray-400">Coolant T(1) &lt;</label>
                                 <div class="relative"><input v-model="valveData.t1_close_valve" type="number" class="w-20 bg-gray-900 border border-gray-600 rounded text-xs p-1 text-white text-right"><span class="absolute right-6 top-1 text-gray-500 text-[10px]">°C</span></div>
                            </div>
                             <div class="h-[34px]"></div> <!-- Spacer -->
                            <button @click="saveValve" class="w-full mt-2 bg-gray-700 hover:bg-gray-600 text-white py-1.5 rounded text-xs font-bold uppercase transition-all">Set Valve Logic</button>
                        </div>
                    </div>

                    <!-- Timeout -->
                     <div class="bg-gray-800/30 p-4 rounded border border-gray-700">
                        <h4 class="font-bold text-cyan-400 text-xs uppercase mb-4 py-1 border-b border-gray-700">Indicator Timeout</h4>
                         <div class="flex flex-col justify-between h-[132px]">
                             <div class="flex justify-between items-center">
                                <label class="text-xs text-gray-400">Light Delay</label>
                                <div class="relative"><input v-model="timeoutLight" type="number" class="w-24 bg-gray-900 border border-gray-600 rounded text-xs p-1 text-white text-right"><span class="absolute right-6 top-1 text-gray-500 text-[10px]">sec</span></div>
                            </div>
                             <p class="text-[10px] text-gray-500 italic">Timeout before status indicators turn off or reset.</p>
                             <button @click="saveTimeout" class="w-full bg-gray-700 hover:bg-gray-600 text-white py-1.5 rounded text-xs font-bold uppercase transition-all">Set Timeout</button>
                         </div>
                    </div>

                </div>
            </div>

        </div>
    </div>
</template>

<style scoped>
/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #111827; 
}
::-webkit-scrollbar-thumb {
    background: #374151; 
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #06b6d4; 
}
</style>
