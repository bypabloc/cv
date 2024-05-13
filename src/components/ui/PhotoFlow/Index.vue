<script setup lang="ts">
import { ref, computed } from "vue";
import { Users } from "astro:db";
import UIImage from "@/components/ui/Image/Index.vue";


const props = defineProps<{
  images: Object;
  user: typeof Users;
  type: string;
  attributes: Object;
}>();

const images = computed(() => {
  return props.images.map((image) => {
    return image?.files;
  });
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
    />
  </div>
</template>

<style scoped>
.photo-flow {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1rem;
}
</style>
