<template>
  <div id="app">
    <header v-if="authStore.isAuthenticated">
      <nav>
        <span>Bienvenido, {{ authStore.user?.name || 'Usuario' }}</span>
        <button @click="handleLogout">Cerrar Sesión</button>
      </nav>
    </header>
    <main>
      <RouterView />
    </main>
  </div>
</template>


<script setup>
import { RouterView } from 'vue-router';
import { useAuthStore } from './stores/auth';
import { onMounted } from 'vue';

const authStore = useAuthStore();

// Al cargar la app, intenta obtener los datos del usuario si hay un token
onMounted(() => {
  if (authStore.isAuthenticated) {
    authStore.fetchUser();
  }
});

const handleLogout = () => {
  authStore.logout();
};
</script>

<style scoped>
header {
  background-color: #f8f9fa;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}
nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>