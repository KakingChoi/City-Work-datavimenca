<template>
  <df-messenger
    location="us-central1"
    project-id="eripson-lab"
    agent-id="243867f5-1383-4187-83ac-7bc1828bbd54"
    language-code="es"
    max-query-length="-1"
  >
    <df-messenger-chat-bubble
     chat-title="myteam_chat">
    </df-messenger-chat-bubble>
  </df-messenger>
</template>

<script setup>
import { onMounted } from 'vue';

// Usamos onMounted para asegurarnos de que el componente ya está en el DOM
// antes de intentar añadir los scripts.
onMounted(() => {
  // URL de la hoja de estilos y del script de Dialogflow
  const cssUrl = "https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/themes/df-messenger-default.css";
  const scriptUrl = "https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/df-messenger.js";

  // --- Cargar la hoja de estilos (CSS) ---
  // Primero, verificamos si la hoja de estilos ya existe para no duplicarla.
  if (!document.querySelector(`link[href="${cssUrl}"]`)) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = cssUrl;
    document.head.appendChild(link);
  }

  // --- Cargar el script de JavaScript ---
  // Verificamos si el script ya existe para no duplicarlo.
  if (!document.querySelector(`script[src="${scriptUrl}"]`)) {
    const script = document.createElement('script');
    script.async = true;
    script.src = scriptUrl;
    document.head.appendChild(script);
  }
});
</script>

<style>
/* Estos estilos NO son 'scoped' a propósito.
  Necesitamos que se apliquen globalmente al elemento <df-messenger>
  que vive en la raíz del body, no dentro del scope de este componente.
*/
df-messenger {
  z-index: 999;
  position: fixed;
  --df-messenger-font-color: #000;
  --df-messenger-font-family: Google Sans;
  --df-messenger-chat-background: #f3f6fc;
  --df-messenger-message-user-background: #d3e3fd;
  --df-messenger-message-bot-background: #fff;
  bottom: 16px;
  right: 16px;
}
</style>