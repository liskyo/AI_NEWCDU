<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  ChartBarIcon, 
  AdjustmentsHorizontalIcon, 
  GlobeAltIcon, 
  ClipboardDocumentListIcon, 
  WrenchScrewdriverIcon, 
  Cog6ToothIcon,
  PresentationChartLineIcon,
  LifebuoyIcon,
  CloudArrowDownIcon,
  ComputerDesktopIcon,
  LanguageIcon
} from '@heroicons/vue/24/outline'

const router = useRouter()
const isKioskMode = ref(false)
let kioskInterval = null
const rotationPages = ['/status', '/trends']
let currentRotationIndex = 0

// --- Lightweight i18n System ---
const currentLang = ref(localStorage.getItem('preferredLang') || 'zh') // Default to Traditional Chinese

const translations = {
  zh: {
    'nav.status': '狀態總覽',
    'nav.control': '設備控制',
    'nav.trends': '趨勢分析',
    'nav.maint': '維護保養',
    'nav.backup': '系統備份',
    'nav.network': '網路通訊',
    'nav.logs': '系統日誌',
    'nav.engineer': '工程模式',
    'nav.settings': '系統設定'
  },
  en: {
    'nav.status': 'Status',
    'nav.control': 'Control',
    'nav.trends': 'Trends',
    'nav.maint': 'Maint.',
    'nav.backup': 'Backup',
    'nav.network': 'Network',
    'nav.logs': 'Logs',
    'nav.engineer': 'Engineer',
    'nav.settings': 'Settings'
  }
}

const t = (key) => {
  return translations[currentLang.value][key] || key
}

const toggleLanguage = () => {
    currentLang.value = currentLang.value === 'zh' ? 'en' : 'zh'
    localStorage.setItem('preferredLang', currentLang.value)
}
// ------------------------------

const navItems = [
  { path: '/status', labelKey: 'nav.status', icon: ChartBarIcon },
  { path: '/control', labelKey: 'nav.control', icon: AdjustmentsHorizontalIcon },
  { path: '/trends', labelKey: 'nav.trends', icon: PresentationChartLineIcon },
  { path: '/maintenance', labelKey: 'nav.maint', icon: LifebuoyIcon },
  { path: '/backup', labelKey: 'nav.backup', icon: CloudArrowDownIcon },
  { path: '/network', labelKey: 'nav.network', icon: GlobeAltIcon },
  { path: '/logs', labelKey: 'nav.logs', icon: ClipboardDocumentListIcon },
  { path: '/engineer-mode', labelKey: 'nav.engineer', icon: WrenchScrewdriverIcon },
  { path: '/settings', labelKey: 'nav.settings', icon: Cog6ToothIcon }
]

const toggleKioskMode = () => {
    isKioskMode.value = !isKioskMode.value
    if (isKioskMode.value) {
        enterKiosk()
    } else {
        exitKiosk()
    }
}

const enterKiosk = () => {
    // Request full screen
    const elem = document.documentElement
    if (elem.requestFullscreen) {
        elem.requestFullscreen().catch(err => {})
    }
    
    // Start rotation
    currentRotationIndex = 0
    router.push(rotationPages[0])
    
    kioskInterval = setInterval(() => {
        currentRotationIndex = (currentRotationIndex + 1) % rotationPages.length
        router.push(rotationPages[currentRotationIndex])
    }, 30000) // 30 seconds
}

const exitKiosk = () => {
    isKioskMode.value = false
    if (document.exitFullscreen && document.fullscreenElement) {
        document.exitFullscreen().catch(err => {})
    }
    if (kioskInterval) clearInterval(kioskInterval)
}

const handleFullscreenChange = () => {
    if (!document.fullscreenElement) {
        // Exited fullscreen externally (e.g. ESC key handled by browser)
        exitKiosk()
    }
}

const handleKeydown = (e) => {
    // Keep ESC listener as backup, though fullscreenchange usually handles it
    if (e.key === 'Escape' && isKioskMode.value) {
        exitKiosk()
    }
}

onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
    document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
    document.removeEventListener('fullscreenchange', handleFullscreenChange)
    if (kioskInterval) clearInterval(kioskInterval)
})
</script>

<template>
  <div class="min-h-screen bg-gray-100 font-sans">
    <!-- Navbar (Hidden in Kiosk Mode) -->
    <nav v-if="!isKioskMode" class="bg-gray-900 text-white shadow-lg sticky top-0 z-50">
      <div class="container mx-auto px-6 py-4 flex justify-between items-center">
        <!-- Logo / Title -->
        <div class="flex items-center space-x-3">
           <img src="/favicon.png" alt="Logo" class="h-8 w-8" />
           <span class="text-xl font-bold tracking-wide">Guchii CDU Control</span>
        </div>
        
        <!-- Navigation Links -->
        <div class="hidden md:flex space-x-1 items-center">
          <router-link v-for="item in navItems" 
          :key="item.path"
          :to="item.path" 
          class="flex items-center px-3 py-2 rounded-md transition-colors duration-200 hover:bg-gray-800 hover:text-blue-400 text-sm font-medium space-x-2"
          active-class="text-blue-500 font-bold bg-gray-800"
          >
            <component :is="item.icon" class="h-5 w-5" />
            <span>{{ t(item.labelKey) }}</span>
          </router-link>

          <!-- Language Toggle -->
          <button @click="toggleLanguage" 
                  title="Toggle Language" 
                  class="flex items-center space-x-1 px-3 py-1.5 ml-2 rounded-md bg-gray-800 border border-gray-700 hover:border-blue-500 hover:bg-gray-700 text-sm font-bold text-gray-300 transition-colors">
              <LanguageIcon class="w-4 h-4" />
              <span>{{ currentLang === 'zh' ? '中(繁)' : 'EN' }}</span>
          </button>

          <!-- Kiosk Mode Toggle -->
          <div class="border-l border-gray-700 h-6 mx-2"></div>
          <button @click="toggleKioskMode" title="Enter Kiosk Mode (War Room)" class="text-gray-400 hover:text-cyan-400 transition-colors p-2">
              <ComputerDesktopIcon class="h-6 w-6" />
          </button>
        </div>
      </div>
    </nav>
    
    <!-- Main Content Area -->
    <main :class="isKioskMode ? 'h-screen overflow-hidden' : 'container mx-auto p-6'" class="transition-all duration-300 ease-in-out">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    
    <!-- Kiosk Exit Hint -->
    <div v-if="isKioskMode" class="fixed top-0 left-0 right-0 z-[100] h-2 bg-transparent hover:bg-gray-900/50 transition-colors group flex justify-center items-start">
         <div class="bg-black/50 text-white text-xs px-3 py-1 rounded-b-lg -translate-y-full group-hover:translate-y-0 transition-transform">
             Press ESC to Exit Kiosk Mode
         </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
