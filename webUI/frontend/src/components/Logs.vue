<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { FunnelIcon, TrashIcon, MagnifyingGlassIcon, ChevronLeftIcon, ChevronRightIcon, ArrowPathIcon } from '@heroicons/vue/24/solid'

// State
const activeTab = ref('all') // 'all' or 'shutdown'
const allLogs = ref([])
const shutdownLogs = ref([])
const loading = ref(false)
const searchQuery = ref('')
const sortKey = ref(null) // 'severity', 'on_time', etc.
const sortDesc = ref(false)

// Pagination
const currentPageAll = ref(1)
const totalPagesAll = ref(1)
const totalRecordsAll = ref(0)
const currentPageShutdown = ref(1)
const totalPagesShutdown = ref(1)
const totalRecordsShutdown = ref(0)
const itemsPerPage = 20

// Selection
const selectedAll = ref({})
const selectedShutdown = ref({})
const selectAllCheckbox = ref(false)

// Columns definitions
const columns = [
    { key: 'signal_name', label: 'Signal', class: 'hidden md:table-cell' },
    { key: 'on_time', label: 'Occur Time', sortable: true },
    { key: 'off_time', label: 'Restore Time', sortable: true },
    { key: 'severity', label: 'Severity', sortable: true },
    { key: 'signal_value', label: 'Message', class: 'w-1/3' },
]

// Computed for current view
const currentLogs = computed(() => {
    let logs = activeTab.value === 'all' ? allLogs.value : shutdownLogs.value
    
    // Client-side sorting for current page
    if (sortKey.value) {
        logs = [...logs].sort((a, b) => {
            let valA, valB
            
            if (sortKey.value === 'severity') {
                // Custom severity ranking: ALERT (2) > ERROR (1) > Other (0)
                const getScore = (name) => {
                    if (name?.startsWith('M2')) return 2
                    if (name?.startsWith('M3')) return 1
                    return 0
                }
                valA = getScore(a.signal_name)
                valB = getScore(b.signal_name)
            } else {
                valA = a[sortKey.value]
                valB = b[sortKey.value]
            }

            if (valA < valB) return sortDesc.value ? 1 : -1
            if (valA > valB) return sortDesc.value ? -1 : 1
            return 0
        })
    }
    return logs
})

const currentTotalRecords = computed(() => activeTab.value === 'all' ? totalRecordsAll.value : totalRecordsShutdown.value)
const currentTotalPages = computed(() => activeTab.value === 'all' ? totalPagesAll.value : totalPagesShutdown.value)
const currentPage = computed(() => activeTab.value === 'all' ? currentPageAll.value : currentPageShutdown.value)

// Actions
const handleSort = (key) => {
    if (sortKey.value === key) {
        sortDesc.value = !sortDesc.value
    } else {
        sortKey.value = key
        sortDesc.value = true // Default to descending logic for severity/time usually
    }
}

// Fetch Data
const fetchLogs = async (type = 'all', page = 1, isBackground = false) => {
    if (!isBackground) loading.value = true
    try {
        const endpoint = type === 'all' ? '/get_signal_records' : '/get_downtime_signal_records'
        const params = {
            page,
            limit: itemsPerPage,
            search: searchQuery.value
        }
        
        const response = await axios.get(endpoint, { params })
        const data = response.data
        
        if (type === 'all') {
            allLogs.value = data.records || []
            totalPagesAll.value = data.total_pages || 1
            totalRecordsAll.value = data.total_records || 0
            currentPageAll.value = page
        } else {
            shutdownLogs.value = data.records || []
            totalPagesShutdown.value = data.total_pages || 1
            totalRecordsShutdown.value = data.total_records || 0
            currentPageShutdown.value = page
        }
        
        // Reset selection on page change only if explicit user action (not background)
        if (!isBackground) {
            selectAllCheckbox.value = false
            if (type === 'all') selectedAll.value = {}
            else selectedShutdown.value = {}
        }
        
    } catch (error) {
        console.error(`Error fetching ${type} logs:`, error)
    } finally {
        if (!isBackground) loading.value = false
    }
}

const refreshCurrent = (isBackground = false) => {
    fetchLogs(activeTab.value, currentPage.value, isBackground)
}

// Helpers
const formatDate = (dateString) => {
    if (!dateString) return '-'
    return dateString
}

const getSeverityClass = (signalName) => {
    if (!signalName) return 'bg-gray-800 text-gray-400'
    if (signalName.startsWith('M2')) return 'bg-red-900/50 text-red-400 border border-red-500/30'
    if (signalName.startsWith('M3')) return 'bg-yellow-900/50 text-yellow-400 border border-yellow-500/30'
    return 'bg-blue-900/50 text-blue-400 border border-blue-500/30'
}

const getSeverityLabel = (signalName) => {
    if (!signalName) return 'INFO'
    if (signalName.startsWith('M2')) return 'ALERT'
    if (signalName.startsWith('M3')) return 'WARNING'
    return 'INFO'
}

const deleteSelected = async () => {
    const toDelete = []
    const source = activeTab.value === 'all' ? selectedAll.value : selectedShutdown.value
    const endpoint = activeTab.value === 'all' ? '/delete_signal_records' : '/delete_downtime_signal_records'
    
    for (const [key, isSelected] of Object.entries(source)) {
        if (isSelected) {
            // Key is 'signal_name-on_time'. Need to careful split since on_time contains hyphens (YYYY-MM-DD...)
            const firstDash = key.indexOf('-')
            const signal_name = key.substring(0, firstDash)
            const on_time = key.substring(firstDash + 1)
            
            toDelete.push({ signal_name, on_time }) 
        }
    }

    if (toDelete.length === 0) return
    
    if (!confirm(`Are you sure you want to delete ${toDelete.length} log entries?`)) return

    try {
        loading.value = true
        await axios.post(endpoint, { signals: toDelete })
        // Clear selection
        if (activeTab.value === 'all') selectedAll.value = {}
        else selectedShutdown.value = {}
        refreshCurrent()
    } catch (error) {
        console.error('Error deleting logs:', error)
        alert('Failed to delete logs. See console.')
    } finally {
        loading.value = false
    }
}

const toggleSelectAll = (checked) => {
    const records = activeTab.value === 'all' ? allLogs.value : shutdownLogs.value
    const selection = {}
    if (checked) {
        records.forEach(log => {
            selection[`${log.signal_name}-${log.on_time}`] = true
        })
    }
    if (activeTab.value === 'all') selectedAll.value = selection
    else selectedShutdown.value = selection
}

onMounted(() => {
    fetchLogs('all', 1)
    // Periodic refresh every 5s
    setInterval(() => {
        if (!loading.value) refreshCurrent(true)
    }, 5000)
})

const generateTestLogs = async () => {
    loading.value = true
    try {
        await axios.post('/api/generate_test_logs')
        setTimeout(() => refreshCurrent(), 500) // Small delay to let backend write file
    } catch (error) {
        console.error('Error generating test logs:', error)
    } finally {
        loading.value = false
    }
}
</script>

<template>
    <div class="min-h-screen bg-gray-900 text-cyan-400 p-6 font-mono selection:bg-cyan-900 selection:text-white pb-20">
        <!-- Background Grid Effect -->
        <div class="fixed inset-0 bg-[linear-gradient(rgba(17,24,39,0.9),rgba(17,24,39,0.9)),url('/grid.png')] pointer-events-none opacity-20 z-0"></div>

        <!-- Header -->
        <header class="relative z-10 mb-6 flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0 border-b border-cyan-800/50 pb-4">
            <div>
                <h1 class="text-3xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">SYSTEM LOGS</h1>
                <p class="text-xs text-gray-400 mt-1 flex items-center">
                    <span class="w-2 h-2 rounded-full mr-2" :class="loading ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'"></span>
                    EVENT TRACKING SYSTEM
                </p>
            </div>
            
             <!-- Global Controls -->
             <div class="flex items-center space-x-3 w-full md:w-auto">
                 <div class="relative flex-1 md:w-64">
                    <input v-model="searchQuery" @keyup.enter="refreshCurrent" type="text" 
                           placeholder="Search logs..." 
                           class="w-full bg-gray-800/50 text-white border border-gray-600 rounded-lg pl-10 pr-4 py-2 text-sm focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all placeholder-gray-600">
                    <MagnifyingGlassIcon class="w-4 h-4 text-cyan-600 absolute left-3 top-1/2 transform -translate-y-1/2" />
                 </div>
                 <button @click="refreshCurrent" class="p-2 bg-gray-800 border border-gray-600 hover:border-cyan-500 text-cyan-400 rounded-lg transition-colors" title="Refresh">
                     <ArrowPathIcon class="w-5 h-5" :class="{ 'animate-spin': loading }" />
                 </button>
             </div>
        </header>

        <!-- Main Content -->
        <div class="relative z-10 space-y-4">
            
            <!-- Filter Tabs & Actions -->
            <div class="flex flex-col md:flex-row justify-between items-center gap-4">
                <div class="flex space-x-2 bg-gray-800 p-1 rounded-lg border border-gray-700">
                    <button 
                        @click="activeTab = 'all'"
                        class="px-4 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider transition-all flex items-center space-x-2"
                        :class="activeTab === 'all' ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-500/30' : 'text-gray-400 hover:text-white hover:bg-gray-700'"
                    >
                        <span>All Logs</span>
                    </button>
                    <button 
                        @click="activeTab = 'shutdown'"
                        class="px-4 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider transition-all flex items-center space-x-2"
                        :class="activeTab === 'shutdown' ? 'bg-red-600 text-white shadow-lg shadow-red-500/30' : 'text-gray-400 hover:text-white hover:bg-gray-700'"
                    >
                        <span>Shutdown Errors</span>
                    </button>
                </div>

                <div class="flex items-center space-x-3">
                    <button @click="generateTestLogs" 
                            class="px-4 py-2 bg-cyan-900/30 border border-cyan-500/50 text-cyan-400 hover:bg-cyan-900/60 hover:text-cyan-300 rounded-lg text-xs font-bold uppercase tracking-widest flex items-center transition-all shadow-sm">
                        Test Log
                    </button>
                    <button @click="deleteSelected" 
                            class="px-4 py-2 bg-red-900/30 border border-red-500/50 text-red-400 hover:bg-red-900/60 hover:text-red-300 rounded-lg text-xs font-bold uppercase tracking-widest flex items-center transition-all shadow-sm">
                        <TrashIcon class="w-4 h-4 mr-2" />
                        Delete Selected
                    </button>
                </div>
            </div>

            <!-- Table Card -->
            <div class="bg-gray-800/40 border border-gray-700/50 rounded-lg overflow-hidden backdrop-blur-sm shadow-xl">
                 <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-700/50">
                        <thead class="bg-gray-900/80">
                            <tr>
                                <th scope="col" class="px-6 py-4 text-left w-12">
                                    <input type="checkbox" v-model="selectAllCheckbox" @change="toggleSelectAll($event.target.checked)" 
                                           class="rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500 cursor-pointer">
                                </th>
                                <th v-for="col in columns" :key="col.key" :class="col.class" scope="col" 
                                    class="px-6 py-4 text-left text-xs font-bold text-cyan-600 uppercase tracking-widest cursor-pointer hover:text-cyan-400 transition-colors select-none"
                                    @click="col.sortable && handleSort(col.key)">
                                    <div class="flex items-center space-x-2">
                                        <span>{{ col.label }}</span>
                                        <span v-if="col.sortable" class="text-[10px] opacity-50">
                                            <template v-if="sortKey === col.key">
                                                {{ sortDesc ? '▼' : '▲' }}
                                            </template>
                                            <template v-else>↕</template>
                                        </span>
                                    </div>
                                </th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-700/50 bg-transparent">
                            <tr v-if="loading && currentLogs.length === 0" class="text-center py-8">
                                <td colspan="6" class="p-8 text-cyan-500/50 animate-pulse">Scanning Logs...</td>
                            </tr>
                            <tr v-else-if="currentLogs.length === 0">
                                <td colspan="6" class="p-8 text-center text-gray-500 italic">No log entries found.</td>
                            </tr>
                            <tr v-for="log in currentLogs" :key="`${log.signal_name}-${log.on_time}`" 
                                class="hover:bg-cyan-900/10 transition-colors group border-l-2 border-transparent hover:border-cyan-500">
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <input type="checkbox" v-model="(activeTab === 'all' ? selectedAll : selectedShutdown)[`${log.signal_name}-${log.on_time}`]" 
                                           class="rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500 cursor-pointer">
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-200 hidden md:table-cell group-hover:text-cyan-300 transition-colors">
                                    {{ log.signal_name }}
                                </td>
                                 <td class="px-6 py-4 whitespace-nowrap text-xs text-gray-400 font-mono">
                                    {{ formatDate(log.on_time) }}
                                </td>
                                 <td class="px-6 py-4 whitespace-nowrap text-xs text-gray-400 font-mono">
                                    {{ formatDate(log.off_time) }}
                                </td>
                                 <td class="px-6 py-4 whitespace-nowrap">
                                    <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider" :class="getSeverityClass(log.signal_name)">
                                        {{ getSeverityLabel(log.signal_name) }}
                                    </span>
                                </td>
                                 <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300 max-w-xs truncate" :title="log.signal_value">
                                    {{ log.signal_value }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                 </div>
            </div>

            <!-- Footer / Pagination -->
            <div class="flex justify-between items-center bg-gray-800/30 p-4 rounded-lg border border-gray-700/50">
                <span class="text-xs text-gray-500 uppercase tracking-widest font-bold">
                    Total Selected: {{ Object.values(activeTab === 'all' ? selectedAll : selectedShutdown).filter(Boolean).length }} / {{ currentTotalRecords }}
                </span>
                <div class="flex items-center space-x-2">
                    <button 
                        @click="fetchLogs(activeTab, currentPage - 1)"
                        :disabled="currentPage <= 1"
                        class="p-2 border border-gray-600 rounded hover:bg-cyan-900/30 hover:border-cyan-500 hover:text-cyan-400 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                    >
                        <ChevronLeftIcon class="w-4 h-4" />
                    </button>
                    <span class="px-4 py-1 bg-gray-900/50 border border-gray-700 rounded text-xs font-mono text-cyan-300">
                        PAGE {{ currentPage }} / {{ currentTotalPages }}
                    </span>
                     <button 
                        @click="fetchLogs(activeTab, currentPage + 1)"
                        :disabled="currentPage >= currentTotalPages"
                        class="p-2 border border-gray-600 rounded hover:bg-cyan-900/30 hover:border-cyan-500 hover:text-cyan-400 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                    >
                        <ChevronRightIcon class="w-4 h-4" />
                    </button>
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
