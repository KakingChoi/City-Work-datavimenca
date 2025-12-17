// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import DashboardView from '../views/DashboardView.vue';
import LoginView from '../views/LoginView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true } // Esta ruta requiere autenticación
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
  ]
});

// Guardia de navegación para proteger rutas
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('jwt_token');

  if (to.meta.requiresAuth && !isAuthenticated) {
    // Si la ruta requiere autenticación y no hay token, redirige al login
    next({ name: 'login' });
  } else if (to.name === 'login' && isAuthenticated) {
    // Si el usuario ya está logueado, no puede volver a la página de login
    next({ name: 'dashboard' });
  }
  else {
    // En cualquier otro caso, permite la navegación
    next();
  }
});

export default router;