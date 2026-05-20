"""
Force UTF-8 on stdout/stderr (Windows consoles often use cp1252).
Armstrong workflow prints and raises messages containing ₹ (U+20B9).
"""

from __future__ import annotations

import os
import sys

_done = False


def force_utf8_stdio() -> None:
    global _done
    if _done:
        return
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        # Prefer original streams so this still works if something wrapped sys.stdout
        out = getattr(sys, "__stdout__", None) or sys.stdout
        err = getattr(sys, "__stderr__", None) or sys.stderr
        if out is not None and hasattr(out, "fileno"):
            sys.stdout = open(  # noqa: SIM115 — intentional reopen of fd
                out.fileno(),
                mode="w",
                encoding="utf-8",
                errors="replace",
                buffering=1,
                closefd=False,
            )
        if err is not None and hasattr(err, "fileno"):
            sys.stderr = open(
                err.fileno(),
                mode="w",
                encoding="utf-8",
                errors="replace",
                buffering=1,
                closefd=False,
            )
        _done = True
    except Exception:
        for stream in (sys.stdout, sys.stderr):
            if stream is not None and hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass
        _done = True
