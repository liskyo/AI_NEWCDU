import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// Global Axios configuration to point to the Flask backend running on port 5588
axios.defaults.baseURL = `http://${window.location.hostname}:5588`

createApp(App)
    .use(router)
    .mount('#app')
