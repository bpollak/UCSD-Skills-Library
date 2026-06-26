---
name: ucsd-branding
description: Apply the TritonAI-flavored UC San Diego Decorator 5 visual system to web pages. Use when asked to match TritonAI, UCSD/UC San Diego web branding, campus page chrome, current TritonAI documentation pages, current Decorator 5 documentation pages, or the components shown in the official Decorator 5 kitchen sink. For TritonAI pages, the live tritonai.ucsd.edu site is the canonical styling source.
catalog:
  title: UCSD Branding
  description: >-
    Apply the TritonAI-flavored UC San Diego Decorator 5 visual system from the
    current tritonai.ucsd.edu pages, Developer/Decorator 5 docs, and Decorator 5
    kitchen-sink pages.
  category: Brand & Communications
  status: review
  publicationStatus: draft
  tier: experimental
  owner: AI Tools
  updated: 2026-06-26
allowed-tools: WebFetch, Read, Write, Edit
---

# UCSD TritonAI/Decorator 5 Branding

This skill is strict by design. It reflects only the current
`tritonai.ucsd.edu` pages, current `developer.ucsd.edu` Decorator 5 pages, and
the linked Decorator 5 kitchen-sink examples. For TritonAI properties and pages
that live in the TritonAI ecosystem, the live TritonAI site is the canonical
visual and layout source. Use Developer/Decorator 5 as the framework reference
and component fallback, not as a reason to override TritonAI-specific styling.

## When to use

- Building or restyling a web page to match the TritonAI site
- Building or restyling a web page to match the UC San Diego Developer site
- Implementing the Decorator 5 page shell: header, title band, navbar, content,
  sidebar, and footer
- Checking whether a page uses only currently documented Decorator 5 elements
- Choosing a Bootstrap 3/Decorator component from the official kitchen sink

Do not use this skill as a general UC San Diego brand manual. If the user asks
for broader brand identity, logos, print typography, email, charts, dark mode,
or non-Decorator application design, fetch the relevant current official source
first and keep that separate from this Decorator 5 contract.

## How to use this skill

### 1. Fetch the live sources first

Before writing any values from memory, fetch the relevant live TritonAI page
first. If a TritonAI page and Developer/Decorator 5 differ in spacing,
navigation behavior, labels, or page composition, the live TritonAI page wins
for TritonAI work.

| Source | URL |
|---|---|
| TritonAI Home | `https://tritonai.ucsd.edu/index.html` |
| TritonAI TritonGPT | `https://tritonai.ucsd.edu/tritongpt/index.html` |
| TritonAI Training & Resources | `https://tritonai.ucsd.edu/training-resources/index.html` |
| TritonAI Faculty AI Symposium | `https://tritonai.ucsd.edu/training-resources/faculty-ai-symposium.html` |
| TritonAI Terms of Use | `https://tritonai.ucsd.edu/tritongpt/terms.html` |
| Sitemap | `https://developer.ucsd.edu/sitemap.xml` |
| Developer Home | `https://developer.ucsd.edu/index.html` |
| Design | `https://developer.ucsd.edu/design/index.html` |
| Decorator 5 overview | `https://developer.ucsd.edu/design/decorator/index.html` |
| Templates | `https://developer.ucsd.edu/design/decorator/templates/index.html` |
| Widgets | `https://developer.ucsd.edu/design/decorator/widgets/index.html` |
| Getting Started | `https://developer.ucsd.edu/design/decorator/getting-started/index.html` |
| CMS setup | `https://developer.ucsd.edu/design/decorator/getting-started/cms.html` |
| HTML Tips | `https://developer.ucsd.edu/design/decorator/getting-started/tips.html` |
| ZIP File Guide | `https://developer.ucsd.edu/design/decorator/getting-started/file-guide/index.html` |
| Kitchen sink index | `https://developer.ucsd.edu/design/v5-kitchen-sink/kitchen-sink/index.html` |

The sitemap also lists archive pages under `/design/archive/`. Do not fold
Decorator 3 or Decorator 4 archive elements into this Decorator 5 skill unless
the user explicitly asks for archived guidance.

### 2. Apply TritonAI first, then current sitemap/kitchen-sink surface

For TritonAI pages and TritonAI-adjacent pages, match these live TritonAI
patterns first:

- Header, title band, top navbar, search, mobile menu, content container,
  breadcrumbs, sidebar navigation, footer, and typography as rendered on
  `tritonai.ucsd.edu`.
- Section sidebar behavior from live TritonAI documentation pages. On mobile,
  the sidebar appears after the main content near the footer. Its
  `.main-content-nav` styling uses the compact TritonAI/Decorator treatment:
  `16px` outer padding, compact `h2`, list rows that bleed to the nav border,
  `16px` links, top-only separators, and the sand active row.
- Top navigation active state from TritonAI pages: the active `.navbar-default`
  item uses the dark blue background, not the yellow underline pattern.
- TritonAI-specific labels, ordering, and section names from the live page being
  matched.

Use these current Developer/Decorator elements as the underlying component
system and fallback reference:

- Developer page chrome: skip link, emergency container, optional login band,
  white title band, blue navbar, offcanvas mobile nav, search toggle, content
  container/sidebar layout, and blue footer.
- Current documentation surfaces: Developer Home, Design, Decorator 5,
  Templates, Widgets, Getting Started, CMS setup, HTML Tips, and ZIP File
  Guide.
- Typography and colors defined by the loaded Decorator CSS.
- Bootstrap 3 components shown in the 19 linked kitchen-sink examples: alerts,
  badges, breadcrumbs, buttons, button dropdowns, code, dropdowns, equal column
  layout, forms, helper classes, icons, images, input groups, JavaScript
  components, pagination, panels, progress bars, tables, and typography.
- Assets loaded by the current site/kitchen sink, including UCSD header/footer
  sprites, Glyphicons, Roboto, and Teko.

Do not invent or infer guidance for:

- shadcn/Tailwind theme token maps
- dark mode
- email templates
- charts, heatmaps, data visualization ramps, or dashboards
- React/Vue application architecture
- non-TritonAI, non-sitemap, or non-kitchen-sink page patterns
- logos or marks not loaded by the current Decorator pages

### 3. Implement the Decorator 5 page shell

Load the real Decorator 5 styles and scripts unless the project has an explicit
offline requirement.

```html
<link href="//cdn.ucsd.edu/cms/decorator-5/styles/bootstrap.min.css" rel="stylesheet">
<link href="//cdn.ucsd.edu/cms/decorator-5/styles/base.min.css" rel="stylesheet">
```

```html
<script src="https://cdn.ucsd.edu/cms/decorator-5/scripts/jquery.min.js"></script>
<script src="https://cdn.ucsd.edu/cms/decorator-5/scripts/bootstrap.min.js"></script>
<script src="https://cdn.ucsd.edu/cms/decorator-5/scripts/vendor.min.js"></script>
<script src="https://cdn.ucsd.edu/cms/decorator-5/scripts/base.min.js"></script>
```

Verified chrome stack:

```text
.layout-header      bg: #2b92b9
  .layout-title     bg: #fff, height: 92px
    .title-header   black uppercase site title, 1.35rem, 1px letter spacing
    .title-logo     229x65 sprite link to ucsd.edu
.navbar-default     bg: #00629b, white links
  hover/open/active bg: #004268
  active state: #004268 background, no yellow underline
  mobile toggle: .mobile-nav-bars and .mobile-nav-icon MENU both inside button
.layout-navbar .navbar-list
  active underline: 3px solid #ffcd00 in that alternate Decorator nav pattern
.layout-main        content area
.main-section       primary content section
.sidebar-section    complementary sidebar
.main-content-nav   sidebar navigation
.footer             bg: #00629b, white links/text, 158x30 footer logo
```

Key facts agents commonly get wrong:

- Footer is UCSD Blue `#00629b`, not navy.
- There is no gold rule on the white title band.
- The kitchen-sink `.navbar-default` active item is dark blue, not a yellow
  underline. Do not put the `.layout-navbar .navbar-list` underline pattern on
  Bootstrap `.navbar-default .navbar-nav` tabs.
- The mobile `MENU` label is not a loose sibling next to the toggle. It lives
  inside `.navbar-toggle` in `.mobile-nav-icon`, alongside `.mobile-nav-bars`.
- The extra-small navbar UCSD wordmark is the white footer wordmark asset
  loaded by Decorator 5, inside `.col-sm-4.pull-right.visible-xs-block` with
  `img.img-responsive.header-logo`; do not resize or replace it with another
  UC San Diego logo asset.
- The outer `.layout-header` wrapper is `#2b92b9`; the white band is
  `.layout-title` inside it.
- Icons are Bootstrap 3 Glyphicons and the social icons shown by the kitchen
  sink; Font Awesome is not part of the current surface.

See `references/decorator5-chrome.md` for the annotated HTML skeleton,
TritonAI-specific page-shell notes, current sitemap additions, and
kitchen-sink component inventory.

### 4. Use current sitemap additions

The current non-archive sitemap pages add these elements beyond the kitchen
sink index:

- Developer Home carousel hero: `.carousel`, `.slide`, `.jumbotron`,
  `.jumbotron-hero`, `.hm`, `.carousel-inner`, `.carousel-indicators`, `.item`,
  `.carousel-control`, pause/previous/next controls, `rt-text-light`,
  `rt-btn-yellow`, `.jumbotron-sand`, and `.overlay-glow-2`.
- Documentation shell landmarks: breadcrumb list labelled "Breadcrumb",
  `section` labelled "Main Content", complementary sidebar labelled "Sidebar",
  complementary logo figure labelled "Logo", and navigation article labelled
  "Sidebar Nav".
- Current documentation topics: Getting Started, Widgets, Templates, ZIP File
  Guide, Decorator 5 for CMS sites, and HTML Tips.
- Current widgets: FullCalendar, DataTable, Wizard, and MaxChar. The page uses
  drawer/accordion-style expandable sections and "Expand All" links.
- ZIP File Guide folders: `kitchen-sink`, `fonts`, `img`, `scripts`, and `css`.
- ZIP File Guide templates: `blank-slate.html`, `index.html`,
  `three-column.html`, `two-column.html`, and `homepage.html`.
- HTML Tips: avoid inline/in-page styling, avoid font tags, use tables only for
  tabular data, use semantic markup, prefer `<strong>` over `<b>` and `<em>`
  over `<i>`, avoid `<br>` except legitimate address/name-title cases, use
  `id` instead of named anchors, use double-quoted attributes, avoid dangling
  elements, and use lowercase tags.

### 5. Use Decorator 5 kitchen-sink components

For component details, fetch the live example at:

`https://developer.ucsd.edu/design/v5-kitchen-sink/kitchen-sink/<component>.html`

Available component pages:

- `alerts.html`
- `badges.html`
- `breadcrumbs.html`
- `buttons.html`
- `button_dropdowns.html`
- `code.html`
- `dropdowns.html`
- `equal_column_layout.html`
- `forms.html`
- `helper_classes.html`
- `icons.html`
- `images.html`
- `input_groups.html`
- `javascript_components.html`
- `pagination.html`
- `panels.html`
- `progress_bars.html`
- `tables.html`
- `typography.html`

## Guardrails

- Follow the live `tritonai.ucsd.edu` page over this static skill for TritonAI
  work if they differ.
- Follow the live `developer.ucsd.edu` pages over this static skill for generic
  Decorator 5 work if they differ.
- Do not import archive page behavior into current Decorator 5 work.
- Do not add non-sitemap components, colors, layouts, or frameworks and label
  them as UCSD Decorator 5.
- Do not fabricate or approximate UCSD logos; use only assets loaded by the
  current Decorator pages or separately verified official logo downloads.

## Sources & currency

- Current TritonAI pages - verified June 26, 2026
- `https://developer.ucsd.edu/sitemap.xml` - verified June 19, 2026
- Current non-archive Developer/Decorator pages - verified June 19, 2026
- Decorator 5 Kitchen Sink - verified June 19, 2026
- Decorator 5 CSS (`base.min.css`) - verified June 19, 2026
- Full annotated reference: `references/decorator5-chrome.md`
