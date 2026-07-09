from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


@dataclass
class SkillDefinition:
    """Definition of a skill/tool that the agent can call."""
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Coroutine[Any, Any, Any]] | Callable[..., Any]
    category: str = "general"
    requires_confirmation: bool = False
    rate_limit_per_minute: int = 60

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert to OpenAI function-calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": [
                        k for k, v in self.parameters.items()
                        if isinstance(v, dict) and v.get("required", False)
                    ],
                },
            },
        }


class SkillRegistry:
    """Registry of all agent skills/tools.
    
    Skills are registered here and made available to the LLM via
    function calling. This mirrors OpenClaw's skill system.
    """

    def __init__(self) -> None:
        self._skills: dict[str, SkillDefinition] = {}
        self._computer_service = None
        self._browser_service = None
        self._design_service = None

    def set_services(self, computer_service: Any = None, browser_service: Any = None, design_service: Any = None) -> None:
        """Set the computer, browser, and design service instances."""
        if computer_service is not None:
            self._computer_service = computer_service
        if browser_service is not None:
            self._browser_service = browser_service
        if design_service is not None:
            self._design_service = design_service

    def register(self, skill: SkillDefinition) -> None:
        """Register a skill."""
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> None:
        """Remove a skill."""
        self._skills.pop(name, None)

    def get(self, name: str) -> SkillDefinition | None:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self, category: str | None = None) -> list[SkillDefinition]:
        """List all registered skills, optionally filtered by category."""
        if category:
            return [s for s in self._skills.values() if s.category == category]
        return list(self._skills.values())

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Convert all skills to OpenAI tool definitions."""
        return [s.to_openai_tool() for s in self._skills.values()]

    async def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a skill by name with given arguments.
        
        Returns standardized result dict with success/error info.
        """
        skill = self.get(name)
        if not skill:
            return {"success": False, "error": f"Unknown skill: {name}"}

        try:
            if name.startswith("computer_"):
                if not self._computer_service:
                    return {"success": False, "error": "Computer service not initialized"}
                result = await self._execute_computer_skill(name, arguments)
            elif name.startswith("browser_"):
                if not self._browser_service:
                    return {"success": False, "error": "Browser service not initialized. Launch browser first."}
                result = await self._execute_browser_skill(name, arguments)
            elif name.startswith("web_"):
                result = await self._execute_web_skill(name, arguments)
            elif name.startswith("design_"):
                if not self._design_service:
                    return {"success": False, "error": "Design service not initialized"}
                result = self._execute_design_skill(name, arguments)
            else:
                result = skill.handler(**arguments)

            # If result is a coroutine (async handler), await it
            if hasattr(result, "__await__"):
                result = await result

            return {
                "success": True,
                "skill": name,
                "result": self._serialize_result(result),
            }
        except Exception as e:
            logger.error("Skill '%s' execution failed: %s", name, e, exc_info=True)
            return {"success": False, "error": str(e)[:1000], "skill": name}

    async def _execute_computer_skill(
        self, name: str, args: dict[str, Any]
    ) -> Any:
        svc = self._computer_service
        skill_map = {
            "computer_list_windows": svc.list_windows,
            "computer_focus_window": lambda: svc.focus_window(**args),
            "computer_move_window": lambda: svc.move_window(**args),
            "computer_open_window": lambda: svc.open_window(**args),
            "computer_close_window": lambda: svc.close_window(**args),
            "computer_get_active_window": svc.get_active_window,
            "computer_get_screen_info": svc.get_screen_info,
            "computer_screenshot": lambda: svc.screenshot(**args),
            "computer_mouse_move": lambda: svc.mouse_move(**args),
            "computer_mouse_click": lambda: svc.mouse_click(**args),
            "computer_mouse_double_click": lambda: svc.mouse_double_click(**args),
            "computer_mouse_right_click": lambda: svc.mouse_right_click(**args),
            "computer_mouse_drag": lambda: svc.mouse_drag(**args),
            "computer_mouse_scroll": lambda: svc.mouse_scroll(**args),
            "computer_mouse_position": svc.mouse_position,
            "computer_keyboard_type": lambda: svc.keyboard_type(**args),
            "computer_keyboard_hotkey": lambda: svc.keyboard_hotkey(**args),
            "computer_keyboard_press": lambda: svc.keyboard_press(**args),
            "computer_list_processes": svc.list_processes,
            "computer_kill_process": lambda: svc.kill_process(**args),
            "computer_get_system_info": svc.get_system_info,
            "computer_run_command": lambda: svc.run_command(**args),
            "computer_list_directory": lambda: svc.list_directory(**args),
            "computer_read_file": lambda: svc.read_file(**args),
            "computer_write_file": lambda: svc.write_file(**args),
        }
        handler = skill_map.get(name)
        if handler:
            result = handler()
            if hasattr(result, "__await__"):
                return await result
            return result
        raise ValueError(f"Unknown computer skill: {name}")

    async def _execute_browser_skill(
        self, name: str, args: dict[str, Any]
    ) -> Any:
        svc = self._browser_service
        skill_map = {
            "browser_launch": lambda: svc.launch_browser(**args),
            "browser_attach": lambda: svc.attach_browser(**args),
            "browser_close": svc.close_browser,
            "browser_navigate": lambda: svc.navigate(**args),
            "browser_get_page_info": svc.get_page_info,
            "browser_get_content": lambda: svc.get_content(**args),
            "browser_get_html": lambda: svc.get_html(**args),
            "browser_click": lambda: svc.click(**args),
            "browser_click_text": lambda: svc.click_text(**args),
            "browser_type_text": lambda: svc.type_text(**args),
            "browser_select_option": lambda: svc.select_option(**args),
            "browser_screenshot": lambda: svc.screenshot(**args),
            "browser_evaluate": lambda: svc.evaluate(**args),
            "browser_wait_for_selector": lambda: svc.wait_for_selector(**args),
            "browser_scroll": lambda: svc.scroll(**args),
            "browser_get_links": svc.get_links,
            "browser_get_forms": svc.get_forms,
            "browser_is_running": svc.is_running,
            "browser_go_back": svc.go_back,
            "browser_go_forward": svc.go_forward,
            "browser_reload": svc.reload,
        }
        handler = skill_map.get(name)
        if handler:
            result = handler()
            if hasattr(result, "__await__"):
                return await result
            return result
        raise ValueError(f"Unknown browser skill: {name}")

    async def _execute_web_skill(
        self, name: str, args: dict[str, Any]
    ) -> Any:
        if name == "web_search":
            return await self._web_search(**args)
        elif name == "web_fetch":
            return await self._web_fetch(**args)
        raise ValueError(f"Unknown web skill: {name}")

    # ── Design Skills ──────────────────────────────────────────────────

    def _execute_design_skill(self, name: str, args: dict[str, Any]) -> Any:
        svc = self._design_service
        skill_map = {
            "design_generate_component": lambda: svc.generate_component(**args),
            "design_generate_landing_page": lambda: svc.generate_landing_page(**args),
            "design_generate_dashboard": lambda: svc.generate_dashboard(**args),
            "design_generate_page": lambda: svc.generate_page_from_description(**args),
            "design_generate_color_palette": lambda: svc.generate_color_palette(**args),
            "design_generate_css_variables": svc.generate_css_variables,
            "design_generate_tailwind_config": svc.generate_tailwind_config,
            "design_create_design_system": lambda: svc.create_design_system(**args),
            "design_get_design_system": svc.get_design_system,
            "design_review_ui": lambda: svc.review_ui(**args),
            "design_score_ui": lambda: svc.score_ui(**args),
            "design_list_animations": svc.list_animations,
            "design_get_animation_css": lambda: svc.get_animation_css(**args),
        }
        handler = skill_map.get(name)
        if handler:
            result = handler()
            if hasattr(result, "__await__"):
                return result  # caller will await via hasattr check
            return result
        raise ValueError(f"Unknown design skill: {name}")

    async def _web_search(self, query: str, num_results: int = 5) -> dict[str, Any]:
        try:
            import httpx
            from noufex_ai.settings import settings

            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                response.raise_for_status()

            import re
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            for i, result in enumerate(soup.select(".result")):
                if i >= num_results:
                    break
                title_el = result.select_one(".result__title a")
                snippet_el = result.select_one(".result__snippet")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": title_el.get("href", ""),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })

            return {"query": query, "results": results, "total": len(results)}
        except Exception as e:
            logger.error("Web search failed: %s", e)
            return {"query": query, "error": str(e), "results": []}

    async def _web_fetch(self, url: str) -> dict[str, Any]:
        try:
            import httpx
            from bs4 import BeautifulSoup

            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            lines = [l for l in text.split("\n") if l.strip()]
            content = "\n".join(lines[:300])

            return {
                "success": True,
                "url": url,
                "title": soup.title.string.strip() if soup.title else "",
                "content": content[:15000],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton registry
_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """Get the global skill registry singleton."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
        _register_default_skills(_registry)
    return _registry


def _register_default_skills(registry: SkillRegistry) -> None:
    """Register all default skills into the registry."""

    # ── Computer: Window Management ──
    registry.register(SkillDefinition(
        name="computer_list_windows",
        description="List all open windows on the desktop with their titles, handles, and positions.",
        parameters={},
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_focus_window",
        description="Bring a window to the foreground by title or handle.",
        parameters={
            "identifier": {
                "type": "string",
                "description": "Window title (partial match) or window handle number",
                "required": True,
            }
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_move_window",
        description="Move and resize a window by title or handle.",
        parameters={
            "identifier": {"type": "string", "description": "Window title or handle", "required": True},
            "x": {"type": "integer", "description": "New X position", "required": True},
            "y": {"type": "integer", "description": "New Y position", "required": True},
            "width": {"type": "integer", "description": "New width (optional)"},
            "height": {"type": "integer", "description": "New height (optional)"},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_open_window",
        description="Open/launch an application or file by name or path.",
        parameters={
            "target": {"type": "string", "description": "Application name, file path, or URL", "required": True},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_close_window",
        description="Close a window by title or process name.",
        parameters={
            "identifier": {"type": "string", "description": "Window title, handle, or process name", "required": True},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_get_active_window",
        description="Get the currently focused window info.",
        parameters={},
        category="computer",
    ))

    # ── Computer: Screen ──
    registry.register(SkillDefinition(
        name="computer_get_screen_info",
        description="Get screen resolution and display info.",
        parameters={},
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_screenshot",
        description="Take a screenshot of the screen or a region. Returns base64 image data that the AI can see.",
        parameters={
            "region": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Optional region [left, top, right, bottom]",
            }
        },
        category="computer",
    ))

    # ── Computer: Mouse ──
    registry.register(SkillDefinition(
        name="computer_mouse_move",
        description="Move the mouse cursor to absolute screen coordinates.",
        parameters={
            "x": {"type": "integer", "description": "X coordinate", "required": True},
            "y": {"type": "integer", "description": "Y coordinate", "required": True},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_mouse_click",
        description="Click at a specific screen position.",
        parameters={
            "x": {"type": "integer", "description": "X coordinate", "required": True},
            "y": {"type": "integer", "description": "Y coordinate", "required": True},
            "button": {"type": "string", "description": "Mouse button: left, right, middle", "enum": ["left", "right", "middle"]},
            "clicks": {"type": "integer", "description": "Number of clicks (1=single, 2=double)"},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_mouse_double_click",
        description="Double-click at a specific screen position.",
        parameters={
            "x": {"type": "integer", "description": "X coordinate", "required": True},
            "y": {"type": "integer", "description": "Y coordinate", "required": True},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_mouse_right_click",
        description="Right-click at a specific screen position.",
        parameters={
            "x": {"type": "integer", "description": "X coordinate", "required": True},
            "y": {"type": "integer", "description": "Y coordinate", "required": True},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_mouse_drag",
        description="Drag the mouse from one position to another.",
        parameters={
            "x1": {"type": "integer", "description": "Start X", "required": True},
            "y1": {"type": "integer", "description": "Start Y", "required": True},
            "x2": {"type": "integer", "description": "End X", "required": True},
            "y2": {"type": "integer", "description": "End Y", "required": True},
            "duration": {"type": "number", "description": "Drag duration in seconds"},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_mouse_scroll",
        description="Scroll the mouse wheel.",
        parameters={
            "clicks": {"type": "integer", "description": "Number of clicks to scroll (positive=up, negative=down)", "required": True},
            "x": {"type": "integer", "description": "X position for scroll"},
            "y": {"type": "integer", "description": "Y position for scroll"},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_mouse_position",
        description="Get the current mouse cursor position.",
        parameters={},
        category="computer",
    ))

    # ── Computer: Keyboard ──
    registry.register(SkillDefinition(
        name="computer_keyboard_type",
        description="Type text at the current cursor position.",
        parameters={
            "text": {"type": "string", "description": "Text to type", "required": True},
            "interval": {"type": "number", "description": "Delay between keystrokes in seconds"},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_keyboard_hotkey",
        description="Press a keyboard shortcut combination (e.g. ctrl+c, alt+tab).",
        parameters={
            "keys": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of keys to press together (e.g. ['ctrl', 'c'])",
                "required": True,
            }
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_keyboard_press",
        description="Press and release a single key.",
        parameters={
            "key": {"type": "string", "description": "Key to press (e.g. enter, tab, escape)", "required": True},
        },
        category="computer",
    ))

    # ── Computer: Processes ──
    registry.register(SkillDefinition(
        name="computer_list_processes",
        description="List running processes on the system.",
        parameters={},
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_kill_process",
        description="Kill a process by PID or name.",
        parameters={
            "pid_or_name": {
                "oneOf": [
                    {"type": "integer", "description": "Process ID"},
                    {"type": "string", "description": "Process name"},
                ],
                "description": "Process ID or name to kill",
                "required": True,
            }
        },
        category="computer",
    ))

    # ── Computer: System ──
    registry.register(SkillDefinition(
        name="computer_get_system_info",
        description="Get system information (OS, CPU, memory, disk).",
        parameters={},
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_run_command",
        description="Run a shell command and return output.",
        parameters={
            "command": {"type": "string", "description": "Shell command to execute", "required": True},
            "timeout": {"type": "integer", "description": "Timeout in seconds"},
        },
        category="computer",
        requires_confirmation=True,
    ))

    # ── Computer: File Operations ──
    registry.register(SkillDefinition(
        name="computer_list_directory",
        description="List files in a directory.",
        parameters={
            "path": {"type": "string", "description": "Directory path (default: current)"},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_read_file",
        description="Read the contents of a text file.",
        parameters={
            "path": {"type": "string", "description": "File path", "required": True},
        },
        category="computer",
    ))
    registry.register(SkillDefinition(
        name="computer_write_file",
        description="Write text content to a file.",
        parameters={
            "path": {"type": "string", "description": "File path", "required": True},
            "content": {"type": "string", "description": "Content to write", "required": True},
        },
        category="computer",
    ))

    # ── Browser ──
    registry.register(SkillDefinition(
        name="browser_launch",
        description="Launch a new browser instance for web automation.",
        parameters={
            "headless": {"type": "boolean", "description": "Run in headless mode (no visible window)"},
            "viewport_width": {"type": "integer", "description": "Browser viewport width"},
            "viewport_height": {"type": "integer", "description": "Browser viewport height"},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_attach",
        description="Attach to an existing browser via CDP WebSocket endpoint.",
        parameters={
            "ws_endpoint": {"type": "string", "description": "CDP WebSocket URL", "required": True},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_close",
        description="Close the browser instance.",
        parameters={},
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_navigate",
        description="Navigate to a URL in the browser.",
        parameters={
            "url": {"type": "string", "description": "URL to navigate to", "required": True},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_get_page_info",
        description="Get current page URL and title.",
        parameters={},
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_get_content",
        description="Extract visible text content from the current page.",
        parameters={
            "max_length": {"type": "integer", "description": "Maximum characters to extract"},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_get_html",
        description="Get HTML content of the page or a specific element.",
        parameters={
            "selector": {"type": "string", "description": "CSS selector (default: body)"},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_click",
        description="Click an element on the page by CSS selector.",
        parameters={
            "selector": {"type": "string", "description": "CSS selector of element to click", "required": True},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_click_text",
        description="Click an element containing specific text.",
        parameters={
            "text": {"type": "string", "description": "Text to search for", "required": True},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_type_text",
        description="Type text into an input field.",
        parameters={
            "selector": {"type": "string", "description": "CSS selector of the input field", "required": True},
            "text": {"type": "string", "description": "Text to type", "required": True},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_select_option",
        description="Select an option in a dropdown menu.",
        parameters={
            "selector": {"type": "string", "description": "CSS selector of the select element", "required": True},
            "value": {
                "oneOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string"}},
                ],
                "description": "Option value(s) to select",
                "required": True,
            },
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_screenshot",
        description="Take a screenshot of the current page. Returns base64 image data.",
        parameters={
            "full_page": {"type": "boolean", "description": "Capture full page or just viewport"},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_evaluate",
        description="Execute JavaScript code in the browser page context.",
        parameters={
            "script": {"type": "string", "description": "JavaScript code to execute", "required": True},
        },
        category="browser",
        requires_confirmation=True,
    ))
    registry.register(SkillDefinition(
        name="browser_wait_for_selector",
        description="Wait for an element to appear on the page.",
        parameters={
            "selector": {"type": "string", "description": "CSS selector to wait for", "required": True},
            "timeout": {"type": "integer", "description": "Timeout in milliseconds"},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_scroll",
        description="Scroll the page by a specified amount.",
        parameters={
            "x": {"type": "integer", "description": "Horizontal scroll amount"},
            "y": {"type": "integer", "description": "Vertical scroll amount"},
        },
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_get_links",
        description="Get all links on the current page.",
        parameters={},
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_get_forms",
        description="Get all forms and their fields on the current page.",
        parameters={},
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_go_back",
        description="Go back to the previous page.",
        parameters={},
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_go_forward",
        description="Go forward to the next page.",
        parameters={},
        category="browser",
    ))
    registry.register(SkillDefinition(
        name="browser_reload",
        description="Reload the current page.",
        parameters={},
        category="browser",
    ))

    # ── Web Skills ──
    registry.register(SkillDefinition(
        name="web_search",
        description="Search the web for information. Returns title, URL, and snippet for each result.",
        parameters={
            "query": {"type": "string", "description": "Search query", "required": True},
            "num_results": {"type": "integer", "description": "Maximum number of results"},
        },
        category="web",
    ))
    registry.register(SkillDefinition(
        name="web_fetch",
        description="Fetch and read the content of a web page.",
        parameters={
            "url": {"type": "string", "description": "URL to fetch", "required": True},
        },
        category="web",
    ))

    # ── Design Skills ──
    registry.register(SkillDefinition(
        name="design_generate_component",
        description="Generate a UI component (button, card, navbar, hero, stats, feature_grid, testimonial, pricing, form, footer, modal, tabs, avatar, alert, badge, progress, table, stat_card). Returns full HTML with Tailwind CSS.",
        parameters={
            "component_type": {"type": "string", "description": "Component type to generate", "required": True,
                               "enum": ["button", "card", "navbar", "hero", "stats", "feature_grid", "testimonial",
                                        "pricing", "form", "footer", "modal", "tabs", "avatar", "alert", "badge",
                                        "progress", "table", "stat_card"]},
            "params": {"type": "object", "description": "Component parameters (variant, size, label, etc.)"},
        },
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_generate_landing_page",
        description="Generate a complete landing page with hero, features, stats, testimonials, pricing, contact form, and footer. Returns full HTML with Tailwind CSS and RTL support.",
        parameters={
            "brand": {"type": "string", "description": "Brand name"},
            "hero_title": {"type": "string", "description": "Hero section title"},
            "hero_subtitle": {"type": "string", "description": "Hero section subtitle"},
            "include_features": {"type": "boolean", "description": "Include features section"},
            "include_stats": {"type": "boolean", "description": "Include stats section"},
            "include_testimonials": {"type": "boolean", "description": "Include testimonials section"},
            "include_pricing": {"type": "boolean", "description": "Include pricing section"},
            "include_contact": {"type": "boolean", "description": "Include contact form"},
        },
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_generate_dashboard",
        description="Generate a dashboard page with navbar, stat cards, table, and progress bars. Returns full HTML with Tailwind CSS and RTL support.",
        parameters={
            "title": {"type": "string", "description": "Dashboard title"},
            "include_table": {"type": "boolean", "description": "Include data table"},
            "include_chart": {"type": "boolean", "description": "Include chart area"},
        },
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_generate_page",
        description="Generate a page from a natural language description. Supports: landing, dashboard, login/auth, shop, blog, contact, email template, resume/CV.",
        parameters={
            "description": {"type": "string", "description": "Description of the page to generate (e.g. 'login page', 'blog', 'shop')", "required": True},
        },
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_generate_color_palette",
        description="Generate a color palette from a primary hex color. Returns all color tokens (primary, secondary, accent, neutral, info, success, warning, error, background, surface, text).",
        parameters={
            "primary": {"type": "string", "description": "Primary color hex (e.g. #3B82F6)"},
            "scheme": {"type": "string", "description": "Color scheme: light, dark, midnight, sunset, pastel, corporate, ocean, forest, autumn, spring, sepia, contrast"},
        },
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_generate_css_variables",
        description="Get the current design system as CSS custom properties.",
        parameters={},
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_generate_tailwind_config",
        description="Get the current design system as a Tailwind CSS configuration object.",
        parameters={},
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_create_design_system",
        description="Create or update the design system with a primary color and font. Use before generating components.",
        parameters={
            "name": {"type": "string", "description": "Design system name"},
            "primary_color": {"type": "string", "description": "Primary color hex"},
            "scheme": {"type": "string", "description": "Color scheme: light, dark, etc."},
            "font_family": {"type": "string", "description": "Font family for the design system"},
        },
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_get_design_system",
        description="Get the current design system configuration.",
        parameters={},
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_review_ui",
        description="Review HTML/CSS/JS for accessibility, visual design, responsiveness, performance, and best practices. Returns issues, suggestions, strengths, and a score.",
        parameters={
            "html": {"type": "string", "description": "HTML content to review", "required": True},
            "css": {"type": "string", "description": "Optional CSS to review"},
            "js": {"type": "string", "description": "Optional JavaScript to review"},
        },
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_score_ui",
        description="Score UI HTML quality from 0-100 based on design rules.",
        parameters={
            "html": {"type": "string", "description": "HTML content to score", "required": True},
        },
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_list_animations",
        description="List all available CSS animations with names and descriptions.",
        parameters={},
        category="design",
    ))
    registry.register(SkillDefinition(
        name="design_get_animation_css",
        description="Get CSS for a specific animation by name, or all animations if no name given.",
        parameters={
            "name": {"type": "string", "description": "Animation name (omit for all)"},
        },
        category="design",
    ))

    logger.info("Registered %d default skills", len(registry._skills))


def _serialize_result(result: Any) -> Any:
    """Serialize result for JSON response."""
    if result is None:
        return None
    if isinstance(result, (str, int, float, bool)):
        return result
    if isinstance(result, dict):
        return {k: _serialize_result(v) for k, v in result.items()}
    if isinstance(result, list):
        return [_serialize_result(v) for v in result]
    if hasattr(result, "to_dict"):
        return result.to_dict()
    if hasattr(result, "__dict__"):
        return {k: _serialize_result(v) for k, v in result.__dict__.items() if not k.startswith("_")}
    return str(result)
