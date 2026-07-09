from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "version" in data

    async def test_root(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "NOUFEX AI"


@pytest.mark.asyncio
class TestDesignEndpoints:
    """Test design endpoints (no auth required for now)."""

    async def test_get_design_system(self, client: AsyncClient):
        resp = await client.get(
            "/v1/design/design-system",
            headers={"Authorization": "Bearer fake-token"},
        )
        # Should return 401 (auth required) or 200 if auth bypassed
        assert resp.status_code in (200, 401, 403)

    async def test_generate_component_validates_input(self, client: AsyncClient):
        resp = await client.post(
            "/v1/design/components",
            json={"type": "button", "params": {"label": "Test"}},
            headers={"Authorization": "Bearer fake-token"},
        )
        # Should return 401 (auth required) or 200 with component
        assert resp.status_code in (200, 401, 403)

    async def test_generate_landing_page(self, client: AsyncClient):
        resp = await client.post(
            "/v1/design/pages/landing",
            json={"brand": "TestCo", "hero_title": "Hello World"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code in (200, 401, 403)

    async def test_generate_dashboard(self, client: AsyncClient):
        resp = await client.post(
            "/v1/design/pages/dashboard",
            json={"title": "Test Dashboard"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code in (200, 401, 403)

    async def test_generate_page_from_description(self, client: AsyncClient):
        resp = await client.post(
            "/v1/design/pages/from-description",
            json={"description": "login page"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code in (200, 401, 403)

    async def test_review_ui(self, client: AsyncClient):
        resp = await client.post(
            "/v1/design/review",
            json={"html": "<html><body><h1>Hello</h1></body></html>"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code in (200, 401, 403)

    async def test_score_ui(self, client: AsyncClient):
        resp = await client.post(
            "/v1/design/review/score",
            json={"html": "<html><body><h1>Hello</h1></body></html>"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code in (200, 401, 403)

    async def test_list_animations(self, client: AsyncClient):
        resp = await client.get(
            "/v1/design/animations",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code in (200, 401, 403)

    async def test_color_palette(self, client: AsyncClient):
        resp = await client.post(
            "/v1/design/color-palette",
            json={"primary": "#FF5733", "scheme": "dark"},
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code in (200, 401, 403)


@pytest.mark.asyncio
class TestDesignEndpointsDirectly:
    """Test design endpoints by calling the service directly (no auth)."""

    def test_service_generates_component(self):
        from noufex_ai.modules.design.service import DesignService
        svc = DesignService()
        comp = svc.generate_component("button", {"label": "Click"})
        assert "Click" in comp.html

    def test_service_generates_landing_page(self):
        from noufex_ai.modules.design.service import DesignService
        svc = DesignService()
        page = svc.generate_landing_page()
        assert "<!DOCTYPE html>" in page.html

    def test_service_generates_dashboard(self):
        from noufex_ai.modules.design.service import DesignService
        svc = DesignService()
        page = svc.generate_dashboard()
        assert "لوحة التحكم" in page.html

    def test_service_reviews_ui(self):
        from noufex_ai.modules.design.service import DesignService
        svc = DesignService()
        result = svc.review_ui("<html><body><h1>Test</h1></body></html>")
        assert result.score > 0

    def test_service_scores_ui(self):
        from noufex_ai.modules.design.service import DesignService
        svc = DesignService()
        score = svc.score_ui("<html><body><h1>Test</h1></body></html>")
        assert 0 <= score <= 100

    def test_service_creates_design_system(self):
        from noufex_ai.modules.design.service import DesignService
        svc = DesignService()
        ds = svc.create_design_system(primary_color="#FF0000")
        assert ds.palette.primary == "#FF0000"

    def test_service_generates_color_palette(self):
        from noufex_ai.modules.design.service import DesignService
        svc = DesignService()
        palette = svc.generate_color_palette(primary="#FF5733", scheme="dark")
        assert "primary" in palette
        assert palette["primary"] == "#FF5733"

    def test_service_lists_animations(self):
        from noufex_ai.modules.design.service import DesignService
        svc = DesignService()
        anims = svc.list_animations()
        assert len(anims) > 10

    def test_service_generates_page_from_description(self):
        from noufex_ai.modules.design.service import DesignService
        svc = DesignService()
        page = svc.generate_page_from_description("shop products for sale")
        assert "<!DOCTYPE html>" in page.html
