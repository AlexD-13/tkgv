<script setup lang="ts">
import type { FormSubmitEvent } from '@nuxt/ui'

definePageMeta({ layout: 'public' })

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
const dishes = ref<any[]>([])
const proposals = ref<any[]>([])
const attendance = ref<any[]>([])
const loading = ref(false)

async function loadAll() {
  if (!admin.isAuthed.value) return
  loading.value = true
  try {
    dishes.value = await admin.get('/admin/dishes')
    proposals.value = await admin.get('/admin/proposals?status=pending')
    attendance.value = await admin.get('/admin/attendance')
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.data?.detail ?? e?.message ?? 'Error al cargar', color: 'error' })
  } finally {
    loading.value = false
  }
}

watch(() => admin.isAuthed.value, (v) => { if (v) loadAll() }, { immediate: true })

// Dish create/edit
const dishModal = ref(false)
const editingDish = ref<any>(null)
const dishForm = reactive({ name: '', description: '', min_quota: 0, max_quota: 5, tested: false, active: true })
const dishLoading = ref(false)

function openCreateDish() {
  editingDish.value = null
  Object.assign(dishForm, { name: '', description: '', min_quota: 0, max_quota: 5, tested: false, active: true })
  dishModal.value = true
}
function openEditDish(d: any) {
  editingDish.value = d
  Object.assign(dishForm, {
    name: d.name, description: d.description ?? '', min_quota: d.min_quota,
    max_quota: d.max_quota, tested: d.tested, active: d.active
  })
  dishModal.value = true
}

async function submitDish(event: FormSubmitEvent<any>) {
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
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.data?.detail ?? e?.message, color: 'error' })
  } finally {
    dishLoading.value = false
  }
}

async function deactivateDish(d: any) {
  try {
    await admin.post(`/admin/dishes/${d.id}/deactivate`)
    toast.add({ title: 'Desactivado', color: 'success' })
    await loadAll()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.data?.detail ?? e?.message, color: 'error' })
  }
}

// Proposals
const approveModal = ref(false)
const approvingProposal = ref<any>(null)
const approveForm = reactive({ min_quota: 0, max_quota: 5, tested: false })
const approveLoading = ref(false)

function openApprove(p: any) {
  approvingProposal.value = p
  Object.assign(approveForm, { min_quota: 0, max_quota: 5, tested: false })
  approveModal.value = true
}

async function submitApprove() {
  if (!approvingProposal.value) return
  approveLoading.value = true
  try {
    await admin.post(`/admin/proposals/${approvingProposal.value.id}/approve`, { ...approveForm })
    toast.add({ title: 'Aprobado', color: 'success' })
    approveModal.value = false
    await loadAll()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.data?.detail ?? e?.message, color: 'error' })
  } finally {
    approveLoading.value = false
  }
}

async function rejectProposalPost(p: any) {
  try {
    await admin.post(`/admin/proposals/${p.id}/reject`, {})
    toast.add({ title: 'Descartado', color: 'success' })
    await loadAll()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.data?.detail ?? e?.message, color: 'error' })
  }
}

// Attendance reassign
const reassignMap = reactive<Record<number, number>>({})

async function deleteReg(reg: any) {
  try {
    await admin.del(`/admin/registrations/${reg.id}`)
    toast.add({ title: 'Eliminado', color: 'success' })
    await loadAll()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.data?.detail ?? e?.message, color: 'error' })
  }
}

async function reassignReg(reg: any) {
  const newId = reassignMap[reg.id]
  if (!newId) return
  try {
    await admin.patch(`/admin/registrations/${reg.id}`, { new_dish_id: newId })
    toast.add({ title: 'Reasignado', color: 'success' })
    await loadAll()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e?.data?.detail ?? e?.message, color: 'error' })
  }
}

const tabs = [
  { label: 'Platos', value: 'dishes', icon: 'i-lucide-utensils' },
  { label: 'Propuestas', value: 'proposals', icon: 'i-lucide-inbox' },
  { label: 'Asistencia', value: 'attendance', icon: 'i-lucide-users' }
]
const activeTab = ref('dishes')
</script>

<template>
  <div class="mx-auto max-w-5xl px-4 py-8">
    <header class="mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-bold">Panel de administración</h1>
      <UButton v-if="admin.isAuthed.value" variant="ghost" size="sm" @click="logout">Salir</UButton>
    </header>

    <!-- Token gate -->
    <UCard v-if="!admin.isAuthed.value">
      <template #header>
        <h2 class="font-semibold">Acceso restringido</h2>
      </template>
      <div class="flex gap-2">
        <UInput v-model="tokenInput" type="password" placeholder="Token de administrador" class="flex-1" />
        <UButton @click="saveToken">Entrar</UButton>
      </div>
    </UCard>

    <div v-else>
      <div class="mb-4 flex items-center justify-between">
        <UTabs v-model="activeTab" :items="tabs" />
        <UButton size="sm" variant="outline" :loading="loading" @click="loadAll">
          <UIcon name="i-lucide-refresh-cw" class="size-4" />
        </UButton>
      </div>

      <!-- Dishes -->
      <div v-if="activeTab === 'dishes'">
        <div class="mb-3 flex justify-end">
          <UButton size="sm" @click="openCreateDish">Nuevo plato</UButton>
        </div>
        <UTable :data="dishes" :columns="[
          { accessorKey: 'name', header: 'Plato' },
          { accessorKey: 'min_quota', header: 'Mín' },
          { accessorKey: 'max_quota', header: 'Máx' },
          { accessorKey: 'registered', header: 'Inscritos' },
          { accessorKey: 'tested', header: 'Probado' },
          { accessorKey: 'active', header: 'Activo' },
          { accessorKey: 'actions', header: '' }
        ]">
          <template #tested-cell="{ row }">
            <UBadge :color="row.original.tested ? 'success' : 'neutral'" variant="subtle">
              {{ row.original.tested ? 'Sí' : 'No' }}
            </UBadge>
          </template>
          <template #active-cell="{ row }">
            <UBadge :color="row.original.active ? 'success' : 'error'" variant="subtle">
              {{ row.original.active ? 'Sí' : 'No' }}
            </UBadge>
          </template>
          <template #actions-cell="{ row }">
            <div class="flex gap-1">
              <UButton size="xs" variant="ghost" @click="openEditDish(row.original)">Editar</UButton>
              <UButton
                v-if="row.original.active"
                size="xs" variant="ghost" color="error"
                @click="deactivateDish(row.original)"
              >Desactivar</UButton>
            </div>
          </template>
        </UTable>
      </div>

      <!-- Proposals -->
      <div v-if="activeTab === 'proposals'">
        <div v-if="proposals.length === 0" class="text-center text-muted py-8">
          No hay propuestas pendientes.
        </div>
        <div v-else class="space-y-3">
          <UCard v-for="p in proposals" :key="p.id">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <h3 class="font-semibold">{{ p.dish_name }}</h3>
                <p v-if="p.description" class="text-sm text-muted mt-1">{{ p.description }}</p>
                <p class="text-xs text-muted mt-1">
                  Propuesto por {{ p.first_name }} {{ p.last_name }} · {{ p.created_at }}
                </p>
              </div>
              <div class="shrink-0 flex gap-2">
                <UButton size="xs" color="success" @click="openApprove(p)">Aprobar</UButton>
                <UButton size="xs" color="error" variant="outline" @click="rejectProposalPost(p)">Descartar</UButton>
              </div>
            </div>
          </UCard>
        </div>
      </div>

      <!-- Attendance -->
      <div v-if="activeTab === 'attendance'">
        <div v-if="attendance.length === 0" class="text-center text-muted py-8">
          Sin datos.
        </div>
        <div v-else class="space-y-4">
          <UCard v-for="g in attendance" :key="g.dish_id">
            <template #header>
              <div class="flex items-center justify-between">
                <h3 class="font-semibold">{{ g.dish_name }}</h3>
                <UBadge variant="subtle">{{ g.registrations.length }} inscritos</UBadge>
              </div>
            </template>
            <div v-if="g.registrations.length === 0" class="text-sm text-muted">
              Sin inscritos.
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="r in g.registrations"
                :key="r.id"
                class="flex items-center justify-between gap-2 rounded border p-2"
              >
                <span class="text-sm">{{ r.first_name }} {{ r.last_name }}</span>
                <div class="flex items-center gap-2">
                  <USelect
                    v-model="reassignMap[r.id]"
                    :items="dishes.filter(d => d.active).map(d => ({ label: d.name, value: d.id }))"
                    size="xs"
                    placeholder="Reasignar a..."
                  />
                  <UButton size="xs" variant="ghost" @click="reassignReg(r)">Mover</UButton>
                  <UButton size="xs" variant="ghost" color="error" @click="deleteReg(r)">Eliminar</UButton>
                </div>
              </div>
            </div>
          </UCard>
        </div>
      </div>
    </div>

    <!-- Dish modal -->
    <UModal v-model:open="dishModal" :title="editingDish ? 'Editar plato' : 'Nuevo plato'">
      <template #body>
        <UForm :state="dishForm" @submit="submitDish">
          <UFormField label="Nombre" name="name" required>
            <UInput v-model="dishForm.name" />
          </UFormField>
          <UFormField label="Descripción" name="description" class="mt-3">
            <UTextarea v-model="dishForm.description" />
          </UFormField>
          <div class="mt-3 grid grid-cols-2 gap-3">
            <UFormField label="Cupo mínimo" name="min_quota">
              <UInput v-model.number="dishForm.min_quota" type="number" />
            </UFormField>
            <UFormField label="Cupo máximo" name="max_quota">
              <UInput v-model.number="dishForm.max_quota" type="number" />
            </UFormField>
          </div>
          <div class="mt-3 flex gap-4">
            <UCheckbox v-model="dishForm.tested" label="Probado/validado" />
            <UCheckbox v-model="dishForm.active" label="Activo" />
          </div>
          <div class="mt-4 flex justify-end gap-2">
            <UButton variant="ghost" @click="dishModal = false">Cancelar</UButton>
            <UButton type="submit" :loading="dishLoading">Guardar</UButton>
          </div>
        </UForm>
      </template>
    </UModal>

    <!-- Approve modal -->
    <UModal v-model:open="approveModal" title="Aprobar propuesta">
      <template #body>
        <p v-if="approvingProposal" class="mb-4 text-sm text-muted">
          Plato: <strong>{{ approvingProposal.dish_name }}</strong>
        </p>
        <UForm :state="approveForm" @submit="submitApprove">
          <div class="grid grid-cols-2 gap-3">
            <UFormField label="Cupo mínimo" name="min_quota">
              <UInput v-model.number="approveForm.min_quota" type="number" />
            </UFormField>
            <UFormField label="Cupo máximo" name="max_quota">
              <UInput v-model.number="approveForm.max_quota" type="number" />
            </UFormField>
          </div>
          <div class="mt-3">
            <UCheckbox v-model="approveForm.tested" label="Probado/validado" />
          </div>
          <div class="mt-4 flex justify-end gap-2">
            <UButton variant="ghost" @click="approveModal = false">Cancelar</UButton>
            <UButton type="submit" :loading="approveLoading">Aprobar y publicar</UButton>
          </div>
        </UForm>
      </template>
    </UModal>
  </div>
</template>
