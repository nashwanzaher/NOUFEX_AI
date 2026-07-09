from __future__ import annotations

from fastapi import APIRouter, Query

from noufex_ai.deps import CurrentUserDep
from noufex_ai.modules.design.router_schemas import (
    CreateDesignSystemRequest,
    GenerateColorPaletteRequest,
    GenerateComponentRequest,
    GenerateDashboardRequest,
    GenerateLandingPageRequest,
    GeneratePageRequest,
    GetAnimationCSSRequest,
    ReviewUIRequest,
    ScoreUIRequest,
)
from noufex_ai.modules.design.service import DesignService

router = APIRouter()


def _get_service() -> DesignService:
    return DesignService()


@router.get("/design-system", summary="Get current design system")
async def get_design_system(user: CurrentUserDep):
    return _get_service().get_design_system()


@router.post("/design-system", summary="Create or update design system")
async def create_design_system(payload: CreateDesignSystemRequest, user: CurrentUserDep):
    ds = _get_service().create_design_system(
        name=payload.name,
        primary_color=payload.primary_color,
        scheme=payload.scheme,
        font_family=payload.font_family,
    )
    return ds


@router.get("/design-system/css-variables", summary="Get CSS variables for design system")
async def get_css_variables(user: CurrentUserDep):
    return {"css": _get_service().generate_css_variables()}


@router.get("/design-system/tailwind-config", summary="Get Tailwind CSS config")
async def get_tailwind_config(user: CurrentUserDep):
    return {"config": _get_service().generate_tailwind_config()}


@router.post("/color-palette", summary="Generate a color palette from a primary color")
async def generate_color_palette(payload: GenerateColorPaletteRequest, user: CurrentUserDep):
    palette = _get_service().generate_color_palette(
        primary=payload.primary,
        scheme=payload.scheme,
    )
    return palette


@router.post("/components", summary="Generate a UI component")
async def generate_component(payload: GenerateComponentRequest, user: CurrentUserDep):
    component = _get_service().generate_component(
        component_type=payload.type,
        params=payload.params,
    )
    return component


@router.post("/pages/landing", summary="Generate a landing page")
async def generate_landing_page(payload: GenerateLandingPageRequest, user: CurrentUserDep):
    page = _get_service().generate_landing_page(
        brand=payload.brand,
        hero_title=payload.hero_title,
        hero_subtitle=payload.hero_subtitle,
        include_features=payload.include_features,
        include_stats=payload.include_stats,
        include_testimonials=payload.include_testimonials,
        include_pricing=payload.include_pricing,
        include_contact=payload.include_contact,
    )
    return page


@router.post("/pages/dashboard", summary="Generate a dashboard page")
async def generate_dashboard(payload: GenerateDashboardRequest, user: CurrentUserDep):
    page = _get_service().generate_dashboard(
        title=payload.title,
        stat_cards=payload.stat_cards,
        include_table=payload.include_table,
        include_chart=payload.include_chart,
    )
    return page


@router.post("/pages/from-description", summary="Generate a page from a natural language description")
async def generate_page_from_description(payload: GeneratePageRequest, user: CurrentUserDep):
    page = _get_service().generate_page_from_description(
        description=payload.description,
    )
    return page


@router.post("/review", summary="Review UI HTML/CSS/JS")
async def review_ui(payload: ReviewUIRequest, user: CurrentUserDep):
    result = _get_service().review_ui(
        html=payload.html,
        css=payload.css,
        js=payload.js,
    )
    return result


@router.post("/review/score", summary="Score UI quality (0-100)")
async def score_ui(payload: ScoreUIRequest, user: CurrentUserDep):
    score = _get_service().score_ui(html=payload.html)
    return {"score": score}


@router.get("/animations", summary="List all available animations")
async def list_animations(user: CurrentUserDep):
    return _get_service().list_animations()


@router.get("/animations/css", summary="Get CSS for all or a specific animation")
async def get_animation_css(
    name: str = Query(None, description="Animation name (omit for all)"),
    user: CurrentUserDep = None,  # type: ignore
):
    css = _get_service().get_animation_css(name)
    return {"css": css}
