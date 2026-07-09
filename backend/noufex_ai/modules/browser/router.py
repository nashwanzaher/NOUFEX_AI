from __future__ import annotations

from fastapi import APIRouter, Depends

from noufex_ai.deps import CurrentUserDep, require_scope
from noufex_ai.modules.browser.schemas import (
    AttachBrowserRequest,
    ClickRequest,
    ClickTextRequest,
    EvaluateRequest,
    GetContentRequest,
    GetHtmlRequest,
    LaunchBrowserRequest,
    NavigateRequest,
    ScreenshotBrowserRequest,
    ScrollRequest,
    SelectOptionRequest,
    TypeTextRequest,
    WaitForSelectorRequest,
)
from noufex_ai.modules.browser.service import BrowserService

router = APIRouter()


def _get_service() -> BrowserService:
    return BrowserService()


@router.post("/launch", summary="Launch a browser instance")
async def launch_browser(payload: LaunchBrowserRequest | None = None, user: CurrentUserDep = None):
    p = payload or LaunchBrowserRequest()
    return await _get_service().launch_browser(
        headless=p.headless,
        viewport_width=p.viewport_width,
        viewport_height=p.viewport_height,
    )


@router.post("/attach", summary="Attach to existing browser via CDP")
async def attach_browser(payload: AttachBrowserRequest, user: CurrentUserDep):
    return await _get_service().attach_browser(payload.cdp_url)


@router.post("/close", summary="Close the browser")
async def close_browser(user: CurrentUserDep):
    return await _get_service().close_browser()


@router.post("/navigate", summary="Navigate to a URL")
async def navigate(payload: NavigateRequest, user: CurrentUserDep):
    return await _get_service().navigate(payload.url)


@router.get("/page", summary="Get current page info")
async def get_page_info(user: CurrentUserDep):
    return await _get_service().get_page_info()


@router.get("/content", summary="Get page text content")
async def get_content(max_length: int = 10000, user: CurrentUserDep = None):
    return await _get_service().get_content(max_length)


@router.get("/html", summary="Get page HTML")
async def get_html(selector: str = "body", user: CurrentUserDep = None):
    return await _get_service().get_html(selector)


@router.post("/click", summary="Click element by CSS selector")
async def click_element(payload: ClickRequest, user: CurrentUserDep):
    return await _get_service().click(payload.selector)


@router.post("/click-text", summary="Click element containing text")
async def click_by_text(payload: ClickTextRequest, user: CurrentUserDep):
    return await _get_service().click_text(payload.text)


@router.post("/type", summary="Type text into field")
async def type_text(payload: TypeTextRequest, user: CurrentUserDep):
    return await _get_service().type_text(payload.selector, payload.text, payload.delay)


@router.post("/select", summary="Select option from dropdown")
async def select_option(payload: SelectOptionRequest, user: CurrentUserDep):
    return await _get_service().select_option(payload.selector, payload.value)


@router.post("/screenshot", summary="Take browser screenshot")
async def take_screenshot(payload: ScreenshotBrowserRequest | None = None, user: CurrentUserDep = None):
    p = payload or ScreenshotBrowserRequest()
    return await _get_service().screenshot(full_page=p.full_page)


@router.post("/evaluate", summary="Execute JavaScript (requires scope: browser:execute)")
async def evaluate(
    payload: EvaluateRequest,
    user: CurrentUserDep = Depends(require_scope("browser:execute")),
):
    return await _get_service().evaluate(payload.expression)


@router.post("/wait", summary="Wait for selector to appear")
async def wait_for_selector(payload: WaitForSelectorRequest, user: CurrentUserDep):
    return await _get_service().wait_for_selector(payload.selector, payload.timeout)


@router.post("/scroll", summary="Scroll the page")
async def scroll(payload: ScrollRequest, user: CurrentUserDep):
    return await _get_service().scroll(payload.x, payload.y)


@router.get("/links", summary="Get all page links")
async def get_links(user: CurrentUserDep):
    return await _get_service().get_links()


@router.get("/forms", summary="Get all page forms")
async def get_forms(user: CurrentUserDep):
    return await _get_service().get_forms()
