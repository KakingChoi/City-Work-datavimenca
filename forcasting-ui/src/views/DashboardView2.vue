<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title class="headline text-uppercase">
        <v-icon left>mdi-brain</v-icon>
        BigQuery Insight Navigator
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="logout" title="Cerrar Sesión">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid class="pa-6">
        <v-row>
          <v-col cols="12" md="4">
            <v-card class="pa-4 custom-card">
              <v-card-title class="headline mb-3">
                <v-icon left>mdi-database</v-icon>
                Objetos Disponibles
              </v-card-title>
              <v-card-text>
                <p class="subtitle-1 grey--text text--darken-1">
                  Estos son los objetos (tablas y vistas) en tu dataset de BigQuery. La IA los usará para generar tus consultas.
                </p>
                <v-list dense>
                  <v-list-item v-for="obj in bigqueryObjects" :key="obj.id" :class="`object-item-${obj.type.toLowerCase()}`">
                    <v-list-item-icon>
                      <v-icon v-if="obj.type === 'TABLE'">mdi-table</v-icon>
                      <v-icon v-else>mdi-eye</v-icon>
                    </v-list-item-icon>
                   
                      <v-list-item-title>
                        <span class="font-weight-medium">{{ obj.id }}</span> 
                        <span class="caption grey--text">({{ obj.type }})</span>
                      </v-list-item-title>
                    
                  </v-list-item>
                  <v-list-item v-if="bigqueryObjects.length === 0 && !loadingObjects">
                      <v-list-item-content>
                        <v-list-item-title class="grey--text">No se encontraron objetos.</v-list-item-title>
                      </v-list-item-content>
                  </v-list-item>
                  <v-list-item v-if="loadingObjects">
                      <v-progress-linear indeterminate color="primary"></v-progress-linear>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="8">
            <v-card class="pa-4 custom-card">
              <v-card-title class="headline mb-3">
                <v-icon left>mdi-chat-question</v-icon>
                Generar Consulta SQL con IA
              </v-card-title>
              <v-card-text>
                <p class="subtitle-1 grey--text text--darken-1 mb-4">
                  Escribe tu pregunta en lenguaje natural y la Inteligencia Artificial generará la consulta SQL y obtendrá los resultados.
                </p>
                <v-textarea
                  v-model="question"
                  label="Ej: '¿Cuántos usuarios se registraron el mes pasado?' o 'Muestra el total de ventas por producto en el último trimestre.'"
                  outlined
                  clearable
                  rows="3"
                  prepend-inner-icon="mdi-pencil"
                  :rules="[v => !!v || 'La pregunta es obligatoria']"
                ></v-textarea>
                <v-btn
                  color="primary"
                  large
                  block
                  @click="askGemini"
                  :loading="loading"
                  :disabled="!question || loading"
                  class="mt-3"
                >
                  <v-icon left>mdi-send</v-icon>
                  {{ loading ? 'Generando Consulta...' : 'Enviar Pregunta' }}
                </v-btn>
              </v-card-text>
            </v-card>

            <v-card v-if="apiResponse" class="pa-4 mt-6 custom-card">
              <v-card-title class="headline mb-3">
                <v-icon left>mdi-chart-bar</v-icon>
                Resultados de la Consulta
              </v-card-title>
              <v-card-text>
                <v-alert v-if="apiResponse.type === 'text'" type="info" prominent text>
                  {{ apiResponse.content }}
                </v-alert>

                <div v-if="apiResponse.type === 'table'">
                  <p class="subtitle-1">
                    Consulta ejecutada en: <strong>{{ apiResponse.identified_object }}</strong>
                  </p>
                  <v-data-table
                    :headers="apiResponse.content.headers.map(h => ({ text: h, value: h, sortable: true }))"
                    :items="apiResponse.content.rows.map(r => { 
                      const obj = {};
                      apiResponse.content.headers.forEach((header, index) => {
                        obj[header] = r[index];
                      });
                      return obj;
                    })"
                    class="elevation-1 mt-4"
                    :items-per-page="10"
                    :loading="loading"
                    no-data-text="No hay datos para mostrar."
                  >
                  </v-data-table>
                </div>

                <v-expansion-panels class="mt-4" popout>
                  <v-expansion-panel>
                    <v-expansion-panel-header>
                      <v-icon left class="mr-2">mdi-code-braces</v-icon>
                      SQL Generado por la IA (Haz clic para ver)
                    </v-expansion-panel-header>
                    <v-expansion-panel-content>
                      <highlightjs autodetect :code="apiResponse.generated_sql"></highlightjs>
                    </v-expansion-panel-content>
                  </v-expansion-panel>
                </v-expansion-panels>

              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import apiClient from '../api'; // Asegúrate de que esta ruta sea correcta para tu instancia de Axios
import { useAuthStore } from '../stores/auth';

const bigqueryObjects = ref([]);
const question = ref('');
const apiResponse = ref(null);
const loading = ref(false);
const loadingObjects = ref(false);

const authStore = useAuthStore();

onMounted(async () => {
  loadingObjects.value = true;
  try {
    const response = await apiClient.get('/bigquery/objects'); 
    bigqueryObjects.value = response.data;
  } catch (error) {
    console.error("Error al cargar los objetos de BigQuery:", error);
    alert('No se pudieron cargar los objetos de BigQuery. Asegúrate de que el backend esté funcionando y tu token JWT sea válido. Posiblemente necesites iniciar sesión de nuevo.');
  } finally {
    loadingObjects.value = false;
  }
});

const askGemini = async () => {
  if (!question.value) {
    alert('Por favor, escribe una pregunta.');
    return;
  }
  
  loading.value = true;
  apiResponse.value = null; 
  
  try {
    const response = await apiClient.post('/bigquery/ask', {
      question: question.value,
    });
    apiResponse.value = response.data;
  } catch (error) {
    console.error("Error en la consulta:", error);
    let errorMessage = "Hubo un error al procesar la pregunta.";
    if (error.response && error.response.data) {
        if (error.response.data.content) {
            errorMessage = `Error: ${error.response.data.content}`;
        } else if (error.response.data.error) {
            errorMessage = `Error: ${error.response.data.error}`;
        } else if (error.response.status === 401) {
            errorMessage = "Tu sesión ha expirado. Por favor, inicia sesión de nuevo.";
            logout(); 
            return;
        }
    }
    alert(errorMessage);
  } finally {
    loading.value = false;
  }
};

const logout = () => {
  authStore.logout();
};
</script>

<style>
/* Estilos generales y de Vuetify */
.v-application {
  background-color: #f5f7fa !important;
  font-family: 'Roboto', sans-serif;
}

.custom-card {
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}
.custom-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.08) !important;
}


.app-title {
  font-weight: 700;
  letter-spacing: 0.05em;
}

.section-title {
  font-weight: 600;
  color: var(--v-primary-base);
}

.section-description {
  color: #616161;
  margin-bottom: 1.5rem;
}

.object-item-table {
  background-color: #e3f2fd;
  border-left: 4px solid #2196f3;
  margin-bottom: 8px;
  border-radius: 8px;
}
.object-item-view {
  background-color: #e8f5e9;
  border-left: 4px solid #4caf50;
  margin-bottom: 8px;
  border-radius: 8px;
}
.v-list-item__icon {
    margin-right: 12px !important;
}

.submit-button {
  text-transform: none !important;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.results-section .subtitle-1 {
  font-weight: 500;
  color: #424242;
}

.v-data-table {
  border-radius: 8px;
  overflow: hidden;
}
.v-data-table th {
  background-color: #f5f5f5 !important;
  font-weight: bold !important;
  color: #333 !important;
}

.v-expansion-panel-header {
  font-weight: 600;
  color: var(--v-primary-base);
  background-color: #f0f4f8;
  border-radius: 8px 8px 0 0;
}
.v-expansion-panel-content {
  padding: 16px;
  background-color: #fafafa;
  border-radius: 0 0 8px 8px;
}
pre code {
  font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace !important;
  font-size: 0.875rem;
  line-height: 1.5;
  padding: 1rem;
  border-radius: 8px;
  display: block;
  overflow-x: auto;
}
</style>