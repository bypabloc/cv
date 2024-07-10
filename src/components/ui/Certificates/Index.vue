<!-- Path: src/components/ui/Certificates/Index.vue -->

<script setup lang="ts">
import { ref, computed } from "vue";
import { useTranslations } from "@/i18n/utils";
import { formatDateToMonthYear } from "@/utils/formatDateToMonthYear";

const props = defineProps({
  certificates: {
    type: Array,
    required: true,
  },
  lang: {
    type: String,
    required: true,
  },
});

const t = useTranslations(props.lang);

const showAll = ref(false);
const sectionRef = ref<HTMLElement | null>(null);

const visibleCertificates = computed(() => {
  return showAll.value ? props.certificates : props.certificates.slice(0, 3);
});

const hiddenCertificates = computed(() => {
  return props.certificates.length - visibleCertificates.value.length;
});

const hasCertificates = computed(() => props.certificates.length > 0);

const toggleShowAll = () => {
  showAll.value = !showAll.value;
  if (!showAll.value) {
    // Si estamos ocultando certificados, hacemos scroll hacia arriba
    setTimeout(() => {
      if (sectionRef.value) {
        sectionRef.value.scrollIntoView({ behavior: 'smooth' });
      }
    }, 0);
  }
};
</script>

<template>
  <section v-if="hasCertificates" ref="sectionRef">
    <h2>{{ t("certifications.title") }}</h2>
    <div class="d-flex flex-direction-column gap-8">
      <div v-for="{ date, url, issuer, name, title } in visibleCertificates" :key="name">
        <article class="nyx-color2-text-primary-on">
          <header>
            <div>
              <h3 class="nyx-color2-text-primary-base">
                <a :href="url" :title="`Ver ${name}`" target="_blank">
                  {{ title }}
                </a>
              </h3>
            </div>
            <div>
              <time :datetime="date" :data-title="date">
                {{ formatDateToMonthYear(date) }}
              </time>
            </div>
          </header>
          <footer>
            <p>{{ issuer.name }}</p>
          </footer>
        </article>
      </div>
    </div>
    <div v-if="props.certificates.length > 3" @click="toggleShowAll" class="no-print nyx-color2-text-primary-on clickable flex items-center">
      <span class="divider"></span>
      <span class="show-all">
        {{ showAll ? t('show.less') : t('show.more', { count: hiddenCertificates }) }}
      </span>
      <span class="divider"></span>
    </div>
  </section>
</template>

<style scoped>
/* Los estilos permanecen iguales */
ul {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.clickable {
  cursor: pointer;
}

.show-all {
  font-size: 1.2rem;
  font-weight: bold;
}

.flex.items-center {
  display: flex;
  align-items: center;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
}

footer {
  margin-top: 4px;
}

.divider {
  flex: 1;
  height: 1px;
  background-color: var(--divider-color, #ccc);
  margin: 0 8px;
  opacity: 0.6;
}

time {
  font-size: 0.85rem;
  min-width: 102px;
}

h3 {
  font-weight: 500;
}

@media (max-width: 700px) {
  time {
    text-align: right;
  }
}
</style>