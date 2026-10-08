# 4. CSS: Graphite Night

One theme. Colours live in `lintheme/tokens.py`; `lintheme/css.py` substitutes them into GTK
CSS for GTK 3 or GTK 4. No colour is written anywhere else (two physical exceptions: ink and
paper colours, which stand for real things and are never themed).

## 4.1 Colour roles

| Role | Hex | Use | Contrast (measured) |
|---|---|---|---|
| `bg` | `#1c1f23` | window | — |
| `surface` | `#262a30` | cards, header, action bar | — |
| `surface_hover` | `#2f343b` | hovered button | — |
| `rail` | `#17191d` | navigation rail | — |
| `border` | `#3a4048` | dividers, card edges (decorative) | — |
| `border_strong` | `#7d8590` | control outlines | 3.87 on surface (≥ 3) |
| `text` | `#eceff3` | text | 12.50 on surface |
| `text_muted` | `#aab2bd` | secondary text | 6.74 on surface (≥ 4.5) |
| `accent` | `#4c9dff` | primary button, selection, links | 5.20 on surface |
| `on_accent` | `#0b1320` | text on accent | 6.71 |
| `accent_soft` | `#1f3350` | active nav item, icon tiles | accent on it 4.60 |
| `focus` | `#ffd75e` | focus ring | 11.92 on bg |
| `ok` / `ok_bg` | `#5fd38d` / `#1d3a2a` | Ready | 7.68 on surface |
| `busy` / `busy_bg` | `#7cb7ff` / `#1f3350` | Busy | 6.92 |
| `attention` / `attention_bg` | `#ffbf4d` / `#3d3220` | Needs you | 8.80 |
| `error` / `error_bg` | `#ff8a80` / `#3f2422` | Can't reach | 6.32 |

`python3 tools/contrast.py` prints all 21 pairs; `tests/test_tokens.py` fails if any drops
below WCAG 2.2 AA.

## 4.2 Type, space, size

| Token | Value |
|---|---|
| Font | Ubuntu (Ubuntu Mono for commands); sizes display 28, title 20, heading 16, body 14, caption 12 (never smaller); weights 400/500 |
| Space | 4 · 8 · 12 · 16 · 24 · 32 · 48 |
| Radius | control 6 · card 10 · dialog 14 · pill fully round |
| Targets | 32 minimum (WCAG floor 24) · 36 controls · 40 frequent buttons · 48 the one main action |
| Layout | window ≥ 720 × 540; two panes from 960 px; options column 380–476 px; header 52; rail 88 (72 compact); action bar 84 |
| Motion | 120 ms state, 200 ms panels; 0 when the system turns animations off |

## 4.3 Classes

All classes start with `lt-`: root `lt-root`; shell `lt-header lt-brand lt-crumb lt-rail
lt-rail-item lt-active lt-compact lt-badge lt-page lt-pane lt-pane-divider lt-actionbar`;
containers `lt-card lt-large lt-hero lt-hero-icon lt-icon-tile lt-empty-icon lt-divider
lt-field-label lt-dropzone`; buttons `lt-btn lt-small lt-primary lt-big lt-danger lt-filled
lt-link lt-icon-btn lt-list-btn lt-thumb`; status `lt-chip lt-banner lt-pill` with `lt-ok
lt-busy lt-attention lt-error`; choices `lt-seg lt-value lt-select lt-entry lt-invalid`; text
`lt-display lt-title lt-heading lt-muted lt-caption lt-mono lt-strong lt-kbd lt-*-text`; steps
`lt-step lt-now lt-next lt-step-num`; tables `lt-row lt-thead`. `css.CLASSES` lists them all.

## 4.4 What GTK CSS can and can't do (and what the kit does instead)

| CSS feature | GTK 3.24 | GTK 4.14 | Kit approach |
|---|---|---|---|
| colours, borders, radius, padding, min sizes, box-shadow | yes | yes | used throughout |
| fonts, weights, text-decoration | yes | yes | Ubuntu, 400/500 |
| outline (focus ring) | longhands only | shorthand | per-toolkit rule in `css.py` |
| `:focus-visible` | no (`:focus`) | yes | per-toolkit |
| transitions | yes | yes | durations from tokens |
| custom properties `var()` | no | 4.16+ | substituted in Python |
| layout (`flex`, `grid`, `gap`, `position`) | no | no | Gtk.Box / Gtk.Grid spacing, `Gtk.Overlay` for badges |
| percentage widths | no | no | `set_size_request` from LAYOUT tokens |

## 4.5 Toolkit differences, as generated

GTK 3 adds `-gtk-icon-style: symbolic`, clears text shadows and uses `:focus` with outline
longhands. GTK 4 uses `:focus-visible` with the `outline` shorthand. Everything else is shared,
and both stylesheets parse with zero errors (tests/test_css.py).
