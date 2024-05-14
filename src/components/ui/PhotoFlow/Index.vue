<script setup lang="ts">
import { ref, computed } from "vue";
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

const currentIndex = ref(0);

const images = computed(() => {
  return props.images.map((image) => image?.files);
});

const advanceSlide = (step) => {
  if (props.images.length === 0) return;

  const newIndex = (currentIndex.value + step + props.images.length) % props.images.length;
  currentIndex.value = newIndex;
};

const currentImage = computed(() => {
  return images.value[currentIndex.value] || [];
});
</script>

<template>
  <div class="photo-flow">
    <UIImage
      :items="currentImage"
      :user="props.user"
      :type="props.type"
      :attributes="props.attributes"
      :aspectRatio="props.aspectRatio"
      :objectFit="props.objectFit"
      :width="props.width"
      :borderRadius="props.borderRadius"
      :height="props.height"
    >
      {{ image }}
    </UIImage>
    <button @click="advanceSlide(-1)">&#10094;</button>
    <button @click="advanceSlide(1)">&#10095;</button>
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
