# Susan Tadlock Bond — artist website

Static site with no build step. It deploys as-is to Cloudflare Pages (or any static host).

| Page | File | In nav? |
|---|---|---|
| Home | `index.html` | yes |
| Gallery / Portfolio | `gallery.html` | yes |
| Contact | `contact.html` | yes |
| Privacy Policy | `privacy.html` | footer only |
| Terms of Service | `terms.html` | footer only |

## Before launch

1. **Artwork.** Put images in `images/art/`, then edit `assets/artworks.js`. That one file drives the home hero, the "Recent pieces" grid, and the full gallery, including filters, lightbox, and "Inquire" links. The site ships with generated color-field placeholders.
2. **Forms.** In `assets/site.js`, set `formEndpoint` and `newsletterEndpoint`. Each one receives a JSON POST. If you leave an endpoint blank, the form falls back to a `mailto:` to `email`. If `email` is also blank, the form says it isn't connected yet.
3. **Artist statement.** The home page "About" block has placeholder text marked with an HTML comment.
4. **Legal pages.** These are templates. Replace every `[BRACKETED]` item and have them reviewed before publishing.

## Local preview

    python3 -m http.server 8000   # then open http://localhost:8000
