"""Optional native desktop frontend for Friday 2.0.

The dark animated web UI is the recommended interface. This keeps the original
typed and wake-word desktop workflow available as well.
"""

import threading
import tkinter as tk
from tkinter import messagebox

from core.router import process_command, run_assistant
from speech.text_to_speech import VOICE_PROFILE, set_voice_profile


class FridayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Friday 2.0")
        self.root.geometry("760x650")
        self.root.minsize(620, 520)
        self.stop_event = None
        self.voice_worker = None
        self.status = tk.StringVar(value="Ready — type a message or start voice mode")
        self._build()
        self._append_message("Friday", "Hello. I am Friday. How can I help you?")
        root.protocol("WM_DELETE_WINDOW", self.close)

    def _build(self):
        header = tk.Frame(self.root)
        header.pack(fill="x", padx=24, pady=(22, 12))
        tk.Label(header, text="FRIDAY 2.0", font=("Helvetica", 26, "bold")).pack(side="left")
        tk.Label(header, text="Local AI assistant", font=("Helvetica", 11)).pack(side="right", pady=10)

        panel = tk.Frame(self.root, borderwidth=1, relief="sunken")
        panel.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        self.chat = tk.Text(panel, relief="flat", borderwidth=0, font=("Helvetica", 14), wrap="word", padx=16, pady=14, state="disabled", cursor="arrow")
        scroll = tk.Scrollbar(panel, command=self.chat.yview)
        self.chat.configure(yscrollcommand=scroll.set)
        self.chat.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        composer = tk.Frame(self.root)
        composer.pack(fill="x", padx=24, pady=(0, 12))
        self.input = tk.Entry(composer, font=("Helvetica", 14))
        self.input.pack(side="left", fill="x", expand=True, ipady=12, padx=(0, 10))
        self.input.bind("<Return>", self.send_message)
        tk.Button(composer, text="Send", command=self.send_message, font=("Helvetica", 12, "bold"), padx=20, pady=8).pack(side="right")

        footer = tk.Frame(self.root)
        footer.pack(fill="x", padx=24, pady=(0, 18))
        tk.Label(footer, textvariable=self.status, font=("Helvetica", 11)).pack(side="left")
        self.start_button = tk.Button(footer, text="Start voice mode", command=self.start_voice, font=("Helvetica", 11, "bold"), padx=14, pady=6)
        self.start_button.pack(side="right")
        self.stop_button = tk.Button(footer, text="Stop", command=self.stop_voice, state="disabled", font=("Helvetica", 11, "bold"), padx=14, pady=6)
        self.stop_button.pack(side="right", padx=(0, 8))
        self.voice_profile = tk.StringVar(value=VOICE_PROFILE if VOICE_PROFILE in {"male", "female"} else "female")
        tk.OptionMenu(footer, self.voice_profile, "female", "male", command=self.change_voice).pack(side="right", padx=(0, 8))
        tk.Label(footer, text="Voice:", font=("Helvetica", 11)).pack(side="right")

    def change_voice(self, profile):
        set_voice_profile(profile)
        self.set_status(f"{profile.title()} voice selected")

    def set_status(self, message):
        self.root.after(0, self.status.set, message)

    def add_message(self, speaker, message):
        self.root.after(0, lambda: self._append_message(speaker, message))

    def _append_message(self, speaker, message):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{speaker}: {message}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def send_message(self, event=None):
        message = self.input.get().strip()
        if not message:
            return
        self.input.delete(0, "end")
        self.set_status("Friday is thinking…")
        threading.Thread(target=self._send_in_background, args=(message,), daemon=True).start()

    def _send_in_background(self, message):
        try:
            process_command(message, self.set_status, self.add_message)
            self.set_status("Ready")
        except Exception as error:
            self.root.after(0, lambda: messagebox.showerror("Friday error", str(error)))
            self.set_status("Could not complete that request")

    def start_voice(self):
        if self.voice_worker and self.voice_worker.is_alive():
            return
        self.stop_event = threading.Event()
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.voice_worker = threading.Thread(target=self._run_voice, daemon=True)
        self.voice_worker.start()

    def _run_voice(self):
        try:
            run_assistant(self.stop_event, self.set_status, self.add_message)
        except Exception as error:
            self.root.after(0, lambda: messagebox.showerror("Friday could not start", str(error)))
        finally:
            self.root.after(0, self._voice_stopped)

    def _voice_stopped(self):
        self.status.set("Voice mode is stopped")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def stop_voice(self):
        if self.stop_event:
            self.stop_event.set()
        self.set_status("Stopping voice mode…")

    def close(self):
        self.stop_voice()
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    FridayApp(window)
    window.mainloop()
