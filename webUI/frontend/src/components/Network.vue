<template>
    <div class="min-h-screen bg-gray-900 text-cyan-400 p-6 font-mono selection:bg-cyan-900 selection:text-white pb-20">
        <!-- Background Grid Effect -->
        <div class="fixed inset-0 bg-[linear-gradient(rgba(17,24,39,0.9),rgba(17,24,39,0.9)),url('/grid.png')] pointer-events-none opacity-20 z-0"></div>

        <!-- Header -->
        <header class="relative z-10 mb-8 flex justify-between items-center border-b border-cyan-800 pb-4">
            <div>
                <h1 class="text-3xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">NETWORK CONFIGURATION</h1>
                <p class="text-xs text-gray-400 mt-1 flex items-center">
                    <span class="w-2 h-2 rounded-full mr-2" :class="loading ? 'bg-yellow-500 animate-pulse' : (networkError ? 'bg-red-500' : 'bg-green-500')"></span>
                    {{ loading ? 'SCANNING...' : (networkError ? 'OFFLINE' : 'ONLINE') }}
                </p>
            </div>
            
            <!-- Global Network Actions -->
            <div class="flex items-center space-x-4">
                <button @click="fetchNetworkInfo" class="px-3 py-1 bg-cyan-900/40 hover:bg-cyan-800 border border-cyan-500/50 hover:border-cyan-400 text-cyan-300 text-xs rounded transition-all uppercase tracking-widest flex items-center">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                    Refresh
                </button>
            </div>
        </header>

        <!-- Main Content -->
        <div class="relative z-10 space-y-8">
            
            <!-- Modbus Master Settings Card -->
            <section class="bg-gray-800/50 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-sm relative overflow-hidden group hover:border-cyan-500/60 transition-colors">
                <div class="absolute top-0 right-0 w-16 h-16 bg-cyan-500/5 rounded-bl-full -mr-8 -mt-8 pointer-events-none"></div>
                
                <h2 class="text-xl font-semibold mb-6 flex items-center text-cyan-300">
                    <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full mr-3 shadow-[0_0_5px_cyan]"></span>
                    MODBUS MASTER SETTINGS
                </h2>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-end">
                    <div class="space-y-2">
                        <label class="text-xs uppercase tracking-widest text-cyan-600 font-bold">Modbus IP Address</label>
                        <div class="relative">
                            <input type="text" v-model="modbusIp" 
                                   class="w-full bg-gray-900/80 text-white border border-gray-600 rounded p-3 pl-4 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all font-mono tracking-wide placeholder-gray-700" 
                                   placeholder="e.g. 192.168.1.50">
                            <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-cyan-500">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                            </div>
                        </div>
                    </div>
                    <button @click="updateModbusIp" class="h-[50px] bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded shadow-lg shadow-cyan-500/20 transition-all uppercase tracking-widest flex items-center justify-center space-x-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
                        <span>Update Config</span>
                    </button>
                </div>
            </section>

             <!-- Interfaces Grid -->
             <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
                 <section v-for="iface in interfaces" :key="iface.id" 
                          class="bg-gray-800/40 border border-gray-700/50 rounded-lg overflow-hidden flex flex-col hover:border-cyan-500/30 transition-all duration-300">
                    
                    <!-- Interface Header -->
                    <div class="bg-gray-900/80 p-4 border-b border-gray-700 flex justify-between items-center cursor-pointer select-none"
                         @click="iface.expandedInfo = !iface.expandedInfo">
                        <div class="flex items-center space-x-3">
                             <div class="w-8 h-8 rounded bg-cyan-900/30 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                                <span class="font-bold text-sm">{{ iface.id }}</span>
                             </div>
                             <div>
                                 <h3 class="font-bold text-cyan-300 tracking-wide">{{ iface.name }}</h3>
                                 <p class="text-[10px] text-gray-500 uppercase tracking-wider">{{ iface.type === 'eth' ? 'Ethernet Interface' : 'USB/Peripheral' }}</p>
                             </div>
                        </div>
                        <div class="flex items-center space-x-3">
                            <span class="text-xs px-2 py-0.5 rounded border" 
                                  :class="iface.info.ipv4?.address ? 'border-green-500/30 text-green-400 bg-green-900/10' : 'border-gray-600 text-gray-500'">
                                {{ iface.info.ipv4?.address ? 'CONNECTED' : 'DOWN' }}
                            </span>
                            <svg class="w-5 h-5 text-gray-500 transition-transform duration-300" 
                                 :class="iface.expandedInfo ? 'rotate-180' : ''"
                                 fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </div>
                    </div>

                    <!-- Interface Settings Body -->
                    <div v-show="iface.expandedInfo" class="p-6 space-y-6 flex-1 bg-gray-800/20">
                        
                        <!-- IPv4 Settings -->
                        <div class="space-y-4">
                             <div class="flex justify-between items-center border-b border-gray-700 pb-2 mb-2">
                                <h4 class="text-xs uppercase tracking-widest text-cyan-600 font-bold">IPv4 Configuration</h4>
                                <label class="flex items-center cursor-pointer space-x-2">
                                    <span class="text-xs text-gray-400 font-bold mr-1">DHCP</span>
                                    <div class="relative">
                                        <input type="checkbox" v-model="iface.setting.ipv4.dhcp" class="sr-only">
                                        <div class="w-10 h-5 bg-gray-700 rounded-full shadow-inner"></div>
                                        <div class="dot absolute left-1 top-1 bg-white w-3 h-3 rounded-full transition" 
                                             :class="iface.setting.ipv4.dhcp ? 'transform translate-x-5 bg-cyan-400' : ''"></div>
                                    </div>
                                </label>
                             </div>

                             <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  <!-- IP Address -->
                                  <div class="space-y-1">
                                      <label class="text-[10px] uppercase text-gray-500">IP Address</label>
                                      <input type="text" v-model="iface.setting.ipv4.ip" :disabled="iface.setting.ipv4.dhcp"
                                             class="w-full bg-gray-900/50 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-cyan-500 focus:bg-gray-900 outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                             placeholder="0.0.0.0">
                                  </div>
                                  <!-- Subnet Mask -->
                                  <div class="space-y-1">
                                      <label class="text-[10px] uppercase text-gray-500">Subnet Mask</label>
                                      <input type="text" v-model="iface.setting.ipv4.mask" :disabled="iface.setting.ipv4.dhcp"
                                             class="w-full bg-gray-900/50 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-cyan-500 focus:bg-gray-900 outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                             placeholder="255.255.255.0">
                                  </div>
                                  <!-- Gateway -->
                                  <div class="space-y-1 md:col-span-2">
                                      <label class="text-[10px] uppercase text-gray-500">Default Gateway</label>
                                      <input type="text" v-model="iface.setting.ipv4.gateway" :disabled="iface.setting.ipv4.dhcp"
                                             class="w-full bg-gray-900/50 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-cyan-500 focus:bg-gray-900 outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                             placeholder="192.168.1.1">
                                  </div>
                             </div>
                        </div>

                              <!-- DNS Settings -->
                              <div class="space-y-4 pt-4 border-t border-gray-700/50">
                                  <div class="flex items-center justify-between">
                                      <label class="flex items-center cursor-pointer space-x-2">
                                        <div class="relative">
                                            <input type="checkbox" v-model="iface.setting.ipv4.dnsAuto" class="sr-only">
                                            <div class="w-8 h-4 bg-gray-700 rounded-full shadow-inner"></div>
                                            <div class="dot absolute left-1 top-1 bg-white w-2 h-2 rounded-full transition" 
                                                 :class="iface.setting.ipv4.dnsAuto ? 'transform translate-x-4 bg-cyan-400' : ''"></div>
                                        </div>
                                        <span class="text-[10px] uppercase text-gray-400">Obtain DNS Automatically</span>
                                      </label>
                                  </div>

                                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                      <div class="space-y-1">
                                          <label class="text-[10px] uppercase text-gray-500">DNS (Primary)</label>
                                          <input type="text" v-model="iface.setting.ipv4.dnsPri" :disabled="iface.setting.ipv4.dnsAuto"
                                                 class="w-full bg-gray-900/50 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-cyan-500 focus:bg-gray-900 outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                                      </div>
                                      <div class="space-y-1">
                                          <label class="text-[10px] uppercase text-gray-500">DNS (Secondary)</label>
                                          <input type="text" v-model="iface.setting.ipv4.dnsSec" :disabled="iface.setting.ipv4.dnsAuto"
                                                 class="w-full bg-gray-900/50 text-white border border-gray-600 rounded p-2 text-sm font-mono focus:border-cyan-500 focus:bg-gray-900 outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                                      </div>
                                  </div>
                              </div>


                         <!-- IPv6 Settings -->
                         <div class="pt-6 border-t border-gray-700">
                             <div class="flex justify-between items-center mb-4">
                                 <h4 class="text-xs uppercase tracking-widest text-[#5c6b7f] font-bold">IPv6 Configuration</h4>
                                 <label class="flex items-center cursor-pointer space-x-2">
                                    <span class="text-xs text-gray-500 font-bold mr-1">DHCP</span>
                                    <div class="relative">
                                        <input type="checkbox" v-model="iface.setting.ipv6.dhcp" class="sr-only">
                                        <div class="w-8 h-4 bg-gray-700 rounded-full shadow-inner"></div>
                                        <div class="dot absolute left-1 top-1 bg-white w-2 h-2 rounded-full transition" 
                                             :class="iface.setting.ipv6.dhcp ? 'transform translate-x-4 bg-cyan-400' : ''"></div>
                                    </div>
                                </label>
                             </div>
                             
                             <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                 <div class="space-y-1 md:col-span-2">
                                      <label class="text-[10px] uppercase text-gray-600">IPv6 Address</label>
                                      <input type="text" v-model="iface.setting.ipv6.ip" :disabled="iface.setting.ipv6.dhcp"
                                             class="w-full bg-gray-900/30 text-gray-400 border border-gray-700/50 rounded p-2 text-sm font-mono focus:border-cyan-500/50 outline-none transition-colors disabled:opacity-50">
                                  </div>
                                  <div class="space-y-1">
                                      <label class="text-[10px] uppercase text-gray-600">Subnet Prefix Length</label>
                                      <input type="text" v-model="iface.setting.ipv6.prefix" :disabled="iface.setting.ipv6.dhcp"
                                             class="w-full bg-gray-900/30 text-gray-400 border border-gray-700/50 rounded p-2 text-sm font-mono focus:border-cyan-500/50 outline-none transition-colors disabled:opacity-50">
                                  </div>
                                  <div class="space-y-1">
                                      <label class="text-[10px] uppercase text-gray-600">Default Gateway</label>
                                      <input type="text" v-model="iface.setting.ipv6.gateway" :disabled="iface.setting.ipv6.dhcp"
                                             class="w-full bg-gray-900/30 text-gray-400 border border-gray-700/50 rounded p-2 text-sm font-mono focus:border-cyan-500/50 outline-none transition-colors disabled:opacity-50">
                                  </div>
                             </div>

                             <!-- IPv6 DNS -->
                             <div class="space-y-4 pt-4 mt-2">
                                  <div class="flex items-center justify-between">
                                      <label class="flex items-center cursor-pointer space-x-2">
                                        <div class="relative">
                                            <input type="checkbox" v-model="iface.setting.ipv6.dnsAuto" class="sr-only">
                                            <div class="w-8 h-4 bg-gray-700 rounded-full shadow-inner"></div>
                                            <div class="dot absolute left-1 top-1 bg-white w-2 h-2 rounded-full transition" 
                                                 :class="iface.setting.ipv6.dnsAuto ? 'transform translate-x-4 bg-cyan-400' : ''"></div>
                                        </div>
                                        <span class="text-[10px] uppercase text-gray-500">Obtain DNS Automatically</span>
                                      </label>
                                  </div>
                                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                      <div class="space-y-1">
                                          <label class="text-[10px] uppercase text-gray-600">DNS (Primary)</label>
                                          <input type="text" v-model="iface.setting.ipv6.dnsPri" :disabled="iface.setting.ipv6.dnsAuto"
                                                 class="w-full bg-gray-900/30 text-gray-400 border border-gray-700/50 rounded p-2 text-sm font-mono focus:border-cyan-500/50 outline-none transition-colors disabled:opacity-50">
                                      </div>
                                      <div class="space-y-1">
                                          <label class="text-[10px] uppercase text-gray-600">DNS (Secondary)</label>
                                          <input type="text" v-model="iface.setting.ipv6.dnsSec" :disabled="iface.setting.ipv6.dnsAuto"
                                                 class="w-full bg-gray-900/30 text-gray-400 border border-gray-700/50 rounded p-2 text-sm font-mono focus:border-cyan-500/50 outline-none transition-colors disabled:opacity-50">
                                      </div>
                                  </div>
                             </div>
                         </div>

                         <!-- Action Footer -->
                         <div class="mt-6 pt-4 border-t border-gray-700/50 flex justify-end">
                             <button class="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded shadow-lg shadow-cyan-500/20 uppercase tracking-wider transition-all"
                                     @click="applySettings(iface)">
                                 Apply Changes
                             </button>
                         </div>

                    </div>
                 </section>
             </div>

        </div>

        <!-- Notification / Status Banner (Optional) -->
        <transition name="fade">
             <div v-if="networkError" class="fixed bottom-6 right-6 bg-red-900/90 border border-red-500 text-white p-4 rounded shadow-2xl z-50 flex items-center space-x-3 backdrop-blur-md max-w-md">
                 <XCircleIcon class="w-6 h-6 text-red-400" />
                 <div>
                     <h4 class="font-bold text-sm">System Alert</h4>
                     <p class="text-xs text-red-200">{{ networkError }}</p>
                 </div>
             </div>
        </transition>

    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { CheckCircleIcon, XCircleIcon } from '@heroicons/vue/24/solid'

const modbusIp = ref('')
const loading = ref(true)
const networkError = ref(null)

// Data structure mimicking legacy UI:
// Interfaces: 1, 2 (Ethernet), U1, U2 (USB/Other)
const interfaces = ref([
    { 
        id: '1', name: 'Interface 1', type: 'eth', info: {}, expandedInfo: true,
        setting: {
            ipv4: { dhcp: false, ip: '', mask: '', gateway: '', dnsAuto: false, dnsPri: '', dnsSec: '' },
            ipv6: { dhcp: false, ip: '', prefix: '', gateway: '', dnsAuto: false, dnsPri: '', dnsSec: '' }
        }
    },
    { 
        id: '2', name: 'Interface 2', type: 'eth', info: {}, expandedInfo: true,
        setting: {
            ipv4: { dhcp: false, ip: '', mask: '', gateway: '', dnsAuto: false, dnsPri: '', dnsSec: '' },
            ipv6: { dhcp: false, ip: '', prefix: '', gateway: '', dnsAuto: false, dnsPri: '', dnsSec: '' }
        }
    },
    { 
        id: 'U1', name: 'USB Interface 1', type: 'usb', info: {}, expandedInfo: false,
        setting: {
            ipv4: { dhcp: false, ip: '', mask: '', gateway: '', dnsAuto: false, dnsPri: '', dnsSec: '' },
            ipv6: { dhcp: false, ip: '', prefix: '', gateway: '', dnsAuto: false, dnsPri: '', dnsSec: '' }
        }
    },
    { 
        id: 'U2', name: 'USB Interface 2', type: 'usb', info: {}, expandedInfo: false,
        setting: {
            ipv4: { dhcp: false, ip: '', mask: '', gateway: '', dnsAuto: false, dnsPri: '', dnsSec: '' },
            ipv6: { dhcp: false, ip: '', prefix: '', gateway: '', dnsAuto: false, dnsPri: '', dnsSec: '' }
        }
    }
])

// Mock Data for fallback
const mockNetworkData = {
    ethernet_info1: { ipv4: { dhcp: false, address: '192.168.1.100', netmask: '255.255.255.0', gateway: '192.168.1.1' } },
    ethernet_info2: { ipv4: { dhcp: true, address: '10.0.0.50', netmask: '255.0.0.0', gateway: '10.0.0.1' } },
    ethernet_info3: {}, ethernet_info4: {}
}

const fetchModbusIp = async () => {
    try {
        // const response = await axios.get('/get_modbus_ip')
        // modbusIp.value = response.data.modbus_ip
        // Mocking for now to ensure UI shows something
         modbusIp.value = '192.168.1.50' 
    } catch (err) {
        console.warn("Failed to fetch Modbus IP", err)
        modbusIp.value = '127.0.0.1' 
    }
}

const updateModbusIp = async () => {
    try {
        const response = await axios.post('/update_modbus_ip', { modbus_ip: modbusIp.value })
        alert(response.data.message || 'Configuration Uploaded')
    } catch (err) {
        alert("Command Failed: Device Unreachable")
    }
}

const fetchNetworkInfo = async () => {
    loading.value = true
    try {
        // Simulate API delay
        await new Promise(r => setTimeout(r, 800))
        
        // Use Mock data since backend might be offline in dev
        const data = mockNetworkData 
        // const response = await axios.get('/get_network_info')
        // const data = response.data 

        const mapping = [data.ethernet_info1, data.ethernet_info2, data.ethernet_info3, data.ethernet_info4]
        
        interfaces.value.forEach((iface, idx) => {
            let raw = mapping[idx]
            if (typeof raw === 'string') {
                try { raw = JSON.parse(raw) } catch(e) { raw = {} }
            }
            iface.info = raw || {}
            
            // Populate settings with current info values as default
            iface.setting.ipv4.ip = iface.info.ipv4?.address || ''
            iface.setting.ipv4.mask = iface.info.ipv4?.netmask || ''
            iface.setting.ipv4.gateway = iface.info.ipv4?.gateway || ''
            iface.setting.ipv4.dhcp = iface.info.ipv4?.dhcp || false 
        })
        networkError.value = null
    } catch (err) {
        console.warn("Using Mock Data due to API error", err)
        networkError.value = "CONNECTION LOST - SHOWING CACHED DATA"
    } finally {
        loading.value = false
    }
}

const applySettings = (iface) => {
    // Logic to save IP settings
    console.log(`Applying settings for ${iface.name}:`, iface.setting)
    alert(`Settings Applied to ${iface.name}`)
}

onMounted(() => {
    fetchModbusIp()
    fetchNetworkInfo()
})
</script>

<style scoped>
/* Custom Scrollbar for this page */
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

.scanline {
    background: linear-gradient(
        to bottom,
        transparent 50%,
        rgba(6, 182, 212, 0.1) 51%,
        transparent 52%
    );
    background-size: 100% 4px;
    animation: scanline 10s linear infinite;
    pointer-events: none;
}
@keyframes scanline {
    0% { background-position: 0 0; }
    100% { background-position: 0 100%; }
}
</style>
