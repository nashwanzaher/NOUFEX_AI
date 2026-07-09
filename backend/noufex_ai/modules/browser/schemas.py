from __future__ import annotations

from pydantic import BaseModel, Field


class LaunchBrowserRequest(BaseModel):
    headless: bool = Field(False, description="Run in headless mode")
    cdp_url: str | None = Field(None, description="Connect to existing browser via CDP URL")
    viewport_width: int = Field(1280, description="Viewport width")
    viewport_height: int = Field(720, description="Viewport height")


class AttachBrowserRequest(BaseModel):
    cdp_url: str = Field(..., description="Chrome DevTools Protocol URL to attach to")


class NavigateRequest(BaseModel):
    url: str = Field(..., description="URL to navigate to")


class ClickRequest(BaseModel):
    selector: str = Field(..., description="CSS selector of element to click")


class ClickTextRequest(BaseModel):
    text: str = Field(..., description="Visible text to find and click")


class TypeTextRequest(BaseModel):
    selector: str = Field(..., description="CSS selector of input element")
    text: str = Field(..., description="Text to type")
    delay: float = Field(0, description="Delay between keystrokes in ms")


class SelectOptionRequest(BaseModel):
    selector: str = Field(..., description="CSS selector of select element")
    value: str = Field(..., description="Option value to select")


class ScreenshotBrowserRequest(BaseModel):
    full_page: bool = Field(False, description="Capture full page")


class EvaluateRequest(BaseModel):
    expression: str = Field(..., description="JavaScript expression to evaluate")
    arg: str | None = Field(None, description="Optional argument to pass")


class WaitForSelectorRequest(BaseModel):
    selector: str = Field(..., description="CSS selector to wait for")
    timeout: int = Field(30000, description="Timeout in milliseconds", ge=1000, le=120000)


class ScrollRequest(BaseModel):
    x: int = Field(0, description="Horizontal scroll amount")
    y: int = Field(500, description="Vertical scroll amount")


class GetContentRequest(BaseModel):
    selector: str = Field("body", description="CSS selector to get content from")


class GetHtmlRequest(BaseModel):
    selector: str = Field("body", description="CSS selector to get HTML from")
