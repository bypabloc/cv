<script setup lang="ts">
import { ref } from "vue";
import { onMounted } from 'vue'
import type { PropType } from 'vue'

const props = defineProps<{
  queryParams: Record<string, string>;
}>();

// Creamos una variable reactiva para guardar los query params
const queryParams = ref<Record<string, string>>({});

const baseUrl = 'http://localhost:4321';  // Ajusta esto según tu configuración local o de producción

async function postData() {
  try {
    const response = await fetch(`${baseUrl}/api/basic`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: 'Vista básica',
        description: 'Vista básica de la aplicación',
      }),
    });
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    console.log('POST Response:', data);
  } catch (error) {
    if (error instanceof Response) {
      const errorData = await error.json();
      console.error('Failed to post:', errorData);
    } else {
      console.error('Error making the request:', error);
    }
  }
}

async function getData() {
  try {
    const response = await fetch(`${baseUrl}/api/basic/?` + new URLSearchParams({
      username: 'bypabloc'
    }), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    console.log('POST Response:', data);
  } catch (error) {
    if (error instanceof Response) {
      const errorData = await error.json();
      console.error('Failed to post:', errorData);
    } else {
      console.error('Error making the request:', error);
    }
  }
}

onMounted(() => {
  getData();
  // postData();
  // Obtener parámetros de consulta desde el cliente
  const params = new URLSearchParams(window.location.search);
  const result: Record<string, string> = {};
  for (const [key, value] of params.entries()) {
    result[key] = value;
  }
  // Actualizamos la variable reactiva
  queryParams.value = result;
});
</script>

<template>
  <div>
    <h1>Información básica</h1>
    <div v-if="queryParams">
      <h2>Query Params:</h2>
      <ul>
        <li v-for="(value, key) in queryParams" :key="key">
          {{ key }}: {{ value }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
/* Estilos según sea necesario */
</style>
