from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnimationDef:
    name: str
    css: str
    description: str
    category: str  # entrance, emphasis, exit, hover, loading, attention


class AnimationEngine:
    """CSS Animation Engine - generates production-ready animations."""

    # ── Entrance Animations ────────────────────────────────────────────

    @staticmethod
    def fade_in(direction: str = "up", duration: str = "0.5s") -> AnimationDef:
        transforms = {
            "up": "translateY(20px)",
            "down": "translateY(-20px)",
            "left": "translateX(20px)",
            "right": "translateX(-20px)",
            "none": "translateY(0)",
        }
        t = transforms.get(direction, "translateY(20px)")
        return AnimationDef(
            name=f"fadeIn{direction.capitalize() if direction != 'none' else ''}",
            css=f"""@keyframes fadeIn{direction.capitalize() if direction != 'none' else ''} {{
  from {{ opacity: 0; transform: {t}; }}
  to {{ opacity: 1; transform: translateY(0) translateX(0); }}
}}
.animate-fade-in-{direction} {{
  animation: fadeIn{direction.capitalize() if direction != 'none' else ''} {duration} ease-out forwards;
}}""",
            description=f"Fade in with {direction} movement",
            category="entrance",
        )

    @staticmethod
    def slide_in(direction: str = "right", duration: str = "0.4s") -> AnimationDef:
        start_pos = {"right": "translateX(100%)", "left": "translateX(-100%)",
                     "top": "translateY(-100%)", "bottom": "translateY(100%)"}
        s = start_pos.get(direction, "translateX(100%)")
        return AnimationDef(
            name=f"slideIn{direction.capitalize()}",
            css=f"""@keyframes slideIn{direction.capitalize()} {{
  from {{ transform: {s}; opacity: 0; }}
  to {{ transform: translateX(0) translateY(0); opacity: 1; }}
}}
.animate-slide-in-{direction} {{
  animation: slideIn{direction.capitalize()} {duration} cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}""",
            description=f"Slide in from {direction}",
            category="entrance",
        )

    @staticmethod
    def scale_in(duration: str = "0.3s") -> AnimationDef:
        return AnimationDef(
            name="scaleIn",
            css=f"""@keyframes scaleIn {{
  from {{ opacity: 0; transform: scale(0.95); }}
  to {{ opacity: 1; transform: scale(1); }}
}}
.animate-scale-in {{
  animation: scaleIn {duration} cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}""",
            description="Scale in from smaller size",
            category="entrance",
        )

    @staticmethod
    def stagger_container(duration: str = "0.3s", delay_between: str = "0.1s") -> AnimationDef:
        return AnimationDef(
            name="staggerContainer",
            css=f"""@keyframes fadeInUp {{
  from {{ opacity: 0; transform: translateY(20px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
.stagger-container > * {{
  animation: fadeInUp {duration} ease-out forwards;
}}
.stagger-container > *:nth-child(1) {{ animation-delay: 0s; }}
.stagger-container > *:nth-child(2) {{ animation-delay: {delay_between}; }}
.stagger-container > *:nth-child(3) {{ animation-delay: calc({delay_between} * 2); }}
.stagger-container > *:nth-child(4) {{ animation-delay: calc({delay_between} * 3); }}
.stagger-container > *:nth-child(5) {{ animation-delay: calc({delay_between} * 4); }}
.stagger-container > *:nth-child(6) {{ animation-delay: calc({delay_between} * 5); }}
.stagger-container > *:nth-child(7) {{ animation-delay: calc({delay_between} * 6); }}
.stagger-container > *:nth-child(8) {{ animation-delay: calc({delay_between} * 7); }}""",
            description="Staggered animation for children elements",
            category="entrance",
        )

    # ── Emphasis / Attention ───────────────────────────────────────────

    @staticmethod
    def pulse(duration: str = "2s") -> AnimationDef:
        return AnimationDef(
            name="pulse",
            css=f"""@keyframes pulse {{
  0%, 100% {{ transform: scale(1); }}
  50% {{ transform: scale(1.05); }}
}}
.animate-pulse-custom {{
  animation: pulse {duration} ease-in-out infinite;
}}""",
            description="Gentle pulsing effect for attention",
            category="attention",
        )

    @staticmethod
    def bounce(duration: str = "1s") -> AnimationDef:
        return AnimationDef(
            name="bounce",
            css=f"""@keyframes bounce {{
  0%, 100% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-10px); }}
}}
.animate-bounce-custom {{
  animation: bounce {duration} cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
}}""",
            description="Bouncing effect",
            category="attention",
        )

    @staticmethod
    def shimmer(duration: str = "2s") -> AnimationDef:
        return AnimationDef(
            name="shimmer",
            css=f"""@keyframes shimmer {{
  0% {{ background-position: -200% 0; }}
  100% {{ background-position: 200% 0; }}
}}
.animate-shimmer {{
  background: linear-gradient(90deg, transparent 25%, rgba(255,255,255,0.2) 50%, transparent 75%);
  background-size: 200% 100%;
  animation: shimmer {duration} ease-in-out infinite;
}}
.skeleton {{
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer {duration} ease-in-out infinite;
  border-radius: 0.5rem;
}}""",
            description="Shimmer loading skeleton effect",
            category="loading",
        )

    @staticmethod
    def spinner(duration: str = "1s") -> AnimationDef:
        return AnimationDef(
            name="spinner",
            css=f"""@keyframes spin {{
  from {{ transform: rotate(0deg); }}
  to {{ transform: rotate(360deg); }}
}}
.animate-spinner {{
  animation: spin {duration} linear infinite;
}}
.spinner {{
  width: 24px;
  height: 24px;
  border: 3px solid #e5e7eb;
  border-top-color: #3B82F6;
  border-radius: 50%;
  animation: spin {duration} linear infinite;
}}""",
            description="Loading spinner animation",
            category="loading",
        )

    # ── Hover Effects ──────────────────────────────────────────────────

    @staticmethod
    def hover_lift(distance: str = "4px", duration: str = "0.2s") -> AnimationDef:
        return AnimationDef(
            name="hoverLift",
            css=f""".hover-lift {{
  transition: transform {duration} ease-out, box-shadow {duration} ease-out;
}}
.hover-lift:hover {{
  transform: translateY(-{distance});
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}}""",
            description="Element lifts up on hover with shadow",
            category="hover",
        )

    @staticmethod
    def hover_glow(color: str = "rgba(59, 130, 246, 0.3)") -> AnimationDef:
        return AnimationDef(
            name="hoverGlow",
            css=f""".hover-glow {{
  transition: box-shadow 0.3s ease-out;
}}
.hover-glow:hover {{
  box-shadow: 0 0 20px {color}, 0 0 40px {color};
}}""",
            description="Glowing effect on hover",
            category="hover",
        )

    @staticmethod
    def hover_scale(scale: str = "1.05", duration: str = "0.2s") -> AnimationDef:
        return AnimationDef(
            name="hoverScale",
            css=f""".hover-scale {{
  transition: transform {duration} ease-out;
}}
.hover-scale:hover {{
  transform: scale({scale});
}}""",
            description="Scale up on hover",
            category="hover",
        )

    # ── Micro-interactions ─────────────────────────────────────────────

    @staticmethod
    def button_press() -> AnimationDef:
        return AnimationDef(
            name="buttonPress",
            css=""".btn-press {
  transition: transform 0.1s ease-out;
}
.btn-press:active {
  transform: scale(0.95);
}""",
            description="Button press effect on click",
            category="hover",
        )

    @staticmethod
    def ripple() -> AnimationDef:
        return AnimationDef(
            name="ripple",
            css=""".ripple {
  position: relative;
  overflow: hidden;
}
.ripple::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  width: 100px;
  height: 100px;
  margin-top: -50px;
  margin-left: -50px;
  top: 50%;
  left: 50%;
  transform: scale(0);
  opacity: 0;
}
.ripple:active::after {
  animation: rippleEffect 0.6s ease-out;
}
@keyframes rippleEffect {
  from { transform: scale(0); opacity: 0.5; }
  to { transform: scale(4); opacity: 0; }
}""",
            description="Material ripple effect on click",
            category="hover",
        )

    # ── Transition Generators ──────────────────────────────────────────

    @staticmethod
    def smooth_transition(properties: str = "all", duration: str = "0.3s") -> str:
        return f"""transition: {properties} {duration} cubic-bezier(0.4, 0, 0.2, 1);"""

    @staticmethod
    def page_transition() -> AnimationDef:
        return AnimationDef(
            name="pageTransition",
            css=""".page-enter {
  animation: pageEnter 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.page-exit {
  animation: pageExit 0.3s ease-in forwards;
}
@keyframes pageEnter {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes pageExit {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(-10px); }
}""",
            description="Page transition enter/exit animations",
            category="entrance",
        )

    @staticmethod
    def list_all() -> list[AnimationDef]:
        return [
            AnimationEngine.fade_in(),
            AnimationEngine.fade_in("left"),
            AnimationEngine.fade_in("right"),
            AnimationEngine.fade_in("down"),
            AnimationEngine.fade_in("none"),
            AnimationEngine.slide_in(),
            AnimationEngine.slide_in("left"),
            AnimationEngine.slide_in("top"),
            AnimationEngine.slide_in("bottom"),
            AnimationEngine.scale_in(),
            AnimationEngine.stagger_container(),
            AnimationEngine.pulse(),
            AnimationEngine.bounce(),
            AnimationEngine.shimmer(),
            AnimationEngine.spinner(),
            AnimationEngine.hover_lift(),
            AnimationEngine.hover_glow(),
            AnimationEngine.hover_scale(),
            AnimationEngine.button_press(),
            AnimationEngine.ripple(),
            AnimationEngine.page_transition(),
        ]

    @staticmethod
    def get_css_package() -> str:
        anims = AnimationEngine.list_all()
        css = "/* NOUFEX Animation Engine */\n\n"
        for a in anims:
            css += a.css + "\n\n"
        return css
