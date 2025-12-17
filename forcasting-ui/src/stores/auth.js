// src/stores/auth.js

import { defineStore } from 'pinia';
import apiClient from '../api';
import router from '../router';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('jwt_token') || null,
    user: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(credentials) {
      try {
        const response = await apiClient.post('/login', credentials);
        const token = response.data.access_token;

        // Guarda el token en el estado y en localStorage
        this.token = token;
        localStorage.setItem('jwt_token', token);

        // Obtiene los datos del usuario
        await this.fetchUser();
        
        // Redirige al dashboard
        router.push('/');

      } catch (error) {
        alert("Error en el email o la contraseña.");
        console.error("Error en el login:", error);
      }
    },
    async fetchUser() {
      if (this.token) {
        try {
          const response = await apiClient.get('/me');
          this.user = response.data;
        } catch (error) {
          // Si el token es inválido, limpia todo
          this.logout();
          console.error("Error al obtener datos del usuario:", error);
        }
      }
    },
    logout() {
      // Limpia el estado
      this.token = null;
      this.user = null;
      localStorage.removeItem('jwt_token');
      
      // Redirige al login
      router.push('/login');
    },
  },
});