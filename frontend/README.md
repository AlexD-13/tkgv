# Frontend — GestionPlatos Web

Nuxt 4 + Nuxt UI web client for the Thanksgiving dinner dish management platform. Mobile-first (primary entry point is WhatsApp links).

## Stack

- Nuxt 4, Vue 3
- Nuxt UI, Tailwind CSS 4
- TypeScript
- @vueuse, zod

## Setup

```bash
cd frontend
pnpm install
pnpm dev       # http://localhost:3000
```

## Scripts

- `pnpm dev` — development server
- `pnpm build` — production build
- `pnpm preview` — preview production build
- `pnpm lint` — eslint
- `pnpm typecheck` — vue-tsc

## Status

Currently the Nuxt UI dashboard template. Pages (home, customers, inbox, settings) and components will be replaced with:

- Public view: welcome + dish list with live occupancy + sign-up / propose dish
- Admin view: dish CRUD + quotas + proposal review + attendance

## Configuration

- `NUXT_PUBLIC_SITE_URL` — public site URL (OG image)
- API base URL — point to the FastAPI backend
