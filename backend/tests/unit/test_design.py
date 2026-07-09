from __future__ import annotations

import pytest

from noufex_ai.modules.design.service import DesignService
from noufex_ai.modules.design.schemas import (
    ColorPalette,
    ColorScheme,
    ComponentType,
    DesignFramework,
    DesignSystem,
)


@pytest.fixture
def svc() -> DesignService:
    return DesignService()


class TestDesignSystem:
    def test_default_design_system(self, svc: DesignService):
        ds = svc.get_design_system()
        assert isinstance(ds, DesignSystem)
        assert ds.name == "NOUFEX Design System"
        assert ds.palette.primary == "#3B82F6"

    def test_create_design_system(self, svc: DesignService):
        ds = svc.create_design_system(
            name="Test DS",
            primary_color="#FF0000",
            scheme=ColorScheme.dark,
        )
        assert ds.name == "Test DS"
        assert ds.palette.primary == "#FF0000"

    def test_css_variables(self, svc: DesignService):
        css = svc.generate_css_variables()
        assert ":root" in css
        assert "--color-primary" in css

    def test_tailwind_config(self, svc: DesignService):
        import json
        cfg = json.loads(svc.generate_tailwind_config())
        assert "theme" in cfg
        assert "extend" in cfg["theme"]


class TestColorPalette:
    def test_from_primary(self):
        palette = ColorPalette.from_primary("#3B82F6")
        assert palette.primary == "#3B82F6"
        assert palette.secondary != palette.primary

    def test_dark_scheme(self):
        palette = ColorPalette.from_primary("#3B82F6", ColorScheme.dark)
        assert palette.background.startswith("#0")

    def test_to_dict(self):
        palette = ColorPalette.from_primary("#3B82F6")
        d = palette.to_dict()
        assert "primary" in d
        assert "secondary" in d
        assert len(d) >= 10


class TestComponentGeneration:
    def test_button(self, svc: DesignService):
        comp = svc.generate_component("button", {"label": "Click me"})
        assert comp.component_type == ComponentType.button
        assert "Click me" in comp.html
        assert "tailwindcss" in comp.html.lower() or "bg-" in comp.html

    def test_card(self, svc: DesignService):
        comp = svc.generate_component("card", {"title": "My Card"})
        assert comp.component_type == ComponentType.card
        assert "My Card" in comp.html

    def test_hero(self, svc: DesignService):
        comp = svc.generate_component("hero", {"title": "Welcome"})
        assert comp.component_type == ComponentType.hero
        assert "Welcome" in comp.html

    def test_footer(self, svc: DesignService):
        comp = svc.generate_component("footer")
        assert comp.component_type == ComponentType.footer

    def test_unknown_component(self, svc: DesignService):
        comp = svc.generate_component("nonexistent")
        assert "Unknown component type" in comp.html

    def test_all_component_types(self, svc: DesignService):
        types = [
            "button", "card", "navbar", "hero", "stats", "feature_grid",
            "testimonial", "pricing", "form", "footer", "modal", "tabs",
            "avatar", "alert", "badge", "progress", "table", "stat_card",
        ]
        for ct in types:
            comp = svc.generate_component(ct)
            assert comp.html, f"Empty HTML for component type: {ct}"


class TestPageGeneration:
    def test_landing_page(self, svc: DesignService):
        page = svc.generate_landing_page()
        assert "<!DOCTYPE html>" in page.html
        assert "rtl" in page.html

    def test_dashboard(self, svc: DesignService):
        page = svc.generate_dashboard()
        assert "<!DOCTYPE html>" in page.html
        assert "لوحة التحكم" in page.html

    def test_auth_page(self, svc: DesignService):
        page = svc.generate_page_from_description("login page")
        assert "تسجيل الدخول" in page.html

    def test_blog_page(self, svc: DesignService):
        page = svc.generate_page_from_description("blog")
        assert "المدونة" in page.html

    def test_shop_page(self, svc: DesignService):
        page = svc.generate_page_from_description("shop products")
        assert "المتجر" in page.html


class TestUIReview:
    def test_review_good_html(self, svc: DesignService):
        html = '<html><body><img src="test.jpg" alt="test"><h1>Hello</h1><p>World</p></body></html>'
        result = svc.review_ui(html)
        assert result.score > 0
        assert isinstance(result.suggestions, list)

    def test_score_html(self, svc: DesignService):
        html = '<html><body><h1>Hello</h1></body></html>'
        score = svc.score_ui(html)
        assert 0 <= score <= 100


class TestAnimations:
    def test_list_animations(self, svc: DesignService):
        anims = svc.list_animations()
        assert len(anims) > 10
        assert all("name" in a for a in anims)

    def test_get_all_css(self, svc: DesignService):
        css = svc.get_animation_css()
        assert "@keyframes" in css

    def test_get_specific_animation(self, svc: DesignService):
        anims = svc.list_animations()
        first_name = anims[0]["name"]
        css = svc.get_animation_css(first_name)
        assert "@keyframes" in css or "animation" in css
