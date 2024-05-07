<script setup lang="ts">
import { ref, reactive } from "vue";
import { onMounted } from 'vue'
import type { PropType } from 'vue'
import { getAttributesByUsername } from "@/utils/getAttributesByUsername";

const props = defineProps<{
  queryParams: Record<string, string>;
}>();

// Creamos una variable reactiva para guardar los query params
const queryParams = ref<Record<string, string>>({});
const data = {
  attributes: {},
};

const baseUrl = 'http://localhost:4321';  // Ajusta esto según tu configuración local o de producción

const attributes = await getAttributesByUsername('bypabloc');
console.log('attributes', attributes);
data.attributes = attributes.attributes || {};

onMounted(() => {
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
      {{ data.attributes }}
    </div>
  </div>
</template>

<style scoped>
/* Estilos según sea necesario */
</style>
