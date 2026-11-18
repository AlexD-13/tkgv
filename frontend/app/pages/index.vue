<script setup lang="ts">
import type { FormSubmitEvent } from '@nuxt/ui'
import type { Dish, Registration } from '~/types'

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

  // Autocomplete previously used name/last name from this device
  const savedFirst = localStorage.getItem('gestionplatos_first_name')
  const savedLast = localStorage.getItem('gestionplatos_last_name')
  if (savedFirst) {
    signupForm.first_name = savedFirst
    proposeForm.first_name = savedFirst
  }
  if (savedLast) {
    signupForm.last_name = savedLast
    proposeForm.last_name = savedLast
  }

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

// Search / filter toolbar
const selectedCategory = ref('Todos')
const hideFull = ref(false)

const categories = computed(() => {
  const set = new Set<string>()
  for (const d of dishes.value) {
    if (d.category) set.add(d.category)
  }
  return ['Todos', ...Array.from(set)]
})

const filteredDishes = computed(() => {
  let list = dishes.value
  if (selectedCategory.value !== 'Todos') {
    list = list.filter(d => d.category === selectedCategory.value)
  }
  if (hideFull.value) {
    list = list.filter(d => !d.is_full)
  }
  return list
})

const groupedDishes = computed(() => {
  if (selectedCategory.value !== 'Todos') {
    return [{ category: selectedCategory.value, items: filteredDishes.value }]
  }
  const groups: { category: string, items: Dish[] }[] = []
  const map = new Map<string, Dish[]>()
  for (const d of filteredDishes.value) {
    const key = d.category || 'Otros'
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(d)
  }
  for (const [category, items] of map) {
    groups.push({ category, items })
  }
  return groups
})

// Sign-up modal
const signupOpen = ref(false)
const signupDish = ref<Dish | null>(null)
const signupForm = reactive({ first_name: '', last_name: '' })
const signupLoading = ref(false)

function openSignup(dish: Dish) {
  signupDish.value = dish
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
    localStorage.setItem('gestionplatos_first_name', event.data.first_name)
    localStorage.setItem('gestionplatos_last_name', event.data.last_name)
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
    localStorage.setItem('gestionplatos_first_name', event.data.first_name)
    localStorage.setItem('gestionplatos_last_name', event.data.last_name)
    toast.add({ title: 'Enviado', description: 'Tu propuesta fue enviada a los organizadores', color: 'success' })
    proposeOpen.value = false
    proposeForm.dish_name = ''
    proposeForm.description = ''
  } catch (e: any) {
    const msg = e?.data?.detail ?? e?.message ?? 'No se pudo enviar la propuesta'
    toast.add({ title: 'Error', description: msg, color: 'error' })
  } finally {
    proposeLoading.value = false
  }
}

function freeSeats(d: Dish) {
  return Math.max(0, d.max_quota - d.registered)
}

function occupancyLabel(d: Dish) {
  const free = freeSeats(d)
  if (free === 0) return 'Mesa cubierta'
  if (free === 1) return '¡Último lugar!'
  if (free === d.max_quota) return `${free} plazas disponibles`
  return `Quedan ${free} lugares`
}

function statusClasses(d: Dish) {
  const free = freeSeats(d)
  if (free === 0) return 'text-[#78716C] bg-[#F5F5F4]'
  if (free === 1) return 'text-[#B45309] bg-[#FEF3C7]'
  return 'text-[#3F624D] bg-[#EBF3EE]'
}

function myDishNames() {
  return myRegistrations.value
    .map(r => dishes.value.find(d => d.id === r.dish_id)?.name)
    .filter(Boolean) as string[]
}
</script>

<template>
  <div class="min-h-screen bg-[#FAF5EE] text-[#2B241B] font-sans">
    <!-- Hero -->
    <header class="px-4 pt-8 pb-6 text-center">
      <div class="mx-auto max-w-2xl">
        <div class="mb-2 text-3xl">🍂</div>
        <h1 class="font-serif text-4xl font-bold tracking-tight text-[#2B241B]">
          Nuestra Cena de Thanksgiving
        </h1>
        <p class="mt-3 text-base text-[#5C4A3A]">
          Un espacio para compartir alrededor de la mesa, celebrar lo vivido este año y dar gracias juntos.
        </p>

        <!-- Invitation note -->
        <div class="mt-6 rounded-2xl border border-[#E6D7C3] bg-[#FFFDF9] p-4 text-left shadow-sm">
          <div class="flex gap-3">
            <UIcon name="i-lucide-mail" class="mt-0.5 size-5 shrink-0 text-[#C2592A]" />
            <p class="text-sm leading-relaxed text-[#5C4A3A]">
              Al ser una cena especial, priorizamos el poder elaborar cada plato con cariño. Pero entendemos que a veces puede ser difícil, así que si quieres comprarlo también está bien.
            </p>
          </div>
        </div>

        <!-- Top action -->
        <div class="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <UButton
            class="bg-[#C2592A] hover:bg-[#A3461D] text-white"
            icon="i-lucide-plus"
            @click="proposeOpen = true"
          >
            Proponer un plato nuevo
          </UButton>
        </div>
      </div>
    </header>

    <!-- User status banner -->
    <div v-if="myRegistrations.length" class="mx-auto max-w-2xl px-4">
      <div class="mb-4 rounded-2xl border border-[#E6D7C3] bg-[#FFFDF9] p-4 shadow-sm">
        <p class="text-sm text-[#5C4A3A]">
          Ya estás apuntado a:
          <strong class="text-[#2B241B]">{{ myDishNames().join(', ') }}</strong>.
          Puedes añadir un acompañante o elegir otro plato.
        </p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="size-8 animate-spin text-[#C2592A]" />
    </div>

    <template v-else>
      <!-- Toolbar -->
      <div class="sticky top-0 z-10 mx-auto max-w-2xl px-4 py-3 backdrop-blur">
        <div class="flex flex-col gap-3 rounded-2xl border border-[#E6D7C3] bg-[#FFFDF9]/90 p-3 shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium text-[#5C4A3A]">Categoría</span>
            <select
              v-model="selectedCategory"
              class="rounded-lg border border-[#E6D7C3] bg-white px-3 py-1.5 text-sm text-[#2B241B] focus:outline-none focus:ring-2 focus:ring-[#C2592A]/40"
            >
              <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <label class="flex items-center gap-2 text-sm text-[#5C4A3A]">
            <input
              v-model="hideFull"
              type="checkbox"
              class="h-4 w-4 rounded border-[#E6D7C3] text-[#C2592A] focus:ring-[#C2592A]"
            />
            Ocultar platos completos
          </label>
        </div>
      </div>

      <!-- Dish groups -->
      <div class="mx-auto max-w-2xl px-4 pb-12">
        <template v-if="filteredDishes.length === 0">
          <p class="py-8 text-center text-[#78716C]">
            No hay platos disponibles todavía.
          </p>
        </template>

        <div v-for="group in groupedDishes" :key="group.category" class="mb-8">
          <h2 class="font-serif mb-3 text-2xl font-semibold text-[#2B241B]">
            {{ group.category }}
          </h2>
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <article
              v-for="dish in group.items"
              :key="dish.id"
              class="rounded-2xl border border-[#E6D7C3] bg-[#FFFDF9] p-4 shadow-sm transition"
              :class="dish.is_full ? 'opacity-60' : ''"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <h3 class="text-lg font-semibold text-[#2B241B]">{{ dish.name }}</h3>
                  <p v-if="dish.description" class="mt-1 text-sm text-[#78716C]">
                    {{ dish.description }}
                  </p>
                </div>
              </div>

              <!-- Seats -->
              <div class="mt-3 flex items-center gap-2">
                <div class="flex gap-1">
                  <span
                    v-for="i in dish.max_quota"
                    :key="i"
                    class="text-base"
                    :class="i <= dish.registered ? 'text-[#C2592A]' : 'text-[#D6C9B6]'"
                  >
                    {{ i <= dish.registered ? '●' : '○' }}
                  </span>
                </div>
                <span
                  class="rounded-full px-2.5 py-0.5 text-xs font-medium"
                  :class="statusClasses(dish)"
                >
                  {{ occupancyLabel(dish) }}
                </span>
              </div>

              <div class="mt-4 flex items-center justify-between gap-2">
                <span v-if="registeredDishIds.has(dish.id)" class="text-xs text-[#78716C]">
                  Ya estás inscrito
                </span>
                <span v-else></span>
                <UButton
                  size="sm"
                  :disabled="dish.is_full"
                  :class="dish.is_full
                    ? 'bg-[#E7E5E4] text-[#78716C] cursor-not-allowed'
                    : 'bg-[#C2592A] hover:bg-[#A3461D] text-white'"
                  @click="openSignup(dish)"
                >
                  {{ dish.is_full ? 'Completo' : (registeredDishIds.has(dish.id) ? 'Registrar acompañante' : 'Apuntarme') }}
                </UButton>
              </div>
            </article>
          </div>
        </div>
      </div>
    </template>

    <!-- Sign-up modal -->
    <UModal
      v-model:open="signupOpen"
      title="Apuntarse a un plato"
      :ui="{ content: 'rounded-2xl bg-[#FFFDF9] border border-[#E6D7C3] shadow-xl', body: 'bg-[#FFFDF9]' }"
    >
      <template #body>
        <div class="rounded-2xl bg-[#FFFDF9] p-1">
          <p v-if="signupDish" class="mb-4 text-sm text-[#5C4A3A]">
            Plato: <strong class="text-[#2B241B]">{{ signupDish.name }}</strong>
          </p>
          <UForm :state="signupForm" @submit="submitSignup">
            <UFormField label="Nombre" name="first_name" required>
              <UInput v-model="signupForm.first_name" autocomplete="given-name" class="bg-white" />
            </UFormField>
            <UFormField label="Apellido" name="last_name" required class="mt-3">
              <UInput v-model="signupForm.last_name" autocomplete="family-name" class="bg-white" />
            </UFormField>
            <div class="mt-4 flex justify-end gap-2">
              <UButton variant="ghost" class="text-[#5C4A3A]" @click="signupOpen = false">Cancelar</UButton>
              <UButton type="submit" :loading="signupLoading" class="bg-[#C2592A] hover:bg-[#A3461D] text-white">
                Confirmar
              </UButton>
            </div>
          </UForm>
        </div>
      </template>
    </UModal>

    <!-- Propose modal -->
    <UModal
      v-model:open="proposeOpen"
      title="Proponer un plato nuevo"
      :ui="{ content: 'rounded-2xl bg-[#FFFDF9] border border-[#E6D7C3] shadow-xl', body: 'bg-[#FFFDF9]' }"
    >
      <template #body>
        <div class="rounded-2xl bg-[#FFFDF9] p-1">
          <UForm :state="proposeForm" @submit="submitPropose">
            <UFormField label="Nombre" name="first_name" required>
              <UInput v-model="proposeForm.first_name" autocomplete="given-name" class="bg-white" />
            </UFormField>
            <UFormField label="Apellido" name="last_name" required class="mt-3">
              <UInput v-model="proposeForm.last_name" autocomplete="family-name" class="bg-white" />
            </UFormField>
            <UFormField label="Nombre del plato" name="dish_name" required class="mt-3">
              <UInput v-model="proposeForm.dish_name" class="bg-white" />
            </UFormField>
            <UFormField label="Descripción (opcional)" name="description" class="mt-3">
              <UTextarea v-model="proposeForm.description" class="bg-white" />
            </UFormField>
            <div class="mt-4 flex justify-end gap-2">
              <UButton variant="ghost" class="text-[#5C4A3A]" @click="proposeOpen = false">Cancelar</UButton>
              <UButton type="submit" :loading="proposeLoading" class="bg-[#C2592A] hover:bg-[#A3461D] text-white">
                Enviar propuesta
              </UButton>
            </div>
          </UForm>
        </div>
      </template>
    </UModal>
  </div>
</template>