<script setup lang="ts">
import { ref, computed } from "vue";
import Section from "../Section.vue"
import { getAttributes } from "@/utils/db/getAttributes";

const props = defineProps<{
  user: typeof Users;
}>();

const attributes = ref([]);
const networks = ref([]);

const attributesResult = await getAttributes(props.user)
attributes.value = attributesResult.isValid ? attributesResult.data?.attributes : {};
</script>

<template>
  <Section title="Sobre mí">
    <p>
      {{ attributes.summary.value }}
    </p>
  </Section>
</template>

<style scoped>
</style>
