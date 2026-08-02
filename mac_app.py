"""Friday's macOS background assistant.

Run this module directly during development, or package it with
``macos/build_macos_app.sh``.  It stays hidden while waiting for the wake
phrase and presents a focused, dark visual only while Friday is listening,
thinking, or speaking.
"""

from __future__ import annotations

import re
import signal
import sys
import threading
import tkinter as tk
from pathlib import Path

from core.router import process_command
from speech.speech_to_text import listen
from speech.text_to_speech import speak


if getattr(sys, "frozen", False):
    # PyInstaller places --add-data files in an app bundle's Resources folder.
    PROJECT_ROOT = Path(sys.executable).resolve().parent.parent / "Resources"
else:
    PROJECT_ROOT = Path(__file__).resolve().parent

CORE_IMAGE = PROJECT_ROOT / "Website" / "Assests" / "Image" / "friday-core-3d.png"
WAKE_PATTERN = re.compile(r"\b(?:hello|hey)\s+friday\b", re.IGNORECASE)


class FridayOverlay:
    """Small, deliberately minimal visual for the background assistant."""

    def __init__(self):
        self.root = tk.Tk(className="Friday")
        self.root.withdraw()
        self.root.configure(bg="#030611")
        self.overlay = tk.Toplevel(self.root, bg="#030611")
        self.overlay.withdraw()
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.97)
        self.overlay.configure(highlightbackground="#49c9ff", highlightthickness=1)
        self.overlay.bind("<Escape>", lambda _event: self.hide())

        self.state = tk.StringVar(value="LISTENING")
        self.message = tk.StringVar(value="Hello. I'm Friday.")
        self._image = None
        self._build()
        self._place_centrally()

    def _build(self):
        frame = tk.Frame(self.overlay, bg="#030611", padx=38, pady=32)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text="FRIDAY 2.0",
            bg="#030611",
            fg="#55c7ff",
            font=("Helvetica Neue", 12, "bold"),
        ).pack(pady=(0, 18))

        image_label = tk.Label(frame, bg="#030611")
        image_label.pack(pady=(0, 18))
        self._load_core_image(image_label)

        tk.Label(
            frame,
            textvariable=self.state,
            bg="#030611",
            fg="#a8e7ff",
            font=("Helvetica Neue", 11, "bold"),
        ).pack()
        tk.Label(
            frame,
            textvariable=self.message,
            bg="#030611",
            fg="#dce9ff",
            font=("Helvetica Neue", 15),
            wraplength=360,
            justify="center",
        ).pack(pady=(11, 0))

    def _load_core_image(self, image_label):
        try:
            from PIL import Image, ImageTk

            image = Image.open(CORE_IMAGE).convert("RGBA")
            image.thumbnail((210, 210), Image.Resampling.LANCZOS)
            self._image = ImageTk.PhotoImage(image)
            image_label.configure(image=self._image)
        except Exception:
            image_label.configure(
                text="◉",
                fg="#55c7ff",
                bg="#030611",
                font=("Helvetica Neue", 140),
            )

    def _place_centrally(self):
        self.root.update_idletasks()
        width, height = 430, 430
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.overlay.geometry(f"{width}x{height}+{x}+{y}")

    def show(self, state, message):
        self.root.after(0, lambda: self._set_visible(state, message))

    def _set_visible(self, state, message):
        self.state.set(state.upper())
        self.message.set(message)
        self.overlay.deiconify()
        self.overlay.lift()

    def hide(self):
        self.root.after(0, self.overlay.withdraw)

    def run(self):
        self.root.mainloop()

    def close(self):
        self.root.after(0, self.root.destroy)


class FridayMacAssistant:
    """Always-on wake phrase loop with a minimal visual response."""

    def __init__(self, overlay):
        self.overlay = overlay
        self.stop_event = threading.Event()

    def _status(self, message):
        self.overlay.show("Working", message)

    def _get_command_after_wake(self, heard):
        match = WAKE_PATTERN.search(heard or "")
        if not match:
            return None
        inline_command = heard[match.end():].strip(" ,.!?")
        if inline_command:
            return inline_command
        self.overlay.show("Listening", "What would you like me to do?")
        while not self.stop_event.is_set():
            command = listen(timeout=5, phrase_time_limit=12, calibrate=False)
            if command:
                return command
        return None

    def _handle_command(self, command):
        self.overlay.show("Thinking", "I'm working on that…")
        try:
            reply = process_command(command, status_callback=self._status)
        except Exception as error:
            reply = f"I couldn't complete that request. {error}"
        self.overlay.show("Friday", reply)
        speak(reply)
        self.overlay.hide()

    def run(self):
        while not self.stop_event.is_set():
            try:
                # Opening a fresh microphone stream lets macOS release it briefly
                # between phrases while still keeping the wake loop responsive.
                heard = listen(timeout=3, phrase_time_limit=5, calibrate=False)
                command = self._get_command_after_wake(heard)
                if command:
                    self._handle_command(command)
            except RuntimeError as error:
                self.overlay.show("Microphone needed", str(error))
                self.stop_event.wait(5)
            except Exception as error:
                print(f"[Friday macOS] {error}")
                self.stop_event.wait(1)

    def stop(self):
        self.stop_event.set()


def main():
    overlay = FridayOverlay()
    assistant = FridayMacAssistant(overlay)
    worker = threading.Thread(target=assistant.run, name="Friday wake listener", daemon=True)
    worker.start()

    def stop(_signal=None, _frame=None):
        assistant.stop()
        overlay.close()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    overlay.run()


if __name__ == "__main__":
    main()
