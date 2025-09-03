import builtins
import os
import types
import threading
import time
import tkinter as tk
from unittest import mock

import pytest
import sys
from pathlib import Path

# Ensure project root is on sys.path for `import slideshow`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from slideshow import TATSlideshowApp


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available in environment")
    # Prevent the window from showing
    root.withdraw()
    try:
        yield root
    finally:
        try:
            root.destroy()
        except Exception:
            pass


def _make_app(root):
    app = TATSlideshowApp(root)
    return app


def test_initial_state_labels(tk_root):
    app = _make_app(tk_root)
    assert app.current_phase == "preparation"
    assert app.is_running is False
    assert app.is_paused is False
    assert app.timer_seconds == 0
    # UI labels exist
    assert app.timer_label.cget("text") == "00:00"
    assert "Ready" in app.phase_label.cget("text")


def test_load_images_when_folder_missing_creates_folder(tmp_path, monkeypatch, tk_root):
    monkeypatch.chdir(tmp_path)

    # Avoid modal message boxes in tests
    with mock.patch("tkinter.messagebox.showwarning") as warn:
        from slideshow import TATSlideshowApp
        app = TATSlideshowApp(tk_root)
        # Newly created folder should exist
        assert os.path.isdir("images")
        warn.assert_called()


def test_load_images_and_sorting(tmp_path, monkeypatch, tk_root):
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    # Create some numbered files out of order
    for name in ["image_10.jpg", "image_2.jpg", "image_1.jpg"]:
        (tmp_path / "images" / name).write_bytes(b"\x00")

    with mock.patch("tkinter.messagebox.showwarning") as warn:
        warn.side_effect = lambda *a, **k: None
        app = _make_app(tk_root)

    assert [os.path.basename(p) for p in app.images] == [
        "image_1.jpg",
        "image_2.jpg",
        "image_10.jpg",
    ]


def test_show_current_image_updates_info(tmp_path, monkeypatch, tk_root):
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)

    # Create a tiny valid JPEG using PIL if available; else skip
    try:
        from PIL import Image

        img_file = tmp_path / "images" / "image_1.jpg"
        Image.new("RGB", (10, 10), color=(255, 0, 0)).save(img_file)
    except Exception:
        pytest.skip("Pillow not available in test environment")

    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)

    # Make Tk callbacks execute immediately (no mainloop in tests)
    app.root.after = lambda delay, func=None, *a, **k: (func() if func else None)

    app.current_image_index = 0
    app.show_current_image()

    assert app.current_image_info.cget("text").startswith("Current: image_1.jpg")
    # image_label should now hold an image reference
    assert hasattr(app.image_label, "image")


def test_timer_transitions_hide_image_and_next(tmp_path, monkeypatch, tk_root):
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)

    try:
        from PIL import Image
        # create two images
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_2.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")

    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)

    # Set short times for fast tests
    app.display_time = 1
    app.preparation_time = 1

    # Avoid real message boxes
    with mock.patch("tkinter.messagebox.showinfo"):
        # Make Tk callbacks execute immediately (no mainloop in tests)
        app.root.after = lambda delay, func=None, *a, **k: (func() if func else None)

        app.start_slideshow()
        # Simulate end of preparation phase
        app.timer_seconds = 0
        app.timer_finished()
        # Writing phase should start and image must be hidden
        assert app.current_phase == "writing"
        assert getattr(app.image_label, "image", None) is None
        assert "Image hidden" in app.image_label.cget("text")

        # Simulate end of writing phase to move to next image
        app.timer_seconds = 0
        app.timer_finished()
        assert app.current_phase == "preparation"
        assert app.current_image_index == 1

        app.stop_slideshow()


def test_pause_resume_updates_phase_label(tmp_path, monkeypatch, tk_root):
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image

        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")

    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    # Ensure after callbacks are synchronous here as well
    app.root.after = lambda delay, func=None, *a, **k: (func() if func else None)

    app.display_time = 2
    app.preparation_time = 2

    app.start_slideshow()
    # Pause
    app.toggle_pause()
    assert app.is_paused is True
    assert app.phase_label.cget("text") == "PAUSED"
    # Resume
    app.toggle_pause()
    assert app.is_paused is False

    app.stop_slideshow()


def test_save_and_clear_answer(tmp_path, monkeypatch, tk_root):
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image

        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")

    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)

    app.current_image_index = 0
    app.show_current_image()

    with mock.patch("tkinter.messagebox.showinfo"):
        app.answer_text.insert("1.0", "My story")
        app.save_current_answer()

    image_name = os.path.basename(app.images[0])
    assert app.answers[image_name] == "My story"

    app.clear_current_answer()
    assert app.answer_text.get("1.0", tk.END).strip() == ""


def test_export_answers(tmp_path, monkeypatch, tk_root):
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image

        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")

    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)

    app.current_image_index = 0
    app.show_current_image()
    image_name = os.path.basename(app.images[0])
    app.answers[image_name] = "A sample answer"

    # Mock save dialog and messageboxes
    with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=str(tmp_path / "out.txt")):
        with mock.patch("tkinter.messagebox.showinfo") as info:
            app.export_answers()
            info.assert_called()

    content = (tmp_path / "out.txt").read_text(encoding="utf-8")
    assert "A sample answer" in content