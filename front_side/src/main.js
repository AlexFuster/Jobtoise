import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import { initializeApp } from "firebase/app";
import { firebaseConfig } from './firebaseConf'
import 'bootstrap-icons/font/bootstrap-icons.css';
import { createPinia } from 'pinia'

// Initialize Firebase
initializeApp(firebaseConfig);

const pinia = createPinia()

createApp(App).use(pinia).use(router).mount('#app')
