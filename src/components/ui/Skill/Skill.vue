<script setup lang="ts">
import { ref, computed } from "vue";
import { useTranslations } from "@/i18n/utils";

const props = defineProps({
  title: {
    type: String,
    default: "",
  },
  items: {
    type: Array,
    default: () => ([]),
  },
  lang: {
    type: String,
    default: "es",
  },
});

const t = useTranslations(props.lang);

const items = computed(() => {
  return props.items.map((item) => {
    const keywords = Array.from(new Set(item.keywords));
    return {
      ...item,
      keywords,
    };
  });
});

const showKeywords = ref(false);

const toggleKeywords = () => {
  showKeywords.value = !showKeywords.value;
};
</script>

<template>
  <div class="d-flex flex-direction-column gap-2">
    <div class="no-print">
      <h4 v-if="title" @click="toggleKeywords" class="clickable">
        <i
          v-if="showKeywords"
          class="i-mdi-eye dark:i-mdi-eye-outline"
          aria-hidden="true"
        />
        <i
          v-else
          class="i-mdi-eye-off dark:i-mdi-eye-off-outline"
          aria-hidden="true"
        />
        {{ title }}
      </h4>
      <transition name="fade">
        <footer v-if="showKeywords">
          <span v-for="item in items" :key="item.id">
            {{ item.description }}
          </span>
        </footer>
      </transition>
    </div>
    <div class="print">
      <h4 class="clickable">
        {{ title }}
      </h4>
      <footer>
        <span v-for="item in items" :key="item.id">
          {{ item.description }}
        </span>
      </footer>
    </div>
  </div>
</template>

<style scoped>
footer {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

footer span {
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.2rem 0.6rem;
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.keywords li {
  border: 1px solid ;
  padding: 5px;
  border-radius: 4px;
  margin-bottom: 5px;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.clickable {
  user-select: none;
  cursor: pointer;
}
</style>
