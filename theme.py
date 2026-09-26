import customtkinter as ctk


# ============================================================
# THEME SETUP
# ============================================================

def set_mode(mode: str):
    """Set theme mode and update module-level color variables.

    mode: 'dark' or 'light'
    """
    mode = (mode or "dark").lower()

    if mode == "light":
        ctk.set_appearance_mode("light")
        palette = {
            # darker, muted light palette: slightly darker gray background to reduce glare
            "BG": "#D0D4D8",            # darker muted gray background
            "SIDEBAR_BG": "#E9EDF1",
            "CARD": "#F4F6F8",
            "CARD_ALT": "#F2F5F7",
            "SURFACE": "#F0F2F5",
            "SURFACE_HOVER": "#E6EAEE",
            "SURFACE_ACTIVE": "#DFE7EB",
            "BORDER": "#D1D7DB",
            "BORDER_LIGHT": "#E6EEF3",
            "DIVIDER": "#E9EEF1",
            "TEXT": "#0F1724",
            "TEXT_SECONDARY": "#475569",
            "GRAY": "#6B7280",
            "TEXT_DISABLED": "#94A3B8",
            "TEXT_ON_ACCENT": "#06120C",
            "GREEN": "#0B7A4A",
            "GREEN_HOVER": "#0A6B43",
            "GREEN_MUTED": "#E8F7EE",
            "RED": "#C62828",
            "RED_HOVER": "#B71C1C",
            "RED_MUTED": "#FBEAEA",
            "CHART_GRID": "#E9EEF3",
            "CHART_AXIS": "#94A3B8",
        }
    else:
        ctk.set_appearance_mode("dark")
        palette = {
            "BG": "#080B10",
            "SIDEBAR_BG": "#0B0F15",
            "CARD": "#10161D",
            "CARD_ALT": "#0D1218",
            "SURFACE": "#151C24",
            "SURFACE_HOVER": "#1B2530",
            "SURFACE_ACTIVE": "#22303D",
            "BORDER": "#25313D",
            "BORDER_LIGHT": "#334252",
            "DIVIDER": "#1C2630",
            "TEXT": "#F4F7FB",
            "TEXT_SECONDARY": "#B2BDCA",
            "GRAY": "#7E8B99",
            "TEXT_DISABLED": "#52606D",
            "TEXT_ON_ACCENT": "#06120C",
            "GREEN": "#39D98A",
            "GREEN_HOVER": "#2CC87C",
            "GREEN_MUTED": "#123B2A",
            "RED": "#FF5C6C",
            "RED_HOVER": "#E84A5B",
            "RED_MUTED": "#3B1C24",
            "CHART_GRID": "#1B2631",
            "CHART_AXIS": "#6F7C89",
        }

    g = globals()
    for k, v in palette.items():
        g[k] = v


def setup_theme():
    # default to dark palette
    set_mode("dark")
    ctk.set_default_color_theme("green")


def enable_light_mode():
    set_mode("light")


def enable_dark_mode():
    set_mode("dark")


# initialize module-level colors
set_mode("dark")

# --- Explicit exports for static analysis ----------------------------------
# Define common theme variables at module level so linters and language
# servers can see them (they are also set dynamically by `set_mode`).
BG = globals().get("BG")
SIDEBAR_BG = globals().get("SIDEBAR_BG")
CARD = globals().get("CARD")
CARD_ALT = globals().get("CARD_ALT")
SURFACE = globals().get("SURFACE")
SURFACE_HOVER = globals().get("SURFACE_HOVER")
SURFACE_ACTIVE = globals().get("SURFACE_ACTIVE")
BORDER = globals().get("BORDER")
BORDER_LIGHT = globals().get("BORDER_LIGHT")
DIVIDER = globals().get("DIVIDER")
TEXT = globals().get("TEXT")
TEXT_SECONDARY = globals().get("TEXT_SECONDARY")
GRAY = globals().get("GRAY")
TEXT_DISABLED = globals().get("TEXT_DISABLED")
TEXT_ON_ACCENT = globals().get("TEXT_ON_ACCENT")
GREEN = globals().get("GREEN")
GREEN_HOVER = globals().get("GREEN_HOVER")
GREEN_MUTED = globals().get("GREEN_MUTED")
RED = globals().get("RED")
RED_HOVER = globals().get("RED_HOVER")
RED_MUTED = globals().get("RED_MUTED")
CHART_GRID = globals().get("CHART_GRID")
CHART_AXIS = globals().get("CHART_AXIS")



# ============================================================
# TYPOGRAPHY
# ============================================================

FONT_FAMILY = "Segoe UI"

FONT_DISPLAY = (
    FONT_FAMILY,
    30,
    "bold"
)

FONT_H1 = (
    FONT_FAMILY,
    25,
    "bold"
)

FONT_H2 = (
    FONT_FAMILY,
    20,
    "bold"
)

FONT_H3 = (
    FONT_FAMILY,
    16,
    "bold"
)

FONT_BODY = (
    FONT_FAMILY,
    13
)

FONT_BODY_MEDIUM = (
    FONT_FAMILY,
    13,
    "bold"
)

FONT_SMALL = (
    FONT_FAMILY,
    11
)

FONT_SMALL_MEDIUM = (
    FONT_FAMILY,
    11,
    "bold"
)

FONT_TINY = (
    FONT_FAMILY,
    10
)

FONT_PRICE = (
    FONT_FAMILY,
    27,
    "bold"
)

FONT_STAT = (
    FONT_FAMILY,
    18,
    "bold"
)


# ============================================================
# LAYOUT
# ============================================================

PAGE_PADDING = 26

CARD_PADDING = 18

SIDEBAR_WIDTH = 220

RADIUS_SM = 7

RADIUS_MD = 10

RADIUS_LG = 14

RADIUS_XL = 18

BUTTON_HEIGHT = 40

INPUT_HEIGHT = 42


# ============================================================
# CHART
# ============================================================

CHART_GRID = globals().get("CHART_GRID", "#1B2631")
CHART_AXIS = globals().get("CHART_AXIS", "#6F7C89")


# ============================================================
# COMMON STYLES
# ============================================================

CARD_STYLE = {
    "fg_color": globals().get("CARD", "#10161D"),
    "corner_radius": RADIUS_LG,
    "border_width": 1,
    "border_color": globals().get("BORDER", "#25313D"),
}

INPUT_STYLE = {
    "fg_color": globals().get("SURFACE", "#151C24"),
    "border_color": globals().get("BORDER", "#25313D"),
    "text_color": globals().get("TEXT", "#F4F7FB"),
    "placeholder_text_color": globals().get("GRAY", "#7E8B99"),
    "corner_radius": RADIUS_MD,
    "height": INPUT_HEIGHT,
    "border_width": 1,
    "font": FONT_BODY,
}

PRIMARY_BUTTON_STYLE = {
    "fg_color": globals().get("GREEN", "#39D98A"),
    "hover_color": globals().get("GREEN_HOVER", "#2CC87C"),
    "text_color": globals().get("TEXT_ON_ACCENT", "#06120C"),
    "corner_radius": RADIUS_MD,
    "height": BUTTON_HEIGHT,
    "font": FONT_BODY_MEDIUM,
}

SECONDARY_BUTTON_STYLE = {
    "fg_color": globals().get("SURFACE", "#151C24"),
    "hover_color": globals().get("SURFACE_HOVER", "#1B2530"),
    "text_color": globals().get("TEXT", "#F4F7FB"),
    "border_width": 1,
    "border_color": globals().get("BORDER", "#25313D"),
    "corner_radius": RADIUS_MD,
    "height": BUTTON_HEIGHT,
    "font": FONT_BODY_MEDIUM,
}


# ============================================================
# HELPERS
# ============================================================

def stock_color(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return globals().get("GRAY", "#7E8B99")
    if value > 0:
        return globals().get("GREEN", "#39D98A")
    if value < 0:
        return globals().get("RED", "#FF5C6C")
    return globals().get("GRAY", "#7E8B99")
