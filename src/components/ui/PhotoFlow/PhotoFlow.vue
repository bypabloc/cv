<script setup lang="ts">
import { ref, computed } from "vue";
import UIImage from "@/components/ui/Image/Image.vue";

const props = defineProps({
  images: {
    type: Array,
    default: () => ([]),
  },
  user: {
    type: Object,
    default: () => ({}),
  },
  type: {
    type: String,
    default: 'perfil'
  },
  attributes: {
    type: Object,
    default: () => ({}),
  },
  aspectRatio: {
    type: String,
    default: '1 / 1'
  },
  objectFit: {
    type: String,
    default: 'cover'
  },
  width: {
    type: String,
    default: 'auto'
  },
  borderRadius: {
    type: String,
    default: '16px'
  },
  height: {
    type: String,
    default: 'auto'
  }
});

const currentIndex = ref(0);

const advanceSlide = (step) => {
  if (props.images.length === 0) return;
  const newIndex = (currentIndex.value + step + props.images.length) % props.images.length;
  currentIndex.value = newIndex;
};

const currentImage = computed(() => {
  return props.images[currentIndex.value] || [];
});
</script>

<template>
  <div>
    <div class="slideshow-container">
      <div class="mySlides fade" v-for="(image, index) in props.images" :key="index" v-show="currentIndex === index">
        <div class="numbertext">{{ index + 1 }} / {{ props.images.length }}</div>
        <UIImage
          :items="image.files"
          :user="props.user"
          :type="props.type"
          :attributes="props.attributes"
          :aspectRatio="props.aspectRatio"
          :objectFit="props.objectFit"
          :width="props.width"
          :borderRadius="props.borderRadius"
          :height="props.height"
        />
        <div class="text">{{ image.caption }}</div>
      </div>
      <a href="#" class="prev" @click.prevent="advanceSlide(-1)">&#10094;</a>
      <a href="#" class="next" @click.prevent="advanceSlide(1)">&#10095;</a>
      <div class="dots-container">
        <span 
          class="dot"
          :class="{ 'active': currentIndex === index }"
          v-for="(image, index) in props.images"
          :key="index"
          @click="currentIndex = index"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.slideshow-container {
  max-width: 1000px;
  position: relative;
  margin: auto;
}

.mySlides {
  display: none;
}

.mySlides.fade {
  display: block;
}

.prev, .next, .numbertext, .dots-container {
  opacity: 0;
  transition: opacity 0.5s ease;
}

.slideshow-container:hover .prev,
.slideshow-container:hover .next,
.slideshow-container:hover .numbertext,
.slideshow-container:hover .dots-container {
  opacity: 1;
}

.prev, .next {
  cursor: pointer;
  position: absolute;
  top: 50%;
  width: auto;
  margin-top: -22px;
  padding: 16px;
  font-weight: bold;
  font-size: 18px;
  transition: 0.6s ease;
  border-radius: 0 3px 3px 0;
  user-select: none;
}

.next {
  right: 0;
  border-radius: 3px 0 0 3px;
}

.prev:hover, .next:hover {
}

.text {
  font-size: 15px;
  padding: 8px 12px;
  position: absolute;
  bottom: 8px;
  width: 100%;
  text-align: center;
}

.numbertext {
  font-size: 12px;
  padding: 8px 12px;
  position: absolute;
  top: 0;
  width: 100%;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
}

.dots-container {
  position: absolute;
  bottom: 15px;
  width: 100%;
  text-align: center;
}

.dot {
  cursor: pointer;
  height: 15px;
  width: 15px;
  margin: 0 2px;
  border-radius: 50%;
  display: inline-block;
  transition: background-color 0.6s ease;
}

.active {
}

.dot:hover {
}

@keyframes fade {
  from {
    opacity: 0.4;
  }
  to {
    opacity: 1;
  }
}
</style>
