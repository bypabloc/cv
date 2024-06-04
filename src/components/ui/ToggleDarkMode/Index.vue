<template>
  <button
    @click="toggleMode"
    @keydown="handleKeydown"
    aria-label="Toggle dark mode"
    :title="!$isDarkMode ? 'Modo claro' : 'Modo oscuro'"
    class="toggle-button"
  >
    <span
      class="nyx-color2-text-primary-on"
      :class="[
        $isDarkMode ? 'i-carbon-moon' : 'i-carbon-sun',
      ]"
      aria-hidden="true"
    />
  </button>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useStore } from '@nanostores/vue';
import { styles, toggleMode, getMode } from '@/stores/styles.ts';

// Inicializa el estado isDarkMode con ref
const isDarkMode = ref(getMode());

// Usar el store de Nano Stores
const $styles = useStore(styles);
const $isDarkMode = computed(() => $styles.value.isDarkMode);

// Sincroniza el estado inicial en el cliente
onMounted(() => {
  isDarkMode.value = getMode();
});

// Función para manejar eventos de teclado
function handleKeydown(event: KeyboardEvent) {
  // Verifica si la tecla presionada es 'Enter' o 'Espacio'
  if (event.key === 'Enter' || event.key === ' ') {
    toggleMode();
  }
}
</script>

<style scoped>
.toggle-button {
  position: relative;
  display: inline-block;
  padding: 16px;
  font-size: 16px;
  border: none;
  cursor: pointer;
}

.toggle-button:hover {
}
</style>
