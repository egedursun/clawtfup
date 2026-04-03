"""PTY-backed interactive path for agent CLI proxy (Unix)."""

from __future__ import annotations

import os
import selectors
import subprocess
import sys
import threading
from pathlib import Path


def run_agent_proxy_pty(
    exe: str,
    child_argv: list[str],
    ws: Path,
) -> int:
    """Interactive path: PTY + real terminal discipline for full-screen TUIs."""
    import fcntl
    import pty
    import signal
    import struct
    import termios
    import tty

    stdin_fd = sys.stdin.fileno()
    master_fd, slave_fd = pty.openpty()

    _tty_apply_attrs = getattr(termios, "tcsetattr")
    try:
        attrs = termios.tcgetattr(stdin_fd)
        _tty_apply_attrs(slave_fd, termios.TCSANOW, attrs)
    except (OSError, termios.error):
        pass

    try:
        winsz = bytearray(struct.calcsize("HHHH"))
        fcntl.ioctl(stdin_fd, termios.TIOCGWINSZ, winsz)
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsz)
    except OSError:
        pass

    try:
        proc = subprocess.Popen(
            [exe, *child_argv],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=str(ws),
            start_new_session=True,
        )
    except FileNotFoundError:
        sys.stderr.write(f"clawtfup cli: executable not found: {exe!r}\n")
        os.close(master_fd)
        os.close(slave_fd)
        return 127

    os.close(slave_fd)

    flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
    fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def forward_winch(*_args: object) -> None:
        try:
            w = bytearray(struct.calcsize("HHHH"))
            fcntl.ioctl(stdin_fd, termios.TIOCGWINSZ, w)
            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, w)
        except OSError:
            pass

    prev_winch = signal.signal(signal.SIGWINCH, forward_winch)
    forward_winch()

    old_term: object | None = None
    try:
        old_term = termios.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd, termios.TCSANOW)
    except (OSError, termios.error):
        old_term = None

    stop = threading.Event()

    def relay_master_to_stdout() -> bool:
        while True:
            try:
                data = os.read(master_fd, 65536)
            except BlockingIOError:
                break
            except OSError:
                stop.set()
                return False
            if not data:
                stop.set()
                return False
            os.write(1, data)
        return True

    def io_loop() -> None:
        sel = selectors.DefaultSelector()
        sel.register(stdin_fd, selectors.EVENT_READ)
        sel.register(master_fd, selectors.EVENT_READ)
        try:
            while not stop.is_set():
                try:
                    events = sel.select(timeout=0.02)
                except (OSError, ValueError):
                    break
                if not events:
                    if proc.poll() is not None:
                        relay_master_to_stdout()
                        break
                    continue
                for key, _ in events:
                    if key.fd == stdin_fd:
                        try:
                            data = os.read(stdin_fd, 65536)
                        except OSError:
                            stop.set()
                            break
                        if not data:
                            stop.set()
                            break
                        try:
                            os.write(master_fd, data)
                        except OSError:
                            stop.set()
                            break
                    elif key.fd == master_fd:
                        if not relay_master_to_stdout():
                            return
        finally:
            for fd in (stdin_fd, master_fd):
                try:
                    sel.unregister(fd)
                except (OSError, ValueError, KeyError):
                    pass
            sel.close()

    io_thread = threading.Thread(target=io_loop, daemon=False, name="clawtfup-pty-io")
    io_thread.start()

    try:
        proc.wait()
    finally:
        stop.set()
        io_thread.join(timeout=5.0)
        if old_term is not None:
            try:
                _tty_apply_attrs(stdin_fd, termios.TCSADRAIN, old_term)
            except (OSError, termios.error):
                pass
        signal.signal(signal.SIGWINCH, prev_winch)
        try:
            os.close(master_fd)
        except OSError:
            pass

    return proc.returncode or 0
