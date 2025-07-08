<template>
  <span v-if="inline" ref="container" class="latex-inline"></span>
  <div v-else ref="container" class="latex-block"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import katex from 'katex'

interface Props {
  content: string
  inline?: boolean
  displayMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  inline: false,
  displayMode: false
})

const container = ref<HTMLElement>()

const renderLatex = () => {
  if (!container.value) return

  try {
    katex.render(props.content, container.value, {
      displayMode: props.displayMode || !props.inline,
      throwOnError: false,
      errorColor: '#cc0000',
      strict: 'warn'
    })
  } catch (error) {
    console.error('LaTeX rendering error:', error)
    if (container.value) {
      container.value.textContent = props.content
    }
  }
}

onMounted(() => {
  renderLatex()
})

watch(() => props.content, () => {
  renderLatex()
})
</script>

<style scoped>
.latex-inline {
  display: inline;
}

.latex-block {
  display: block;
  margin: 1em 0;
  text-align: center;
}
</style>
