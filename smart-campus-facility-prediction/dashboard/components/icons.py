"""
Lucide Outline SVG Icons Utility for FIPP.
Provides consistent, professional 24x24 outline vector icons
styled according to the Modern Sage & Forest design system.
Replaces decorative emoji symbols across navigation, badges, and headers.
"""
import urllib.parse
from typing import Dict

# Standard Lucide 24x24 SVG path definitions (stroke-based outline icons)
_LUCIDE_PATHS: Dict[str, str] = {
    # Navigation icons
    "layout-dashboard": (
        '<rect width="7" height="9" x="3" y="3" rx="1"/>'
        '<rect width="7" height="5" x="14" y="3" rx="1"/>'
        '<rect width="7" height="9" x="14" y="12" rx="1"/>'
        '<rect width="7" height="5" x="3" y="16" rx="1"/>'
    ),
    "clipboard-list": (
        '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>'
        '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
        '<path d="M12 11h4"/>'
        '<path d="M12 16h4"/>'
        '<path d="M8 11h.01"/>'
        '<path d="M8 16h.01"/>'
    ),
    "inbox": (
        '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/>'
        '<path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>'
    ),
    "wrench": (
        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'
    ),
    "check-circle": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="m9 12 2 2 4-4"/>'
    ),
    "chart-no-axes-combined": (
        '<path d="M12 16v5"/>'
        '<path d="M16 14v7"/>'
        '<path d="M20 10v11"/>'
        '<path d="m22 3-8.646 8.646a.5.5 0 0 1-.708 0L9.354 8.354a.5.5 0 0 0-.707 0L2 15"/>'
        '<path d="M4 18v3"/>'
        '<path d="M8 14v7"/>'
    ),
    # Branding and Identity icons
    "shield": (
        '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
    ),
    "user": (
        '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>'
    ),
    "graduation-cap": (
        '<path d="M22 10v6M2 10l10-5 10 5-10 5z"/>'
        '<path d="M6 12v5c3 3 9 3 12 0v-5"/>'
    ),
    "plus": (
        '<path d="M5 12h14"/>'
        '<path d="M12 5v14"/>'
    ),
    "star": (
        '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>'
    ),
    "bell": (
        '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>'
        '<path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>'
    ),
    "building": (
        '<rect width="16" height="20" x="4" y="2" rx="2" ry="2"/>'
        '<path d="M9 22v-4h6v4"/>'
        '<path d="M8 6h.01"/>'
        '<path d="M16 6h.01"/>'
        '<path d="M12 6h.01"/>'
        '<path d="M12 10h.01"/>'
        '<path d="M12 14h.01"/>'
        '<path d="M16 10h.01"/>'
        '<path d="M16 14h.01"/>'
        '<path d="M8 10h.01"/>'
        '<path d="M8 14h.01"/>'
    ),
    "log-out": (
        '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
        '<polyline points="16 17 21 12 16 7"/>'
        '<line x1="21" x2="9" y1="12" y2="12"/>'
    ),
    "search": (
        '<circle cx="11" cy="11" r="8"/>'
        '<path d="m21 21-4.3-4.3"/>'
    ),
    "download": (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/>'
        '<line x1="12" x2="12" y1="15" y2="3"/>'
    ),
    "alert-triangle": (
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<line x1="12" x2="12" y1="9" y2="13"/>'
        '<line x1="12" x2="12.01" y1="17" y2="17"/>'
    ),
    "calendar": (
        '<path d="M8 2v4"/>'
        '<path d="M16 2v4"/>'
        '<rect width="18" height="18" x="3" y="4" rx="2"/>'
        '<path d="M3 10h18"/>'
    ),
    "map-pin": (
        '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/>'
        '<circle cx="12" cy="10" r="3"/>'
    ),
    "clock": (
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="12 6 12 12 16 14"/>'
    ),
    "sliders": (
        '<line x1="4" x2="4" y1="21" y2="14"/>'
        '<line x1="4" x2="4" y1="10" y2="3"/>'
        '<line x1="12" x2="12" y1="21" y2="12"/>'
        '<line x1="12" x2="12" y1="8" y2="3"/>'
        '<line x1="20" x2="20" y1="21" y2="16"/>'
        '<line x1="20" x2="20" y1="12" y2="3"/>'
        '<line x1="1" x2="7" y1="14" y2="14"/>'
        '<line x1="9" x2="15" y1="8" y2="8"/>'
        '<line x1="17" x2="23" y1="16" y2="16"/>'
    ),
}


def render_lucide_icon(
    name: str,
    size: int = 18,
    color: str = "currentColor",
    stroke_width: float = 2.0,
    extra_style: str = "",
) -> str:
    """
    Generates an inline SVG element for the requested Lucide outline icon.

    Args:
        name: Name of the icon (e.g. 'layout-dashboard', 'wrench').
        size: Width and height in pixels (default 18).
        color: Stroke color (hex or CSS color keyword, default 'currentColor').
        stroke_width: Vector outline stroke weight (default 2.0).
        extra_style: Additional inline CSS styles.

    Returns:
        HTML SVG string.
    """
    paths = _LUCIDE_PATHS.get(name, _LUCIDE_PATHS["layout-dashboard"])
    style_str = f"vertical-align: middle; display: inline-block; flex-shrink: 0; {extra_style}".strip()
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-{name}" '
        f'style="{style_str}">{paths}</svg>'
    )


def get_lucide_icon_data_uri(
    name: str,
    color: str = "%23DCE5D8",
    size: int = 18,
    stroke_width: float = 2.0,
) -> str:
    """
    Generates a CSS data URI string for use in background-image / content.

    Args:
        name: Icon name.
        color: Color string (if hex, '#' should be encoded as '%23' or will be converted).
        size: Viewbox render size.
        stroke_width: Stroke weight.

    Returns:
        data:image/svg+xml string suitable for CSS url().
    """
    if color.startswith("#"):
        encoded_color = "%23" + color[1:]
    else:
        encoded_color = color
    paths = _LUCIDE_PATHS.get(name, _LUCIDE_PATHS["layout-dashboard"])
    svg_raw = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{encoded_color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
    )
    encoded_svg = urllib.parse.quote(svg_raw)
    return f"data:image/svg+xml;utf8,{encoded_svg}"
