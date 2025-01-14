import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import { initializeApp } from "firebase/app";
import { firebaseConfig } from './firebaseConf'

// Initialize Firebase
initializeApp(firebaseConfig);

createApp(App).use(store).use(router).mount('#app')
