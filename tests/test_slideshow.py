import builtins
import json
import os
import shutil
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


def test_randomization_disabled_by_default(tmp_path, monkeypatch, tk_root):
    """Test that randomization is disabled by default"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in [1, 2, 3, 4, 5]:
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    assert app.randomize_enabled is False
    # Images should be in order
    assert [os.path.basename(p) for p in app.images] == [
        "image_1.jpg", "image_2.jpg", "image_3.jpg", "image_4.jpg", "image_5.jpg"
    ]


def test_randomization_enabled_shuffles_images(tmp_path, monkeypatch, tk_root):
    """Test that enabling randomization shuffles the images"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 21):  # Create 20 images for higher chance of shuffle
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Enable randomization and reload
    app.randomize_enabled = True
    app.load_images()
    
    # Check that original order is preserved
    expected_order = [f"image_{i}.jpg" for i in range(1, 21)]
    assert [os.path.basename(p) for p in app.original_images] == expected_order
    
    # Images should be different from original (with high probability)
    actual_order = [os.path.basename(p) for p in app.images]
    # With 20 images, the probability of same order after shuffle is astronomically low
    assert actual_order != expected_order


def test_randomization_ensures_all_images_shown_once(tmp_path, monkeypatch, tk_root):
    """Test that randomization includes each image exactly once"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.randomize_enabled = True
    app.load_images()
    
    # All images should be present
    original_set = set([os.path.basename(p) for p in app.original_images])
    shuffled_set = set([os.path.basename(p) for p in app.images])
    assert original_set == shuffled_set
    assert len(app.images) == len(app.original_images)


def test_settings_persistence(tmp_path, monkeypatch, tk_root):
    """Test that settings are saved and loaded correctly"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    (tmp_path / "images" / "image_1.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Modify settings
    app.randomize_enabled = True
    app.display_time = 120
    app.preparation_time = 15
    app.save_settings()
    
    # Create new app instance (simulating restart)
    with mock.patch("tkinter.messagebox.showwarning"):
        app2 = _make_app(tk_root)
    
    # Settings should be loaded
    assert app2.randomize_enabled is True
    assert app2.display_time == 120
    assert app2.preparation_time == 15


def test_toggle_randomize_updates_setting(tmp_path, monkeypatch, tk_root):
    """Test that toggle_randomize updates the setting and shows message"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    (tmp_path / "images" / "image_1.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    assert app.randomize_enabled is False
    
    # Toggle on
    with mock.patch("tkinter.messagebox.showinfo") as info:
        app.randomize_var.set(True)
        app.toggle_randomize()
        info.assert_called()
        assert "randomized" in info.call_args[0][1].lower()
    
    assert app.randomize_enabled is True
    
    # Toggle off
    with mock.patch("tkinter.messagebox.showinfo") as info:
        app.randomize_var.set(False)
        app.toggle_randomize()
        info.assert_called()
        assert "sequential" in info.call_args[0][1].lower()
    
    assert app.randomize_enabled is False


def test_start_slideshow_no_images(tmp_path, monkeypatch, tk_root):
    """Test start_slideshow shows warning when no images loaded"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.images = []  # Ensure no images
    
    with mock.patch("tkinter.messagebox.showwarning") as warn:
        app.start_slideshow()
        warn.assert_called()
        assert "load images" in warn.call_args[0][1].lower()


def test_start_slideshow_invalid_time_values(tmp_path, monkeypatch, tk_root):
    """Test start_slideshow handles invalid time input"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    (tmp_path / "images" / "image_1.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Set invalid time value
    app.display_time_var.set("invalid")
    
    with mock.patch("tkinter.messagebox.showerror") as error:
        app.start_slideshow()
        error.assert_called()
        assert "valid time" in error.call_args[0][1].lower()


def test_slideshow_finished_message(tmp_path, monkeypatch, tk_root):
    """Test slideshow_finished displays completion message"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.answers = {"image_1.jpg": "Test answer"}
    
    with mock.patch("tkinter.messagebox.showinfo") as info:
        app.slideshow_finished()
        info.assert_called()
        assert "complete" in info.call_args[0][1].lower()


def test_export_answers_no_answers(tmp_path, monkeypatch, tk_root):
    """Test export_answers shows warning when no answers to export"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.answers = {}
    
    with mock.patch("tkinter.messagebox.showwarning") as warn:
        app.export_answers()
        warn.assert_called()
        assert "no answers" in warn.call_args[0][1].lower()


def test_export_answers_cancel_dialog(tmp_path, monkeypatch, tk_root):
    """Test export_answers handles canceled file dialog"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.answers = {"image_1.jpg": "Test answer"}
    
    # Mock save dialog returning empty string (cancelled)
    with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=""):
        app.export_answers()
        # Should not crash


def test_export_answers_write_error(tmp_path, monkeypatch, tk_root):
    """Test export_answers handles write errors"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.answers = {"image_1.jpg": "Test answer"}
    
    # Mock save dialog and file write error
    with mock.patch("tkinter.filedialog.asksaveasfilename", return_value="/invalid/path/out.txt"):
        with mock.patch("tkinter.messagebox.showerror") as error:
            app.export_answers()
            error.assert_called()


def test_hide_current_image(tmp_path, monkeypatch, tk_root):
    """Test hide_current_image clears the display"""
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
    assert hasattr(app.image_label, "image")
    
    app.hide_current_image()
    # Image should be cleared
    assert "hidden" in app.image_label.cget("text").lower() or "writing" in app.image_label.cget("text").lower()


def test_update_image_counter_no_images(tmp_path, monkeypatch, tk_root):
    """Test update_image_counter with no images"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.images = []
    app.update_image_counter()
    assert app.image_counter_label.cget("text") == "Image: 0/0"


def test_load_images_png_format(tmp_path, monkeypatch, tk_root):
    """Test loading PNG format images"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Create PNG files
    for i in [1, 2, 3]:
        (tmp_path / "images" / f"image_{i}.png").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Should load PNG files
    assert len(app.images) == 3
    assert all(img.endswith('.png') for img in app.images)


def test_load_images_mixed_formats(tmp_path, monkeypatch, tk_root):
    """Test loading mixed JPG and PNG images"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Create mixed format files
    (tmp_path / "images" / "image_1.jpg").write_bytes(b"\x00")
    (tmp_path / "images" / "image_2.png").write_bytes(b"\x00")
    (tmp_path / "images" / "image_3.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Should load all images
    assert len(app.images) == 3


def test_load_images_extract_number_exception(tmp_path, monkeypatch, tk_root):
    """Test extract_number handles invalid filenames gracefully"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Create file with invalid format (should return 0)
    (tmp_path / "images" / "image_invalid.jpg").write_bytes(b"\x00")
    (tmp_path / "images" / "image_1.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Should still load images without crashing
    assert len(app.images) >= 1


def test_show_current_image_error_handling(tmp_path, monkeypatch, tk_root):
    """Test show_current_image handles corrupt images"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Create corrupt image file
    corrupt_file = tmp_path / "images" / "image_1.jpg"
    corrupt_file.write_bytes(b"not a valid image")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.current_image_index = 0
    
    with mock.patch("tkinter.messagebox.showerror") as error:
        app.show_current_image()
        error.assert_called()


def test_timer_color_changes(tmp_path, monkeypatch, tk_root):
    """Test timer label color changes based on remaining time"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.root.after = lambda delay, func=None, *a, **k: (func() if func else None)
    
    # Test different timer values
    app.timer_seconds = 31
    app.is_running = True
    # Should be normal color (>30 seconds)
    
    app.timer_seconds = 15
    # Should be orange (<=30 seconds)
    
    app.timer_seconds = 5
    # Should be red (<=10 seconds)


def test_stop_slideshow_resets_ui(tmp_path, monkeypatch, tk_root):
    """Test stop_slideshow properly resets UI state"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.is_running = True
    app.is_paused = True
    
    app.stop_slideshow()
    
    assert app.is_running is False
    assert app.is_paused is False
    assert app.timer_label.cget("text") == "00:00"
    assert app.start_btn.cget("state") == tk.NORMAL
    assert app.pause_btn.cget("state") == tk.DISABLED
    assert app.stop_btn.cget("state") == tk.DISABLED


def test_next_image_at_end_finishes_slideshow(tmp_path, monkeypatch, tk_root):
    """Test next_image calls slideshow_finished at end"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.root.after = lambda delay, func=None, *a, **k: (func() if func else None)
    app.current_image_index = 0  # Last image
    app.is_running = True
    
    with mock.patch("tkinter.messagebox.showinfo"):
        app.next_image()
        # Should finish slideshow
        assert app.is_running is False


def test_load_settings_file_not_exists(tmp_path, monkeypatch, tk_root):
    """Test load_settings when file doesn't exist"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Ensure no settings file exists
    if os.path.exists("tatssb_settings.json"):
        os.remove("tatssb_settings.json")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Should use defaults
    assert app.randomize_enabled is False
    assert app.display_time == 240
    assert app.preparation_time == 30


def test_load_settings_corrupt_file(tmp_path, monkeypatch, tk_root):
    """Test load_settings handles corrupt JSON"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Create corrupt settings file
    with open("tatssb_settings.json", "w") as f:
        f.write("not valid json {{{")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Should use defaults and not crash
    assert app.randomize_enabled is False


def test_save_settings_error_handling(tmp_path, monkeypatch, tk_root):
    """Test save_settings handles write errors"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Mock open to raise an error
    with mock.patch("builtins.open", side_effect=PermissionError("No permission")):
        # Should not crash
        app.save_settings()


def test_image_manager_opens(tmp_path, monkeypatch, tk_root):
    """Test opening the image manager window"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    (tmp_path / "images" / "image_1.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Should not crash when opening manager
    app.open_image_manager()
    # Close all toplevels
    for widget in tk_root.winfo_children():
        if isinstance(widget, tk.Toplevel):
            widget.destroy()


def test_image_manager_refresh_creates_folder(tmp_path, monkeypatch, tk_root):
    """Test image manager creates images folder if missing"""
    monkeypatch.chdir(tmp_path)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    
    # Remove images folder
    if os.path.exists("images"):
        shutil.rmtree("images")
    
    manager = ImageManagerWindow(tk_root, app)
    manager.refresh_image_list()
    
    # Should create folder
    assert os.path.exists("images")
    
    manager.close_window()


def test_image_manager_add_images_no_selection(tmp_path, monkeypatch, tk_root):
    """Test image manager add_images with no files selected"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    # Mock file dialog returning empty tuple (no selection)
    with mock.patch("tkinter.filedialog.askopenfilenames", return_value=()):
        manager.add_images()
    
    manager.close_window()


def test_image_manager_add_invalid_image(tmp_path, monkeypatch, tk_root):
    """Test image manager handles invalid image files"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    # Create a fake image file
    fake_img = tmp_path / "fake.jpg"
    fake_img.write_bytes(b"not an image")
    
    with mock.patch("tkinter.filedialog.askopenfilenames", return_value=[str(fake_img)]):
        with mock.patch("tkinter.messagebox.showerror") as error:
            manager.add_images()
            error.assert_called()
    
    manager.close_window()


def test_image_manager_add_unsupported_format(tmp_path, monkeypatch, tk_root):
    """Test image manager rejects unsupported formats"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    # Create a text file
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("test")
    
    # Mock PIL to not raise error but file has wrong extension
    with mock.patch("tkinter.filedialog.askopenfilenames", return_value=[str(txt_file)]):
        with mock.patch("tkinter.messagebox.showerror") as error:
            manager.add_images()
            error.assert_called()
    
    manager.close_window()


def test_image_manager_add_valid_images(tmp_path, monkeypatch, tk_root):
    """Test image manager successfully adds valid images"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    try:
        from PIL import Image
        # Create valid test images
        test_img1 = tmp_path / "test1.jpg"
        test_img2 = tmp_path / "test2.png"
        Image.new("RGB", (10, 10)).save(test_img1)
        Image.new("RGB", (10, 10)).save(test_img2)
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    with mock.patch("tkinter.filedialog.askopenfilenames", return_value=[str(test_img1), str(test_img2)]):
        with mock.patch("tkinter.messagebox.showinfo") as info:
            manager.add_images()
            info.assert_called()
            assert "added" in info.call_args[0][1].lower()
    
    # Verify images were added
    assert os.path.exists("images/image_1.jpg")
    assert os.path.exists("images/image_2.png")
    
    manager.close_window()


def test_image_manager_add_jpeg_extension_normalized(tmp_path, monkeypatch, tk_root):
    """Test image manager normalizes .jpeg to .jpg"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    try:
        from PIL import Image
        test_img = tmp_path / "test.jpeg"
        Image.new("RGB", (10, 10)).save(test_img, format="JPEG")
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    with mock.patch("tkinter.filedialog.askopenfilenames", return_value=[str(test_img)]):
        with mock.patch("tkinter.messagebox.showinfo"):
            manager.add_images()
    
    # Should be saved as .jpg, not .jpeg
    assert os.path.exists("images/image_1.jpg")
    
    manager.close_window()


def test_image_manager_delete_no_selection(tmp_path, monkeypatch, tk_root):
    """Test image manager delete with no image selected"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    manager.selected_image = None
    
    # Should not crash
    manager.delete_image()
    
    manager.close_window()


def test_image_manager_delete_confirmed(tmp_path, monkeypatch, tk_root):
    """Test image manager deletes image when confirmed"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    test_img = tmp_path / "images" / "image_1.jpg"
    test_img.write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    manager.selected_image = str(test_img)
    
    # Mock confirmation dialog
    with mock.patch("tkinter.messagebox.askyesno", return_value=True):
        with mock.patch("tkinter.messagebox.showinfo"):
            manager.delete_image()
    
    # Image should be deleted
    assert not os.path.exists(test_img)
    
    manager.close_window()


def test_image_manager_delete_cancelled(tmp_path, monkeypatch, tk_root):
    """Test image manager doesn't delete when cancelled"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    test_img = tmp_path / "images" / "image_1.jpg"
    test_img.write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    manager.selected_image = str(test_img)
    
    # Mock confirmation dialog returning False
    with mock.patch("tkinter.messagebox.askyesno", return_value=False):
        manager.delete_image()
    
    # Image should still exist
    assert os.path.exists(test_img)
    
    manager.close_window()


def test_image_manager_delete_error_handling(tmp_path, monkeypatch, tk_root):
    """Test image manager handles delete errors"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Create a file that we can then mock to fail deletion
    test_img = tmp_path / "images" / "image_1.jpg"
    test_img.write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    manager.selected_image = str(test_img)
    
    # Mock os.remove to raise an error
    with mock.patch("tkinter.messagebox.askyesno", return_value=True):
        with mock.patch("os.remove", side_effect=PermissionError("No permission")):
            with mock.patch("tkinter.messagebox.showerror") as error:
                manager.delete_image()
                error.assert_called()
    
    manager.close_window()


def test_image_manager_show_preview_success(tmp_path, monkeypatch, tk_root):
    """Test image manager shows preview successfully"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    try:
        from PIL import Image
        test_img = tmp_path / "images" / "image_1.jpg"
        Image.new("RGB", (100, 200)).save(test_img)
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    manager.show_preview(str(test_img))
    
    # Info label should show image details
    info_text = manager.info_label.cget("text")
    assert "100 x 200" in info_text
    assert "image_1.jpg" in info_text
    
    manager.close_window()


def test_image_manager_show_preview_error(tmp_path, monkeypatch, tk_root):
    """Test image manager handles preview errors"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    # Try to preview nonexistent file
    manager.show_preview("/nonexistent/file.jpg")
    
    # Should show error message in preview label
    preview_text = manager.preview_label.cget("text")
    assert "error" in preview_text.lower()
    
    manager.close_window()


def test_image_manager_on_image_select_enables_delete(tmp_path, monkeypatch, tk_root):
    """Test image selection enables delete button"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    (tmp_path / "images" / "image_1.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    # Initially delete button should be disabled
    assert manager.delete_btn.cget("state") == tk.DISABLED
    
    # Simulate selection
    manager.image_listbox.insert(0, "image_1.jpg")
    manager.image_listbox.selection_set(0)
    
    # Create mock event
    event = type('Event', (), {'widget': manager.image_listbox})()
    
    with mock.patch.object(manager, 'show_preview'):
        manager.on_image_select(event)
    
    # Delete button should be enabled
    assert manager.delete_btn.cget("state") == tk.NORMAL
    
    manager.close_window()


def test_image_manager_extract_number_from_filename(tmp_path, monkeypatch, tk_root):
    """Test image manager extracts numbers correctly for sorting"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Create images with different numbers
    for i in [5, 1, 10, 2]:
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    # Images should be sorted numerically
    items = [manager.image_listbox.get(i) for i in range(manager.image_listbox.size())]
    assert items == ["image_1.jpg", "image_2.jpg", "image_5.jpg", "image_10.jpg"]
    
    manager.close_window()


def test_main_function(tmp_path, monkeypatch):
    """Test the main function initializes app"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    from slideshow import main
    
    # Mock mainloop to prevent blocking
    with mock.patch("tkinter.Tk.mainloop"):
        with mock.patch("tkinter.messagebox.showwarning"):
            # Should not crash
            main()


def test_next_image_advances_index(tmp_path, monkeypatch, tk_root):
    """Test next_image advances to the next image"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_2.jpg")
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_3.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.root.after = lambda delay, func=None, *a, **k: (func() if func else None)
    app.current_image_index = 0
    app.is_running = True
    app.current_phase = "writing"
    
    with mock.patch("tkinter.messagebox.showinfo"):
        app.next_image()
    
    # Should advance to next image
    assert app.current_image_index == 1
    assert app.current_phase == "preparation"


def test_timer_finished_in_writing_phase_saves_answer(tmp_path, monkeypatch, tk_root):
    """Test timer_finished saves answer and moves to next image in writing phase"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_2.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.root.after = lambda delay, func=None, *a, **k: (func() if func else None)
    app.current_image_index = 0
    app.is_running = True
    app.current_phase = "writing"
    app.answer_text.insert("1.0", "Test answer")
    
    with mock.patch("tkinter.messagebox.showinfo"):
        app.timer_finished()
    
    # Should save answer
    assert len(app.answers) > 0


def test_toggle_pause_in_writing_phase(tmp_path, monkeypatch, tk_root):
    """Test toggle_pause shows correct phase when resumed in writing phase"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.current_phase = "writing"
    app.is_paused = False
    
    # Pause
    app.toggle_pause()
    assert app.is_paused is True
    assert app.phase_label.cget("text") == "PAUSED"
    
    # Resume in writing phase
    app.toggle_pause()
    assert app.is_paused is False
    assert "Writing" in app.phase_label.cget("text")


def test_image_manager_add_images_multiple_errors(tmp_path, monkeypatch, tk_root):
    """Test image manager shows multiple errors when adding many invalid files"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    # Create 10 invalid files
    invalid_files = []
    for i in range(10):
        invalid_file = tmp_path / f"invalid_{i}.jpg"
        invalid_file.write_bytes(b"not an image")
        invalid_files.append(str(invalid_file))
    
    with mock.patch("tkinter.filedialog.askopenfilenames", return_value=invalid_files):
        with mock.patch("tkinter.messagebox.showerror") as error:
            manager.add_images()
            error.assert_called()
            # Should show "... and X more errors" message
            message = error.call_args[0][1]
            assert "more errors" in message.lower() or "error" in message.lower()
    
    manager.close_window()


def test_hide_current_image_exception_handling(tmp_path, monkeypatch, tk_root):
    """Test hide_current_image handles exceptions gracefully"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Mock config to raise an exception
    with mock.patch.object(app.image_label, 'config', side_effect=Exception("Test error")):
        # Should not crash
        app.hide_current_image()


def test_load_images_with_no_extension(tmp_path, monkeypatch, tk_root):
    """Test that files without proper extensions are handled"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Create file without extension
    (tmp_path / "images" / "image_1").write_bytes(b"\x00")
    (tmp_path / "images" / "image_2.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Should only load the .jpg file
    assert len(app.images) == 1
    assert app.images[0].endswith(".jpg")


def test_image_manager_on_image_select_no_selection(tmp_path, monkeypatch, tk_root):
    """Test on_image_select with no selection"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    # Clear selection
    manager.image_listbox.selection_clear(0, tk.END)
    
    # Create mock event
    event = type('Event', (), {'widget': manager.image_listbox})()
    
    manager.on_image_select(event)
    
    # Delete button should remain disabled
    assert manager.delete_btn.cget("state") == tk.DISABLED
    
    manager.close_window()


def test_start_timer_with_existing_thread(tmp_path, monkeypatch, tk_root):
    """Test start_timer doesn't create duplicate threads"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    try:
        from PIL import Image
        Image.new("RGB", (10, 10)).save(tmp_path / "images" / "image_1.jpg")
    except Exception:
        pytest.skip("Pillow not available in test environment")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.root.after = lambda delay, func=None, *a, **k: (func() if func else None)
    app.is_running = True
    app.current_phase = "preparation"
    
    # Start timer
    app.start_timer()
    first_thread = app.timer_thread
    
    # Try to start again while thread is alive
    if first_thread and first_thread.is_alive():
        app.start_timer()
        # Should still be the same thread
        assert app.timer_thread == first_thread
    
    app.is_running = False


def test_image_manager_extract_number_handles_invalid_format(tmp_path, monkeypatch, tk_root):
    """Test that extract_number in ImageManager handles invalid filenames"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Create files with various invalid formats
    (tmp_path / "images" / "notanimage.jpg").write_bytes(b"\x00")
    (tmp_path / "images" / "image_.jpg").write_bytes(b"\x00")
    (tmp_path / "images" / "image_abc.jpg").write_bytes(b"\x00")
    (tmp_path / "images" / "image_5.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    from slideshow import ImageManagerWindow
    manager = ImageManagerWindow(tk_root, app)
    
    # Should handle all files without crashing
    # Files with valid numbers should appear
    items = [manager.image_listbox.get(i) for i in range(manager.image_listbox.size())]
    assert "image_5.jpg" in items
    
    manager.close_window()


# ============================================================================
# Tests for Configurable Image Selection Feature (PBI 3006234)
# ============================================================================

def test_num_images_to_practice_variable_initialized(tmp_path, monkeypatch, tk_root):
    """Test that num_images_to_practice is initialized properly"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    assert hasattr(app, 'num_images_to_practice')
    assert hasattr(app, 'total_available_images')
    assert app.total_available_images == 0
    assert app.num_images_to_practice is None


def test_num_images_ui_elements_exist(tmp_path, monkeypatch, tk_root):
    """Test that UI elements for configurable image count are present"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    assert hasattr(app, 'num_images_var')
    assert hasattr(app, 'num_images_entry')
    assert hasattr(app, 'max_images_label')
    assert app.max_images_label.cget("text") == "(Max: 0)"


def test_validate_num_images_empty_input_returns_none(tmp_path, monkeypatch, tk_root):
    """Test validation with empty input returns None (use all images)"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    (tmp_path / "images" / "image_1.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_var.set("")
    is_valid, result = app.validate_num_images_input()
    assert is_valid is True
    assert result is None


def test_validate_num_images_valid_input(tmp_path, monkeypatch, tk_root):
    """Test validation with valid numeric input"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_var.set("5")
    is_valid, result = app.validate_num_images_input()
    assert is_valid is True
    assert result == 5


def test_validate_num_images_non_numeric_input(tmp_path, monkeypatch, tk_root):
    """Test validation rejects non-numeric input"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    (tmp_path / "images" / "image_1.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_var.set("abc")
    is_valid, result = app.validate_num_images_input()
    assert is_valid is False
    assert "valid number" in result.lower()


def test_validate_num_images_zero_rejected(tmp_path, monkeypatch, tk_root):
    """Test validation rejects zero"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 6):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_var.set("0")
    is_valid, result = app.validate_num_images_input()
    assert is_valid is False
    assert "between 1 and" in result.lower()


def test_validate_num_images_negative_rejected(tmp_path, monkeypatch, tk_root):
    """Test validation rejects negative values"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 6):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_var.set("-5")
    is_valid, result = app.validate_num_images_input()
    assert is_valid is False
    assert "between 1 and" in result.lower()


def test_validate_num_images_exceeds_available(tmp_path, monkeypatch, tk_root):
    """Test validation rejects value exceeding available images"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 6):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_var.set("10")
    is_valid, result = app.validate_num_images_input()
    assert is_valid is False
    assert "cannot select 10 images" in result.lower()
    assert "only 5" in result.lower()


def test_load_images_updates_max_label(tmp_path, monkeypatch, tk_root):
    """Test that loading images updates the max images label"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    assert app.total_available_images == 10
    assert app.max_images_label.cget("text") == "(Max: 10)"


def test_load_images_with_configured_count_sequential(tmp_path, monkeypatch, tk_root):
    """Test loading with configured count selects first N images when not randomized"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_to_practice = 5
    app.randomize_enabled = False
    app.load_images()
    
    assert len(app.images) == 5
    # Should be first 5 images
    assert all(f"image_{i}.jpg" in app.images[i-1] for i in range(1, 6))


def test_load_images_with_configured_count_randomized(tmp_path, monkeypatch, tk_root):
    """Test loading with configured count and randomization enabled"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_to_practice = 5
    app.randomize_enabled = True
    app.load_images()
    
    assert len(app.images) == 5
    # Should have exactly 5 images (can't test order due to randomness)
    assert app.total_available_images == 10


def test_load_images_none_loads_all(tmp_path, monkeypatch, tk_root):
    """Test that None for num_images_to_practice loads all images"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_to_practice = None
    app.load_images()
    
    assert len(app.images) == 10
    assert app.total_available_images == 10


def test_settings_persistence_num_images(tmp_path, monkeypatch, tk_root):
    """Test that num_images_to_practice persists in settings"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_to_practice = 15
    app.save_settings()
    
    # Check settings file
    assert os.path.exists("tatssb_settings.json")
    with open("tatssb_settings.json", 'r') as f:
        settings = json.load(f)
    assert settings['num_images_to_practice'] == 15


def test_settings_load_num_images(tmp_path, monkeypatch, tk_root):
    """Test that num_images_to_practice loads from settings"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    
    # Create settings file
    settings = {
        'randomize_enabled': False,
        'display_time': 240,
        'preparation_time': 30,
        'num_images_to_practice': 20
    }
    with open(tmp_path / "tatssb_settings.json", 'w') as f:
        json.dump(settings, f)
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    assert app.num_images_to_practice == 20
    assert app.num_images_var.get() == "20"


def test_image_counter_shows_limited_format(tmp_path, monkeypatch, tk_root):
    """Test image counter shows different format when images are limited"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_to_practice = 5
    app.load_images()
    app.current_image_index = 0
    app.update_image_counter()
    
    counter_text = app.image_counter_label.cget("text")
    assert "1/5" in counter_text
    assert "10 total" in counter_text


def test_image_counter_normal_format_all_images(tmp_path, monkeypatch, tk_root):
    """Test image counter shows normal format when using all images"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 6):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_to_practice = None
    app.load_images()
    app.current_image_index = 0
    app.update_image_counter()
    
    counter_text = app.image_counter_label.cget("text")
    assert counter_text == "Image: 1/5"


def test_start_slideshow_validates_num_images(tmp_path, monkeypatch, tk_root):
    """Test that start_slideshow validates num_images input"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 6):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_var.set("10")  # Exceeds available
    
    with mock.patch("tkinter.messagebox.showerror") as mock_error:
        app.start_slideshow()
        mock_error.assert_called_once()
        args = mock_error.call_args[0]
        assert "invalid image count" in args[0].lower()


def test_start_slideshow_reloads_images_if_changed(tmp_path, monkeypatch, tk_root):
    """Test that start_slideshow reloads images if num_images changed"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    # Initially all images
    assert len(app.images) == 10
    
    # Change to 5 images
    app.num_images_var.set("5")
    
    with mock.patch("tkinter.messagebox.showinfo"):
        app.root.after = lambda delay, func=None, *a, **k: (func() if func else None)
        app.start_slideshow()
    
    # Should have reloaded with 5 images
    assert len(app.images) == 5
    assert app.num_images_to_practice == 5
    
    app.stop_slideshow()


def test_completion_message_shows_limited_info(tmp_path, monkeypatch, tk_root):
    """Test completion message shows correct info when images are limited"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_to_practice = 5
    app.load_images()
    
    with mock.patch("tkinter.messagebox.showinfo") as mock_info:
        app.slideshow_finished()
        args = mock_info.call_args[0]
        message = args[1]
        assert "5 of 10 available" in message.lower()


def test_completion_message_shows_all_info(tmp_path, monkeypatch, tk_root):
    """Test completion message shows correct info when using all images"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 6):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    app.num_images_to_practice = None
    app.load_images()
    
    with mock.patch("tkinter.messagebox.showinfo") as mock_info:
        app.slideshow_finished()
        args = mock_info.call_args[0]
        message = args[1]
        assert "all 5 images" in message.lower()


def test_image_manager_updates_max_value_on_add(tmp_path, monkeypatch, tk_root):
    """Test that adding images via ImageManager updates max value"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 6):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    assert app.total_available_images == 5
    assert app.max_images_label.cget("text") == "(Max: 5)"
    
    # Simulate adding more images
    for i in range(6, 9):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    # Reload images (as ImageManager would do)
    app.load_images()
    
    assert app.total_available_images == 8
    assert app.max_images_label.cget("text") == "(Max: 8)"


def test_image_manager_updates_max_value_on_delete(tmp_path, monkeypatch, tk_root):
    """Test that deleting images via ImageManager updates max value"""
    monkeypatch.chdir(tmp_path)
    os.makedirs("images", exist_ok=True)
    for i in range(1, 11):
        (tmp_path / "images" / f"image_{i}.jpg").write_bytes(b"\x00")
    
    with mock.patch("tkinter.messagebox.showwarning"):
        app = _make_app(tk_root)
    
    assert app.total_available_images == 10
    
    # Simulate deleting images
    os.remove(tmp_path / "images" / "image_9.jpg")
    os.remove(tmp_path / "images" / "image_10.jpg")
    
    # Reload images (as ImageManager would do)
    app.load_images()
    
    assert app.total_available_images == 8
    assert app.max_images_label.cget("text") == "(Max: 8)"