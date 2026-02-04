import { createRouter, createWebHistory } from 'vue-router'
import StatusEngineer from '../components/StatusEngineer.vue'
import Settings from '../components/Settings.vue'
import Network from '../components/Network.vue'
import Control from '../components/Control.vue'
import Logs from '../components/Logs.vue'
import EngineerMode from '../components/EngineerMode.vue'
import Trends from '../components/Trends.vue'
import Maintenance from '../components/Maintenance.vue'
import Backup from '../components/Backup.vue'

const routes = [
    {
        path: '/',
        redirect: '/status'
    },
    {
        path: '/status',
        name: 'Status',
        component: StatusEngineer
    },
    {
        path: '/control',
        name: 'Control',
        component: Control
    },
    {
        path: '/trends',
        name: 'Trends',
        component: Trends
    },
    {
        path: '/maintenance',
        name: 'Maintenance',
        component: Maintenance
    },
    {
        path: '/backup',
        name: 'Backup',
        component: Backup
    },
    {
        path: '/network',
        name: 'Network',
        component: Network
    },
    {
        path: '/logs',
        name: 'Logs',
        component: Logs
    },
    {
        path: '/engineer-mode',
        name: 'Engineer Mode',
        component: EngineerMode
    },
    {
        path: '/settings',
        name: 'Settings',
        component: Settings
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
