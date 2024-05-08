<script setup lang="ts">
import { ref, reactive } from "vue";
import { Users } from "astro:db";
import { getAttributes } from "@/utils/db/getAttributes";

const props = defineProps<{
  user: typeof Users;
}>();

const attributes = ref([]);
console.log('props', props.user);

const attributesResult = await getAttributes(props.user)
attributes.value = attributesResult.isValid ? attributesResult.data?.attributes : {};

</script>

<template>
  <div class="container">
    <div class="info">
      <h1>Información básica</h1>
      {{ props.user }}
      <h1>{{attributes.names.value}} {{ attributes.lastName.value }}</h1>
      <h2>{{attributes.label.value}}</h2>
    </div>
  </div>
</template>

<style scoped>
.container {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-right: 32px;
}

h1 {
  font-size: 2rem;
}

h2 {
  color: #444;
  font-weight: 500;
  font-size: 1.1rem;
  text-wrap: balance;
}

img {
  aspect-ratio: 1 / 1;
  object-fit: cover;
  width: 128px;
  border-radius: 16px;
}

span {
  color: #666;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.85rem;
  letter-spacing: -0.05rem;
}

footer {
  color: #555;
  font-size: 0.65rem;
  display: flex;
  gap: 4px;
  margin-top: 8px;
}

footer a {
  color: #777;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #eee;
  padding: 4px;
  height: 32px;
  width: 32px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

footer a:hover {
  background: #eee;
  border: 1px solid #ddd;
}

@media (width <= 700px) {
  .container {
    flex-direction: column-reverse;
  }

  .info {
    justify-content: center;
    align-items: center;
    padding-right: 0;
    text-align: center;
  }

  figure {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  h2 {
    text-wrap: balance;
  }

  figure {
    margin: 0 auto;
  }
}
</style>
