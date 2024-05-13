<script setup lang="ts">
import { ref, computed } from "vue";
import { Users } from "astro:db";

const props = defineProps<{
  items: Object;
  user: typeof Users;
  type: string;
  attributes: Object;
}>();

console.log('props', props)

const firstName = computed(() => {
  return props.attributes?.names?.value ? props.attributes?.names?.value?.split(' ')[0] : '';
});
const lastName = computed(() => {
  return props.attributes?.lastName?.value ? props.attributes?.lastName?.value?.split(' ')[0] : '';
});

</script>

<template>
  <div class="photo-flow">
    <picture>
      <template
        v-for="({ id, url, typeInfo }, index) in items"
        :key="`ui-image-${id}`"
      >
        <source v-if="typeInfo.tag !== 'img'" :srcset="url" :type="typeInfo.mime" />
        <img
          v-else
          :src="url"
          loading="lazy"
          :title="`Image de ${type} de ${firstName} ${lastName}, número ${index + 1}`"
          :alt="`Image de ${type} de ${firstName} ${lastName}, número ${index + 1}`"
        />
      </template>
    </picture>
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
