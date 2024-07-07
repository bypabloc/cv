<!-- Path: src/components/ui/Experience/Index.vue -->

<script setup lang="ts">
import { ref, computed } from "vue";
import Skill from "@/components/ui/Skill/Skill.vue";
import { useTranslations } from "@/i18n/utils";

const props = defineProps({
  works: {
    type: Object,
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

const employers = computed(() => Object.values(props.works));
const visibleEmployers = computed(() => {
  return showAll.value ? employers.value : employers.value.slice(0, 3);
});
const hiddenEmployers = computed(() => {
  return employers.value.length - visibleEmployers.value.length;
});

const formatDate = (date) => {
  if (!date) return t("current");
  const parsedDate = new Date(date);
  return parsedDate.toLocaleDateString(
    props.lang,
    {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    },
  );
};

const toggleShowAll = () => {
  showAll.value = !showAll.value;
  if (!showAll.value) {
    // Si estamos ocultando empleadores, hacemos scroll hacia arriba
    setTimeout(() => {
      if (sectionRef.value) {
        sectionRef.value.scrollIntoView({ behavior: 'smooth' });
      }
    }, 0);
  }
};
</script>

<template>
  <section v-if="employers.length > 0" ref="sectionRef">
    <h2>{{ t("work-experience.title") }}</h2>
    <div class="d-flex flex-direction-column gap-8">
      <div v-for="employerGroup in visibleEmployers" :key="employerGroup.employer?.id || employerGroup.works[0].id">
        <header>
          <div>
            <h3 class="employer-name nyx-color2-text-primary-on">
              <a v-if="employerGroup.employer" :href="employerGroup.employer.url" :title="'Ver ' + employerGroup.employer.name" target="_blank">
                {{ employerGroup.employer.name }}
              </a>
              <span v-else>Freelance</span>
            </h3>
          </div>
        </header>

        <div v-if="employerGroup.works.length > 1" class="timeline">
          <article v-for="work in employerGroup.works" :key="work.id" class="timeline-item nyx-color2-text-primary-on">
            <div class="d-flex flex-direction-row flex-justify-space-between nyx-color2-text-primary-base">
              <h4>{{ work.position }}</h4>
              <div>
                <time :datetime="work.startDate" :title="formatDate(work.startDate)">
                  {{ new Date(work.startDate).getFullYear() }}
                </time>
                -
                <time :datetime="work.endDate" :title="formatDate(work.endDate)">
                  {{ work.endDate ? new Date(work.endDate).getFullYear() : t('current') }}
                </time>
              </div>
            </div>
            <footer class="d-flex flex-direction-column gap-4">
              <div v-if="work.summary" class="d-flex flex-direction-column gap-2">
                <p>
                  <strong>{{ t("summary") }}:</strong> {{ work.summary }}
                </p>
              </div>
              <div v-if="work.responsibilitiesNProjects.length > 0" class="d-flex flex-direction-column gap-2">
                <h4>{{ t("work-experience.responsibilitiesNProjects") }}</h4>
                <p v-for="responsibility in work.responsibilitiesNProjects" :key="responsibility">• {{ responsibility }}</p>
              </div>
              <div v-if="work.achievements.length > 0" class="d-flex flex-direction-column gap-2">
                <h4>{{ t("work-experience.achievements") }}</h4>
                <p v-for="achievement in work.achievements" :key="achievement">• {{ achievement }}</p>
              </div>
              <div class="d-flex flex-direction-column gap-2">
                <Skill :title="t('technicalSkills.title')" :items="work.technicalSkills" client:load />
                <Skill :title="t('softSkills.title')" :items="work.softSkills" client:load />
              </div>
            </footer>
          </article>
        </div>

        <div v-else>
          <article v-for="work in employerGroup.works" :key="work.id" class="ml-4 nyx-color2-text-primary-on">
            <div class="flex f-row mt-4">
              <h4 class="nyx-color2-text-primary-base">{{ work.position }}</h4>
              <div>
                <time :datetime="work.startDate" :title="formatDate(work.startDate)">
                  {{ new Date(work.startDate).getFullYear() }}
                </time>
                -
                <time :datetime="work.endDate" :title="formatDate(work.endDate)">
                  {{ work.endDate ? new Date(work.endDate).getFullYear() : t('current') }}
                </time>
              </div>
            </div>
            <footer class="d-flex flex-direction-column gap-4">
              <div v-if="work.summary" class="d-flex flex-direction-column gap-2">
                <p>
                  <strong>{{ t("summary") }}:</strong> {{ work.summary }}
                </p>
              </div>
              <div v-if="work.responsibilitiesNProjects.length > 0" class="d-flex flex-direction-column gap-2">
                <h4>{{ t("work-experience.responsibilitiesNProjects") }}</h4>
                <p v-for="responsibility in work.responsibilitiesNProjects" :key="responsibility">• {{ responsibility }}</p>
              </div>
              <div v-if="work.achievements.length > 0" class="d-flex flex-direction-column gap-2">
                <h4>{{ t("work-experience.achievements") }}</h4>
                <p v-for="achievement in work.achievements" :key="achievement">• {{ achievement }}</p>
              </div>
              <div class="d-flex flex-direction-column gap-2">
                <Skill :title="t('technicalSkills.title')" :items="work.technicalSkills" client:load />
                <Skill :title="t('softSkills.title')" :items="work.softSkills" client:load />
              </div>
            </footer>
          </article>
        </div>
      </div>
    </div>
    <div v-if="employers.length > 3" @click="toggleShowAll" class="nyx-color2-text-primary-on clickable flex items-center">
      <span class="divider"></span>
      <span class="show-all">
        {{ showAll ? t('show.less') : t('show.more', { count: hiddenEmployers }) }}
      </span>
      <span class="divider"></span>
    </div>
  </section>
</template>

<style scoped>
/* Aquí puedes incluir tu CSS adaptado del original */
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

.flex.f-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

footer {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.divider {
  flex: 1;
  height: 1px;
  background-color: var(--divider-color, #ccc); /* Color del divider */
  margin: 0 8px;
  opacity: 0.6;
}

footer span {
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.2rem 0.6rem;
}

.employer-name {
  font-size: 1.2rem;
  font-weight: bold;
}

.timeline {
  position: relative;
  padding-left: 20px;
}

.timeline::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--timeline-bg);
}

.timeline-item {
  position: relative;
  margin-left: 20px;
  padding: 10px 0;
}

.timeline-item::before {
  content: "";
  position: absolute;
  left: -25px;
  top: 10px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--timeline-item-bg);
}

@media (max-width: 700px) {
  time {
    text-align: right;
  }
}

</style>
