<script setup lang="ts">
const colorMode = useColorMode()
colorMode.preference = 'light'

useHead({
  htmlAttrs: { lang: 'es' },
  meta: [
    { charset: 'utf-8' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { key: 'theme-color', name: 'theme-color', content: '#FAF5EE' }
  ],
  link: [
    { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap'
    }
  ]
})

const title = 'Thanksgiving-Q Málaga'
const description = 'Un espacio para compartir alrededor de la mesa, celebrar lo vivido este año y dar gracias juntos.'

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description
})
</script>

<template>
  <UApp class="bg-[#FAF5EE] font-sans">
    <NuxtLoadingIndicator color="#C2592A" />

    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>

<style>
.font-serif { font-family: 'Playfair Display', serif; }
.font-sans { font-family: 'Inter', sans-serif; }
</style>