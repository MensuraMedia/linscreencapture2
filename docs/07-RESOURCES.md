# 7. Resources in this repository

LinAppTemplate is the single place to start a simple Linux utility app: everything a new Lin* app
needs is here, and an app copies what it uses into its own tree (copy, don't reference).

| Resource | Where | Licence | How an app uses it |
|---|---|---|---|
| Theme and component kit `lintheme` | `lintheme/` | the repository's (to be chosen) | copy into `src/lintheme`; record the version (06-ADOPTING) |
| Bundled icons (20, regular weight) | `lintheme/icons/` | MIT (Phosphor) | ship with the kit; `ui.icon("printer", 24)` |
| **Full Phosphor Icons v2.0.8** (1,248 icons × 6 weights: regular, thin, light, bold, fill, duotone) | `assets/icons/phosphor/` (`INDEX.txt`, `SOURCE.txt` with the SHA-256, `LICENSE`) | MIT, © 2023 Phosphor Icons | pick an icon, copy it into the kit (below); never load from `assets/` at runtime |
| UI/UX design and build principles | `docs/design/GUI-GUIDE-AND-DESIGN-REFERENCE.md` | — | the brief for a new app or redesign |
| Redesign mockups and Graphite Night references | `docs/design/redesign-2026/` | — | pattern library in context |
| Working UX rules | `docs/05-UX.md` | — | requirements; the design adversary enforces them |
| Stack and versions | `docs/01-STACK.md` | — | the verified versions and how to check a machine |
| Universal instruction set | `CLAUDE.md`, `.claude/`, `changelog.*` | — | copy into the new app's repository and rename |

## Adding an icon to the kit

The kit bundles only the icons the apps use (regular weight, recoloured at runtime). To add one:

```bash
grep -i 'cable' assets/icons/phosphor/INDEX.txt          # find it by name or tag
cp assets/icons/phosphor/regular/plug.svg lintheme/icons/
# bump lintheme.__version__, add a changelog entry, run the tests and look at the gallery
```

Other weights live at `assets/icons/phosphor/<weight>/<name>-<weight>.svg`. Keep
`lintheme/icons/LICENSE-phosphor` with the icons in every app that ships them.
