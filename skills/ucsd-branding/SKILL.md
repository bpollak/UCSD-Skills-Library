---
name: ucsd-branding
description: Apply UC San Diego's official visual identity to a web app, email template, or document. Use when asked to brand a UI as UC San Diego / UCSD, apply campus branding, check brand compliance, or build anything that should look like a UCSD campus web property — including colors, typography, the Decorator 5 page shell, logos, and UI components. Trigger on phrases like "UCSD branding", "campus brand", "Decorator 5", "make it look like UCSD", or "UC San Diego style".
allowed-tools: WebFetch, Read, Write, Edit
---

# UCSD Branding

Applies UC San Diego's official visual identity to web pages, apps, emails, and documents — steering to authoritative live sources rather than bundling static copies of assets.

## When to use

- Building or restyling a web page or app to match UCSD's visual identity
- Checking whether colors, fonts, or page chrome are brand-compliant
- Implementing the Decorator 5 page shell (header, navbar, footer)
- Choosing the correct logo, font, color, or UI component for a campus-facing product
- Producing an email template in UCSD brand style

## How to use this skill

### 1. Fetch the live sources first

Before writing any brand values from memory, fetch these. They are the ground truth — if anything in this skill conflicts with them, the live source wins.

| Source | URL |
|---|---|
| Brand guidelines (colors, typography, logo rules) | https://brand.ucsd.edu |
| Decorator 5 overview | https://developer.ucsd.edu/design/decorator/index.html |
| Kitchen sink (all components, live rendered) | https://developer.ucsd.edu/design/v5-kitchen-sink/kitchen-sink/index.html |
| Getting started / file guide | https://developer.ucsd.edu/design/decorator/getting-started/index.html |
| Templates (blank slate, homepage, two-column, three-column) | https://developer.ucsd.edu/design/decorator/templates/index.html |

### 2. Apply the color palette

**Core (Blue must be dominant in every external material):**

| Name | Hex | Primary use |
|---|---|---|
| UC San Diego Blue | `#00629B` | Navbar bg, footer bg, buttons, links, focus rings — required dominant color |
| UC San Diego Navy | `#182B49` | Body text, h2 headings, dark surfaces — use instead of black |
| UC San Diego Yellow | `#FFCD00` | Active nav tab underline only; highlight on dark surfaces; never as text on white |
| UC San Diego Gold | `#C69214` | Accent rules, decorative borders (PMS 1245) |

**Accent (secondary — never dominant):** Turquoise `#00C6D7`, Magenta `#D462AD`, Orange `#FC8900`, Green `#6E963B`, Citron `#F3E500`, Sand `#F5F0E6`

**Neutrals:** Cool Gray `#747678` (darken to `#5D6066` for small muted text to pass WCAG AA), Stone `#B6B1A9`, White `#FFFFFF`

**Accessibility:** WCAG 2 Level AA — ≥ 4.5:1 contrast for normal text. Blue and Navy pass on white. Never use Yellow or Citron as text on light backgrounds.

### 3. Apply typography

There are two contexts: the **UC San Diego Brand Guidelines** (print, digital, signage) and **Decorator 5** (the campus web framework). They use different font stacks — apply the one that matches the medium.

**Brand Guidelines (general materials):**
- **Primary:** [Brix Sans](https://www.myfonts.com/collections/brix-sans-font-hvd-fonts) (licensed) — do not bundle without a MyFonts license
- **Recommended alternate:** [Source Sans 3](https://fonts.google.com/specimen/Source+Sans+3) (Google Fonts) — per the UC San Diego Brand Guidelines
- **Headlines:** [Refrigerator Deluxe](https://fonts.adobe.com/fonts/refrigerator-deluxe) (Adobe Fonts) with [Teko](https://www.fontshare.com/fonts/teko) as the free substitute
- **Serif:** Chronicle (licensed from typography.com)

**Decorator 5 (web pages and apps using the campus framework):**
- **Body / UI text:** [Roboto](https://fonts.google.com/specimen/Roboto) (weights 400, 700) — loaded by the Decorator 5 CDN via Google Fonts `@import`. This is the Decorator 5 implementation choice, not the brand-wide alternate.
- **Display headings (h1/h2 only):** [Teko SemiBold weight 600](https://www.fontshare.com/fonts/teko) — loaded from the CDN's `teko.css`. h1 in Blue `#00629B`, h2 in Navy `#182B49`, `letter-spacing: 0.5px`, `line-height: 1.1`.
- **Fallback stack:** `Roboto, Helvetica Neue, Helvetica, Arial, sans-serif`

### 4. Implement the Decorator 5 page shell

Load the real CDN assets — do not copy them locally unless the project has an explicit offline requirement.

**Stylesheets (in `<head>`):**
```html
<link href="//cdn.ucsd.edu/cms/decorator-5/styles/bootstrap.min.css" rel="stylesheet">
<link href="//cdn.ucsd.edu/cms/decorator-5/styles/base.min.css" rel="stylesheet">
```

**Scripts (end of `<body>`):**
```html
<script src="https://cdn.ucsd.edu/cms/decorator-5/scripts/jquery.min.js"></script>
<script src="https://cdn.ucsd.edu/cms/decorator-5/scripts/bootstrap.min.js"></script>
<script src="https://cdn.ucsd.edu/cms/decorator-5/scripts/vendor.min.js"></script>
<script src="https://cdn.ucsd.edu/cms/decorator-5/scripts/base.min.js"></script>
```

**Chrome stack — verified against `base.min.css` (June 2026):**

```
.layout-header      bg: #2b92b9  (medium blue outer wrapper)
  └─ .layout-title  bg: #fff, height: 92px
       ├─ .title-header  color: #000, uppercase, 1.35rem, 1px letter-spacing (LEFT)
       └─ .title-logo    229×65px sprite, image-replaced link to ucsd.edu (RIGHT)
.navbar-default     bg: #00629b, min-height: 50px
  └─ .active > a    border-bottom: 3px solid #ffcd00  ← ONLY place Yellow appears
.layout-main        (content area)
.footer             bg: #00629b, border-top: 1px solid #ccc
  ├─ .col-sm-8      address + copyright + .footer-links (white, underlined, pipe-separated)
  └─ .col-sm-4      .footer-logo white wordmark, 158×30px
```

**Key facts agents commonly get wrong:**
- Footer is **Blue `#00629b`**, not navy
- There is **no gold rule on the header band** — yellow `#ffcd00` appears only on the active nav tab
- The outer `.layout-header` wrapper is `#2b92b9` (medium blue); the white band is `.layout-title` inside it

See `references/decorator5-chrome.md` for the full annotated HTML skeleton and component list.

### 5. Use logo assets from the CDN

Never redraw, recolor, or approximate logos — they are licensed assets.

| Asset | URL |
|---|---|
| Header sprite (1x) | `https://cdn.ucsd.edu/cms/decorator-5/styles/img/sprite_base.png` |
| Header sprite (2x retina) | `https://cdn.ucsd.edu/cms/decorator-5/styles/img/sprite_base2x.png` |
| Footer wordmark (white PNG) | `https://cdn.ucsd.edu/developer/decorator/5.0.2/img/ucsd-footer-logo-white.png` |
| Official logo downloads (SVG/PNG) | https://brand.ucsd.edu → Visual Brand → Logos (campus login may be required) |

Until official files are in the project, use a text wordmark: **"UC San Diego"** bold + unit name.

### 6. Use Decorator 5 components

Decorator 5 is Bootstrap 3 + UCSD brand overrides. For any component, fetch the live kitchen sink example at `https://developer.ucsd.edu/design/v5-kitchen-sink/kitchen-sink/<component>.html`. Available components: alerts, badges, breadcrumbs, buttons, button\_dropdowns, code, dropdowns, equal\_column\_layout, forms, helper\_classes, icons, images, input\_groups, javascript\_components, pagination, panels, progress\_bars, tables, typography.

### 7. For emails

Use inline CSS only. Pattern: Sand `#F5F0E6` page bg → white card with `#E2DED5` border → Blue `#00629B` header strip → Navy `#182B49` headings → Blue `#00629B` buttons → `#747678` fine print → Roboto/Helvetica font stack.

## Guardrails

- **Never fabricate or approximate the UCSD logo** — use CDN assets or the text wordmark only
- **Never use Yellow `#FFCD00` or Citron as text on white or light backgrounds** — fails WCAG AA
- **Never set the footer to navy** — it is UCSD Blue `#00629b`
- **Do not bundle Brix Sans** without confirming a MyFonts license is in place — use Source Sans 3 (Brand Guidelines) or Roboto (Decorator 5) instead depending on context
- If the live brand.ucsd.edu or kitchen sink contradicts this skill, follow the live source and note the discrepancy

## Sources & currency

- UC San Diego Brand Guidelines: https://brand.ucsd.edu — current as of June 2026
- Decorator 5 CDN CSS (`base.min.css`): https://cdn.ucsd.edu/cms/decorator-5/styles/base.min.css — verified June 2026
- Decorator 5 Kitchen Sink: https://developer.ucsd.edu/design/v5-kitchen-sink/ — verified June 2026
- Full annotated chrome and component reference: `references/decorator5-chrome.md`
