<script setup lang="ts">
import { ref, onMounted } from "vue";

const baseUrl = 'http://localhost:4321';  // Ajusta esto según tu configuración local o de producción

async function postData() {
  try {
    const response = await fetch(`${baseUrl}/api/views`, {
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
    const response = await fetch(`${baseUrl}/api/views?` + new URLSearchParams({}));
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
  postData();
});
</script>

<template>
  <section class="section">
    Información básica
  </section>
</template>

<style scoped>
/* Estilos según sea necesario */
</style>
