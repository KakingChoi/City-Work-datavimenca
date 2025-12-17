// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

// Highlight.js para el código SQL
import 'highlight.js/styles/github-dark.css'
import hljs from 'highlight.js/lib/core'
import sql from 'highlight.js/lib/languages/sql'
import HighlightjsVue from '@highlightjs/vue-plugin'

// Pinia
import { createPinia } from 'pinia'

hljs.registerLanguage('sql', sql)

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
  },
  theme: {
    themes: {
      light: {
        colors: {
          primary: '#3F51B5',
          secondary: '#FFC107',
          accent: '#03A9F4',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FFC107',
        },
      },
    },
  },
})

const app = createApp(App)

app.use(createPinia()) // <--- ESTA LÍNEA ES CLAVE
app.use(router)
app.use(vuetify)
app.use(HighlightjsVue)

app.mount('#app')
