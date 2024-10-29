<!-- Path: src/components/ui/Interests/Index.vue -->

<script setup lang="ts">
import { ref, computed } from "vue";
import { useTranslations } from "@/i18n/utils";

const props = defineProps({
  interests: {
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

const visibleInterests = computed(() => {
  return showAll.value ? props.interests : props.interests.slice(0, 5);
});

const hiddenInterests = computed(() => {
  return props.interests.length - visibleInterests.value.length;
});

const hasInterests = computed(() => props.interests.length > 0);

const toggleShowAll = () => {
  showAll.value = !showAll.value;
  if (!showAll.value) {
    // Si estamos ocultando intereses, hacemos scroll hacia arriba
    setTimeout(() => {
      if (sectionRef.value) {
        sectionRef.value.scrollIntoView({ behavior: 'smooth' });
      }
    }, 0);
  }
};
</script>

<template>
  <section v-if="hasInterests" ref="sectionRef">
    <div class="d-flex flex-direction-column gap-2">
      <div v-for="{ name } in visibleInterests" :key="name">
        <article class="nyx-color2-text-primary-on">
          <header>
            <div>
              <h3>• {{ name }}</h3>
            </div>
          </header>
        </article>
      </div>
    </div>
    <div v-if="props.interests.length > 5" @click="toggleShowAll" class="no-print nyx-color2-text-primary-on clickable flex items-center mt-4">
      <span class="divider"></span>
      <span class="show-all">
        {{ showAll ? t('show.less') : t('show.more', { count: hiddenInterests }) }}
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

.gap-2 {
  gap: 2px;
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
  font-weight: 400;
}

@media (max-width: 700px) {
  time {
    text-align: right;
  }
}
</style>