import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import Toast from 'vue-toastification'

// Vuetify styles
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

// Toast notifications styles
import 'vue-toastification/dist/index.css'

// Application
import App from './App.vue'
import router from './router'

// Theme configuration
import { lightTheme, darkTheme } from './themes'

// Global styles
import './styles/main.scss'

// Create Vuetify instance
const vuetify = createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: lightTheme,
      dark: darkTheme,
    },
  },
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  defaults: {
    VBtn: {
      variant: 'flat',
      rounded: 'lg',
    },
    VCard: {
      rounded: 'lg',
      elevation: 2,
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VTextarea: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VDataTable: {
      itemsPerPageOptions: [10, 25, 50, 100],
    },
  },
})

// Create Pinia store
const pinia = createPinia()

// Toast configuration
const toastOptions = {
  position: 'top-right' as const,
  timeout: 5000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false,
}

// Create and mount app
const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(vuetify)
app.use(Toast, toastOptions)

app.mount('#app')