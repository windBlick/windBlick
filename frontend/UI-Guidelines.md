# WindBlick Frontend — UI & Code Guidelines

## Tech Stack & Conventions
- **Framework:** Vue 3 (`<script setup>`, JavaScript — no TypeScript)
- **Styling:** Tailwind CSS v4 (utility classes only, no custom `<style>` blocks unless required for Leaflet)
- **Icons:** Inline SVGs or clean Unicode/icon components; keep UI labels in English.

## Color Palette
- **Primary (Forest Green):** `#14532D` — main action buttons, active step badges, primary headings/accents (`bg-[#14532D]`, `text-[#14532D]`, `hover:bg-[#14532D]/90`)
- **Secondary (Soft Mint):** `#9FD3B0` — secondary buttons, completed steps, subtle highlights (`bg-[#9FD3B0]/35`, `border-[#9FD3B0]`)
- **App Background:** `#F8FAFC` (`bg-[#F8FAFC]`)
- **Card Surface:** `#FFFFFF` (`bg-white border border-slate-200 rounded-2xl shadow-sm`)
- **Text:** `text-slate-900` (headings), `text-slate-600` (body), `text-slate-400` (muted/disabled)

## Layout & Component Rules
- **Cards:** Always use `rounded-2xl border border-slate-200 bg-white p-5 shadow-sm` (or `p-6` for larger containers).
- **Buttons:** Rounded corners `rounded-xl`, medium/semibold text `text-sm font-semibold`, clear disabled state `disabled:opacity-40 disabled:cursor-not-allowed`.
- **Stability:** Use CSS Grid (`grid-cols-1 lg:grid-cols-12 items-start`) with `min-w-0` on grid children so cards never push or resize neighboring cards.
- **Scope:** Never introduce `vue-router` or external UI libraries; state is managed centrally in `src/App.vue` and passed down via `props` and `emits`.