# TASK.md — GestionPlatos

Plan de implementación para cumplir el Resumen Ejecutivo: plataforma web ligera (sin registro) para organizar aportaciones de comida de la cena de Thanksgiving. Stack: FastAPI + SQLite (aiosqlite) + SQLAlchemy async en backend; Nuxt 4 + Nuxt UI en frontend. Mobile-first.

Leyenda de estados: `[ ]` pendiente · `[x]` hecho · `[-]` en progreso.

---

## Fase 0 — Infraestructura y dependencias

- [x] Instalar dependencias backend: `sqlalchemy[asyncio]`, `aiosqlite`, `alembic`.
- [x] Crear estructura de carpetas: `backend/database/`, `backend/models/`, `backend/schemas/`, `backend/routers/`, `backend/services/`, `backend/core/`.
- [x] Configurar `core/config.py` con `python-decouple` leyendo `.env` (DATABASE_URL, SECRET_KEY, CORS_ORIGINS, ADMIN_TOKEN).
- [x] Crear engine async + session factory en `database/session.py` con:
  - `connect_args={"check_same_thread": False, "timeout": 30}`
  - PRAGMA `foreign_keys=ON` y `busy_timeout` vía `event.listen`.
- [x] Inicializar Alembic y generar migración inicial desde `docs/schema.sql`.
- [x] Definir `core/security.py` para el acceso admin (token en cookie/header o enlace privado con token).
- [x] Verificar CORS y logging actuales (ya configurados).

## Fase 1 — Esquema y acceso a datos (backend)

- [x] Crear tablas según `docs/schema.sql` (vía migración Alembic con SQL crudo).
- [x] Implementar `database/session.py` (engine async + sesiones + PRAGMAs).
- [x] Implementar repositorio/servicio con SQL crudo (`text()`): consultas de dishes, registrations, proposals.
- [x] Mapear filas (`result.mappings()`) a schemas Pydantic manualmente.
- [x] Schemas Pydantic de entrada/salida para cada entidad.
- [x] Seed de platos iniciales (vía `backend/seeds/seed_dishes.sql` + `backend/scripts/run_seed.py`).

## Fase 2 — API pública (RF-01 … RF-05)

- [x] `GET /api/dishes` — lista de platos activos con ocupación (`registered`, `max_quota`, estado: disponible/queda N/lleno). **RF-02**
- [x] `POST /api/registrations` — inscripción a plato existente (name, last_name, dish_id, client_id). Decremento atómico de cupo; bloqueo si `registered >= max_quota`. **RF-04, RNF-01**
- [x] Detección de "ya inscrito en este dispositivo": devolver inscripciones del `client_id` para que el frontend muestre estado. **RF-03**
- [x] `POST /api/proposals` — propuesta de plato nuevo (name, last_name, dish_name, description). Queda en `pending`. **RF-05**
- [ ] Endpoint de bienvenida/mensaje (o estático en frontend). **RF-02**

## Fase 3 — API admin (RF-06 … RF-09)

- [x] Proteger rutas `/api/admin/*` con token/credencial. **RF-06**
- [x] `POST /api/admin/dishes` — crear plato (name, description, min_quota, max_quota, tested, active). **RF-07**
- [x] `PATCH /api/admin/dishes/{id}` — editar/desactivar plato y cupos. **RF-07**
- [x] `GET /api/admin/proposals` — listar sugerencias pendientes. **RF-08**
- [x] `POST /api/admin/proposals/{id}/approve` — aprobar asignando cupos y estado probado → crea plato publicado. **RF-08**
- [x] `POST /api/admin/proposals/{id}/reject` — descartar. **RF-08**
- [x] `GET /api/admin/registrations` — listado completo agrupado por plato. **RF-09**
- [x] `DELETE /api/admin/registrations/{id}` — eliminar inscripción liberando cupo. **RF-09**
- [x] `PATCH /api/admin/registrations/{id}` — reasignar a otro plato liberando/asignando cupo. **RF-09**

## Fase 4 — Frontend público (mobile-first)

- [x] Página de bienvenida con mensaje de Thanksgiving. **RF-02**
- [x] Lista de platos activos con ocupación en tiempo real (3/5, "queda 1", "disponible"). **RF-02**
- [x] Estados por dispositivo: botón "Apuntarme" o "Ya estás inscrito" (con opción de registrar acompañante). **RF-03**
- [x] Formulario de inscripción (Nombre, Apellido, selección de plato con cupo libre). **RF-04**
- [x] Formulario de propuesta de plato nuevo. **RF-05**
- [x] Generación/almacenamiento de `client_id` en `localStorage` para detección de dispositivo. **RF-03**
- [x] Refresco de datos (polling o SSE) para ocupación en tiempo real. **RNF-02**
- [x] Optimización móvil: layout responsive, tap targets, carga rápida. **RNF-02**

## Fase 5 — Frontend admin

- [x] Ruta `/admin` protegida por token/credencial. **RF-06**
- [x] CRUD de platos con cupo mínimo/máximo y flag "probado". **RF-07**
- [x] Bandeja de propuestas con aprobar/descartar. **RF-08**
- [x] Vista de asistencia agrupada por plato con eliminar/reasignar. **RF-09**
- [x] Indicadores internos (min_quota, tested) solo en panel admin. Regla de negocio.

## Fase 6 — Concurrencia y robustez

- [x] Implementar registro con transacción `BEGIN IMMEDIATE` + verificación de cupo + `busy_timeout`. **RNF-01**
- [x] Manejo de `SQLITE_BUSY` / conflictos (respuesta 409 amigable).
- [x] Tests de concurrencia (dos inscripciones simultáneas al último cupo). **RNF-01**
- [x] Persistencia verificada tras reinicio del servidor. **RNF-03**
- [x] Backup simple (copiar `database.db`).

## Fase 7 — Cierre y despliegue

- [x] Build del frontend y servir estáticos desde FastAPI (`public/`) o hosting estático.
- [x] Smoke test en móvil real vía enlace de WhatsApp. **RNF-02**
- [x] Documentar flujo de revisión (martes) → lanzamiento (miércoles) → cierre (lunes). **RNF-03**
- [x] README final con instrucciones de operación para Alexis y Mariló.

---

## Reglas de negocio (checklist de validación)

- [ ] Un plato en cupo máximo deja de aceptar inscripciones automáticamente. **RF-04**
- [ ] Las propuestas no se publican automáticamente; requieren aprobación admin. **RF-08**
- [ ] `min_quota` y `tested` son indicadores internos (no expuestos en vista pública). **RF-07**

## Mapeo rápido RF → fase

| RF | Fase |
|----|------|
| RF-01 | 2, 4 |
| RF-02 | 2, 4 |
| RF-03 | 2, 4 |
| RF-04 | 2, 6 |
| RF-05 | 2, 4 |
| RF-06 | 3, 5 |
| RF-07 | 1, 3, 5 |
| RF-08 | 3, 5 |
| RF-09 | 3, 5 |
| RNF-01 | 6 |
| RNF-02 | 4, 7 |
| RNF-03 | 6, 7 |
