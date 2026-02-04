<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Cog6ToothIcon } from '@heroicons/vue/24/solid'

const loading = ref(true)
const settingsData = ref({})

// Unit
const currentUnit = ref('metric')
const pendingUnit = ref('metric')

// Password
const pwdLast = ref('')
const pwdNew = ref('')
const pwdConfirm = ref('')
const showPwd = ref(false)

// Time
const timeMode = ref('setTime')
const manualTime = ref('')
const selectedTimezone = ref('Asia/Taipei')
const ntpServer = ref('ntp.ubuntu.com')
const systemTime = ref('')

// Other
const logInterval = ref(5)
const closeValveStop = ref(false)
const snmp = ref({ trapIp: '', community: '' })

// Initialization
const fetchSettings = async () => {
    try {
        const [sysRes, timeRes, snmpRes, valveRes] = await Promise.all([
            axios.get('/get_data_systemset'),
            axios.get('/get_system_time'),
            axios.get('/get_snmp_setting'),
            axios.get('/read_close_valve_stop')
        ])

        // Unit & Interval
        const sys = sysRes.data
        currentUnit.value = sys.system_data.value.unit
        pendingUnit.value = currentUnit.value
        logInterval.value = sys.sampling_rate.number

        // Time
        systemTime.value = timeRes.data.system_time
        manualTime.value = timeRes.data.system_time // default to current
        
        // SNMP
        snmp.value.trapIp = snmpRes.data.trap_ip_address
        snmp.value.community = snmpRes.data.read_community

        // Valve
        closeValveStop.value = valveRes.data.success

    } catch (err) {
        console.error("Fetch settings error:", err)
    } finally {
        loading.value = false
    }
}

// Actions
const applyUnit = async () => {
    try {
        await axios.post('/systemSetting/unit_set', { value: pendingUnit.value })
        alert('Unit setting updated')
        fetchSettings()
    } catch (err) {
        alert('Failed to update unit')
    }
}

const updatePassword = async () => {
    if (pwdNew.value !== pwdConfirm.value) {
        alert('Passwords do not match')
        return
    }
    if (!confirm('Are you sure you want to change the password?')) return

    try {
        const payload = {
            pwd_package: {
                last_pwd: pwdLast.value,
                password: pwdNew.value,
                passwordcfm: pwdConfirm.value
            }
        }
        const res = await axios.post('/update_password', payload)
        if (res.data.status === 'success') {
            alert('Password updated successfully')
            pwdLast.value = ''
            pwdNew.value = ''
            pwdConfirm.value = ''
        } else {
            alert('Failed: ' + res.data.message)
        }
    } catch (err) {
        alert('Error updating password')
    }
}

const applyTime = async () => {
    if (!confirm('Updating time will log out all users. Continue?')) return
    
    try {
        await axios.post('/set_time', { value: manualTime.value })
         alert('Time updated. Please verify.')
         fetchSettings()
    } catch (err) {
        alert('Failed to update time')
    }
}

const applyLogInterval = async () => {
    const val = parseFloat(logInterval.value)
    if (isNaN(val) || val < 2 || val > 30) {
        alert('Interval must be between 2 and 30 seconds')
        return
    }
     try {
        await axios.post('/store_sampling_rate', { sampleRate: val })
        alert('Log interval updated')
    } catch (err) {
        alert('Failed to update interval')
    }
}

const applySnmp = async () => {
     try {
        await axios.post('/store_snmp_setting', { 
            trap_ip_address: snmp.value.trapIp,
            read_community: snmp.value.community,
            v3_switch: false
        })
        alert('SNMP settings updated')
    } catch (err) {
        alert('Failed to update SNMP')
    }
}

const resetPasswordDefault = async () => {
    if (!confirm('Reset password to default (123456)?')) return
    try {
        // alert('Password reset functionality requires backend implementation.')
        // Simulating the behavior mentioned in legacy code, or alerting user
         alert('Reset request sent (Simulation)')
    } catch (err) {
        alert('Error resetting password')
    }
}

const applyValve = async () => {
    try {
        await axios.post('/store_close_valve_stop', { success: closeValveStop.value })
        alert('Valve setting updated')
    } catch (err) {
        alert('Failed to update Valve setting')
    }
}

onMounted(() => {
    fetchSettings()
    // Periodic refresh of system time could be added here
})
</script>

<template>
    <div class="min-h-screen bg-gray-900 text-cyan-400 p-6 font-mono selection:bg-cyan-900 selection:text-white pb-20">
        <!-- Background Grid Effect -->
        <div class="fixed inset-0 bg-[linear-gradient(rgba(17,24,39,0.9),rgba(17,24,39,0.9)),url('/grid.png')] pointer-events-none opacity-20 z-0"></div>

        <!-- Header -->
        <header class="relative z-10 mb-8 flex justify-between items-center border-b border-cyan-800 pb-4">
            <div>
                <h1 class="text-3xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">SYSTEM SETTINGS</h1>
                <p class="text-xs text-gray-400 mt-1 flex items-center">
                    <span class="w-2 h-2 rounded-full mr-2 bg-green-500"></span>
                    CONFIGURATION PANEL
                </p>
            </div>
            <div class="flex items-center space-x-4">
                <button @click="fetchSettings" class="px-3 py-1 bg-cyan-900/40 hover:bg-cyan-800 border border-cyan-500/50 hover:border-cyan-400 text-cyan-300 text-xs rounded transition-all uppercase tracking-widest flex items-center">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                    Refresh Data
                </button>
            </div>
        </header>

        <!-- Main Grid -->
        <div class="relative z-10 grid grid-cols-1 xl:grid-cols-2 gap-8">

            <!-- 1. Unit Settings -->
            <section class="bg-gray-800/50 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-sm relative overflow-hidden group hover:border-cyan-500/60 transition-colors">
                <div class="absolute top-0 right-0 w-12 h-12 bg-cyan-500/5 rounded-bl-full -mr-6 -mt-6 pointer-events-none"></div>
                <h3 class="text-sm font-bold uppercase tracking-widest text-cyan-300 mb-6 border-b border-cyan-500/30 pb-2 flex items-center">
                    <span class="w-1.5 h-4 bg-cyan-500 mr-3"></span>
                    Unit Standard
                </h3>
                
                <div class="flex items-center justify-between">
                    <label class="text-xs uppercase text-gray-400 font-bold">Display Unit System</label>
                    <div class="flex items-center space-x-4">
                         <div class="relative">
                            <select v-model="pendingUnit" class="appearance-none bg-gray-900/80 border border-gray-600 hover:border-cyan-500 text-white text-sm rounded px-4 py-2 pr-8 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition-colors cursor-pointer min-w-[150px]">
                                <option value="metric">Metric (SI)</option>
                                <option value="imperial">Imperial</option>
                            </select>
                            <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-cyan-500">
                                <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                            </div>
                         </div>
                         <div class="flex space-x-2">
                             <button @click="applyUnit" class="px-3 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded uppercase tracking-wider shadow-[0_0_10px_rgba(6,182,212,0.2)] transition-all">
                                 Apply
                             </button>
                             <button @click="pendingUnit = currentUnit" class="px-3 py-2 border border-gray-600 hover:border-gray-400 text-gray-400 hover:text-white text-xs font-bold rounded uppercase tracking-wider transition-all">
                                 Reset
                             </button>
                         </div>
                    </div>
                </div>
            </section>

             <!-- 2. DateTime Settings -->
            <section class="bg-gray-800/50 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-sm relative overflow-hidden group hover:border-cyan-500/60 transition-colors">
                <div class="absolute top-0 right-0 w-12 h-12 bg-cyan-500/5 rounded-bl-full -mr-6 -mt-6 pointer-events-none"></div>
                <h3 class="text-sm font-bold uppercase tracking-widest text-cyan-300 mb-6 border-b border-cyan-500/30 pb-2 flex items-center">
                    <span class="w-1.5 h-4 bg-cyan-500 mr-3"></span>
                    System Time
                </h3>
                
                <div class="space-y-6">
                    <div class="flex justify-between items-center bg-gray-900/50 p-3 rounded border border-gray-700">
                        <span class="text-xs uppercase text-gray-500 font-bold">Current Time</span>
                        <span class="font-mono text-xl text-yellow-400 tracking-wider">{{ systemTime || '--:--:--' }}</span>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
                        <div class="space-y-1">
                            <label class="text-[10px] uppercase text-gray-500 font-bold">Manual Set</label>
                            <input type="datetime-local" v-model="manualTime" step="1" 
                                   class="w-full bg-gray-900/80 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all [color-scheme:dark]">
                        </div>
                        <button @click="applyTime" class="h-[38px] bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded uppercase tracking-wider shadow-[0_0_10px_rgba(6,182,212,0.2)] transition-all flex items-center justify-center">
                            Synchronize
                        </button>
                    </div>
                </div>
            </section>

             <!-- 3. Valve Logic -->
             <section class="bg-gray-800/50 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-sm relative overflow-hidden group hover:border-cyan-500/60 transition-colors">
                <div class="absolute top-0 right-0 w-12 h-12 bg-cyan-500/5 rounded-bl-full -mr-6 -mt-6 pointer-events-none"></div>
                <h3 class="text-sm font-bold uppercase tracking-widest text-cyan-300 mb-6 border-b border-cyan-500/30 pb-2 flex items-center">
                    <span class="w-1.5 h-4 bg-cyan-500 mr-3"></span>
                    Valve Control Logic
                </h3>
                
                <div class="flex items-center justify-between">
                     <div class="space-y-1">
                        <label class="text-sm text-gray-300 font-bold">Auto-Close on Stop</label>
                        <p class="text-[10px] text-gray-500 max-w-[250px]">Automatically close water valve when system enters STOP mode.</p>
                     </div>
                     <div class="flex items-center space-x-4">
                        <label class="flex items-center cursor-pointer space-x-3">
                            <div class="relative">
                                <input type="checkbox" v-model="closeValveStop" class="sr-only">
                                <div class="w-12 h-6 bg-gray-700 rounded-full shadow-inner border border-gray-600"></div>
                                <div class="dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform duration-300" 
                                     :class="closeValveStop ? 'transform translate-x-6 bg-cyan-400 shadow-[0_0_8px_cyan]' : ''"></div>
                            </div>
                            <span class="text-xs font-bold uppercase" :class="closeValveStop ? 'text-cyan-400' : 'text-gray-500'">{{ closeValveStop ? 'Enabled' : 'Disabled' }}</span>
                        </label>
                        <button @click="applyValve" class="ml-4 px-3 py-1.5 border border-cyan-500/50 text-cyan-400 hover:bg-cyan-900/30 text-xs rounded uppercase transition-all">Save</button>
                     </div>
                </div>
            </section>

             <!-- 4. Log Interval -->
             <section class="bg-gray-800/50 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-sm relative overflow-hidden group hover:border-cyan-500/60 transition-colors">
                <div class="absolute top-0 right-0 w-12 h-12 bg-cyan-500/5 rounded-bl-full -mr-6 -mt-6 pointer-events-none"></div>
                <h3 class="text-sm font-bold uppercase tracking-widest text-cyan-300 mb-6 border-b border-cyan-500/30 pb-2 flex items-center">
                    <span class="w-1.5 h-4 bg-cyan-500 mr-3"></span>
                    Data Logging
                </h3>
                
                <div class="flex items-end space-x-4">
                     <div class="space-y-1 flex-1">
                        <label class="text-[10px] uppercase text-gray-500 font-bold">Sampling Interval (Sec)</label>
                        <div class="relative">
                             <input type="number" v-model="logInterval" min="2" max="30"
                                   class="w-full bg-gray-900/80 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all">
                             <span class="absolute right-3 top-2 text-xs text-gray-500">sec</span>
                        </div>
                     </div>
                     <button @click="applyLogInterval" class="h-[38px] px-6 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded uppercase tracking-wider shadow-[0_0_10px_rgba(6,182,212,0.2)] transition-all">
                        Update Rate
                     </button>
                </div>
                <p class="text-[10px] text-gray-500 mt-2">* Allowed range: 2 - 30 seconds.</p>
            </section>

             <!-- 5. SNMP Settings -->
             <section class="bg-gray-800/50 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-sm relative overflow-hidden group hover:border-cyan-500/60 transition-colors">
                <div class="absolute top-0 right-0 w-12 h-12 bg-cyan-500/5 rounded-bl-full -mr-6 -mt-6 pointer-events-none"></div>
                <h3 class="text-sm font-bold uppercase tracking-widest text-cyan-300 mb-6 border-b border-cyan-500/30 pb-2 flex items-center">
                    <span class="w-1.5 h-4 bg-cyan-500 mr-3"></span>
                    SNMP Configuration
                </h3>
                
                <div class="grid grid-cols-1 gap-4">
                     <div class="space-y-1">
                        <label class="text-[10px] uppercase text-gray-500 font-bold">Trap Server IP</label>
                        <input v-model="snmp.trapIp" type="text" 
                               class="w-full bg-gray-900/80 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all" 
                               placeholder="e.g. 192.168.1.100">
                    </div>
                    <div class="space-y-1">
                        <label class="text-[10px] uppercase text-gray-500 font-bold">Read Community String</label>
                        <input v-model="snmp.community" type="text" 
                               class="w-full bg-gray-900/80 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all" 
                               placeholder="public">
                    </div>
                    <div class="flex justify-end mt-2">
                        <button @click="applySnmp" class="px-6 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded uppercase tracking-wider shadow-[0_0_10px_rgba(6,182,212,0.2)] transition-all">
                            Save Config
                        </button>
                    </div>
                </div>
            </section>

             <!-- 6. Security (Password) -->
             <section class="bg-gray-800/50 border border-red-500/30 rounded-lg p-6 backdrop-blur-sm relative overflow-hidden group hover:border-red-500/60 transition-colors xl:col-span-2">
                <div class="absolute top-0 right-0 w-12 h-12 bg-red-500/5 rounded-bl-full -mr-6 -mt-6 pointer-events-none"></div>
                <h3 class="text-sm font-bold uppercase tracking-widest text-red-400 mb-6 border-b border-red-500/30 pb-2 flex items-center">
                    <span class="w-1.5 h-4 bg-red-500 mr-3"></span>
                    Security Access
                </h3>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
                     <div class="space-y-1">
                        <label class="text-[10px] uppercase text-gray-500 font-bold">Current Password</label>
                        <input :type="showPwd ? 'text' : 'password'" v-model="pwdLast" 
                               class="w-full bg-gray-900/80 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-red-500 focus:ring-1 focus:ring-red-500 outline-none transition-all">
                    </div>
                    <div class="space-y-1">
                        <label class="text-[10px] uppercase text-gray-500 font-bold">New Password</label>
                        <input :type="showPwd ? 'text' : 'password'" v-model="pwdNew" 
                               class="w-full bg-gray-900/80 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-red-500 focus:ring-1 focus:ring-red-500 outline-none transition-all">
                    </div>
                     <div class="space-y-1">
                        <label class="text-[10px] uppercase text-gray-500 font-bold">Confirm New Password</label>
                        <input :type="showPwd ? 'text' : 'password'" v-model="pwdConfirm" 
                               class="w-full bg-gray-900/80 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-red-500 focus:ring-1 focus:ring-red-500 outline-none transition-all">
                    </div>
                </div>

                <div class="flex items-center justify-between mt-6 pt-4 border-t border-gray-700/50">
                     <label class="flex items-center space-x-2 text-xs text-gray-500 cursor-pointer select-none hover:text-gray-300">
                        <input type="checkbox" v-model="showPwd" class="rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500">
                        <span>Reveal Characters</span>
                    </label>
                    <div class="space-x-3">
                        <button @click="resetPasswordDefault" class="px-4 py-2 border border-red-500/40 text-red-400 hover:bg-red-900/20 text-xs font-bold rounded uppercase tracking-wider transition-all">
                            Reset Default
                        </button>
                         <button @click="updatePassword" class="px-6 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded uppercase tracking-wider shadow-[0_0_10px_rgba(239,68,68,0.2)] transition-all">
                            Change Password
                        </button>
                    </div>
                </div>
            </section>

        </div>
    </div>
</template>

<style scoped>
/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
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
