<script setup lang="ts">
import { ref, computed, watchEffect, onMounted } from "vue";
import { Users } from "astro:db";
import UIImage from "@/components/ui/Image/Index.vue";

const props = defineProps({
  images: {
    type: Array,
    default: () => ([]),
  },
  user: {
    type: Object,
    default: () => ({}),
  },
  type: {
    type: String,
    default: 'perfil'
  },
  attributes: {
    type: Object,
    default: () => ({}),
  },
  aspectRatio: {
    type: String,
    default: '1 / 1'
  },
  objectFit: {
    type: String,
    default: 'cover'
  },
  width: {
    type: String,
    default: 'auto'
  },
  borderRadius: {
    type: String,
    default: '16px'
  },
  height: {
    type: String,
    default: 'auto'
  }
});

const images = computed(() => {
  return props.images.map((image) => image?.files);
});

const currentIndex = ref(0);

watchEffect(() => {
  console.log('currentIndex ha cambiado:', currentIndex.value);
});

const advanceSlide = (step) => {
  console.log('Valor actual de currentIndex:', currentIndex.value);
  currentIndex.value = (currentIndex.value + step + props.images.length) % props.images.length;
  console.log('Nuevo valor de currentIndex:', currentIndex.value);
};

const currentImage = computed(() => {
  return props.images[currentIndex.value];
});

onMounted(() => {
  console.log('Componente montado');
});
</script>

<template>
  <div class="photo-flow">
    <UIImage
      v-for="(image, index) in images"
      :key="index"
      :items="image"
      :user="user"
      :type="type"
      :attributes="attributes"
      :aspectRatio="aspectRatio"
      :objectFit="objectFit"
      :width="width"
      :borderRadius="borderRadius"
      :height="height"
    />
    <button @click="window.console.log('Botón clickeado'); advanceSlide(-1)">&#10094;</button>
    <button @click="window.console.log('Botón clickeado'); advanceSlide(1)">&#10095;</button>
  </div>
</template>

<style scoped>
.photo-flow {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

button {
  all: unset;
  cursor: pointer;
  padding: 10px;
  background-color: #eee;
  border: 1px solid #ccc;
  border-radius: 5px;
}

button:hover {
  background-color: #ddd;
}
</style>
