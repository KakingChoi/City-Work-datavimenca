// src/stores/auth.js
import { defineStore } from 'pinia'
import apiClient from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('jwt_token') || null,
    user: (() => {
      try {
        return JSON.parse(localStorage.getItem('user')) || null
      } catch {
        return null
      }
    })(),
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    async login({ email, password }) {
      this.loading = true
      this.error = null

      try {
        // OAuth2PasswordRequestForm => x-www-form-urlencoded
        const form = new URLSearchParams()
        // Backend espera "username". Si tu backend valida "admin",
        // aquí debes escribir "admin" (no un email) o cambiar la validación en backend.
        form.append('username', email)
        form.append('password', password)

        const { data } = await apiClient.post('/token', form.toString(), {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })

        if (!data?.access_token) {
          throw new Error('Respuesta inválida: falta access_token')
        }

        // Guardar token
        this.token = data.access_token
        localStorage.setItem('jwt_token', data.access_token)

        // Usuario SIMULADO (backend aún no lo devuelve)
        this.user = {
          username: email,
          role: 'admin'
        }
        localStorage.setItem('user', JSON.stringify(this.user))

        await router.push('/dashboard')
      } catch (err) {
        // Axios da información útil en err.response / err.request
        const status = err?.response?.status
        const detail = err?.response?.data?.detail

        if (status === 400) {
          // credenciales incorrectas (tu backend usa 400)
          this.error = detail || 'Usuario o contraseña incorrectos'
        } else if (status === 401) {
          this.error = detail || 'No autorizado'
        } else if (status === 422) {
          this.error = detail || 'Datos inválidos (revisa el formulario enviado)'
        } else if (status === 503) {
          this.error = 'Servicio no disponible (Cloud Run está respondiendo 503). Revisa logs del servicio.'
        } else if (err?.message?.includes('Network Error')) {
          // suele ser CORS, DNS, o el backend caído
          this.error = 'Error de red (posible CORS o API caída). Verifica baseURL y Cloud Run.'
        } else {
          this.error = detail || 'Ocurrió un error al iniciar sesión'
        }

        console.error('Error login:', err)
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.token = null
      this.user = null
      this.error = null
      localStorage.removeItem('jwt_token')
      localStorage.removeItem('user')
      router.push('/login')
    }
  }
})
