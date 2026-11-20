<script setup lang="ts">
import type { FormSubmitEvent } from '@nuxt/ui'

definePageMeta({ layout: 'public' })

interface AdminRegistration {
  id: number
  dish_id: number
  first_name: string
  last_name: string
  note?: string | null
}

interface AdminDish {
  id: number
  name: string
  description: string | null
  category: string | null
  min_quota: number
  max_quota: number
  tested: boolean
  active: boolean
  registered: number
  registrations: AdminRegistration[]
}

interface AttendanceGroup {
  dish_id: number
  dish_name: string
  registrations: AdminRegistration[]
}

const admin = useAdmin()
const toast = useToast()

// Token gate
const tokenInput = ref('')

function saveToken() {
  admin.setToken(tokenInput.value.trim())
  if (admin.isAuthed.value) {
    tokenInput.value = ''
    loadAll()
  }
}
function logout() {
  admin.setToken('')
}

// Data
const dishes = ref<AdminDish[]>([])
const attendance = ref<AttendanceGroup[]>([])
const loading = ref(false)

async function loadAll() {
  if (!admin.isAuthed.value) return
  loading.value = true
  try {
    const [dishesRes, attendanceRes] = await Promise.allSettled([
      admin.get('/admin/dishes'),
      admin.get('/admin/attendance')
    ])
    if (dishesRes.status === 'fulfilled') {
      dishes.value = dishesRes.value as AdminDish[]
    } else {
      toast.add({ title: 'Error', description: (dishesRes.reason as { data?: { detail?: string }, message?: string })?.data?.detail ?? (dishesRes.reason as { data?: { detail?: string }, message?: string })?.message ?? 'No se pudieron cargar los platos', color: 'error' })
    }
    if (attendanceRes.status === 'fulfilled') {
      attendance.value = attendanceRes.value as AttendanceGroup[]
    } else {
      toast.add({ title: 'Error', description: (attendanceRes.reason as { data?: { detail?: string }, message?: string })?.data?.detail ?? (attendanceRes.reason as { data?: { detail?: string }, message?: string })?.message ?? 'No se pudo cargar la asistencia', color: 'error' })
    }
  } finally {
    loading.value = false
  }
}

watch(
  () => admin.isAuthed.value,
  (v) => {
    if (v) loadAll()
  },
  { immediate: true }
)

// Dish create/edit
const dishModal = ref(false)
const editingDish = ref<AdminDish | null>(null)
const dishForm = reactive({ name: '', description: '', category: 'Comida', min_quota: 0, max_quota: 5, tested: false, active: true })
const dishLoading = ref(false)

function openCreateDish() {
  editingDish.value = null
  Object.assign(dishForm, { name: '', description: '', category: 'Comida', min_quota: 0, max_quota: 5, tested: false, active: true })
  dishModal.value = true
}
function openEditDish(d: AdminDish) {
  editingDish.value = d
  Object.assign(dishForm, {
    name: d.name, description: d.description ?? '', category: d.category ?? 'Comida', min_quota: d.min_quota,
    max_quota: d.max_quota, tested: d.tested, active: d.active
  })
  dishModal.value = true
}

async function submitDish(_event: FormSubmitEvent<Record<string, unknown>>) {
  dishLoading.value = true
  try {
    const payload = { ...dishForm }
    if (editingDish.value) {
      await admin.patch(`/admin/dishes/${editingDish.value.id}`, payload)
      toast.add({ title: 'Actualizado', color: 'success' })
    } else {
      await admin.post('/admin/dishes', payload)
      toast.add({ title: 'Creado', color: 'success' })
    }
    dishModal.value = false
    await loadAll()
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string }, message?: string }
    toast.add({ title: 'Error', description: err?.data?.detail ?? err?.message, color: 'error' })
  } finally {
    dishLoading.value = false
  }
}

async function deactivateDish(d: AdminDish) {
  try {
    await admin.post(`/admin/dishes/${d.id}/deactivate`)
    toast.add({ title: 'Desactivado', color: 'success' })
    await loadAll()
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string }, message?: string }
    toast.add({ title: 'Error', description: err?.data?.detail ?? err?.message, color: 'error' })
  }
}

async function toggleTested(dish: AdminDish) {
  try {
    await admin.patch(`/admin/dishes/${dish.id}`, { tested: !dish.tested })
    await loadAll()
    toast.add({ title: 'Estado probado actualizado', color: 'success' })
  } catch (error: unknown) {
    const err = error as { data?: { detail?: string }, message?: string }
    toast.add({ title: 'Error', description: err?.data?.detail || err?.message, color: 'error' })
  }
}

async function toggleActive(dish: AdminDish) {
  try {
    await admin.patch(`/admin/dishes/${dish.id}`, { active: !dish.active })
    await loadAll()
    toast.add({ title: 'Estado activo actualizado', color: 'success' })
  } catch (error: unknown) {
    const err = error as { data?: { detail?: string }, message?: string }
    toast.add({ title: 'Error', description: err?.data?.detail || err?.message, color: 'error' })
  }
}

// Attendance reassign / delete
const reassignMap = reactive<Record<number, number>>({})

async function deleteReg(reg: AdminRegistration) {
  try {
    await admin.del(`/admin/registrations/${reg.id}`)
    toast.add({ title: 'Eliminado', color: 'success' })
    await loadAll()
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string }, message?: string }
    toast.add({ title: 'Error', description: err?.data?.detail ?? err?.message, color: 'error' })
  }
}

async function reassignReg(reg: AdminRegistration) {
  const newId = reassignMap[reg.id]
  if (!newId) return
  try {
    await admin.patch(`/admin/registrations/${reg.id}`, { new_dish_id: newId })
    toast.add({ title: 'Reasignado', color: 'success' })
    await loadAll()
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string }, message?: string }
    toast.add({ title: 'Error', description: err?.data?.detail ?? err?.message, color: 'error' })
  }
}

// Tabs
const tabs = [
  { label: 'Platos', value: 'dishes', icon: 'i-lucide-utensils' },
  { label: 'Asistencia', value: 'attendance', icon: 'i-lucide-users' }
]
const activeTab = ref('dishes')

// People grouping for attendance
const categoryEmoji: Record<string, string> = {
  Aperitivo: '🧀',
  Comida: '🍗',
  Postre: '🥧',
  Bebida: '🥂'
}

const people = computed(() => {
  const map = new Map<string, { name: string, dishes: { dish: string, note?: string | null }[] }>()
  for (const group of attendance.value) {
    for (const r of group.registrations || []) {
      const name = `${r.first_name} ${r.last_name}`.trim()
      const key = name.toLowerCase()
      if (!map.has(key)) map.set(key, { name, dishes: [] })
      map.get(key)!.dishes.push({ dish: group.dish_name, note: r.note })
    }
  }
  return [...map.values()].sort((a, b) => a.name.localeCompare(b.name))
})

const totalParticipants = computed(() => people.value.length)

// WhatsApp messages
async function copyMessage(message: string) {
  try {
    await navigator.clipboard.writeText(message)
    toast.add({ title: '¡Copiado!', description: 'Mensaje listo para WhatsApp', color: 'success' })
  } catch {
    toast.add({ title: 'Error', description: 'No se pudo copiar al portapapeles', color: 'error' })
    console.log()
  }
}

function dishCategoryEmoji(dish: AdminDish) {
  return categoryEmoji[dish.category?.trim() || ""] || "🍽️"
}

function copyFreeSeats() {
  const freeDishes = dishes.value
    .filter(d => d.active && d.registered < d.max_quota)
    .sort((a, b) => {
      const aNeeds = a.registered < (a.min_quota ?? 0)
      const bNeeds = b.registered < (b.min_quota ?? 0)
      if (aNeeds !== bNeeds) return aNeeds ? -1 : 1
      return String(a.category || '').localeCompare(String(b.category || ''))
    })

  if (!freeDishes.length) {
    copyMessage('🦃 Thanksgiving-Q Málaga\n\nTodos los platos están completos. ¡Gracias a todos! 🎉')
    return
  }

  const lines: string[] = ['🦃 Thanksgiving-Q Málaga · Plazas libres', '']
  const categories = ['Aperitivo', 'Comida', 'Postre', 'Bebida']
  for (const category of categories) {
    const items = freeDishes.filter(d => (d.category?.trim().toLowerCase() || '') === category.toLowerCase())
    if (!items.length) continue
    lines.push(`${categoryEmoji[category]} ${category}`)
    for (const dish of items) {
      const free = dish.max_quota - dish.registered
      lines.push(`• ${dishCategoryEmoji(dish)} ${dish.name} (quedan ${free} plaza${free === 1 ? '' : 's'})`)
    }
    lines.push('')
  }
  // dishes with unknown category
  const unknown = freeDishes.filter(d => !categories.map(c => c.toLowerCase()).includes((d.category?.trim().toLowerCase() || '')))
  if (unknown.length) {
    lines.push('🍽️ Otros')
    for (const dish of unknown) {
      const free = dish.max_quota - dish.registered
      lines.push(`• ${dishCategoryEmoji(dish)} ${dish.name} (quedan ${free} plaza${free === 1 ? '' : 's'})`)
    }
    lines.push('')
  }
  copyMessage(lines.join('\n').trim())
}

function copyFullSummary() {
  const activeDishes = dishes.value.filter(d => d.active)
  const lines: string[] = ['🦃 Thanksgiving-Q Málaga · Resumen completo', '']
  let totalComensales = 0
  let platosCubiertos = 0
  const categories = ['Aperitivo', 'Comida', 'Postre', 'Bebida']
  const allCats = [...categories, ...new Set(activeDishes.map(d => d.category?.trim()).filter(c => c && !categories.includes(c)))]

  for (const category of allCats) {
    const items = activeDishes.filter(d => (d.category?.trim().toLowerCase() || '') === String(category).toLowerCase())
    if (!items.length) continue
    lines.push(`${categoryEmoji[category as string] || '🍽️'} ${category}`)
    for (const dish of items) {
      const regs = dish.registrations || []
      const peopleNames = regs.map((r: AdminRegistration) => `${r.first_name} ${r.last_name}${r.note ? ` (${r.note})` : ''}`).join(', ') || 'Sin apuntados'
      const pending = Math.max(0, dish.max_quota - dish.registered)
      lines.push(`• ${dish.name}: ${dish.registered}/${dish.max_quota} (${pending} libres)`)
      lines.push(`  ${peopleNames}`)
      totalComensales += (dish.registered || 0)
      if ((dish.registered || 0) >= (dish.min_quota || 0)) platosCubiertos++
    }
    lines.push('')
  }
  lines.push(`Total comensales: ${totalComensales}`)
  lines.push(`Platos cubiertos: ${platosCubiertos}/${activeDishes.length}`)
  copyMessage(lines.join('\n').trim())
}

function dishStatusClasses(dish: AdminDish) {
  const registered = dish.registered || 0
  const min = dish.min_quota || 0
  const max = dish.max_quota || 1
  if (registered >= max) return 'bg-[#EEE9E1] text-[#78716C]'
  if (registered >= min) return 'bg-[#E8EFE7] text-[#4F6A53]'
  return 'bg-[#F6E8C7] text-[#A66A1F]'
}
</script>

<template>
  <div class="min-h-dvh bg-[#FAF6F0] px-4 py-6 text-[#2B241B]">
    <div class="mx-auto max-w-5xl">
      <header class="mb-6 flex items-center justify-between">
        <h1 class="font-serif text-2xl font-bold">
          Panel de administración
        </h1>
        <UButton
          v-if="admin.isAuthed.value"
          variant="ghost"
          size="sm"
          class="text-[#78716C]"
          @click="logout"
        >
          Salir
        </UButton>
      </header>

      <!-- Token gate -->
      <div v-if="!admin.isAuthed.value" class="rounded-2xl border border-[#E8DFD5] bg-white p-5 shadow-sm">
        <h2 class="mb-3 font-semibold">
          Acceso restringido
        </h2>
        <div class="flex gap-2">
          <UInput
            v-model="tokenInput"
            type="password"
            placeholder="Token de administrador"
            class="flex-1 bg-white"
          />
          <UButton class="bg-[#C2592A] text-white hover:bg-[#A3461D]" @click="saveToken">
            Entrar
          </UButton>
        </div>
      </div>

      <div v-else>
        <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div class="flex gap-2">
            <button
              v-for="tab in tabs"
              :key="tab.value"
              type="button"
              class="flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition"
              :class="activeTab === tab.value
                ? 'bg-[#C2592A] text-white shadow-sm'
                : 'border border-[#E8DFD5] bg-white text-[#5C4A3A]'"
              @click="activeTab = tab.value"
            >
              <UIcon :name="tab.icon" class="size-4" />
              {{ tab.label }}
            </button>
          </div>
          <div class="flex flex-wrap gap-2">
            <UButton
              size="sm"
              variant="outline"
              class="border-[#E8DFD5] text-[#5C4A3A]"
              @click="copyFreeSeats"
            >
              Copiar plazas libres
            </UButton>
            <UButton
              size="sm"
              variant="outline"
              class="border-[#E8DFD5] text-[#5C4A3A]"
              @click="copyFullSummary"
            >
              Resumen completo
            </UButton>
            <UButton
              size="sm"
              variant="outline"
              class="border-[#E8DFD5] text-[#5C4A3A]"
              :loading="loading"
              @click="loadAll"
            >
              <UIcon name="i-lucide-refresh-cw" class="size-4" />
            </UButton>
          </div>
        </div>

        <!-- Dishes -->
        <div v-if="activeTab === 'dishes'">
          <div class="mb-3 flex justify-end">
            <UButton size="sm" class="bg-[#C2592A] text-white hover:bg-[#A3461D]" @click="openCreateDish">
              Nuevo plato
            </UButton>
          </div>

          <div v-if="loading && dishes.length === 0" class="flex justify-center py-12">
            <UIcon name="i-lucide-loader-2" class="size-8 animate-spin text-[#C2592A]" />
          </div>

          <div v-else class="space-y-4">
            <div
              v-for="dish in dishes"
              :key="dish.id"
              class="rounded-2xl border border-[#E8DFD5] bg-white p-4 shadow-sm"
              :class="!dish.active ? 'opacity-60' : ''"
            >
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="text-lg">{{ dishCategoryEmoji(dish) }}</span>
                    <h3 class="text-lg font-bold leading-snug">
                      {{ dish.name }}
                    </h3>
                    <UBadge variant="subtle" class="border border-[#E8DFD5] bg-[#FAF6F0] text-[#78716C]">
                      {{ dish.category || 'Sin categoría' }}
                    </UBadge>
                  </div>
                  <p v-if="dish.description" class="mt-1 text-sm text-[#78716C]">
                    {{ dish.description }}
                  </p>
                  <div class="mt-2 flex flex-wrap items-center gap-3 text-sm text-[#5C4A3A]">
                    <span>Mín: <strong>{{ dish.min_quota }}</strong></span>
                    <span>Máx: <strong>{{ dish.max_quota }}</strong></span>
                    <span>Inscritos: <strong>{{ dish.registered }}</strong></span>
                    <UBadge variant="subtle" :class="dishStatusClasses(dish)">
                      {{ dish.registered }}/{{ dish.max_quota }}
                    </UBadge>
                    <span v-if="dish.registered < dish.min_quota" class="text-xs font-medium text-[#A66A1F]">
                      Faltan {{ dish.min_quota - dish.registered }} para cubrir el mínimo
                    </span>
                  </div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <UButton
                    size="xs"
                    :class="dish.tested ? 'bg-[#4F6A53] text-white' : 'border border-[#E8DFD5] text-[#78716C]'"
                    @click="toggleTested(dish)"
                  >
                    {{ dish.tested ? 'Probado ✓' : 'Sin probar' }}
                  </UButton>
                  <UButton
                    size="xs"
                    :class="dish.active ? 'bg-[#C2592A] text-white' : 'border border-[#E8DFD5] text-[#78716C]'"
                    @click="toggleActive(dish)"
                  >
                    {{ dish.active ? 'Activo' : 'Inactivo' }}
                  </UButton>
                  <UButton
                    size="xs"
                    variant="ghost"
                    class="text-[#5C4A3A]"
                    @click="openEditDish(dish)"
                  >
                    Editar
                  </UButton>
                  <UButton
                    v-if="dish.active"
                    size="xs"
                    variant="ghost"
                    class="text-[#9A5140]"
                    @click="deactivateDish(dish)"
                  >
                    Desactivar
                  </UButton>
                </div>
              </div>

              <!-- Inscritos badges -->
              <div class="mt-3 border-t border-[#E8DFD5] pt-3">
                <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-[#78716C]">
                  Inscritos
                </p>
                <div v-if="(dish.registrations || []).length === 0" class="text-sm text-[#78716C]">
                  Sin inscritos.
                </div>
                <div v-else class="flex flex-wrap gap-2">
                  <UBadge
                    v-for="reg in dish.registrations"
                    :key="reg.id"
                    variant="subtle"
                    class="border border-[#E8DFD5] bg-[#FAF6F0] text-[#2B241B]"
                  >
                    {{ reg.first_name }} {{ reg.last_name }}<span v-if="reg.note" class="ml-1 text-[#78716C]">· {{ reg.note }}</span>
                  </UBadge>
                </div>
              </div>
            </div>

            <div v-if="dishes.length === 0" class="rounded-2xl border border-dashed border-[#E8DFD5] py-10 text-center text-sm text-[#78716C]">
              No hay platos.
            </div>
          </div>
        </div>

        <!-- Attendance -->
        <div v-if="activeTab === 'attendance'">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="font-serif text-xl font-bold">
              Asistencia
            </h2>
            <UBadge variant="subtle" class="border border-[#E8DFD5] bg-white text-[#2B241B]">
              {{ totalParticipants }} participantes confirmados
            </UBadge>
          </div>

          <div v-if="loading && attendance.length === 0" class="flex justify-center py-12">
            <UIcon name="i-lucide-loader-2" class="size-8 animate-spin text-[#C2592A]" />
          </div>

          <div v-else-if="people.length === 0" class="rounded-2xl border border-dashed border-[#E8DFD5] py-10 text-center text-sm text-[#78716C]">
            Sin asistentes.
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="person in people"
              :key="person.name"
              class="rounded-2xl border border-[#E8DFD5] bg-white p-4 shadow-sm"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <h3 class="font-semibold">
                    {{ person.name }}
                  </h3>
                  <p class="mt-1 text-sm text-[#78716C]">
                    Lleva {{ person.dishes.length }} plato{{ person.dishes.length === 1 ? '' : 's' }}:
                    {{ person.dishes.map(d => d.dish).join(', ') }}
                  </p>
                  <div v-if="person.dishes.some(d => d.note)" class="mt-2 flex flex-wrap gap-2">
                    <UBadge
                      v-for="(d, idx) in person.dishes.filter(d => d.note)"
                      :key="idx"
                      variant="subtle"
                      class="border border-[#E8DFD5] bg-[#FAF6F0] text-[#78716C]"
                    >
                      {{ d.dish }}: {{ d.note }}
                    </UBadge>
                  </div>
                </div>
              </div>
            </div>

            <!-- Per-dish detail -->
            <div class="mt-6">
              <h3 class="mb-2 font-serif text-lg font-bold">
                Detalle por plato
              </h3>
              <div class="space-y-3">
                <div
                  v-for="g in attendance"
                  :key="g.dish_id"
                  class="rounded-2xl border border-[#E8DFD5] bg-white p-4 shadow-sm"
                >
                  <div class="mb-2 flex items-center justify-between">
                    <h4 class="font-semibold">
                      {{ g.dish_name }}
                    </h4>
                    <UBadge variant="subtle" class="border border-[#E8DFD5] bg-[#FAF6F0] text-[#2B241B]">
                      {{ g.registrations.length }} inscritos
                    </UBadge>
                  </div>
                  <div v-if="g.registrations.length === 0" class="text-sm text-[#78716C]">
                    Sin inscritos.
                  </div>
                  <div v-else class="space-y-2">
                    <div
                      v-for="r in g.registrations"
                      :key="r.id"
                      class="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[#E8DFD5] bg-[#FAF6F0] p-2"
                    >
                      <span class="text-sm">{{ r.first_name }} {{ r.last_name }}<span v-if="r.note" class="ml-1 text-[#78716C]">· {{ r.note }}</span></span>
                      <div class="flex items-center gap-2">
                        <USelect
                          v-model="reassignMap[r.id]"
                          :items="dishes.filter(d => d.active).map(d => ({ label: d.name, value: d.id }))"
                          size="xs"
                          placeholder="Reasignar a..."
                        />
                        <UButton
                          size="xs"
                          variant="ghost"
                          class="text-[#5C4A3A]"
                          @click="reassignReg(r)"
                        >
                          Mover
                        </UButton>
                        <UButton
                          size="xs"
                          variant="ghost"
                          class="text-[#9A5140]"
                          @click="deleteReg(r)"
                        >
                          Eliminar
                        </UButton>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dish modal -->
    <UModal v-model:open="dishModal" :title="editingDish ? 'Editar plato' : 'Nuevo plato'">
      <template #body>
        <UForm :state="dishForm" @submit="submitDish">
          <UFormField label="Nombre" name="name" required>
            <UInput v-model="dishForm.name" class="bg-white" />
          </UFormField>
          <UFormField label="Descripción" name="description" class="mt-3">
            <UTextarea v-model="dishForm.description" class="bg-white" />
          </UFormField>
          <UFormField label="Categoría" name="category" class="mt-3">
            <USelect
              v-model="dishForm.category"
              :items="[
                { label: 'Aperitivo', value: 'Aperitivo' },
                { label: 'Comida', value: 'Comida' },
                { label: 'Postre', value: 'Postre' },
                { label: 'Bebida', value: 'Bebida' }
              ]"
            />
          </UFormField>
          <div class="mt-3 grid grid-cols-2 gap-3">
            <UFormField label="Cupo mínimo" name="min_quota">
              <UInput v-model.number="dishForm.min_quota" type="number" class="bg-white" />
            </UFormField>
            <UFormField label="Cupo máximo" name="max_quota">
              <UInput v-model.number="dishForm.max_quota" type="number" class="bg-white" />
            </UFormField>
          </div>
          <div class="mt-3 flex gap-4">
            <UCheckbox v-model="dishForm.tested" label="Probado/validado" />
            <UCheckbox v-model="dishForm.active" label="Activo" />
          </div>
          <div class="mt-4 flex justify-end gap-2">
            <UButton variant="ghost" @click="dishModal = false">
              Cancelar
            </UButton>
            <UButton type="submit" :loading="dishLoading" class="bg-[#C2592A] text-white hover:bg-[#A3461D]">
              Guardar
            </UButton>
          </div>
        </UForm>
      </template>
    </UModal>
  </div>
</template>
