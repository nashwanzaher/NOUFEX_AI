from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4


class DesignSkill(str, Enum):
    component_generation = "component_generation"
    page_generation = "page_generation"
    design_system = "design_system"
    ui_review = "ui_review"
    animation = "animation"
    form_generation = "form_generation"
    responsive_design = "responsive_design"
    accessibility = "accessibility"
    screenshot_to_code = "screenshot_to_code"
    design_critique = "design_critique"


class ComponentType(str, Enum):
    button = "button"
    card = "card"
    navbar = "navbar"
    sidebar = "sidebar"
    modal = "modal"
    form = "form"
    input = "input"
    dropdown = "dropdown"
    table = "table"
    badge = "badge"
    alert = "alert"
    toast = "toast"
    tooltip = "tooltip"
    avatar = "avatar"
    progress = "progress"
    tabs = "tabs"
    accordion = "accordion"
    carousel = "carousel"
    footer = "footer"
    hero = "hero"
    section = "section"
    grid = "grid"
    list_group = "list_group"
    breadcrumb = "breadcrumb"
    pagination = "pagination"
    stepper = "stepper"
    timeline = "timeline"
    chart = "chart"
    stats = "stats"
    testimonial = "testimonial"
    pricing = "pricing"
    feature = "feature"
    team = "team"
    contact = "contact"
    faq = "faq"
    cta = "cta"
    blog_card = "blog_card"
    custom = "custom"


class DesignFramework(str, Enum):
    tailwind = "tailwind"
    bootstrap = "bootstrap"
    material_ui = "material_ui"
    chakra = "chakra"
    shadcn_ui = "shadcn_ui"
    daisy_ui = "daisy_ui"
    flowbite = "flowbite"
    plain_css = "plain_css"
    styled_components = "styled_components"
    css_modules = "css_modules"


class ColorScheme(str, Enum):
    light = "light"
    dark = "dark"
    sepia = "sepia"
    contrast = "contrast"
    pastel = "pastel"
    corporate = "corporate"
    sunset = "sunset"
    forest = "forest"
    ocean = "ocean"
    midnight = "midnight"
    autumn = "autumn"
    spring = "spring"


@dataclass
class DesignToken:
    name: str
    value: str
    description: str = ""
    type: str = "color"  # color, spacing, typography, shadow, radius

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "value": self.value, "description": self.description, "type": self.type}


@dataclass
class ColorPalette:
    primary: str = "#3B82F6"
    secondary: str = "#8B5CF6"
    accent: str = "#F59E0B"
    neutral: str = "#1F2937"
    base: str = "#FFFFFF"
    info: str = "#06B6D4"
    success: str = "#10B981"
    warning: str = "#F59E0B"
    error: str = "#EF4444"
    background: str = "#F9FAFB"
    surface: str = "#FFFFFF"
    text_primary: str = "#111827"
    text_secondary: str = "#6B7280"
    border: str = "#E5E7EB"

    def to_dict(self) -> dict[str, str]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "neutral": self.neutral,
            "base": self.base,
            "info": self.info,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "background": self.background,
            "surface": self.surface,
            "text_primary": self.text_primary,
            "text_secondary": self.text_secondary,
            "border": self.border,
        }

    @classmethod
    def from_primary(cls, primary: str, scheme: ColorScheme = ColorScheme.light) -> "ColorPalette":
        import colorsys
        import re

        def hex_to_rgb(h: str) -> tuple[float, ...]:
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

        def rgb_to_hex(r: float, g: float, b: float) -> str:
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

        try:
            r, g, b = hex_to_rgb(primary)
            h, s, v = colorsys.rgb_to_hsv(r, g, b)

            is_dark = scheme in (ColorScheme.dark, ColorScheme.midnight, ColorScheme.sunset)
            bg_factor = 0.15 if is_dark else 0.97
            surface_factor = 0.20 if is_dark else 1.0
            text_factor = 0.95 if is_dark else 0.07
            text_sec_factor = 0.70 if is_dark else 0.41
            border_factor = 0.30 if is_dark else 0.90

            secondary_h = (h + 0.15) % 1.0
            accent_h = (h + 0.5) % 1.0

            secondary = rgb_to_hex(*colorsys.hsv_to_rgb(secondary_h, min(s * 0.8, 0.8), v))
            accent = rgb_to_hex(*colorsys.hsv_to_rgb(accent_h, min(s * 1.2, 1.0), v))

            return cls(
                primary=primary,
                secondary=secondary,
                accent=accent,
                neutral=rgb_to_hex(*colorsys.hsv_to_rgb(h, 0.1, 0.12 if is_dark else 0.12)),
                base=rgb_to_hex(bg_factor, bg_factor, bg_factor),
                background=rgb_to_hex(bg_factor, bg_factor, bg_factor),
                surface=rgb_to_hex(surface_factor, surface_factor, surface_factor),
                text_primary=rgb_to_hex(text_factor, text_factor, text_factor),
                text_secondary=rgb_to_hex(text_sec_factor, text_sec_factor, text_sec_factor),
                border=rgb_to_hex(border_factor, border_factor, border_factor),
            )
        except Exception:
            return cls()


@dataclass
class TypographySystem:
    font_family: str = "Inter, system-ui, -apple-system, sans-serif"
    font_mono: str = "JetBrains Mono, Fira Code, monospace"
    font_heading: str = "Inter, system-ui, -apple-system, sans-serif"
    base_size: str = "16px"
    scale_ratio: float = 1.25

    h1: str = "3rem"
    h2: str = "2.25rem"
    h3: str = "1.75rem"
    h4: str = "1.25rem"
    h5: str = "1rem"
    h6: str = "0.875rem"
    body: str = "1rem"
    small: str = "0.875rem"
    caption: str = "0.75rem"
    line_height: float = 1.6
    letter_spacing: str = "0em"

    def to_dict(self) -> dict[str, Any]:
        return {
            "font_family": self.font_family,
            "font_mono": self.font_mono,
            "font_heading": self.font_heading,
            "base_size": self.base_size,
            "scale_ratio": self.scale_ratio,
            "sizes": {"h1": self.h1, "h2": self.h2, "h3": self.h3, "h4": self.h4,
                       "h5": self.h5, "h6": self.h6, "body": self.body,
                       "small": self.small, "caption": self.caption},
            "line_height": self.line_height,
            "letter_spacing": self.letter_spacing,
        }


@dataclass
class SpacingSystem:
    unit: int = 4
    xs: str = "0.25rem"    # 4px
    sm: str = "0.5rem"     # 8px
    md: str = "1rem"       # 16px
    lg: str = "1.5rem"     # 24px
    xl: str = "2rem"       # 32px
    xxl: str = "3rem"      # 48px
    xxxl: str = "4rem"     # 64px
    section: str = "6rem"  # 96px

    def to_dict(self) -> dict[str, str]:
        return {"xs": self.xs, "sm": self.sm, "md": self.md, "lg": self.lg,
                "xl": self.xl, "xxl": self.xxl, "xxxl": self.xxxl, "section": self.section}


@dataclass
class DesignSystem:
    name: str = "NOUFEX Design System"
    palette: ColorPalette = field(default_factory=ColorPalette)
    typography: TypographySystem = field(default_factory=TypographySystem)
    spacing: SpacingSystem = field(default_factory=SpacingSystem)
    border_radius: str = "0.5rem"
    border_width: str = "1px"
    shadow_sm: str = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    shadow_md: str = "0 4px 6px -1px rgb(0 0 0 / 0.1)"
    shadow_lg: str = "0 10px 15px -3px rgb(0 0 0 / 0.1)"
    transition_fast: str = "150ms"
    transition_normal: str = "250ms"
    transition_slow: str = "350ms"
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = uuid4().hex[:8]

    def to_css_variables(self) -> str:
        vars = []
        for key, val in self.palette.to_dict().items():
            vars.append(f"  --color-{key}: {val};")
        vars.append(f"  --font-family: {self.typography.font_family};")
        vars.append(f"  --font-mono: {self.typography.font_mono};")
        vars.append(f"  --font-heading: {self.typography.font_heading};")
        for key in ["xs", "sm", "md", "lg", "xl", "xxl", "xxxl", "section"]:
            vars.append(f"  --spacing-{key}: {getattr(self.spacing, key)};")
        vars.append(f"  --radius: {self.border_radius};")
        vars.append(f"  --shadow-sm: {self.shadow_sm};")
        vars.append(f"  --shadow-md: {self.shadow_md};")
        vars.append(f"  --shadow-lg: {self.shadow_lg};")
        vars.append(f"  --transition-fast: {self.transition_fast};")
        vars.append(f"  --transition-normal: {self.transition_normal};")
        return ":root {\n" + "\n".join(vars) + "\n}"

    def to_tailwind_config(self) -> dict[str, Any]:
        colors = {k.replace("_", "-"): v for k, v in self.palette.to_dict().items()}
        return {
            "theme": {
                "extend": {
                    "colors": colors,
                    "fontFamily": {
                        "sans": [self.typography.font_family.split(",")[0].strip().strip('"').strip("'")],
                        "mono": [self.typography.font_mono.split(",")[0].strip().strip('"').strip("'")],
                        "heading": [self.typography.font_heading.split(",")[0].strip().strip('"').strip("'")],
                    },
                    "borderRadius": {"DEFAULT": self.border_radius},
                    "boxShadow": {
                        "sm": self.shadow_sm,
                        "md": self.shadow_md,
                        "lg": self.shadow_lg,
                    },
                    "transitionDuration": {
                        "fast": self.transition_fast,
                        "normal": self.transition_normal,
                        "slow": self.transition_slow,
                    },
                }
            }
        }


@dataclass
class GeneratedComponent:
    html: str
    css: str = ""
    js: str = ""
    framework: DesignFramework = DesignFramework.tailwind
    component_type: ComponentType = ComponentType.custom
    design_system: DesignSystem | None = None
    preview_url: str = ""
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = uuid4().hex[:8]

    def to_full_html(self) -> str:
        css_link = '<script src="https://cdn.tailwindcss.com"></script>' if self.framework == DesignFramework.tailwind else ""
        style_tag = f"<style>\n{self.css}\n</style>" if self.css else ""
        script_tag = f"<script>\n{self.js}\n</script>" if self.js else ""
        return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NOUFEX Design - {self.component_type.value}</title>
{css_link}
{style_tag}
</head>
<body class="bg-gray-50">
{self.html}
{script_tag}
</body>
</html>"""


@dataclass
class DesignReviewResult:
    score: int
    issues: list[dict[str, Any]]
    suggestions: list[str]
    strengths: list[str]
    accessibility_issues: list[dict[str, Any]]
    performance_notes: list[str]
    responsive_issues: list[str]


@dataclass
class AnimationSpec:
    name: str
    css: str
    html_sample: str
    description: str
    duration: str = "0.3s"
    timing_function: str = "ease-out"
    category: str = "entrance"  # entrance, emphasis, exit, hover, loading


@dataclass
class PageBlueprint:
    layout: str  # single, sidebar, dashboard, landing, blog
    sections: list[dict[str, Any]]
    design_system: DesignSystem = field(default_factory=DesignSystem)
    framework: DesignFramework = DesignFramework.tailwind
    direction: Literal["ltr", "rtl"] = "rtl"
    language: str = "ar"
