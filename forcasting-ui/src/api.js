// src/api.js

import axios from 'axios';
// Crea una instancia de Axios con la URL base de tu API
const apiClient = axios.create({
 // baseURL:  'https://flask-api-service-727191877368.us-central1.run.app/api', // Asegúrate de que coincida con tu servidor Laravel
  baseURL: 'http://127.0.0.1:8000',

 headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  }
});

// Interceptor para añadir el token JWT a las peticiones
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

export default apiClient;