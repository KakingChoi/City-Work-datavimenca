<template>
  <v-container class="fill-height pa-4" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <div class="text-center">
          <v-img
            :src="logo"
            alt="MIP Logo"
            max-height="80"
            contain
            class="mb-6"
          />

          <p class="text-h5 font-weight-bold text-primary">DATA VIMENCA</p>
          <p class="text-medium-emphasis mb-6">Iniciar Sesión</p>

          <v-form @submit.prevent="handleLogin">
            <v-alert
              v-if="auth.error"
              type="error"
              density="compact"
              class="mb-4"
            >
              {{ auth.error }}
            </v-alert>

            <v-text-field
              v-model="email"
              label="Correo Electrónico"
              prepend-inner-icon="mdi-email-outline"
              type="email"
              variant="outlined"
              required
              density="compact"
              bg-color="white"
            />

            <v-text-field
              v-model="password"
              label="Contraseña"
              prepend-inner-icon="mdi-lock-outline"
              :type="showPassword ? 'text' : 'password'"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showPassword = !showPassword"
              variant="outlined"
              required
              density="compact"
              bg-color="white"
            />

            <v-btn
              :loading="auth.loading"
              type="submit"
              color="primary"
              block
              size="large"
              class="mt-2"
            >
              Entrar
            </v-btn>
          </v-form>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import logo from '@/assets/miplogo.png'

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const auth = useAuthStore()

const handleLogin = () => {
  auth.login({
    email: email.value,
    password: password.value
  })
}
</script>

<style scoped>
.fill-height {
  background-color: #f0f2f50c;
}
</style>
