<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-toolbar-title class="headline text-uppercase">
        <v-icon left>mdi-brain</v-icon>
        BigQuery Insight Navigator
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-toolbar-items class="hidden-sm-and-down align-center">
        <span class="mr-4 white--text font-weight-medium">
          Hola, {{ userEmail }}
        </span>
      </v-toolbar-items>
      <v-btn icon @click="logout" title="Cerrar Sesión">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid class="pa-6">
        <v-row>
          <v-col cols="12">
            
          <v-img
            :src="logo"
            alt="MIP Logo"
            max-height="40"
            contain
            class="mb-6"
          ></v-img>
          </v-col>
        </v-row>
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
                    <v-list-item-content>
                      <v-list-item-title>
                        <span class="font-weight-medium">{{ obj.id }}</span>
                        <span class="caption grey--text">({{ obj.type }})</span>
                      </v-list-item-title>
                    </v-list-item-content>
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
                  :label="`Ej:  - ¿Qué tipo de información hay en las tablas de homicidios, robos o transito?
                                  - ¿Cuál es el número total de homicidios en 2023?
                                  - ¿Cuántos robos se reportaron por provincia? (¡Intenta graficar esto!)
                                  - ¿Cuál es la cantidad de accidentes de tránsito por municipio? (¡Intenta graficar esto!)`"
                  outlined
                  clearable
                  rows="3"
                  prepend-inner-icon="mdi-pencil"
                  :rules="[v => !!v || 'La pregunta es obligatoria']"
                  @keyup.enter="askGemini"
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
              <v-card-title class="d-flex justify-space-between align-center">
                <div>
                  <v-icon left>mdi-chart-bar</v-icon>
                  Resultados de la Consulta
                </div>
                <v-btn
                 ref="exportButtonRef"  
                  color="secondary"
                  class="export-button"
                  prepend-icon="mdi-file-pdf-box"
                  @click="exportToPDF"
                >
                  Exportar PDF
                </v-btn>
              </v-card-title>
              
              <v-card-text ref="resultsContainer">
                <v-alert v-if="apiResponse.type === 'text'" type="info" prominent text>
                  {{ apiResponse.content }}
                </v-alert>

                <div v-if="apiResponse && apiResponse.type === 'table'">
                  <p class="subtitle-1">
                    Consulta ejecutada en: <strong>{{ apiResponse.identified_object }}</strong>
                  </p>
                  
                  <v-data-table
                    :headers="apiResponse.content.headers.map(h => ({ title: h, key: h, sortable: true }))"
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
                  ></v-data-table>
                </div>

                <v-card v-if="shouldShowChart" class="mt-4 pa-4 elevation-1">
                    <v-card-title class="headline d-flex justify-space-between align-center">
                        Visualización
                        <v-select
                            v-model="selectedChartType"
                            :items="chartTypes"
                            label="Tipo de Gráfico"
                            dense
                            hide-details
                            class="chart-type-selector"
                        ></v-select>
                    </v-card-title>
                    <v-card-text>
                        <BarChart v-if="selectedChartType === 'bar'" :chart-data="chartData" />
                        <LineChart v-if="selectedChartType === 'line'" :chart-data="chartData" />
                        <PieChart v-if="selectedChartType === 'pie'" :chart-data="chartData" />
                    </v-card-text>
                </v-card>

                <v-expansion-panels class="mt-4" variant="popout">
                  <v-expansion-panel>
                    <v-expansion-panel-title> <v-icon left class="mr-2">mdi-code-braces</v-icon>
                      SQL Generado por la IA (Haz clic para ver)
                    </v-expansion-panel-title>
                    <v-expansion-panel-text> <highlightjs autodetect :code="apiResponse.generated_sql"></highlightjs>
                    </v-expansion-panel-text>
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
import { ref, onMounted, computed } from 'vue';
import apiClient from '../api'; // Asegúrate de que esta ruta sea correcta para tu instancia de Axios
import { useAuthStore } from '../stores/auth';
import html2pdf from 'html2pdf.js';

// Importa los componentes de gráfico
import BarChart from '../components/BarChart.vue';
import LineChart from '../components/LineChart.vue';
import PieChart from '../components/PieChart.vue';
import logo from '@/assets/miplogo.png';

const bigqueryObjects = ref([]);
const question = ref('');
const apiResponse = ref(null);
const loading = ref(false);
const loadingObjects = ref(false);

const authStore = useAuthStore();

// Refs para el gráfico
const chartData = ref(null);
const shouldShowChart = ref(false);
const selectedChartType = ref('bar');
const chartTypes = ['bar', 'line', 'pie'];

// Ref para la exportación a PDF
const resultsContainer = ref(null);
const exportButtonRef = ref(null); // <-- AÑADE ESTA LÍNEA

// Propiedad computada para obtener el email del usuario autenticado
const userEmail = computed(() => authStore.user?.email || 'Invitado');

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
  shouldShowChart.value = false;
  chartData.value = null;

  try {
    const response = await apiClient.post('/bigquery/ask', {
      question: question.value,
    });
    apiResponse.value = response.data;
    processChartData(apiResponse.value);
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

const processChartData = (response) => {
    if (response.type === 'table' && response.content.rows.length > 1 && response.content.headers.length > 1) {
        const headers = response.content.headers;
        const rows = response.content.rows;
        const labels = rows.map(row => row[0]);
        const data = rows.map(row => row[1]);

        chartData.value = {
            labels: labels,
            datasets: [{
                label: headers[1],
                backgroundColor: generateColors(data.length),
                data: data
            }]
        };
        shouldShowChart.value = true;
    } else {
        shouldShowChart.value = false;
        chartData.value = null;
    }
};

const generateColors = (numColors) => {
  const colors = [];
  const baseHue = Math.floor(Math.random() * 360);
  for (let i = 0; i < numColors; i++) {
    const hue = (baseHue + (i * (360 / numColors))) % 360;
    colors.push(`hsl(${hue}, 70%, 50%)`);
  }
  return colors;
};


const exportToPDF = () => {
  const buttonEl = exportButtonRef.value.$el;
  if (buttonEl) buttonEl.style.display = 'none';

  // AQUÍ ESTÁ LA CORRECCIÓN
  const element = resultsContainer.value.$el;

  const options = {
    margin: 0.5,
    filename: 'resultados_consulta.pdf',
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: 'in', format: 'letter', orientation: 'landscape' }
  };

  html2pdf()
    .set(options)
    .from(element)
    .save()
    .catch(err => {
      console.error("Hubo un error al exportar el PDF:", err);
      alert("No se pudo generar el PDF. Por favor, inténtalo de nuevo.");
    })
    .finally(() => {
      if (buttonEl) buttonEl.style.display = 'flex';
    });
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
  /* Asegura que el texto no se oculte */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 16px !important; /* Añade un poco de padding para que el texto no esté pegado al borde */
  padding-right: 16px !important;
}
.v-data-table td {
  /* Alineación y estilo para las celdas de datos */
  vertical-align: middle;
  padding-left: 16px !important; /* Añade el mismo padding a las celdas de datos */
  padding-right: 16px !important;
}

/* Estilos para el selector de tipo de gráfico */
.chart-type-selector {
  max-width: 150px; /* Ajusta el ancho según sea necesario */
}
/* Asegura que el selector no afecte el título del gráfico */
.v-card-title.d-flex.justify-space-between.align-center {
  flex-wrap: nowrap;
}

/* Estilos para el panel de expansión (si son necesarios, ya que Vuetify 3 maneja la mayoría) */
.v-expansion-panel-title { /* Nuevo nombre de clase para el encabezado en Vuetify 3 */
  font-weight: 600;
  color: var(--v-primary-base);
  background-color: #f0f4f8;
  border-radius: 8px 8px 0 0;
}
.v-expansion-panel-text { /* Nuevo nombre de clase para el contenido en Vuetify 3 */
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