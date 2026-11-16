<script setup lang="ts">
import type { FormSubmitEvent } from '@nuxt/ui'

definePageMeta({ layout: 'public' })

const api = useApi()
const toast = useToast()

// Device identifier for "already registered" detection
const clientId = ref<string>('')
onMounted(() => {
  let id = localStorage.getItem('gestionplatos_client_id')
  if (!id) {
    id = (crypto?.randomUUID?.() ?? Math.random().toString(36).slice(2))
    localStorage.setItem('gestionplatos_client_id', id)
  }
  clientId.value = id
  load()
  const timer = setInterval(load, 15000)
  onBeforeUnmount(() => clearInterval(timer))
})

const dishes = ref<Dish[]>([])
const myRegistrations = ref<Registration[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    dishes.value = await api.get<Dish[]>('/dishes')
    if (clientId.value) {
      myRegistrations.value = await api.get<Registration[]>(`/registrations?client_id=${encodeURIComponent(clientId.value)}`)
    }
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.message ?? 'No se pudieron cargar los platos', color: 'error' })
  } finally {
    loading.value = false
  }
}

const registeredDishIds = computed(() => new Set(myRegistrations.value.map(r => r.dish_id)))

// Sign-up modal
const signupOpen = ref(false)
const signupDish = ref<Dish | null>(null)
const signupForm = reactive({ first_name: '', last_name: '' })
const signupLoading = ref(false)

function openSignup(dish: Dish) {
  signupDish.value = dish
  signupForm.first_name = ''
  signupForm.last_name = ''
  signupOpen.value = true
}

async function submitSignup(event: FormSubmitEvent<{ first_name: string, last_name: string }>) {
  if (!signupDish.value) return
  signupLoading.value = true
  try {
    await api.post('/registrations', {
      first_name: event.data.first_name,
      last_name: event.data.last_name,
      dish_id: signupDish.value.id,
      client_id: clientId.value
    })
    toast.add({ title: 'Inscrito', description: `Te apuntaste a ${signupDish.value.name}`, color: 'success' })
    signupOpen.value = false
    await load()
  } catch (e: any) {
    const msg = e?.data?.detail ?? e?.message ?? 'No se pudo inscribir'
    toast.add({ title: 'Error', description: msg, color: 'error' })
  } finally {
    signupLoading.value = false
  }
}

// Propose dish modal
const proposeOpen = ref(false)
const proposeForm = reactive({ first_name: '', last_name: '', dish_name: '', description: '' })
const proposeLoading = ref(false)

async function submitPropose(event: FormSubmitEvent<{ first_name: string, last_name: string, dish_name: string, description?: string }>) {
  proposeLoading.value = true
  try {
    await api.post('/proposals', {
      first_name: event.data.first_name,
      last_name: event.data.last_name,
      dish_name: event.data.dish_name,
      description: event.data.description || null
    })
    toast.add({ title: 'Enviado', description: 'Tu propuesta fue enviada a los organizadores', color: 'success' })
    proposeOpen.value = false
    proposeForm.first_name = ''
    proposeForm.last_name = ''
    proposeForm.dish_name = ''
    proposeForm.description = ''
  } catch (e: any) {
    const msg = e?.data?.detail ?? e?.message ?? 'No se pudo enviar la propuesta'
    toast.add({ title: 'Error', description: msg, color: 'error' })
  } finally {
    proposeLoading.value = false
  }
}

function occupancyText(d: Dish) {
  if (d.registered === 0) return '0/' + d.max_quota + ' — disponible'
  if (d.is_full) return d.registered + '/' + d.max_quota + ' — completo'
  return d.registered + '/' + d.max_quota + ' — queda ' + (d.max_quota - d.registered)
}
</script>

<template>
  <div class="mx-auto max-w-2xl px-4 py-8">
    <!-- Welcome -->
    <header class="mb-8 text-center">
      <h1 class="text-3xl font-bold tracking-tight">Cena de Thanksgiving 🦃</h1>
      <p class="mt-2 text-muted">
        Bienvenido/a. Elegí un plato con cupo libre o proponé uno nuevo.
      </p>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="size-8 animate-spin" />
    </div>

    <!-- Dish list -->
    <div v-else class="space-y-4">
      <UCard
        v-for="dish in dishes"
        :key="dish.id"
        :ui="{ body: 'p-4' }"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h2 class="text-lg font-semibold truncate">{{ dish.name }}</h2>
            <p v-if="dish.description" class="text-sm text-muted mt-1">{{ dish.description }}</p>
            <UBadge
              class="mt-2"
              :color="dish.is_full ? 'error' : (dish.registered === 0 ? 'success' : 'warning')"
              variant="subtle"
            >
              {{ occupancyText(dish) }}
            </UBadge>
          </div>

          <div class="shrink-0 flex flex-col items-end gap-2">
            <span v-if="registeredDishIds.has(dish.id)" class="text-xs text-muted">
              Ya estás inscrito
            </span>
            <UButton
              :disabled="dish.is_full"
              size="sm"
              @click="openSignup(dish)"
            >
              {{ registeredDishIds.has(dish.id) ? 'Registrar acompañante' : 'Apuntarme' }}
            </UButton>
          </div>
        </div>
      </UCard>

      <p v-if="dishes.length === 0" class="text-center text-muted py-8">
        No hay platos disponibles todavía.
      </p>
    </div>

    <!-- Propose dish -->
    <div class="mt-8 text-center">
      <UButton variant="outline" @click="proposeOpen = true">
        Proponer un plato nuevo
      </UButton>
    </div>

    <!-- Sign-up modal -->
    <UModal v-model:open="signupOpen" title="Apuntarse a un plato">
      <template #body>
        <p v-if="signupDish" class="mb-4 text-sm text-muted">
          Plato: <strong>{{ signupDish.name }}</strong>
        </p>
        <UForm :state="signupForm" @submit="submitSignup">
          <UFormField label="Nombre" name="first_name" required>
            <UInput v-model="signupForm.first_name" autocomplete="given-name" />
          </UFormField>
          <UFormField label="Apellido" name="last_name" required class="mt-3">
            <UInput v-model="signupForm.last_name" autocomplete="family-name" />
          </UFormField>
          <div class="mt-4 flex justify-end gap-2">
            <UButton variant="ghost" @click="signupOpen = false">Cancelar</UButton>
            <UButton type="submit" :loading="signupLoading">Confirmar</UButton>
          </div>
        </UForm>
      </template>
    </UModal>

    <!-- Propose modal -->
    <UModal v-model:open="proposeOpen" title="Proponer un plato nuevo">
      <template #body>
        <UForm :state="proposeForm" @submit="submitPropose">
          <UFormField label="Nombre" name="first_name" required>
            <UInput v-model="proposeForm.first_name" autocomplete="given-name" />
          </UFormField>
          <UFormField label="Apellido" name="last_name" required class="mt-3">
            <UInput v-model="proposeForm.last_name" autocomplete="family-name" />
          </UFormField>
          <UFormField label="Nombre del plato" name="dish_name" required class="mt-3">
            <UInput v-model="proposeForm.dish_name" />
          </UFormField>
          <UFormField label="Descripción (opcional)" name="description" class="mt-3">
            <UTextarea v-model="proposeForm.description" />
          </UFormField>
          <div class="mt-4 flex justify-end gap-2">
            <UButton variant="ghost" @click="proposeOpen = false">Cancelar</UButton>
            <UButton type="submit" :loading="proposeLoading">Enviar propuesta</UButton>
          </div>
        </UForm>
      </template>
    </UModal>
  </div>
</template>
