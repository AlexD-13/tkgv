<script setup lang="ts">
import type { FormSubmitEvent } from '@nuxt/ui'
import type { Dish, Registration } from '~/types'

definePageMeta({ layout: 'public' })

const ENABLE_PROPOSALS = false
const api = useApi()
const toast = useToast()

interface LocalRegistration {
  id: number
  dish_id: number
  dish_name: string
  first_name: string
  last_name: string
}

const LOCAL_KEY = 'gestionplatos_registrations'
const NAME_KEY = 'gestionplatos_name'
const dishes = ref<Dish[]>([])
const myRegistrations = ref<LocalRegistration[]>([])
const loading = ref(false)
const clientId = ref('')

const categories = ['Aperitivo', 'Comida', 'Postre', 'Bebida'] as const
type Category = typeof categories[number]
const selectedCategory = ref<Category>('Aperitivo')
const hideFull = ref(false)
const slider = ref<HTMLElement | null>(null)

const signupOpen = ref(false)
const signupDish = ref<Dish | null>(null)
const signupLoading = ref(false)
const signupForm = reactive({ first_name: '', last_name: '' })

const changing = ref<LocalRegistration | null>(null)
const recoveryOpen = ref(false)
const recoveryQuery = ref('')
const recoveryResults = ref<Registration[]>([])
const recoveryLoading = ref(false)

function normalizeCategory(category?: string | null): Category | null {
  const normalized = category?.trim().toLowerCase()
  return categories.find(item => item.toLowerCase() === normalized) ?? null
}

function readLocalRegistrations(): LocalRegistration[] {
  try {
    return JSON.parse(localStorage.getItem(LOCAL_KEY) || '[]')
  } catch {
    return []
  }
}

function saveLocalRegistrations(registrations: LocalRegistration[]) {
  myRegistrations.value = registrations
  localStorage.setItem(LOCAL_KEY, JSON.stringify(registrations))
}

function syncLocalRegistrations(serverRegistrations: Registration[]) {
  const byId = new Map(serverRegistrations.map(registration => [registration.id, registration]))
  const saved = readLocalRegistrations()
  const active = saved.filter(item => byId.has(item.id)).map(item => ({
    ...item,
    dish_name: dishes.value.find(dish => dish.id === item.dish_id)?.name || item.dish_name
  }))
  saveLocalRegistrations(active)
}

async function load() {
  loading.value = true
  try {
    dishes.value = await api.get<Dish[]>('/dishes')
    if (clientId.value) {
      const serverRegistrations = await api.get<Registration[]>(`/registrations?client_id=${encodeURIComponent(clientId.value)}`)
      syncLocalRegistrations(serverRegistrations)
    }
  } catch (error: any) {
    toast.add({ title: 'Error', description: error?.message || 'No se pudieron cargar los platos', color: 'error' })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  let id = localStorage.getItem('gestionplatos_client_id')
  if (!id) {
    id = crypto?.randomUUID?.() || Math.random().toString(36).slice(2)
    localStorage.setItem('gestionplatos_client_id', id)
  }
  clientId.value = id

  myRegistrations.value = readLocalRegistrations()
  const savedName = localStorage.getItem(NAME_KEY)
  if (savedName) {
    const separator = savedName.lastIndexOf(' ')
    signupForm.first_name = separator > 0 ? savedName.slice(0, separator) : savedName
    signupForm.last_name = separator > 0 ? savedName.slice(separator + 1) : ''
  }

  load()
  const timer = window.setInterval(load, 15000)
  onBeforeUnmount(() => window.clearInterval(timer))
})

function dishesForCategory(category: Category) {
  return dishes.value.filter((dish) => {
    if (normalizeCategory(dish.category) !== category) return false
    return !hideFull.value || !dish.is_full
  })
}

function categoryFreeSeats(category: Category) {
  return dishesForCategory(category).reduce((total, dish) => {
    return total + Math.max(0, dish.max_quota - dish.registered)
  }, 0)
}

function selectCategory(category: Category) {
  selectedCategory.value = category
  const index = categories.indexOf(category)
  slider.value?.children[index]?.scrollIntoView({ behavior: 'smooth', inline: 'start', block: 'nearest' })
}

function syncCategoryFromScroll() {
  if (!slider.value) return
  const left = slider.value.scrollLeft
  const width = slider.value.clientWidth
  if (!width) return
  const index = Math.round(left / width)
  const category = categories[Math.max(0, Math.min(categories.length - 1, index))]
  if (category) selectedCategory.value = category
}

function openSignup(dish: Dish) {
  if (dish.is_full) return
  signupDish.value = dish
  signupOpen.value = true
}

async function submitSignup(event: FormSubmitEvent<{ first_name: string, last_name: string }>) {
  if (!signupDish.value) return
  signupLoading.value = true

  try {
    if (changing.value) {
      const result = await api.post<Registration>('/registrations', {
        first_name: event.data.first_name,
        last_name: event.data.last_name,
        dish_id: signupDish.value.id,
        client_id: clientId.value
      })

      await api.del(`/registrations/${changing.value.id}?client_id=${encodeURIComponent(clientId.value)}`)

      const rest = readLocalRegistrations().filter(item => item.id !== changing.value?.id)
      saveLocalRegistrations([...rest, {
        id: result.id,
        dish_id: result.dish_id,
        dish_name: signupDish.value.name,
        first_name: result.first_name,
        last_name: result.last_name
      }])
      changing.value = null
      toast.add({ title: 'Plato cambiado', description: `Ahora estás apuntado a ${signupDish.value.name}`, color: 'success' })
    } else {
      const result = await api.post<Registration>('/registrations', {
        first_name: event.data.first_name,
        last_name: event.data.last_name,
        dish_id: signupDish.value.id,
        client_id: clientId.value
      })
      saveLocalRegistrations([...readLocalRegistrations(), {
        id: result.id,
        dish_id: result.dish_id,
        dish_name: signupDish.value.name,
        first_name: result.first_name,
        last_name: result.last_name
      }])
      toast.add({ title: 'Apuntado', description: `Te apuntaste a ${signupDish.value.name}`, color: 'success' })
    }

    localStorage.setItem(NAME_KEY, `${event.data.first_name} ${event.data.last_name}`.trim())
    signupOpen.value = false
    await load()
  } catch (error: any) {
    toast.add({ title: 'Error', description: error?.data?.detail || error?.message || 'No se pudo completar la operación', color: 'error' })
  } finally {
    signupLoading.value = false
  }
}

function startChange(registration: LocalRegistration) {
  changing.value = registration
  const savedName = localStorage.getItem(NAME_KEY)
  if (savedName) {
    const separator = savedName.lastIndexOf(' ')
    signupForm.first_name = separator > 0 ? savedName.slice(0, separator) : savedName
    signupForm.last_name = separator > 0 ? savedName.slice(separator + 1) : ''
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelChange() {
  changing.value = null
}

async function removeRegistration(registration: LocalRegistration) {
  if (!window.confirm(`¿Quieres quitarte de ${registration.dish_name}?`)) return
  try {
    await api.del(`/registrations/${registration.id}?client_id=${encodeURIComponent(clientId.value)}`)
    saveLocalRegistrations(readLocalRegistrations().filter(item => item.id !== registration.id))
    toast.add({ title: 'Plaza liberada', description: `Te quitaste de ${registration.dish_name}`, color: 'success' })
    await load()
  } catch (error: any) {
    toast.add({ title: 'Error', description: error?.data?.detail || 'No se pudo quitar la inscripción', color: 'error' })
  }
}

watch(recoveryQuery, async (value) => {
  const query = value.trim()
  if (query.length < 2) {
    recoveryResults.value = []
    return
  }
  recoveryLoading.value = true
  try {
    recoveryResults.value = await api.get<Registration[]>(`/registrations/search?q=${encodeURIComponent(query)}`)
  } catch {
    recoveryResults.value = []
  } finally {
    recoveryLoading.value = false
  }
})

async function recoverRegistration(registration: Registration) {
  try {
    const linked = await api.post<Registration>(`/registrations/${registration.id}/claim?client_id=${encodeURIComponent(clientId.value)}`, {})
    const local = {
      id: linked.id,
      dish_id: linked.dish_id,
      dish_name: dishes.value.find(dish => dish.id === linked.dish_id)?.name || 'Plato',
      first_name: linked.first_name,
      last_name: linked.last_name
    }
    const saved = readLocalRegistrations()
    saveLocalRegistrations(saved.some(item => item.id === linked.id) ? saved : [...saved, local])
    localStorage.setItem(NAME_KEY, `${linked.first_name} ${linked.last_name}`.trim())
    recoveryOpen.value = false
    recoveryQuery.value = ''
    toast.add({ title: 'Inscripciones recuperadas', color: 'success' })
    await load()
  } catch (error: any) {
    toast.add({ title: 'Error', description: error?.data?.detail || 'No se pudo vincular la inscripción', color: 'error' })
  }
}

function freeSeats(dish: Dish) {
  return Math.max(0, dish.max_quota - dish.registered)
}

function occupancyLabel(dish: Dish) {
  const free = freeSeats(dish)
  if (free === 0) return 'Completo'
  if (dish.max_quota === 1) return '1 plaza disponible'
  if (free === 1) return '¡Último lugar!'
  return `${free} plazas disponibles`
}

function statusClasses(dish: Dish) {
  const free = freeSeats(dish)
  if (free === 0) return 'bg-[#EEE9E1] text-[#78716C]'
  if (free === 1) return 'bg-[#F6E8C7] text-[#A66A1F]'
  return 'bg-[#E8EFE7] text-[#4F6A53]'
}
</script>

<template>
  <div class="min-h-dvh overflow-x-hidden bg-[#FAF5EE] font-sans text-[#2B241B]">
    <header class="px-4 pt-7 pb-5">
      <div class="mx-auto max-w-2xl text-center">
        <div class="mb-2 text-3xl" aria-hidden="true">🍂</div>
        <h1 class="font-serif text-[2.15rem] leading-tight font-bold tracking-tight">
          Nuestra Cena de Thanksgiving
        </h1>
        <p class="mx-auto mt-3 max-w-md text-base leading-relaxed text-[#5C4A3A]">
          Un espacio para compartir alrededor de la mesa, celebrar lo vivido este año y dar gracias juntos.
        </p>

        <div class="mt-5 rounded-2xl border border-[#E6D7C3] bg-[#FFFDF9] p-4 text-left shadow-sm">
          <div class="flex gap-3">
            <UIcon name="i-lucide-calendar-days" class="mt-0.5 size-5 shrink-0 text-[#C2592A]" />
            <div class="text-sm leading-relaxed text-[#5C4A3A]">
              <p><strong class="text-[#2B241B]">Miércoles 25 · A partir de las 20:00h</strong></p>
              <p class="mt-1">
                <strong>Ágape</strong> — Calle Demóstenes, 21
                <a
                  href="https://maps.google.com/?q=Calle+Demostenes+21+Malaga"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="ml-1 font-semibold text-[#C2592A] underline decoration-[#C2592A]/40 underline-offset-2"
                >Ver mapa</a>
              </p>
            </div>
          </div>
        </div>

        <div class="mt-4 rounded-2xl border border-[#E6D7C3] bg-[#FFFDF9] p-4 text-left shadow-sm">
          <div class="flex gap-3">
            <UIcon name="i-lucide-heart-handshake" class="mt-0.5 size-5 shrink-0 text-[#C2592A]" />
            <p class="text-sm leading-relaxed text-[#5C4A3A]">
              “Al ser una cena especial, priorizamos el poder elaborar cada plato con cariño. Pero entendemos que a veces puede ser difícil, así que si quieres comprarlo también está bien.”
            </p>
          </div>
        </div>

        <button
          v-if="ENABLE_PROPOSALS"
          type="button"
          class="mt-5 rounded-xl bg-[#C2592A] px-4 py-3 text-sm font-semibold text-white"
        >
          Proponer un plato nuevo
        </button>
      </div>
    </header>

    <main class="mx-auto max-w-2xl px-4 pb-12">
      <section v-if="changing" class="mb-4 rounded-2xl border border-[#DDBB76] bg-[#F8EBCF] p-4">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-xs font-bold uppercase tracking-wide text-[#A66A1F]">Cambio de plato</p>
            <p class="mt-1 text-sm font-semibold text-[#2B241B]">Cambiando {{ changing.dish_name }}</p>
            <p class="mt-1 text-xs text-[#78716C]">Elige otro plato libre y confirma tu nombre.</p>
          </div>
          <UButton size="sm" variant="ghost" @click="cancelChange">Cancelar</UButton>
        </div>
      </section>

      <section v-if="myRegistrations.length" class="mb-5 rounded-2xl border border-[#E6D7C3] bg-[#FFFDF9] p-4 shadow-sm">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h2 class="font-serif text-xl font-bold">Tus platos para la cena</h2>
          <UIcon name="i-lucide-utensils" class="size-5 text-[#C2592A]" />
        </div>
        <div class="space-y-2">
          <article
            v-for="registration in myRegistrations"
            :key="registration.id"
            class="flex items-center justify-between gap-3 rounded-xl border border-[#EEE4D5] bg-[#FAF5EE] px-3 py-3"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold">{{ registration.dish_name }}</p>
              <p class="mt-0.5 text-xs text-[#78716C]">{{ registration.first_name }} {{ registration.last_name }}</p>
            </div>
            <div class="flex shrink-0 gap-1">
              <UButton
                size="xs"
                variant="ghost"
                class="text-[#A66A1F]"
                @click="startChange(registration)"
              >Cambiar</UButton>
              <UButton
                size="xs"
                variant="ghost"
                class="text-[#9A5140]"
                @click="removeRegistration(registration)"
              >Quitar</UButton>
            </div>
          </article>
        </div>
      </section>

      <button
        type="button"
        class="mb-5 block w-full rounded-xl border border-[#E6D7C3] bg-transparent px-4 py-3 text-sm font-medium text-[#5C4A3A]"
        @click="recoveryOpen = true"
      >
        ¿Ya te apuntaste desde otro móvil? <strong class="text-[#C2592A]">Busca tu nombre</strong>
      </button>

      <div v-if="loading" class="flex justify-center py-12">
        <UIcon name="i-lucide-loader-2" class="size-8 animate-spin text-[#C2592A]" />
      </div>

      <div v-else>
        <nav class="sticky top-0 z-20 -mx-4 overflow-x-auto border-y border-[#E6D7C3] bg-[#FAF5EE]/95 px-4 py-3 backdrop-blur" aria-label="Categorías">
          <div class="flex min-w-max gap-2">
            <button
              v-for="category in categories"
              :key="category"
              type="button"
              class="rounded-full px-4 py-2 text-sm font-semibold transition"
              :class="selectedCategory === category
                ? 'bg-[#C2592A] text-white shadow-sm'
                : 'border border-[#E6D7C3] bg-[#FFFDF9] text-[#5C4A3A]'"
              @click="selectCategory(category)"
            >
              {{ category }} · {{ categoryFreeSeats(category) }} libres
            </button>
          </div>
        </nav>

        <div
          ref="slider"
          class="flex w-full snap-x snap-mandatory overflow-x-auto scroll-smooth"
          style="scrollbar-width: none"
          @scroll.passive="syncCategoryFromScroll"
        >
          <section
            v-for="category in categories"
            :key="category"
            class="w-full shrink-0 snap-start px-0.5 pt-5"
          >
            <div class="mb-4 flex items-center justify-between gap-3">
              <h2 class="font-serif text-2xl font-bold">{{ category }}</h2>
              <label class="flex min-h-11 items-center gap-2 text-sm text-[#5C4A3A]">
                <input
                  v-model="hideFull"
                  type="checkbox"
                  class="size-4 accent-[#C2592A]"
                />
                Ocultar completos
              </label>
            </div>

            <div v-if="dishesForCategory(category).length" class="space-y-4">
              <article
                v-for="dish in dishesForCategory(category)"
                :key="dish.id"
                class="rounded-2xl border border-[#E6D7C3] bg-[#FFFDF9] p-4 shadow-sm"
                :class="dish.is_full ? 'opacity-75' : ''"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <h3 class="text-lg font-bold leading-snug">{{ dish.name }}</h3>
                    <p v-if="dish.description" class="mt-1 text-sm leading-relaxed text-[#78716C]">
                      {{ dish.description }}
                    </p>
                  </div>
                </div>

                <div class="mt-3 flex flex-wrap items-center gap-2">
                  <div class="flex max-w-full gap-1" aria-hidden="true">
                    <span
                      v-for="i in dish.max_quota"
                      :key="i"
                      class="text-lg leading-none"
                      :class="i <= dish.registered ? 'text-[#C2592A]' : 'text-[#D6C9B6]'"
                    >{{ i <= dish.registered ? '●' : '○' }}</span>
                  </div>
                  <span class="rounded-full px-2.5 py-1 text-xs font-bold" :class="statusClasses(dish)">
                    {{ occupancyLabel(dish) }}
                  </span>
                </div>

                <div class="mt-4 flex items-center justify-end">
                  <UButton
                    size="sm"
                    :disabled="dish.is_full"
                    class="min-h-11 px-4"
                    :class="dish.is_full
                      ? 'cursor-not-allowed bg-[#E7E5E4] text-[#78716C]'
                      : 'bg-[#C2592A] text-white hover:bg-[#A3461D]'"
                    @click="openSignup(dish)"
                  >
                    {{ dish.is_full ? 'Completo' : (changing ? `Cambiar a ${dish.name}` : 'Apuntarme') }}
                  </UButton>
                </div>
              </article>
            </div>

            <p v-else class="rounded-2xl border border-dashed border-[#E6D7C3] py-10 text-center text-sm text-[#78716C]">
              No hay platos disponibles en esta categoría.
            </p>
          </section>
        </div>
      </div>
    </main>

    <UModal
      v-model:open="signupOpen"
      :title="changing ? `Cambiar por ${signupDish?.name}` : 'Apuntarse a un plato'"
      :ui="{ content: 'rounded-2xl bg-[#FFFDF9] border border-[#E6D7C3] shadow-xl', body: 'bg-[#FFFDF9]' }"
    >
      <template #body>
        <p v-if="signupDish" class="mb-4 text-sm text-[#5C4A3A]">
          Plato: <strong class="text-[#2B241B]">{{ signupDish.name }}</strong>
        </p>
        <UForm :state="signupForm" @submit="submitSignup">
          <UFormField label="Nombre" name="first_name" required>
            <UInput v-model="signupForm.first_name" autocomplete="given-name" class="min-h-11 bg-white" />
          </UFormField>
          <UFormField label="Apellido" name="last_name" required class="mt-3">
            <UInput v-model="signupForm.last_name" autocomplete="family-name" class="min-h-11 bg-white" />
          </UFormField>
          <div class="mt-5 flex justify-end gap-2">
            <UButton variant="ghost" @click="signupOpen = false">Cancelar</UButton>
            <UButton type="submit" :loading="signupLoading" class="min-h-11 bg-[#C2592A] text-white">
              Confirmar
            </UButton>
          </div>
        </UForm>
      </template>
    </UModal>

    <UModal
      v-model:open="recoveryOpen"
      title="Recuperar inscripción"
      :ui="{ content: 'rounded-2xl bg-[#FFFDF9] border border-[#E6D7C3] shadow-xl', body: 'bg-[#FFFDF9]' }"
    >
      <template #body>
        <label class="mb-2 block text-sm font-medium text-[#5C4A3A]">Nombre o apellido</label>
        <UInput
          v-model="recoveryQuery"
          autocomplete="name"
          placeholder="Ej. Ana García"
          class="min-h-11 bg-white"
        />

        <div v-if="recoveryLoading" class="py-5 text-center">
          <UIcon name="i-lucide-loader-2" class="size-5 animate-spin text-[#C2592A]" />
        </div>
        <div v-else-if="recoveryQuery.trim().length >= 2 && recoveryResults.length === 0" class="py-5 text-center text-sm text-[#78716C]">
          No se encontraron inscripciones.
        </div>

        <div v-else class="mt-3 space-y-2">
          <article
            v-for="registration in recoveryResults"
            :key="registration.id"
            class="flex items-center justify-between gap-3 rounded-xl border border-[#E6D7C3] p-3"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold">
                {{ dishes.find(dish => dish.id === registration.dish_id)?.name || 'Plato' }}
              </p>
              <p class="text-xs text-[#78716C]">{{ registration.first_name }} {{ registration.last_name }}</p>
            </div>
            <UButton size="sm" class="shrink-0 bg-[#C2592A] text-white" @click="recoverRegistration(registration)">
              Vincular
            </UButton>
          </article>
        </div>
      </template>
    </UModal>
  </div>
</template>