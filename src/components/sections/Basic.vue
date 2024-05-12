<script setup lang="ts">
import { ref, computed } from "vue";
import { Users } from "astro:db";
import { getAttributes } from "@/utils/db/getAttributes";
import { getUserNetworks } from "@/utils/db/getUserNetworks";

const props = defineProps<{
  user: typeof Users;
}>();

const attributes = ref([]);
const networks = ref([]);

const attributesResult = await getAttributes(props.user)
attributes.value = attributesResult.isValid ? attributesResult.data?.attributes : {};

const networksResult = await getUserNetworks(props.user, attributes.value)
networks.value = networksResult.isValid ? networksResult.data?.networks : [];

const linksPrint = computed(() => {
  return networks.value.filter((network) => {
    if (!network.printUrl.url) return false;
    return true;
  }).map((network) => {
    return network.printUrl
  });
});
</script>

<template>
  <div class="container">
    <div class="info">
      <h1>{{attributes.names.value}} {{ attributes.lastName.value }}</h1>
      <h2>{{attributes.label.value}}</h2>
      <span>
        <span
          class="i-clarity-world-line dark:i-clarity-world-solid"
          aria-hidden="true"
        />
        {{attributes.location.value.city}}, {{attributes.location.value.region}}
      </span>
      <footer class="print">
        <div>
          <template
            v-for="({url, link}, index) in linksPrint"
            :key="`linksPrint-${index}`"
          >
            <a
              v-if="link"
              :href="url"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ url }}{{ index < linksPrint.length - 1 ? ' • ' : '' }}
            </a>
            <span
              v-else
            >
              {{ url }}{{ index < linksPrint.length - 1 ? ' • ' : '' }}
            </span>
          </template>
        </div>
      </footer>
      <footer class="no-print">
        <a
          v-for="network in networks"
          :key="`network-${network.id}`"
          :href="network.webUrl"
          :title="`Visitar el perfil de ${attributes.names.value} ${attributes.lastName.value} en ${network.name}`"
          target="_blank"
          rel="noopener noreferrer"
        >
          <span
            :class="`${network.icons.join(' ')}`"
            aria-hidden="true"
          />
        </a>
      </footer>
      <pre><code>{{ }}</code></pre>
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

footer.print a {
  color: #666;
  /* display: flex;*/
  align-items: center;
  gap: 0.25rem;
  font-size: 0.85rem;
  letter-spacing: -0.05rem;
}
span {
  color: #666;
  /* display: flex;*/
  align-items: center;
  gap: 0.25rem;
  font-size: 0.85rem;
  letter-spacing: -0.05rem;
}

footer.no-print {
  color: #555;
  font-size: 0.65rem;
  display: flex;
  gap: 4px;
  margin-top: 8px;
}

footer.no-print a {
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

footer.no-print a:hover {
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
