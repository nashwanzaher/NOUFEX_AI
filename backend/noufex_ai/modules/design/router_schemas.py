from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from noufex_ai.modules.design.schemas import ColorScheme, ComponentType


class CreateDesignSystemRequest(BaseModel):
    name: str = Field("NOUFEX Design System", description="Design system name")
    primary_color: str = Field("#3B82F6", description="Primary color hex", pattern=r"^#[0-9A-Fa-f]{6}$")
    scheme: str = Field("light", description="Color scheme")
    font_family: str = Field("Inter, system-ui, sans-serif", description="Font family")


class GenerateColorPaletteRequest(BaseModel):
    primary: str = Field("#3B82F6", description="Primary color hex", pattern=r"^#[0-9A-Fa-f]{6}$")
    scheme: str = Field("light", description="Color scheme: light, dark, midnight, sunset, pastel, corporate, ocean, forest, autumn, spring, sepia, contrast")


class GenerateComponentRequest(BaseModel):
    type: str = Field(..., description="Component type", examples=["button", "card", "navbar", "hero"])
    params: dict[str, Any] | None = Field(None, description="Component-specific parameters")


class GenerateLandingPageRequest(BaseModel):
    brand: str = Field("NOUFEX", description="Brand name")
    hero_title: str = Field("حلول ذكية لمستقبل أفضل", description="Hero section title")
    hero_subtitle: str = Field("نقدم أفضل الحلول التقنية المبتكرة", description="Hero section subtitle")
    include_features: bool = Field(True, description="Include features section")
    include_stats: bool = Field(True, description="Include stats section")
    include_testimonials: bool = Field(True, description="Include testimonials section")
    include_pricing: bool = Field(False, description="Include pricing section")
    include_contact: bool = Field(True, description="Include contact form")


class GenerateDashboardRequest(BaseModel):
    title: str = Field("لوحة التحكم", description="Dashboard title")
    stat_cards: int = Field(4, description="Number of stat cards", ge=1, le=12)
    include_table: bool = Field(True, description="Include data table")
    include_chart: bool = Field(True, description="Include chart area")


class GeneratePageRequest(BaseModel):
    description: str = Field(..., description="Description of the page (login, blog, shop, contact, email, resume)")


class ReviewUIRequest(BaseModel):
    html: str = Field(..., description="HTML content to review")
    css: str = Field("", description="Optional CSS to review")
    js: str = Field("", description="Optional JavaScript to review")


class ScoreUIRequest(BaseModel):
    html: str = Field(..., description="HTML content to score")


class GetAnimationCSSRequest(BaseModel):
    name: str | None = Field(None, description="Animation name (omit for all)")
