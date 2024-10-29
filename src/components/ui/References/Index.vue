<!-- Path: src/components/ui/References/Index.vue -->

<script setup lang="ts">
import { ref, computed } from "vue";
import { useTranslations } from "@/i18n/utils";

const props = defineProps({
  references: {
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

const visibleReferences = computed(() => {
  return showAll.value ? props.references : props.references.slice(0, 3);
});

const hiddenReferences = computed(() => {
  return props.references.length - visibleReferences.value.length;
});

const hasReferences = computed(() => props.references.length > 0);

const toggleShowAll = () => {
  showAll.value = !showAll.value;
  if (!showAll.value) {
    // Si estamos ocultando referencias, hacemos scroll hacia arriba
    setTimeout(() => {
      if (sectionRef.value) {
        sectionRef.value.scrollIntoView({ behavior: 'smooth' });
      }
    }, 0);
  }
};
</script>

<template>
  <section v-if="hasReferences" ref="sectionRef">
    <div class="d-flex flex-direction-column gap-8">
      <div v-for="{ name, position, reference, url } in visibleReferences" :key="name">
        <article class="nyx-color2-text-primary-on">
          <header>
            <div>
              <h3 class="nyx-color2-text-primary-base">
                <a :href="url" :title="`Ver ${name}`" target="_blank">
                  {{ name }}
                </a>
              </h3>
              <h4>{{ position }}</h4>
            </div>
          </header>
          <footer>
            <p>{{ reference }}</p>
          </footer>
        </article>
      </div>
    </div>
    <div v-if="props.references.length > 3" @click="toggleShowAll" class="no-print nyx-color2-text-primary-on clickable flex items-center mt-4">
      <span class="divider"></span>
      <span class="show-all">
        {{ showAll ? t('show.less') : t('show.more', { count: hiddenReferences }) }}
      </span>
      <span class="divider"></span>
    </div>
  </section>
</template>

<style scoped>
.d-flex {
  display: flex;
}

.flex-direction-column {
  flex-direction: column;
}

.gap-8 {
  gap: 2rem;
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

.mt-4 {
  margin-top: 1rem;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
}

.divider {
  flex: 1;
  height: 1px;
  background-color: var(--divider-color, #ccc);
  margin: 0 8px;
  opacity: 0.6;
}

h3 {
  font-weight: 500;
}

h4 {
  font-weight: 400;
  font-style: italic;
}

footer {
  margin-top: 0.5rem;
}

@media (max-width: 700px) {
  time {
    text-align: right;
  }
}
</style>