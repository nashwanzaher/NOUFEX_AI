from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from typing import Any

from noufex_ai.exceptions import ValidationError


# ── Path Traversal Prevention ──────────────────────────────────────

ALLOWED_ROOTS = [
    Path.home(),
    Path("/tmp"),
    Path(os.environ.get("TEMP", "/tmp")),
]

BLOCKED_PATHS = [
    "/etc/shadow",
    "/etc/passwd",
    "/etc/sudoers",
    "/root/.ssh",
    "~/.ssh",
    "~/.aws",
    "~/.gnupg",
]

BLOCKED_EXTENSIONS = [
    ".key", ".pem", ".p12", ".pfx", ".jks",
    ".env", ".credentials",
]


def validate_path(path: str, *, must_exist: bool = False, must_be_file: bool = False) -> Path:
    """Validate and resolve a file path, preventing path traversal attacks.

    Args:
        path: The path to validate
        must_exist: If True, path must exist
        must_be_file: If True, path must be a file (not directory)

    Returns:
        Resolved Path object

    Raises:
        ValidationError: If path is invalid or not allowed
    """
    if not path or not path.strip():
        raise ValidationError("Path cannot be empty")

    p = Path(path).expanduser().resolve()

    # Check for blocked paths
    path_str = str(p).lower()
    for blocked in BLOCKED_PATHS:
        blocked_resolved = str(Path(blocked).expanduser().resolve()).lower()
        if path_str.startswith(blocked_resolved):
            raise ValidationError(f"Access to path '{path}' is not allowed")

    # Check for blocked extensions
    if p.suffix.lower() in BLOCKED_EXTENSIONS:
        raise ValidationError(f"Access to '{p.suffix}' files is not allowed")

    # Check for path traversal attempts
    if ".." in path:
        # After resolution, verify it's under allowed roots
        under_allowed = False
        for root in ALLOWED_ROOTS:
            try:
                p.relative_to(root)
                under_allowed = True
                break
            except ValueError:
                continue
        if not under_allowed:
            raise ValidationError("Path traversal detected: access denied")

    if must_exist and not p.exists():
        raise ValidationError(f"Path does not exist: {path}")

    if must_be_file and p.exists() and not p.is_file():
        raise ValidationError(f"Path is not a file: {path}")

    return p


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent injection and traversal.

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"

    # Remove path separators and null bytes
    sanitized = filename.replace("/", "_").replace("\\", "_").replace("\0", "")

    # Remove special characters except dots, dashes, underscores
    sanitized = re.sub(r'[^\w\-\.]', '_', sanitized)

    # Remove leading dots (hidden files)
    sanitized = sanitized.lstrip(".")

    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255 - len(ext)] + ext

    return sanitized or "unnamed"


# ── Command Injection Prevention ───────────────────────────────────

DANGEROUS_COMMANDS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=",
    ":(){:|:&};:",  # fork bomb
    "chmod -R 777 /",
    "chown -R",
    "> /dev/sda",
]

DANGEROUS_PATTERNS = [
    r';\s*rm\s',       # ; rm
    r'\|\s*rm\s',      # | rm
    r'&&\s*rm\s',      # && rm
    r'`[^`]*rm[^`]*`', # backtick rm
    r'\$\(.*rm.*\)',   # $(rm)
    r'>\s*/dev/',      # redirect to /dev
    r'mkfs\.',         # mkfs
    r'dd\s+if=',       # dd
]


def validate_command(command: str, *, allowed_commands: list[str] | None = None) -> str:
    """Validate a shell command to prevent injection attacks.

    Args:
        command: The command to validate
        allowed_commands: Optional whitelist of allowed commands

    Returns:
        Validated command string

    Raises:
        ValidationError: If command is dangerous or not allowed
    """
    if not command or not command.strip():
        raise ValidationError("Command cannot be empty")

    command = command.strip()

    # Check against dangerous commands
    cmd_lower = command.lower()
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous.lower() in cmd_lower:
            raise ValidationError(f"Dangerous command detected: '{dangerous}'")

    # Check against dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            raise ValidationError("Potentially dangerous command pattern detected")

    # If whitelist provided, check first token
    if allowed_commands:
        try:
            parts = shlex.split(command)
        except ValueError:
            raise ValidationError("Invalid command syntax")

        if not parts:
            raise ValidationError("Empty command")

        base_cmd = os.path.basename(parts[0])
        if base_cmd not in allowed_commands:
            raise ValidationError(
                f"Command '{base_cmd}' is not in the allowed list: {allowed_commands}"
            )

    # Check for null bytes
    if "\0" in command:
        raise ValidationError("Command contains null bytes")

    return command


def validate_command_safe(command: str, timeout: int = 30) -> dict[str, Any]:
    """Run a command safely using subprocess with argument list (no shell=True).

    This is the preferred way to run commands as it avoids shell injection.

    Args:
        command: The command to run
        timeout: Timeout in seconds

    Returns:
        Dict with success, returncode, stdout, stderr
    """
    import subprocess

    try:
        # Parse command into argument list (avoids shell injection)
        try:
            args = shlex.split(command)
        except ValueError as e:
            return {"success": False, "error": f"Invalid command syntax: {e}"}

        if not args:
            return {"success": False, "error": "Empty command"}

        # Run without shell=True to prevent injection
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:5000],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"success": False, "error": f"Command not found: {args[0] if args else command}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── JavaScript Injection Prevention ────────────────────────────────

BLOCKED_JS_PATTERNS = [
    r'require\s*\(',           # Node.js require
    r'import\s*\(',            # Dynamic import
    r'fs\.',                   # File system access
    r'child_process',          # Process execution
    r'process\.',              # Process access
    r'__dirname',              # Directory name
    r'__filename',             # File name
    r'eval\s*\(',              # eval()
    r'new\s+Function\s*\(',    # new Function()
    r'setTimeout\s*\(\s*["\']', # setTimeout with string
    r'setInterval\s*\(\s*["\']', # setInterval with string
    r'document\.cookie',       # Cookie access
    r'localStorage',           # Local storage
    r'sessionStorage',         # Session storage
    r'XMLHttpRequest',         # XHR
    r'fetch\s*\(',             # Fetch API
]


def validate_javascript(script: str, *, allow_fetch: bool = False) -> str:
    """Validate JavaScript code to prevent dangerous operations.

    Args:
        script: The JavaScript code to validate
        allow_fetch: If True, allow fetch() calls

    Returns:
        Validated script string

    Raises:
        ValidationError: If script contains dangerous patterns
    """
    if not script or not script.strip():
        raise ValidationError("Script cannot be empty")

    script = script.strip()

    # Check for null bytes
    if "\0" in script:
        raise ValidationError("Script contains null bytes")

    # Check against blocked patterns
    patterns = BLOCKED_JS_PATTERNS.copy()
    if allow_fetch:
        patterns = [p for p in patterns if 'fetch' not in p]

    for pattern in patterns:
        if re.search(pattern, script, re.IGNORECASE):
            raise ValidationError(
                f"Script contains blocked pattern: '{pattern}'"
            )

    # Check script length
    if len(script) > 50000:
        raise ValidationError("Script too long (max 50000 characters)")

    return script


# ── Input Sanitization ─────────────────────────────────────────────

def sanitize_string(value: str, *, max_length: int = 10000, strip_html: bool = True) -> str:
    """Sanitize a string input.

    Args:
        value: The string to sanitize
        max_length: Maximum allowed length
        strip_html: If True, strip HTML tags

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Remove null bytes
    sanitized = value.replace("\0", "")

    # Strip HTML if requested
    if strip_html:
        sanitized = re.sub(r'<[^>]+>', '', sanitized)

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()


def validate_url(url: str) -> str:
    """Validate a URL.

    Args:
        url: The URL to validate

    Returns:
        Validated URL string

    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not url.strip():
        raise ValidationError("URL cannot be empty")

    url = url.strip()

    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )

    if not url_pattern.match(url):
        raise ValidationError(f"Invalid URL format: {url}")

    # Block internal/private IPs in production
    if "127.0.0.1" in url or "0.0.0.0" in url or "localhost" in url:
        # Allow in development
        from noufex_ai.settings import settings
        if settings.is_production:
            raise ValidationError("Access to internal URLs is not allowed in production")

    return url
