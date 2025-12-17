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
              v-model.trim="username"
              label="Usuario"
              hint="Para pruebas: admin"
              persistent-hint
              prepend-inner-icon="mdi-account-outline"
              variant="outlined"
              required
              density="compact"
              bg-color="white"
              :disabled="auth.loading"
              @keyup.enter="handleLogin"
            />

            <v-text-field
              v-model="password"
              label="Contraseña"
              hint="Para pruebas: vimenca2025"
              persistent-hint
              prepend-inner-icon="mdi-lock-outline"
              :type="showPassword ? 'text' : 'password'"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showPassword = !showPassword"
              variant="outlined"
              required
              density="compact"
              bg-color="white"
              :disabled="auth.loading"
              @keyup.enter="handleLogin"
            />

            <v-btn
              :loading="auth.loading"
              :disabled="auth.loading || !canSubmit"
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
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import logo from '@/assets/miplogo.png'

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const auth = useAuthStore()

const canSubmit = computed(() => {
  return username.value.length > 0 && password.value.length > 0
})

const handleLogin = async () => {
  if (!canSubmit.value || auth.loading) return

  await auth.login({
    email: username.value,      // mantiene tu store sin cambios (usa "email" como campo)
    password: password.value
  })
}
</script>

<style scoped>
.fill-height {
  background-color: #f0f2f50c;
}
</style>
