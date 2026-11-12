# HBALS Research Website

This directory is the static website root for GitHub Pages. See `../README-WEBSITE-SETUP.md` for instructions to add it to the existing HBALS-TSP repository and publish from `main /docs`.


## Social preview image (Open Graph)

The page uses `assets/img/hbals-social-preview.jpg` (1200 × 630 px) for link previews. The `og:image` and `twitter:image` tags in `index.html` point to the public GitHub Pages URL. Keep the image at this exact path when deploying the `docs/` folder.

After deployment, refresh LinkedIn's cached preview with the [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/) by entering `https://erfankhadiv.github.io/HBALS-TSP/`.

## Mobile and RTL layout notes

The mobile header uses a compact menu button with a dropdown anchored to the header container. The menu is scrollable on short screens, supports outside-click and Escape-to-close behavior, and follows the current language direction. Layout guardrails keep Persian text and mixed Persian/Latin content inside their cards without introducing page-level horizontal scrolling; wide research tables and code samples retain their own contained horizontal scrolling where needed.
