<!-- Path: src/components/ui/Publications/Index.vue -->

<script setup lang="ts">
import { ref, computed } from "vue";
import { useTranslations } from "@/i18n/utils";
import { formatDateToMonthYear } from "@/utils/formatDateToMonthYear";

const props = defineProps({
  publications: {
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

const visiblePublications = computed(() => {
  return showAll.value ? props.publications : props.publications.slice(0, 3);
});

const hiddenPublications = computed(() => {
  return props.publications.length - visiblePublications.value.length;
});

const hasPublications = computed(() => props.publications.length > 0);

const toggleShowAll = () => {
  showAll.value = !showAll.value;
  if (!showAll.value) {
    // Si estamos ocultando publicaciones, hacemos scroll hacia arriba
    setTimeout(() => {
      if (sectionRef.value) {
        sectionRef.value.scrollIntoView({ behavior: 'smooth' });
      }
    }, 0);
  }
};
</script>

<template>
  <section v-if="hasPublications" ref="sectionRef">
    <h2>{{ t("publications.title") }}</h2>
    <div class="d-flex flex-direction-column gap-8">
      <div v-for="{ name, publisher, releaseDate, summary, url } in visiblePublications" :key="name">
        <article class="nyx-color2-text-primary-on">
          <header>
            <div>
              <h3 class="nyx-color2-text-primary-base">
                <a :href="url" :title="`Ver ${name}`" target="_blank">
                  {{ name }}
                </a>
              </h3>
              <h4>{{ publisher.name }}</h4>
            </div>
            <div>
              <time :datetime="releaseDate" :data-title="releaseDate">
                {{ formatDateToMonthYear(releaseDate) }}
              </time>
            </div>
          </header>
          <footer>
            <p>{{ summary }}</p>
          </footer>
        </article>
      </div>
    </div>
    <div v-if="props.publications.length > 3" @click="toggleShowAll" class="nyx-color2-text-primary-on clickable flex items-center">
      <span class="divider"></span>
      <span class="show-all">
        {{ showAll ? t('show.less') : t('show.more', { count: hiddenPublications }) }}
      </span>
      <span class="divider"></span>
    </div>
  </section>
</template>

<style scoped>
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

h4 {
  font-weight: 400;
  font-style: italic;
}

@media (max-width: 700px) {
  time {
    text-align: right;
  }
}
</style>