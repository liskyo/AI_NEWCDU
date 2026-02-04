<script setup>
import { ref } from 'vue'
import { CloudArrowDownIcon, CloudArrowUpIcon, DocumentCheckIcon, ShieldCheckIcon } from '@heroicons/vue/24/solid'

const isProcessing = ref(false)
const processStatus = ref('')
const processProgress = ref(0)
const lastBackup = ref('2025-10-24 14:30:22')

const downloadConfig = () => {
    isProcessing.value = true
    processStatus.value = 'Preparing Configuration Package...'
    processProgress.value = 10
    
    setTimeout(() => { processProgress.value = 40; processStatus.value = 'Encrypting Sensitive Data...' }, 1000)
    setTimeout(() => { processProgress.value = 80; processStatus.value = 'Finalizing JSON Structure...' }, 2000)
    setTimeout(() => { 
        processProgress.value = 100; 
        processStatus.value = 'Download Started' 
        isProcessing.value = false
        
        // Mock Download
        const element = document.createElement('a');
        const file = new Blob(['{"mock_config": "true", "version": "1.0"}'], {type: 'application/json'});
        element.href = URL.createObjectURL(file);
        element.download = `cdu_config_backup_${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(element);
        element.click();
        
        lastBackup.value = new Date().toLocaleString()
    }, 3000)
}

const restoreConfig = () => {
     // Mock File Input Trigger
     document.getElementById('file-upload').click()
}

const handleFile = (e) => {
    if(e.target.files.length > 0) {
        if(confirm(`Restore configuration from ${e.target.files[0].name}? System will restart.`)) {
             isProcessing.value = true
             processStatus.value = 'Verifying Integrity...'
             processProgress.value = 20
             setTimeout(() => { processProgress.value = 60; processStatus.value = 'Writing Parameters...' }, 1500)
             setTimeout(() => { 
                 processProgress.value = 100; 
                 processStatus.value = 'Success! System Restarting...' 
                 setTimeout(() => isProcessing.value = false, 1000)
             }, 3000)
        }
    }
}
</script>

<template>
    <div class="min-h-screen bg-gray-900 text-cyan-400 p-6 font-mono pb-20 flex items-center justify-center">
        <div class="fixed inset-0 bg-[linear-gradient(rgba(17,24,39,0.95),rgba(17,24,39,0.95)),url('/grid.png')] pointer-events-none opacity-20 z-0"></div>

        <div class="relative z-10 w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-8">
            
            <!-- Backup Card -->
            <div class="bg-gray-800/60 border border-gray-700 hover:border-cyan-500 transition-all rounded-xl p-8 flex flex-col items-center text-center group cursor-pointer" @click="downloadConfig">
                <div class="w-24 h-24 rounded-full bg-cyan-900/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 border border-cyan-500/30 group-hover:border-cyan-400">
                    <CloudArrowDownIcon class="w-12 h-12 text-cyan-400" />
                </div>
                <h2 class="text-2xl font-bold text-white mb-2">BACKUP CONFIG</h2>
                <p class="text-sm text-gray-400 mb-6">Export all system parameters, PID settings, and thresholds to a secure JSON file.</p>
                
                <div class="w-full bg-black/40 rounded p-3 text-xs text-gray-500 border border-gray-800">
                    Last Backup: <span class="text-cyan-500 font-bold">{{ lastBackup }}</span>
                </div>
                
                <button class="mt-6 px-8 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded uppercase tracking-widest shadow-lg shadow-cyan-500/20 transition-all w-full">
                    Download
                </button>
            </div>

            <!-- Restore Card -->
            <div class="bg-gray-800/60 border border-gray-700 hover:border-purple-500 transition-all rounded-xl p-8 flex flex-col items-center text-center group cursor-pointer relative overflow-hidden" @click="restoreConfig">
                 <div class="absolute inset-0 bg-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                 
                <div class="w-24 h-24 rounded-full bg-purple-900/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 border border-purple-500/30 group-hover:border-purple-400 relative z-10">
                    <CloudArrowUpIcon class="w-12 h-12 text-purple-400" />
                </div>
                <h2 class="text-2xl font-bold text-white mb-2 relative z-10">RESTORE SYSTEM</h2>
                <p class="text-sm text-gray-400 mb-6 relative z-10">Import parameters from a previously saved backup file. Requires system restart.</p>
                
                <div class="w-full bg-black/40 rounded p-3 text-xs text-gray-500 border border-gray-800 relative z-10">
                    <div class="flex items-center justify-center space-x-2">
                        <ShieldCheckIcon class="w-4 h-4 text-green-500" />
                        <span>Integrity Check Active</span>
                    </div>
                </div>

                <button class="mt-6 px-8 py-3 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded uppercase tracking-widest shadow-lg shadow-purple-500/20 transition-all w-full relative z-10">
                    Select File
                </button>
                <input type="file" id="file-upload" class="hidden" accept=".json" @change="handleFile">
            </div>

            <!-- Overlay for Processing -->
            <div v-if="isProcessing" class="absolute inset-0 bg-gray-900/90 backdrop-blur-md rounded-xl z-50 flex flex-col items-center justify-center border border-cyan-500">
                <div class="w-64 h-2 bg-gray-700 rounded-full overflow-hidden mb-4">
                    <div class="h-full bg-cyan-400 transition-all duration-300 relative" :style="{ width: processProgress + '%' }">
                         <div class="absolute inset-0 bg-white/30 animate-[shimmer_1s_infinite]"></div>
                    </div>
                </div>
                <div class="font-mono text-cyan-400 animate-pulse text-lg">{{ processStatus }}</div>
                <div class="text-4xl font-bold text-white mt-2">{{ processProgress }}%</div>
            </div>

        </div>
    </div>
</template>

<style>
@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
</style>
