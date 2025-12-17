// src/stores/auth.js

import { defineStore } from 'pinia'
import apiClient from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('jwt_token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
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
        // FastAPI usa OAuth2PasswordRequestForm → form-urlencoded
        const form = new URLSearchParams()
        form.append('username', email)   // ⚠️ backend espera "username"
        form.append('password', password)

        const { data } = await apiClient.post('/token', form, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        })

        // Guardar token
        this.token = data.access_token
        localStorage.setItem('jwt_token', data.access_token)

        // Usuario SIMULADO (backend aún no lo devuelve)
        this.user = {
          username: email,
          role: 'admin'
        }
        localStorage.setItem('user', JSON.stringify(this.user))

        // Redirigir al dashboard
        router.push('/dashboard')

      } catch (error) {
        this.error = 'Usuario o contraseña incorrectos'
        console.error('Error login:', error)
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
