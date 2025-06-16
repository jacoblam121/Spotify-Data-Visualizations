"""Utility helpers for text measurement and truncation that are reused across animation frames.

Public function
---------------
truncate_to_fit(text, font_properties, renderer, max_width_px) -> str
    Returns the original text if it fits in the requested pixel width, otherwise
    returns a shortened version ending with a single Unicode ellipsis (…).

The routine performs a binary-search over the candidate length so that we call
`renderer.get_text_width_height_descent` only O(log n) times, which is fast
enough to run for every label in every animation frame.
"""
from matplotlib.textpath import TextPath  # noqa: F401 – imported so MPL loads FreeType early
from matplotlib import font_manager as fm

# Re-export type to avoid callers needing to import font_manager directly.
FontProperties = fm.FontProperties

ELLIPSIS = "\u2026"  # Unicode character …


def _text_width_px(text: str, font_props: fm.FontProperties, renderer) -> float:
    """Return rendered text width in *pixels* using Matplotlib's low-level API."""
    w, _h, _d = renderer.get_text_width_height_descent(text, font_props, ismath=False)
    return w


def truncate_to_fit(text: str, font_properties: fm.FontProperties, renderer, max_width_px: float) -> str:
    """Return *text* if it fits within *max_width_px* pixels, else shorten with ….

    The algorithm keeps as many leading characters as possible so that the
    beginning of the song title is still visible while guaranteeing the whole
    string is no wider than *max_width_px*.
    """
    if not text:
        return ""
    if max_width_px <= 0:
        return ELLIPSIS  # No space at all

    # Fast path – text already fits.
    if _text_width_px(text, font_properties, renderer) <= max_width_px:
        return text

    # Reserve width for the ellipsis.
    ellipsis_width = _text_width_px(ELLIPSIS, font_properties, renderer)
    if ellipsis_width >= max_width_px:
        return ELLIPSIS  # Even the ellipsis alone does not fit; show it anyway.

    # Binary search the largest prefix that fits when we append …
    low = 0
    high = len(text)
    best_good = 0
    while low <= high:
        mid = (low + high) // 2
        candidate = text[:mid] + ELLIPSIS
        if _text_width_px(candidate, font_properties, renderer) <= max_width_px:
            best_good = mid  # fits – try to take more characters
            low = mid + 1
        else:
            high = mid - 1

    return text[:best_good] + ELLIPSIS 