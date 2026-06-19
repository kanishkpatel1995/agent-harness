# Founsi brand assets — for the deck and the research figures

Everything here follows [`founsi-brand-guide.md`](founsi-brand-guide.md). Purple
is the accent (~5%), never the background. Syne for display, Manrope for body.

## Logo set

Generated from the one source lockup by [`build_logos.py`](build_logos.py)
(`python presentation/brand/build_logos.py` to regenerate). Three mark paths, nine
wordmark paths.

| File | Use |
|---|---|
| `founsi-logo-horizontal.svg` | source lockup (icon + "Founsi.ai", grey wordmark) |
| `founsi-logo-horizontal-primary.svg` | **light backgrounds** — ink wordmark + purple |
| `founsi-logo-horizontal-inverted.svg` | **dark backgrounds** — white wordmark + purple |
| `founsi-logo-horizontal-mono-black.svg` / `-mono-white.svg` | single-colour contexts |
| `founsi-mark.svg` | the icon mark alone (purple) — corner mark on appendix slides |
| `founsi-mark-inverted.svg` / `-mono-black.svg` | mark on dark / single-colour |
| `founsi-wordmark.svg` | wordmark only (ink + purple `.ai`) |
| `founsi-app-icon.svg` / `-light.svg` | rounded-square app/social icon |
| `founsi-favicon.svg` | 64px square mark |

**Never:** stretch/rotate/skew, recolor the purple period, add effects, or place
on a busy background without a container.

## Charts

[`chart_style.py`](chart_style.py) gives every research figure one consistent,
on-brand look (off-white surface, purple-tinted grid, ink text, fixed per-policy
colours, a "Founsi." corner wordmark). Use it for all appendix graphs:

```python
from presentation.brand.chart_style import apply, POLICY_COLORS, save
apply()
# ... matplotlib plotting, colouring each policy via POLICY_COLORS ...
save(fig, "presentation/figures/pareto.png")
```

Fixed policy colours so the same policy is the same colour in every figure:
truncate = grey, recency = purple, importance = purple-dark, semantic = ink,
baseline = red.
