<template>
  <section class="experience-section">
    <div class="flex column gap-8">
      <div v-for="(work, index) in works" :key="index">
        <article>
          <header>
            <div>
              <h3>
                <a :href="work.url" :title="`Ver ${work.name}`" target="_blank">
                  {{ work.name }}
                </a>
              </h3>
              <h4>{{ work.position }}</h4>
            </div>
            <div>
              <time :datetime="work.startDate" :data-title="work.startDate">
                {{ new Date(work.startDate).getFullYear() }}
              </time>
              -
              <time :datetime="work.endDate" :data-title="work.endDate">
                {{ work.endDate ? new Date(work.endDate).getFullYear() : 'Actual' }}
              </time>
            </div>
          </header>
          <footer class="flex column gap-4">
            <div class="flex column gap-2">
              <h4>Responsabilidades y proyectos</h4>
              <div>
                <div class="responsibilities-n-projects" v-for="(responsibility, index) in work.responsibilitiesNProjects" :key="index">
                  <p :data-content="responsibility">
                    • {{ responsibility }}
                  </p>
                </div>
              </div>
            </div>
            <div class="flex column gap-2">
              <h4>Logros</h4>
              <ul>
                <li v-for="(achievement, index) in work.achievements" :key="index">
                  <p>• {{ achievement }}</p>
                </li>
              </ul>
            </div>
            <div v-for="section in sections[index]" :key="section.title" class="flex column gap-2">
              <button @click="section.show = !section.show">{{ section.title }}</button>
              <div v-show="section.show">
                <span v-for="(item, index) in section.items" :key="index">{{ item }}<span v-if="index < section.items.length - 1">, </span></span>
              </div>
            </div>
          </footer>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
console.log('Experience > script setup')
import { ref, reactive, onMounted } from 'vue';
import { work as works } from "@cv";
// console.log('works', works)

const sections = ref([]);

onMounted(() => {

  sections.value = works.map(work => ({
    technicalSkills: {
      title: 'Habilidades técnicas',
      items: work.technicalSkills,
      show: false
    },
    softSkills: {
      title: 'Habilidades blandas',
      items: work.softSkills,
      show: false
    },
    aptitudes: {
      title: 'Aptitudes',
      items: work.aptitudes,
      show: false
    }
  }));
});
</script>

<style scoped>
.flex {
  display: flex;
}
.flex.column {
  flex-direction: column;
}
/* Más estilos según sea necesario */
</style>
