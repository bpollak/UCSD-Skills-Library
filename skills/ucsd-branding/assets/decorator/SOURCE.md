# Decorator 5 Assets — Online Partial Cache

## Provenance

- **Product:** UC San Diego Decorator 5
- **Source URL:** https://developer.ucsd.edu/design/v5-kitchen-sink/
- **CDN Base:** https://cdn.ucsd.edu/cms/decorator-5/
- **Version:** 5.0.2
- **Retrieved:** 2026-06-24

## Scope: Online Partial Cache

This is a **network-dependent partial cache** of commonly needed Decorator 5
assets — CSS, core fonts, and key images. It is **not** a complete offline
bundle and should not be selected for offline rendering.

**What is included:**
- Core CSS (`bootstrap.min.css`, `base.min.css`, `teko.css`)
- Glyphicon Halflings font (`woff2`, `woff`, `ttf`)
- Key images (sprite, footer logo)

**What is NOT included** (loaded from remote URLs or unresolved relative paths at
runtime):
- Google Fonts (Roboto): `fonts.googleapis.com/css?family=Roboto:400,700`
- Teko font files from `cdn.ucsd.edu` and `qa-cdn.ucsd.edu`
- Most images/SVGs/GIFs referenced in `base.min.css` (50+ files in `../img/`)
- Glyphicon `.eot` and `.svg` font formats (legacy IE support)

The committed CSS is preserved from the upstream Decorator release. It still
contains remote `@import` and `url()` references, plus local relative references
to assets that are intentionally not vendored here. This cache reduces requests
for the included files only; it does **not** enable fully offline rendering.

## Runtime Network References

The committed CSS may request these exact external URLs at runtime:

- `https://fonts.googleapis.com/css?family=Roboto:400,700`
- `https://cdn.ucsd.edu/cms/decorator-5/styles/teko.css`
- `https://cdn.ucsd.edu/cms/decorator-5/fonts/Teko-Regular.woff2`
- `https://cdn.ucsd.edu/cms/decorator-5/fonts/Teko-Medium.woff2`
- `https://cdn.ucsd.edu/cms/decorator-5/fonts/Teko-SemiBold.woff2`
- `https://qa-cdn.ucsd.edu/cms/decorator-5/fonts/Teko-Regular.woff`
- `https://qa-cdn.ucsd.edu/cms/decorator-5/fonts/Teko-Regular.ttf`
- `https://qa-cdn.ucsd.edu/cms/decorator-5/fonts/Teko-Medium.woff`
- `https://qa-cdn.ucsd.edu/cms/decorator-5/fonts/Teko-Medium.ttf`
- `https://qa-cdn.ucsd.edu/cms/decorator-5/fonts/Teko-SemiBold.woff`
- `https://qa-cdn.ucsd.edu/cms/decorator-5/fonts/Teko-SemiBold.ttf`
- `https://cdn.ucsd.edu/cms/decorator-5/img/quote.svg`
- `https://cdn.ucsd.edu/cms/decorator-5/img/som-logo-header-2x.png`
- `https://cdn.ucsd.edu/cms/decorator-5/img/testimonial-bg-desktop.png`
- `https://cdn.ucsd.edu/cms/decorator-5/img/testimonial-bg-mobile.png`
- `http://cdn.ucsd.edu/developer/decorator/4.5.4/img/blink_nav.png`
- `http://cdn.ucsd.edu/developer/decorator/4.5.4/img/current_students_nav.png`

The final two entries are legacy plain-HTTP Decorator 4.5.4 image references
preserved from upstream `base.min.css`; consumers should allow those network
requests only if they accept that legacy behavior.

The vendored CSS also contains these non-runtime upstream project, provenance,
and license URLs in comments:

- `http://getbootstrap.com`
- `https://github.com/h5bp/html5-boilerplate/blob/master/src/css/main.css`
- `https://github.com/twbs/bootstrap/blob/master/LICENSE`
- `https://www.fontshare.com/fonts/teko`

## Files

| Local Path | Source URL |
|---|---|
| `styles/bootstrap.min.css` | https://cdn.ucsd.edu/cms/decorator-5/styles/bootstrap.min.css |
| `styles/base.min.css` | https://cdn.ucsd.edu/cms/decorator-5/styles/base.min.css |
| `styles/teko.css` | https://cdn.ucsd.edu/cms/decorator-5/styles/teko.css |
| `img/sprite_base.png` | https://cdn.ucsd.edu/cms/decorator-5/img/sprite_base.png |
| `img/ucsd-footer-logo-white.png` | https://cdn.ucsd.edu/developer/decorator/5.0.2/img/ucsd-footer-logo-white.png |
| `fonts/glyphicons-halflings-regular.woff2` | https://cdn.ucsd.edu/cms/decorator-5/fonts/glyphicons-halflings-regular.woff2 |
| `fonts/glyphicons-halflings-regular.woff` | https://cdn.ucsd.edu/cms/decorator-5/fonts/glyphicons-halflings-regular.woff |
| `fonts/glyphicons-halflings-regular.ttf` | https://cdn.ucsd.edu/cms/decorator-5/fonts/glyphicons-halflings-regular.ttf |

## License & Redistribution

These assets are part of the UC San Diego Decorator 5 design system,
published by UC San Diego for use in UCSD-affiliated web applications.
Redistribution is permitted for UCSD-affiliated projects.

The Glyphicon Halflings font set is included as part of Bootstrap 3,
which is licensed under the MIT License. See:
https://github.com/twbs/bootstrap/blob/main/LICENSE

## Integrity

Checksums (SHA-256) are in `checksums.sha256` in this directory.
Verify with:
  cd skills/ucsd-branding/assets/decorator && sha256sum -c checksums.sha256
