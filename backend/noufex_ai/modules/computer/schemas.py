from __future__ import annotations

from pydantic import BaseModel, Field


class FocusWindowRequest(BaseModel):
    identifier: str = Field(..., description="Window title, handle, or process name")


class MoveWindowRequest(BaseModel):
    identifier: str = Field(..., description="Window title, handle, or process name")
    x: int = Field(0, description="X position")
    y: int = Field(0, description="Y position")
    width: int | None = Field(None, description="Window width")
    height: int | None = Field(None, description="Window height")


class OpenWindowRequest(BaseModel):
    target: str = Field(..., description="URL, file path, or application name")


class CloseWindowRequest(BaseModel):
    identifier: str = Field(..., description="Window title, handle, or process name")


class ScreenshotRequest(BaseModel):
    region: list[int] | None = Field(None, description="Region [left, top, right, bottom]")


class MouseMoveRequest(BaseModel):
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")


class MouseClickRequest(BaseModel):
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    button: str = Field("left", description="Mouse button: left, right, middle")
    clicks: int = Field(1, description="Number of clicks (1=single, 2=double)")


class MouseDragRequest(BaseModel):
    x1: int = Field(..., description="Start X")
    y1: int = Field(..., description="Start Y")
    x2: int = Field(..., description="End X")
    y2: int = Field(..., description="End Y")
    duration: float = Field(0.5, description="Drag duration in seconds")


class MouseScrollRequest(BaseModel):
    clicks: int = Field(..., description="Scroll amount (positive=up, negative=down)")
    x: int | None = Field(None, description="X position")
    y: int | None = Field(None, description="Y position")


class KeyboardTypeRequest(BaseModel):
    text: str = Field(..., description="Text to type")
    interval: float = Field(0.05, description="Delay between keystrokes in seconds")


class KeyboardHotkeyRequest(BaseModel):
    keys: list[str] = Field(..., description="Keys to press together, e.g. ['ctrl', 'c']")


class KeyboardPressRequest(BaseModel):
    key: str = Field(..., description="Key to press, e.g. enter, tab, escape")


class KillProcessRequest(BaseModel):
    pid_or_name: int | str = Field(..., description="Process ID or name")


class RunCommandRequest(BaseModel):
    command: str = Field(..., description="Shell command to execute")
    timeout: int = Field(30, description="Timeout in seconds", ge=1, le=300)


class ListDirectoryRequest(BaseModel):
    path: str = Field(".", description="Directory path")


class ReadFileRequest(BaseModel):
    path: str = Field(..., description="File path to read")


class WriteFileRequest(BaseModel):
    path: str = Field(..., description="File path to write")
    content: str = Field(..., description="Content to write")
