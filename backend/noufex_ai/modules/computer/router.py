from __future__ import annotations

from fastapi import APIRouter, Depends

from noufex_ai.deps import CurrentUserDep, require_scope
from noufex_ai.modules.computer.schemas import (
    CloseWindowRequest,
    FocusWindowRequest,
    KillProcessRequest,
    KeyboardHotkeyRequest,
    KeyboardPressRequest,
    KeyboardTypeRequest,
    ListDirectoryRequest,
    MouseClickRequest,
    MouseDragRequest,
    MouseMoveRequest,
    MouseScrollRequest,
    MoveWindowRequest,
    OpenWindowRequest,
    ReadFileRequest,
    RunCommandRequest,
    ScreenshotRequest,
    WriteFileRequest,
)
from noufex_ai.modules.computer.service import ComputerService

router = APIRouter()


def _get_service() -> ComputerService:
    return ComputerService()


@router.get("/windows", summary="List all open windows")
async def list_windows(user: CurrentUserDep):
    return _get_service().list_windows()


@router.post("/windows/focus")
async def focus_window(payload: FocusWindowRequest, user: CurrentUserDep):
    return _get_service().focus_window(payload.identifier)


@router.post("/windows/move")
async def move_window(payload: MoveWindowRequest, user: CurrentUserDep):
    return _get_service().move_window(
        payload.identifier, payload.x, payload.y, payload.width, payload.height
    )


@router.post("/windows/open")
async def open_window(payload: OpenWindowRequest, user: CurrentUserDep):
    return _get_service().open_window(payload.target)


@router.post("/windows/close")
async def close_window(payload: CloseWindowRequest, user: CurrentUserDep):
    return _get_service().close_window(payload.identifier)


@router.get("/windows/active", summary="Get active window info")
async def get_active_window(user: CurrentUserDep):
    return _get_service().get_active_window()


@router.get("/screen", summary="Get screen info")
async def get_screen_info(user: CurrentUserDep):
    return _get_service().get_screen_info()


@router.post("/screenshot", summary="Take a screenshot")
async def take_screenshot(payload: ScreenshotRequest | None = None, user: CurrentUserDep = None):
    region = payload.region if payload else None
    return _get_service().screenshot(region)


@router.post("/mouse/move")
async def mouse_move(payload: MouseMoveRequest, user: CurrentUserDep):
    return _get_service().mouse_move(payload.x, payload.y)


@router.post("/mouse/click")
async def mouse_click(payload: MouseClickRequest, user: CurrentUserDep):
    return _get_service().mouse_click(payload.x, payload.y, payload.button, payload.clicks)


@router.post("/mouse/drag")
async def mouse_drag(payload: MouseDragRequest, user: CurrentUserDep):
    return _get_service().mouse_drag(payload.x1, payload.y1, payload.x2, payload.y2, payload.duration)


@router.post("/mouse/scroll")
async def mouse_scroll(payload: MouseScrollRequest, user: CurrentUserDep):
    return _get_service().mouse_scroll(payload.clicks, payload.x, payload.y)


@router.post("/keyboard/type")
async def keyboard_type(payload: KeyboardTypeRequest, user: CurrentUserDep):
    return _get_service().keyboard_type(payload.text, payload.interval)


@router.post("/keyboard/hotkey")
async def keyboard_hotkey(payload: KeyboardHotkeyRequest, user: CurrentUserDep):
    return _get_service().keyboard_hotkey(*payload.keys)


@router.post("/keyboard/press")
async def keyboard_press(payload: KeyboardPressRequest, user: CurrentUserDep):
    return _get_service().keyboard_press(payload.key)


@router.get("/processes")
async def list_processes(user: CurrentUserDep):
    return _get_service().list_processes()


@router.post("/processes/kill")
async def kill_process(payload: KillProcessRequest, user: CurrentUserDep = None):
    return _get_service().kill_process(payload.pid_or_name)


@router.get("/system")
async def get_system_info(user: CurrentUserDep):
    return _get_service().get_system_info()


@router.post("/command", summary="Run shell command (requires scope: computer:execute)")
async def run_command(
    payload: RunCommandRequest,
    user: CurrentUserDep = Depends(require_scope("computer:execute")),
):
    return _get_service().run_command(payload.command, payload.timeout)


@router.post("/files/list")
async def list_directory(payload: ListDirectoryRequest, user: CurrentUserDep):
    return _get_service().list_directory(payload.path)


@router.post("/files/read")
async def read_file(payload: ReadFileRequest, user: CurrentUserDep):
    return _get_service().read_file(payload.path)


@router.post("/files/write", summary="Write file (requires scope: computer:write)")
async def write_file(
    payload: WriteFileRequest,
    user: CurrentUserDep = Depends(require_scope("computer:write")),
):
    return _get_service().write_file(payload.path, payload.content)
