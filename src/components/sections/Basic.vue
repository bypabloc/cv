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

const networksResult = await getUserNetworks(props.user)
networks.value = networksResult.isValid ? networksResult.data?.networks : [];

const linkedInfo = computed(() => {
  return networks.value.find(({ codeName }) => codeName === "linkedin")
});
const linkedUrl = computed(() => linkedInfo.value?.networksUsersUrl);

const email = computed(() => attributes.value.email.value);
const phone = computed(() => attributes.value.phone.value);

const printInfo = computed(() => {
  return [email.value, phone.value, linkedUrl.value].filter(Boolean).join(" • ")
})

</script>

<template>
  <div class="container">
    <div class="info">
      <h1>{{attributes.names.value}} {{ attributes.lastName.value }}</h1>
      <h2>{{attributes.label.value}}</h2>
      <span>
        <WorldMap />
        {{attributes.location.value.city}}, {{attributes.location.value.region}}
      </span>
      <footer class="print">
        {{printInfo}}
      </footer>
      <footer class="no-print">
        <a
          v-if="email"
          :href="`mailto:${email}`"
          :title="`Enviar un correo electrónico a ${attributes.names.value} ${attributes.lastName.value} al correo ${email}`"
          target="_blank"
          rel="noopener noreferrer"
        >
          mail
        </a>
        <a
          v-if="phone"
          :href="`tel:${phone}`"
          :title="`Llamar por teléfono a ${attributes.names.value} ${attributes.lastName.value} al número ${phone}`"
          target="_blank"
          rel="noopener noreferrer"
        >
          phone
        </a>
        <a
          v-for="network in networks"
          :key="`network-${network.id}`"
          :href="network.networksUsersUrl"
          :title="`Visitar el perfil de ${attributes.names.value} ${attributes.lastName.value} en ${network.name}`"
          target="_blank"
          rel="noopener noreferrer"
        >
          {{ network.codeName }}
        </a>
      </footer>
      <pre><code>{{ networks }}</code></pre>
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
