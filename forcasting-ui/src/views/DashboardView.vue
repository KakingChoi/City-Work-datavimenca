<template>
  <div class="forecast-container">
    <div class="card upload-section">
      <h3>🚀 Subir Forecasting (Origins.xlsx)</h3>
      <p class="subtitle">El sistema unificará las 3 pestañas automáticamente en BigQuery.</p>
      
      <div 
        class="drop-zone" 
        :class="{ 'drop-zone--active': isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <div v-if="!selectedFile">
          <p>Arrastra tu archivo aquí o <strong>haz clic para buscar</strong></p>
          <input type="file" @change="onFileSelected" accept=".xlsx" class="file-input" />
        </div>
        <div v-else class="file-info">
          <span>📄 {{ selectedFile.name }}</span>
          <button @click="selectedFile = null" class="btn-remove">✖</button>
        </div>
      </div>

      <button 
        @click="uploadFile" 
        :disabled="!selectedFile || isLoading" 
        class="btn-primary"
      >
        {{ isLoading ? 'Procesando en BigQuery...' : 'Subir y Procesar' }}
      </button>
    </div>

    <div class="card data-section">
      <div class="header-row">
        <h3>📊 Vista Previa de BigQuery</h3>
        <button @click="fetchData" class="btn-refresh">🔄 Actualizar Datos</button>
      </div>

      <div class="table-wrapper">
        <table v-if="forecastData.length > 0">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Intervalo</th>
              <th>Llamadas (F)</th>
              <th>AHT (F)</th>
              <th>FTE Req.</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in forecastData" :key="index">
              <td>{{ row.date }}</td>
              <td>{{ row.period }}</td>
              <td>{{ row.calls_forecast }}</td>
              <td>{{ row.aht_forecast }}s</td>
              <td class="fte-cell">{{ row.fte_required }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">
          No hay datos disponibles. Sube un archivo para comenzar.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// CONFIGURACIÓN: Cambia a la URL de tu API (Local o Cloud Run)
const API_BASE_URL = 'http://localhost:8000'; 

const selectedFile = ref(null);
const isDragging = ref(false);
const isLoading = ref(false);
const forecastData = ref([]);

// Obtener token del localStorage (asumiendo que ya hiciste login)
const token = localStorage.getItem('user_token'); 

const onFileSelected = (e) => {
  selectedFile.value = e.target.files[0];
};

const handleDrop = (e) => {
  isDragging.value = false;
  selectedFile.value = e.dataTransfer.files[0];
};

const uploadFile = async () => {
  if (!selectedFile.value) return;
  
  isLoading.value = true;
  const formData = new FormData();
  formData.append('file', selectedFile.value);

  try {
    await axios.post(`${API_BASE_URL}/upload-forecast`, formData, {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data' 
      }
    });
    alert('¡Éxito! El forecast ha sido procesado y guardado en BigQuery.');
    selectedFile.value = null;
    fetchData(); // Refrescar tabla
  } catch (error) {
    console.error(error);
    alert('Error al subir el archivo. Revisa la consola.');
  } finally {
    isLoading.value = false;
  }
};

const fetchData = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/view-data`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    forecastData.value = response.data;
  } catch (error) {
    console.error("Error cargando datos:", error);
  }
};

onMounted(() => {
  if (token) fetchData();
});
</script>

<style scoped>
.forecast-container {
  max-width: 1000px;
  margin: 2rem auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.drop-zone {
  border: 2px dashed #004a99;
  padding: 2rem;
  text-align: center;
  border-radius: 8px;
  margin: 1rem 0;
  transition: all 0.3s;
  position: relative;
}

.drop-zone--active {
  background: #eef4ff;
  border-color: #007bff;
}

.file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0; left: 0;
  opacity: 0;
  cursor: pointer;
}

.btn-primary {
  background: #004a99;
  color: white;
  border: none;
  padding: 0.8rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  width: 100%;
  font-weight: bold;
}

.btn-primary:disabled { background: #ccc; }

.table-wrapper {
  overflow-x: auto;
  margin-top: 1rem;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th { background: #f8f9fa; color: #555; }

.fte-cell {
  font-weight: bold;
  color: #004a99;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-refresh {
  background: none;
  border: 1px solid #004a99;
  color: #004a99;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
}
</style>