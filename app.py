import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import ffmpeg

# --- PORTABLE FFmpeg BINARY DETECTOR ---
if getattr(sys, 'frozen', False):
    # Running inside the compiled PyInstaller executable environment
    bundle_dir = sys._MEIPASS
    ffmpeg_bin = os.path.join(bundle_dir, "ffmpeg.exe")
else:
    # Running natively as a standard script (uses system PATH fallback)
    ffmpeg_bin = "ffmpeg"


class SubtitleEmbedderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Standalone Subtitle Embedder")
        self.root.geometry("550x400")
        self.root.resizable(False, False)

        self.video_path = None
        self.srt_path = None

        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self.root, text="Standalone Subtitle Embedder", font=("Arial", 16, "bold"))
        title.pack(pady=15)

        self.video_box = tk.Label(self.root, text="Drag & Drop .mp4 Video Here", bg="#e1e1e1", width=60, height=3, relief="groove")
        self.video_box.pack(pady=10)
        self.video_box.drop_target_register(DND_FILES)
        self.video_box.dnd_bind('<<Drop>>', self.drop_video)

        self.srt_box = tk.Label(self.root, text="Drag & Drop .srt Subtitle Here", bg="#e1e1e1", width=60, height=3, relief="groove")
        self.srt_box.pack(pady=10)
        self.srt_box.drop_target_register(DND_FILES)
        self.srt_box.dnd_bind('<<Drop>>', self.drop_srt)

        self.sub_type = tk.StringVar(value="soft")
        radio_frame = tk.Frame(self.root)
        radio_frame.pack(pady=15)

        tk.Radiobutton(radio_frame, text="Softsubs (Selectable / Fast)", variable=self.sub_type, value="soft", font=("Arial", 10)).pack(side=tk.LEFT, padx=15)
        tk.Radiobutton(radio_frame, text="Hardsubs (Burned-in / Slower)", variable=self.sub_type, value="hard", font=("Arial", 10)).pack(side=tk.LEFT, padx=15)

        self.status_lbl = tk.Label(self.root, text="Ready", fg="blue", font=("Arial", 10, "italic"))
        self.status_lbl.pack(pady=5)

        self.process_btn = tk.Button(self.root, text="Embed Subtitles", command=self.process_video, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
        self.process_btn.pack(pady=10)

    def clean_path(self, path):
        return path.strip("{}").strip('"')

    def drop_video(self, event):
        path = self.clean_path(event.data)
        if path.lower().endswith('.mp4'):
            self.video_path = path
            self.video_box.config(text=f"Video Loaded:\n{os.path.basename(path)}", bg="#d4edda")
        else:
            messagebox.showerror("Error", "Please drop a valid .mp4 file.")

    def drop_srt(self, event):
        path = self.clean_path(event.data)
        if path.lower().endswith('.srt'):
            self.srt_path = path
            self.srt_box.config(text=f"SRT Loaded:\n{os.path.basename(path)}", bg="#d4edda")
        else:
            messagebox.showerror("Error", "Please drop a valid .srt file.")

    def process_video(self):
        if not self.video_path or not self.srt_path:
            messagebox.showwarning("Missing Files", "Please drop both an .mp4 and an .srt file.")
            return

        original_cwd = os.getcwd()
        video_dir = os.path.dirname(self.video_path)
        base_name = os.path.splitext(os.path.basename(self.video_path))[0]
        mode = self.sub_type.get()
        output_filename = f"{base_name}_{mode}sub.mp4"
        output_path = os.path.join(video_dir, output_filename)

        self.status_lbl.config(text="Processing... please wait.", fg="orange")
        self.root.update_idletasks()

        try:
            if mode == "soft":
                video_input = ffmpeg.input(self.video_path)
                subtitle_input = ffmpeg.input(self.srt_path)
                stream = ffmpeg.output(video_input, subtitle_input, output_path, **{'c': 'copy', 'c:s': 'mov_text'})
            else:
                srt_dir = os.path.dirname(self.srt_path)
                srt_filename = os.path.basename(self.srt_path)
                os.chdir(srt_dir)
                stream = ffmpeg.input(self.video_path).output(output_path, vf=f"subtitles={srt_filename}")

            # FORCED STANDALONE EXECUTION PATH:
            # We explicitly target our dynamic bundle path via cmd override
            ffmpeg.run(stream, cmd=ffmpeg_bin, overwrite_output=True)

            self.status_lbl.config(text="Done!", fg="green")
            messagebox.showinfo("Success", f"File saved successfully to:\n{output_path}")

        except ffmpeg.Error as e:
            self.status_lbl.config(text="Error occurred", fg="red")
            stderr_msg = e.stderr.decode('utf-8') if e.stderr else "Check log console details."
            messagebox.showerror("FFmpeg Error", f"FFmpeg failed:\n\n{stderr_msg}")
        except Exception as e:
            self.status_lbl.config(text="Error occurred", fg="red")
            messagebox.showerror("Error", str(e))
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = SubtitleEmbedderApp(root)
    root.mainloop()
