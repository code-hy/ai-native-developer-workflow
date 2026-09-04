# Design System — Household Chores Manager

> **Load when:** `area:ui`, touching `templates/`, `static/`, or any chore/bill/grocery UI.
> **Stack:** Django Templates + Tailwind CSS 3.4 + HTMX + Alpine.js 3. No React/Vue without ADR in `_docs/stack-decision.md`.

## 1. Principles

- **Calm, not gamified (V1).** Fairness over flash; no leaderboards yet. Borders/shadows subtle, colors muted unless indicating `overdue` or `points`.
- **Server-rendered first.** HTML from Django, HTMX for list filtering/modal/drawer, Alpine only for local state (sliders, disclosure). JS bundle budget 40KB gz.
- **Content-first a11y:** WCAG AA, keyboard nav, visible focus ring, color not sole indicator.
- **Mobile usable, desktop primary.** Nav collapses to hamburger <768px; tables become cards.

## 2. Tokens

### Colors (Tailwind config `core/tailwind.config.js`)

| Token | Value | Use |
|---|---|---|
| `primary` | `teal-600` `#0d9488` | Primary buttons, active nav |
| `primary-hover` | `teal-700` | Hover |
| `accent` | `amber-500` | Fairness bar fill, effort high |
| `success` | `emerald-600` | Completed badge |
| `warning` | `amber-600` | Due today |
| `danger` | `rose-600` | Overdue, delete |
| `muted` | `slate-500` | Secondary text |
| `surface` | `white` / `slate-50` | Cards, page bg |
| `border` | `slate-200` | Card/table borders |
| User colors | 8 palette: `teal, sky, violet, rose, amber, emerald, indigo, orange` | Avatar / member dot |

Tailwind `content: ["./templates/**/*.html", "./household/**/templates/**/*.html"]`.

### Typography

- **Sans:** `Inter` (via `static/fonts/` or Google Fonts fallback), `system-ui` sans stack fallback.
- **Scale:** `text-xs` (labels), `text-sm` (body), `text-base` (card titles), `text-lg` (page titles), `text-2xl` (dashboard numbers).
- **Mono:** `JetBrains Mono` for dates/points where alignment matters.

### Spacing & Radius

- Spacing scale `4` (16px) base; cards `p-4`, sections `gap-6`, page `max-w-6xl mx-auto px-4`.
- Radius `rounded-lg` for cards, `rounded-full` for avatars/badges, `rounded-md` for buttons.

### Elevation

- Cards: `shadow-sm border border-slate-200`.
- Drawer/modal: `shadow-xl`.

## 3. Components

### Button

- `btn-primary`: `bg-teal-600 text-white hover:bg-teal-700 px-4 py-2 rounded-md font-medium`
- `btn-ghost`: `bg-slate-100 hover:bg-slate-200`
- `btn-danger`: `bg-rose-600 text-white`
- Sizes: `sm` (`px-3 py-1.5 text-sm`), `md` default, `lg` for CTAs.

### Card & Stat

```html
<div class="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
  <div class="text-xs text-slate-500 uppercase tracking-wide">Overdue</div>
  <div class="text-2xl font-semibold">3</div>
</div>
```

### Badges (Status)

- `todo` slate, `in_progress` sky, `completed` emerald, `overdue` rose, `pool` violet, `rotating` amber.
- Always include icon + text (not color alone): e.g., `⏰ Overdue`.

### Navigation

- Top bar: logo (ChoreHive or `🏠 Household`) + nav `Dashboard | Chores | Groceries | Bills | Maintenance | History | Settings` + bell (htmx poll) + avatar dropdown.
- Mobile: hamburger → slide drawer (`x-data`).

### Chores List

- **Desktop:** table (`Title | Assignee (avatar) | Effort (1–5 dots) | Due | Status | Actions`).
- **Mobile:** stacked card per chore, effort as `●●●○○`.
- **Filters bar:** `hx-get="{% url 'chores:list' %}" hx-target="#chore-list" hx-push-url="true"`; inputs `assignee`, `status`, `category`, `q`.
- **Bulk:** checkbox + bottom bar `Mark done`.

### Chore Drawer/Modal

- Slide-over from right (`x-data="{open:true}"`), form POST with `{% csrf_token %}`, effort slider `type="range" 1–5` with live label via Alpine `x-model`.

### Fairness Bar

```html
<div class="w-full bg-slate-100 rounded-full h-3 flex">
  {% for m in members %}
  <div class="h-3 rounded-full" style="width: {{ m.pct }}%; background: {{ m.color }}"></div>
  {% endfor %}
</div>
<!-- tooltip: {{ m.name }}: {{ m.points }} pts -->
```

### Forms

- Labels top (`text-sm font-medium`), `aria-describedby` for errors, error text `text-rose-600 text-sm`.
- `widget_tweaks |add_class:"w-full rounded-md border-slate-300 focus:border-teal-500"`.

### Empty States

- Illustration (emoji) + line + CTA: “No chores this week — add one” `btn-primary`.

## 4. HTMX Patterns (canonical)

- **List filter:** `<form hx-get="{{ request.path }}" hx-target="#chore-list" hx-trigger="change, submit"> … </form>`
- **Claim:** `<button hx-post="{% url 'chores:claim' chore.id %}" hx-swap="outerHTML" hx-target="#chore-{{ chore.id }}">Claim</button>`
- **Complete (one-click):** `<button hx-post="{% url 'chores:complete' chore.id %}" hx-confirm="Mark done?">✓ Done</button>`
- **Drawer:** `<div id="drawer" hx-get="{% url 'chores:detail' chore.id %}" hx-target="#drawer"></div>`
- Always include `{% csrf_token %}` for POST; use `django-htmx` middleware to handle `HX-Redirect`.

## 5. Accessibility Checklist (per PR)

- [ ] Keyboard: tab order logical, `Esc` closes modal/drawer, focus returns to trigger.
- [ ] Focus ring `focus-visible:ring-2 ring-teal-500`.
- [ ] `aria-label` on icon-only buttons.
- [ ] Color contrast ≥4.5:1; status badges have icon+text.
- [ ] Axe 0 violations (`npx playwright test --project=a11y` or `axe-core` in CI).

## 6. Do / Don’t

- **Do:** Server-render, progressive enhancement, Tailwind utility-first, keep JS sprinkles.
- **Don’t:** Add React/Vue, heavy chart libs (use server bars or `Chart.js` lightweight only for 30-day trend), or install `shadcn`-style component library (server HTML is the system).

## 7. Story Locations

- `templates/base.html` (layout, nav, toasts)
- `templates/chores/`, `templates/dashboard/`, `templates/households/`, etc. per app
- `static/src/input.css` Tailwind entry, `static/css/app.css` built output
