# HBALS v2 — Official Research Website Package

This package adds a dedicated static research website to the existing [`ErfanKhadiv/HBALS-TSP`](https://github.com/ErfanKhadiv/HBALS-TSP) repository. It is designed to be published from the repository's `docs/` folder using GitHub Pages.

## Add it to the existing HBALS repository

1. Download and extract this archive.
2. Copy the included `docs/` directory into the root of your existing `HBALS-TSP` repository. If your repository already has a `docs/` directory, merge the contents rather than deleting unrelated files.
3. Commit and push the new `docs/` directory to the `main` branch. Do not replace or remove the existing `v2/` source, data, results or README files.
4. In GitHub, open **Settings → Pages**.
5. Under **Build and deployment**, choose **Deploy from a branch**, select `main`, and set the folder to `/docs`.
6. Save. GitHub Pages should publish the site at:

   `https://erfankhadiv.github.io/HBALS-TSP/`

The HTML's canonical URL and Open Graph URL are already set to that address.

## Preview locally

From the root of the repository, run:

```bash
python -m http.server 8000 --directory docs
```

Then open `http://localhost:8000/`.

The site is static and has no npm build step. It uses local HTML, CSS, JavaScript, figures and experiment data. Google Fonts are optional network-loaded typography; the page remains usable with system-font fallbacks.

## What the site contains

- Research overview, problem definition and final v2 algorithm design
- Exact configuration and experimental-budget description
- Main 12-instance results and the 3 larger-instance results
- Friedman and Holm-adjusted Wilcoxon results, and ablation table/figures
- Saved per-instance convergence curves from the supplied Python experiments
- Interactive browser implementation of the final HBALS v2 procedure
- Reproducibility notes, repository map, preprint citation and BibTeX
- English/Persian language switch, RTL support, dark/light themes and responsive layout
- Author signature in the copyright footer

## Important interpretation notes

The live browser lab is a shortened stochastic JavaScript preview for exploration; it is not a reproduction of the paper's full fixed-budget Python experiments. The experiment explorer reads the supplied saved Python results.

The v2 preprint is not peer reviewed. Journal submission does not imply acceptance. The main-study result does not establish universal superiority: the overall HBALS–ILS-2opt difference is not statistically significant, and ILS-2opt has lower mean gaps on two of the three larger instances.

## Package tree

```text
HBALS-TSP-Website.zip
├── README-WEBSITE-SETUP.md
└── docs/
    ├── index.html
    ├── favicon.svg
    └── assets/
        ├── css/site.css
        ├── js/site.js
        ├── js/hbals-demo.js
        ├── data/hbals-v2-data.js
        ├── figures/
        └── img/erfan-signature-gold.png
```
