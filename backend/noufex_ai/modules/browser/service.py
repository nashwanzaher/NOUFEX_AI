from __future__ import annotations

import base64
import json
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class PageInfo:
    url: str
    title: str
    content_snapshot: str | None = None
    screenshot_b64: str | None = None
    viewport: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "content_length": len(self.content_snapshot) if self.content_snapshot else 0,
        }


class BrowserService:
    """Browser automation service using Playwright.
    
    Mirrors OpenClaw's browser capabilities: managed (headless) and
    attached (existing browser) modes, page interaction, screenshots,
    form filling, and content extraction.
    """

    def __init__(self) -> None:
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        self._attached = False
        self._screenshot_dir = Path(tempfile.gettempdir()) / "noufex_screenshots"
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)

    async def _ensure_playwright(self) -> None:
        if self._playwright is not None:
            return
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
        except ImportError:
            raise ImportError(
                "Playwright not installed. Install with: pip install playwright && playwright install chromium"
            )

    async def launch_browser(
        self,
        headless: bool = False,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        user_data_dir: str | None = None,
    ) -> dict[str, Any]:
        """Launch a managed browser instance."""
        try:
            await self._ensure_playwright()
            if self._browser:
                await self.close_browser()

            launch_options: dict[str, Any] = {
                "headless": headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            }

            if user_data_dir:
                launch_options["user_data_dir"] = user_data_dir

            self._browser = await self._playwright.chromium.launch_persistent_context(
                user_data_dir or tempfile.mkdtemp(prefix="noufex_browser_"),
                headless=headless,
                viewport={"width": viewport_width, "height": viewport_height},
                args=launch_options["args"],
                no_viewport=False,
                ignore_default_args=["--enable-automation"],
            )

            pages = self._browser.pages
            self._page = pages[0] if pages else await self._browser.new_page()
            self._attached = False

            return {
                "success": True,
                "mode": "managed",
                "viewport": {"width": viewport_width, "height": viewport_height},
                "headless": headless,
            }
        except ImportError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Browser launch failed: %s", e)
            return {"success": False, "error": str(e)}

    async def attach_browser(self, ws_endpoint: str) -> dict[str, Any]:
        """Attach to an existing browser via CDP endpoint.
        
        Args:
            ws_endpoint: WebSocket URL like ws://127.0.0.1:9222/devtools/browser/...
        """
        try:
            await self._ensure_playwright()
            if self._browser:
                await self.close_browser()

            from playwright.async_api import async_playwright

            self._browser = await self._playwright.chromium.connect_over_cdp(ws_endpoint)
            pages = self._browser.contexts[0].pages if self._browser.contexts else []
            self._page = pages[0] if pages else await self._browser.new_page()
            self._attached = True

            return {"success": True, "mode": "attached", "endpoint": ws_endpoint}
        except ImportError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("Browser attach failed: %s", e)
            return {"success": False, "error": str(e)}

    async def close_browser(self) -> dict[str, Any]:
        """Close the browser."""
        try:
            if self._browser:
                if self._attached:
                    await self._browser.close()
                else:
                    await self._browser.close()
                self._browser = None
                self._context = None
                self._page = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def navigate(self, url: str, wait_until: str = "load") -> dict[str, Any]:
        """Navigate to a URL with validation."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            from noufex_ai.modules.security.validation import validate_url
            validated_url = validate_url(url)
            response = await self._page.goto(validated_url, wait_until=wait_until, timeout=30000)
            status = response.status if response else None
            return {"success": True, "url": self._page.url, "status_code": status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_page_info(self) -> dict[str, Any]:
        """Get current page URL, title, and metadata."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            url = self._page.url
            title = await self._page.title()
            return {
                "success": True,
                "url": url,
                "title": title,
                "viewport": await self._page.evaluate(
                    "() => ({ width: window.innerWidth, height: window.innerHeight })"
                ),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_content(self, max_length: int = 10000) -> dict[str, Any]:
        """Extract page text content."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            content = await self._page.evaluate("() => document.body.innerText")
            if content and len(content) > max_length:
                content = content[:max_length] + "... [truncated]"
            return {"success": True, "content": content or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_html(self, selector: str = "body") -> dict[str, Any]:
        """Get HTML content of a page or element."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            if selector == "body" or selector == "html":
                html = await self._page.content()
            else:
                element = await self._page.query_selector(selector)
                if not element:
                    return {"success": False, "error": f"Element '{selector}' not found"}
                html = await element.inner_html()
            return {"success": True, "html": html[:50000]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click(self, selector: str, timeout: int = 5000) -> dict[str, Any]:
        """Click an element by CSS selector."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            await self._page.click(selector, timeout=timeout)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click_text(self, text: str, timeout: int = 5000) -> dict[str, Any]:
        """Click an element containing specific text."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            element = self._page.get_by_text(text, exact=False)
            await element.click(timeout=timeout)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def type_text(
        self, selector: str, text: str, delay: float = 0.05
    ) -> dict[str, Any]:
        """Type text into an input field."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            await self._page.fill(selector, "")
            await self._page.type(selector, text, delay=delay)
            return {"success": True, "selector": selector, "text_length": len(text)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def select_option(
        self, selector: str, value: str | list[str]
    ) -> dict[str, Any]:
        """Select an option in a dropdown."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            await self._page.select_option(selector, value)
            return {"success": True, "selector": selector, "value": value}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def screenshot(self, full_page: bool = False) -> dict[str, Any]:
        """Take a screenshot of the current page."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            filename = f"browser_{uuid4().hex[:8]}.png"
            filepath = str(self._screenshot_dir / filename)

            await self._page.screenshot(path=filepath, full_page=full_page)

            with open(filepath, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            viewport = await self._page.evaluate(
                "() => ({ width: window.innerWidth, height: window.innerHeight })"
            )

            return {
                "success": True,
                "data": img_b64,
                "format": "png",
                "filepath": filepath,
                "viewport": viewport,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def evaluate(self, script: str) -> dict[str, Any]:
        """Execute JavaScript in the page context with validation."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            from noufex_ai.modules.security.validation import validate_javascript
            validated_script = validate_javascript(script)
            result = await self._page.evaluate(validated_script)
            return {"success": True, "result": str(result)[:5000]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def wait_for_selector(
        self, selector: str, timeout: int = 10000, state: str = "visible"
    ) -> dict[str, Any]:
        """Wait for an element to appear."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            await self._page.wait_for_selector(
                selector, timeout=timeout, state=state
            )
            return {"success": True, "selector": selector, "state": state}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def scroll(self, x: int = 0, y: int = 500) -> dict[str, Any]:
        """Scroll the page."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            await self._page.evaluate("window.scrollBy(arguments[0], arguments[1])", [x, y])
            return {"success": True, "scrolled_by": {"x": x, "y": y}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_links(self) -> dict[str, Any]:
        """Get all links on the page."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            links = await self._page.evaluate(
                """() => Array.from(document.querySelectorAll('a[href]'))
                    .map(a => ({ text: a.innerText.trim(), href: a.href }))
                    .filter(l => l.text && l.href)"""
            )
            return {"success": True, "links": links[:200]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_forms(self) -> dict[str, Any]:
        """Get all forms and their fields on the page."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            forms = await self._page.evaluate(
                """() => Array.from(document.querySelectorAll('form')).map((f, i) => ({
                    index: i,
                    action: f.action,
                    method: f.method,
                    fields: Array.from(f.querySelectorAll('input, select, textarea')).map(el => ({
                        name: el.name,
                        type: el.type || el.tagName.toLowerCase(),
                        placeholder: el.placeholder || '',
                        value: el.value || '',
                        required: el.required || false,
                    })),
                }))"""
            )
            return {"success": True, "forms": forms}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def is_running(self) -> bool:
        """Check if browser is still running."""
        if not self._page:
            return False
        try:
            await self._page.evaluate("1")
            return True
        except Exception:
            return False

    async def go_back(self) -> dict[str, Any]:
        """Go back in history."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            await self._page.go_back()
            return {"success": True, "url": self._page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def go_forward(self) -> dict[str, Any]:
        """Go forward in history."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            await self._page.go_forward()
            return {"success": True, "url": self._page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def reload(self) -> dict[str, Any]:
        """Reload the current page."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            await self._page.reload()
            return {"success": True, "url": self._page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def download_file(self, url: str, download_path: str | None = None) -> dict[str, Any]:
        """Download a file from a URL using the browser session."""
        if not self._page:
            return {"success": False, "error": "Browser not launched"}
        try:
            from noufex_ai.modules.security.validation import validate_url
            validated_url = validate_url(url)

            import httpx
            cookies = await self._page.context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}

            async with httpx.AsyncClient(cookies=cookie_dict, follow_redirects=True) as client:
                response = await client.get(validated_url, timeout=30)
                response.raise_for_status()

            dest = download_path or str(self._screenshot_dir / validated_url.split("/")[-1])
            with open(dest, "wb") as f:
                f.write(response.content)

            return {"success": True, "path": dest, "size_bytes": len(response.content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
