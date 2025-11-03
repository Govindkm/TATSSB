import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
import os
import glob
import threading
import time
import random
import json
import shutil

class TATSlideshowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TATSSB - TAT Image Slideshow Tool")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.images = []
        self.original_images = []  # Keep track of original order
        self.current_image_index = 0
        self.timer_seconds = 0
        self.is_running = False
        self.is_paused = False
        self.display_time = 240  # Default 30 seconds per image
        self.preparation_time = 30  # Default 30 seconds preparation
        self.timer_thread = None
        self.current_phase = "preparation"  # "preparation" or "writing"
        self.randomize_enabled = False  # Randomization toggle
        self.num_images_to_practice = None  # Number of images to practice (None = all)
        self.total_available_images = 0  # Total images available in folder
        self.settings_file = "tatssb_settings.json"
        
        self.load_settings()
        self.setup_ui()
        
        # Update UI with loaded settings after UI is created
        if self.num_images_to_practice:
            self.num_images_var.set(str(self.num_images_to_practice))
        
        self.load_images()
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top control panel
        control_frame = tk.Frame(main_frame, bg='#e8e8e8', relief=tk.RAISED, bd=2)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Timer and status display
        timer_frame = tk.Frame(control_frame, bg='#e8e8e8')
        timer_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.timer_label = tk.Label(timer_frame, text="00:00", font=('Arial', 24, 'bold'), 
                                   fg='#2c3e50', bg='#e8e8e8')
        self.timer_label.pack()
        
        self.phase_label = tk.Label(timer_frame, text="Ready to Start", font=('Arial', 12), 
                                   fg='#34495e', bg='#e8e8e8')
        self.phase_label.pack()
        
        self.image_counter_label = tk.Label(timer_frame, text="Image: 0/0", font=('Arial', 10), 
                                           fg='#7f8c8d', bg='#e8e8e8')
        self.image_counter_label.pack()
        
        # Control buttons
        button_frame = tk.Frame(control_frame, bg='#e8e8e8')
        button_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.start_btn = tk.Button(button_frame, text="Start Test", command=self.start_slideshow,
                                  bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                  padx=20, pady=5)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = tk.Button(button_frame, text="Pause", command=self.toggle_pause,
                                  bg='#f39c12', fg='white', font=('Arial', 12),
                                  padx=20, pady=5, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(button_frame, text="Stop", command=self.stop_slideshow,
                                 bg='#e74c3c', fg='white', font=('Arial', 12),
                                 padx=20, pady=5, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(button_frame, text="Next →", command=self.next_image,
                                 bg='#3498db', fg='white', font=('Arial', 12),
                                 padx=15, pady=5, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        self.manage_btn = tk.Button(button_frame, text="Manage Images", command=self.open_image_manager,
                                    bg='#9b59b6', fg='white', font=('Arial', 12),
                                    padx=15, pady=5)
        self.manage_btn.pack(side=tk.LEFT, padx=5)
        
        # Settings frame
        settings_frame = tk.Frame(control_frame, bg='#e8e8e8')
        settings_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(settings_frame, text="Display Time (sec):", bg='#e8e8e8', font=('Arial', 10)).pack()
        self.display_time_var = tk.StringVar(value=self.display_time)
        display_time_entry = tk.Entry(settings_frame, textvariable=self.display_time_var, width=5)
        display_time_entry.pack()
        
        tk.Label(settings_frame, text="Prep Time (sec):", bg='#e8e8e8', font=('Arial', 10)).pack()
        self.prep_time_var = tk.StringVar(value=self.preparation_time)
        prep_time_entry = tk.Entry(settings_frame, textvariable=self.prep_time_var, width=5)
        prep_time_entry.pack()
        
        # Randomization toggle
        self.randomize_var = tk.BooleanVar(value=self.randomize_enabled)
        randomize_check = tk.Checkbutton(settings_frame, text="Randomize Images", 
                                        variable=self.randomize_var, bg='#e8e8e8',
                                        font=('Arial', 10), command=self.toggle_randomize)
        randomize_check.pack(pady=(5, 0))
        
        # Number of images to practice
        tk.Label(settings_frame, text="Number of Images:", bg='#e8e8e8', font=('Arial', 10)).pack(pady=(5, 0))
        num_images_frame = tk.Frame(settings_frame, bg='#e8e8e8')
        num_images_frame.pack()
        self.num_images_var = tk.StringVar(value="")
        self.num_images_entry = tk.Entry(num_images_frame, textvariable=self.num_images_var, width=5)
        self.num_images_entry.pack(side=tk.LEFT)
        self.max_images_label = tk.Label(num_images_frame, text="(Max: 0)", bg='#e8e8e8', 
                                         font=('Arial', 9), fg='#7f8c8d')
        self.max_images_label.pack(side=tk.LEFT, padx=(3, 0))
        
        # Tooltip label
        tooltip_label = tk.Label(settings_frame, text="Leave empty for all images", 
                               bg='#e8e8e8', font=('Arial', 8), fg='#95a5a6')
        tooltip_label.pack()
        
        # Content area
        content_frame = tk.Frame(main_frame, bg='#f0f0f0')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Image display
        image_frame = tk.Frame(content_frame, bg='white', relief=tk.SUNKEN, bd=2)
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.image_label = tk.Label(image_frame, text="Load images to begin\nPlace images in 'images' folder\nFormat: image_1.jpg, image_2.jpg, etc.", 
                                   font=('Arial', 14), bg='white', fg='#7f8c8d')
        self.image_label.pack(expand=True)
        
        # Right panel - Answer input
        answer_frame = tk.Frame(content_frame, bg='#ecf0f1', relief=tk.RAISED, bd=2)
        answer_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        answer_frame.config(width=400)
        answer_frame.pack_propagate(False)
        
        # Answer input header
        answer_header = tk.Label(answer_frame, text="TAT Story Writing", font=('Arial', 14, 'bold'), 
                                bg='#34495e', fg='white', pady=10)
        answer_header.pack(fill=tk.X)
        
        # Current image info
        self.current_image_info = tk.Label(answer_frame, text="Image: Not Started", 
                                          font=('Arial', 12), bg='#ecf0f1', fg='#2c3e50')
        self.current_image_info.pack(pady=5)
        
        # Instructions
        instructions = tk.Label(answer_frame, 
                               text="Write your story covering:\n• What is happening?\n• What led to this situation?\n• What are the characters thinking/feeling?\n• What will happen next?",
                               font=('Arial', 10), bg='#ecf0f1', fg='#5d6d7e', justify=tk.LEFT)
        instructions.pack(pady=10, padx=10, anchor=tk.W)
        
        # Answer text area
        self.answer_text = scrolledtext.ScrolledText(answer_frame, wrap=tk.WORD, font=('Arial', 11),
                                                    height=20, bg='white')
        self.answer_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Answer controls
        answer_controls = tk.Frame(answer_frame, bg='#ecf0f1')
        answer_controls.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.save_answer_btn = tk.Button(answer_controls, text="Save Answer", command=self.save_current_answer,
                                        bg='#16a085', fg='white', font=('Arial', 10))
        self.save_answer_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_answer_btn = tk.Button(answer_controls, text="Clear", command=self.clear_current_answer,
                                         bg='#95a5a6', fg='white', font=('Arial', 10))
        self.clear_answer_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = tk.Button(answer_controls, text="Export All", command=self.export_answers,
                                   bg='#8e44ad', fg='white', font=('Arial', 10))
        self.export_btn.pack(side=tk.RIGHT)
        
        # Storage for answers
        self.answers = {}
        
    def hide_current_image(self):
        """Hide the image during writing/display phase."""
        # Clear any image reference and show a neutral message/background
        try:
            self.image_label.config(image="", text="Writing phase in progress\nImage hidden", fg='#7f8c8d')
            # Remove reference to prevent Tk keeping the old image
            if hasattr(self.image_label, "image"):
                self.image_label.image = None
        except Exception:
            pass

    def load_images(self):
        """Load images from the images folder"""
        image_folder = "images"
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)
            messagebox.showwarning("No Images", "Images folder created. Please add images in format: image_1.jpg, image_2.jpg, etc.")
            self.total_available_images = 0
            self.max_images_label.config(text="(Max: 0)")
            return
            
        # Load images in numerical order
        image_files = glob.glob(os.path.join(image_folder, "image_*.jpg"))
        image_files.extend(glob.glob(os.path.join(image_folder, "image_*.png")))
        
        if not image_files:
            messagebox.showwarning("No Images", "No images found. Please add images in format: image_1.jpg, image_2.jpg, etc.")
            self.total_available_images = 0
            self.max_images_label.config(text="(Max: 0)")
            return
            
        # Sort by number in filename
        def extract_number(filename):
            try:
                return int(filename.split('image_')[1].split('.')[0])
            except:
                return 0
                
        image_files.sort(key=extract_number)
        self.original_images = image_files.copy()  # Keep original order
        self.total_available_images = len(image_files)
        
        # Update max images label
        self.max_images_label.config(text=f"(Max: {self.total_available_images})")
        
        # Determine how many images to use
        num_to_use = self.num_images_to_practice if self.num_images_to_practice else self.total_available_images
        
        # Select images based on configuration
        if num_to_use < self.total_available_images:
            # Apply randomization if enabled
            if self.randomize_enabled:
                selected_images = random.sample(image_files, num_to_use)
            else:
                selected_images = image_files[:num_to_use]
            self.images = selected_images
        else:
            # Use all images
            if self.randomize_enabled:
                self.images = image_files.copy()
                random.shuffle(self.images)
            else:
                self.images = image_files
            
        self.update_image_counter()
        
        if self.images:
            randomize_status = " (Randomized)" if self.randomize_enabled else ""
            self.image_label.config(text=f"Loaded {len(self.images)} images{randomize_status}\nReady to start TAT practice")
    
    def validate_num_images_input(self):
        """
        Validate the number of images input.
        Returns (is_valid, num_images_or_error_msg)
        If is_valid is True, second value is the validated number (or None for all images)
        If is_valid is False, second value is the error message
        """
        input_value = self.num_images_var.get().strip()
        
        # Empty input means use all images
        if not input_value:
            return True, None
        
        # Check if input is numeric
        try:
            num_images = int(input_value)
        except ValueError:
            return False, "Please enter a valid number."
        
        # Check for zero or negative values
        if num_images <= 0:
            return False, f"Please enter a value between 1 and {self.total_available_images}."
        
        # Check if exceeds available images
        if num_images > self.total_available_images:
            return False, f"Cannot select {num_images} images. Only {self.total_available_images} images available."
        
        return True, num_images
            
    def update_image_counter(self):
        """Update the image counter display"""
        total = len(self.images)
        current = self.current_image_index + 1 if self.images else 0
        
        # Show different format if images are limited vs all images
        if self.num_images_to_practice and self.num_images_to_practice < self.total_available_images:
            self.image_counter_label.config(text=f"Image: {current}/{total} (of {self.total_available_images} total)")
        else:
            self.image_counter_label.config(text=f"Image: {current}/{total}")
        
    def start_slideshow(self):
        """Start the slideshow"""
        if not self.images:
            messagebox.showwarning("No Images", "Please load images first!")
            return
            
        try:
            self.display_time = int(self.display_time_var.get())
            self.preparation_time = int(self.prep_time_var.get())
        except ValueError:
            messagebox.showerror("Invalid Time", "Please enter valid time values!")
            return
        
        # Validate num_images_to_practice input
        is_valid, result = self.validate_num_images_input()
        if not is_valid:
            messagebox.showerror("Invalid Image Count", result)
            return
        
        # Update num_images_to_practice and reload images if changed
        new_num_images = result
        if new_num_images != self.num_images_to_practice:
            self.num_images_to_practice = new_num_images
            self.save_settings()
            self.load_images()  # Reload with new configuration
        
        # Show confirmation message
        randomize_text = " (randomized)" if self.randomize_enabled else ""
        if self.num_images_to_practice:
            confirmation = f"Starting test with {len(self.images)} images{randomize_text}"
        else:
            confirmation = f"Starting test with all {len(self.images)} images{randomize_text}"
        self.phase_label.config(text=confirmation)
        self.root.update()
        time.sleep(0.5)  # Brief pause to show confirmation
            
        self.is_running = True
        self.is_paused = False
        self.current_image_index = 0
        self.current_phase = "preparation"
        
        # Update UI state
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        self.next_btn.config(state=tk.NORMAL)
        
        self.show_current_image()
        self.start_timer()
        
    def show_current_image(self):
        """Display the current image"""
        if self.current_image_index < len(self.images):
            image_path = self.images[self.current_image_index]
            
            try:
                # Load and resize image
                pil_image = Image.open(image_path)
                
                # Calculate size to fit in display area (keeping aspect ratio)
                display_width = 700
                display_height = 500
                
                img_width, img_height = pil_image.size
                ratio = min(display_width/img_width, display_height/img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(pil_image)
                
                self.image_label.config(image=photo, text="")
                self.image_label.image = photo  # Keep a reference
                
                # Update answer panel
                image_name = os.path.basename(image_path)
                self.current_image_info.config(text=f"Current: {image_name}")
                
                # Load existing answer if any
                if image_name in self.answers:
                    self.answer_text.delete(1.0, tk.END)
                    self.answer_text.insert(1.0, self.answers[image_name])
                else:
                    self.answer_text.delete(1.0, tk.END)
                    
                self.update_image_counter()
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image: {e}")
                
    def start_timer(self):
        """Start the timer for current phase"""
        if self.current_phase == "preparation":
            self.timer_seconds = self.preparation_time
            self.phase_label.config(text="Preparation Phase", fg='#e67e22')
        else:  # writing phase
            self.timer_seconds = self.display_time
            self.phase_label.config(text="Writing Phase", fg='#27ae60')
            # Ensure image is hidden whenever writing timer starts (covers resume cases)
            self.hide_current_image()
            
        if self.timer_thread and self.timer_thread.is_alive():
            return
            
        self.timer_thread = threading.Thread(target=self.timer_countdown, daemon=True)
        self.timer_thread.start()
        
    def timer_countdown(self):
        """Timer countdown logic"""
        while self.timer_seconds > 0 and self.is_running:
            if not self.is_paused:
                minutes = self.timer_seconds // 60
                seconds = self.timer_seconds % 60
                self.root.after(0, lambda: self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}"))
                
                # Color coding for urgency
                if self.timer_seconds <= 10:
                    self.root.after(0, lambda: self.timer_label.config(fg='#e74c3c'))  # Red
                elif self.timer_seconds <= 30:
                    self.root.after(0, lambda: self.timer_label.config(fg='#f39c12'))  # Orange
                else:
                    self.root.after(0, lambda: self.timer_label.config(fg='#2c3e50'))  # Dark blue
                    
                self.timer_seconds -= 1
            time.sleep(1)
            
        if self.is_running:
            self.root.after(0, self.timer_finished)
            
    def timer_finished(self):
        """Handle timer completion"""
        if self.current_phase == "preparation":
            # Switch to writing phase
            self.current_phase = "writing"
            # Hide image as soon as writing/display time starts
            self.hide_current_image()
            self.start_timer()
        else:
            # Move to next image or finish
            self.save_current_answer()  # Auto-save current answer
            self.next_image()
            
    def next_image(self):
        """Move to the next image"""
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.current_phase = "preparation"
            self.show_current_image()
            self.start_timer()
        else:
            self.slideshow_finished()
            
    def slideshow_finished(self):
        """Handle slideshow completion"""
        self.stop_slideshow()
        
        # Show completion message with proper context
        if self.num_images_to_practice and self.num_images_to_practice < self.total_available_images:
            completion_msg = f"TAT practice session completed!\n\n"
            completion_msg += f"Completed {len(self.images)} of {self.total_available_images} available images.\n"
            completion_msg += f"Answered {len(self.answers)} images."
        else:
            completion_msg = f"TAT practice session completed!\n\n"
            completion_msg += f"Completed all {len(self.images)} images.\n"
            completion_msg += f"Answered {len(self.answers)} images."
        
        messagebox.showinfo("Complete", completion_msg)
        
    def toggle_pause(self):
        """Pause or resume the slideshow"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.config(text="Resume", bg='#27ae60')
            self.phase_label.config(text="PAUSED", fg='#e74c3c')
        else:
            self.pause_btn.config(text="Pause", bg='#f39c12')
            if self.current_phase == "preparation":
                self.phase_label.config(text="Preparation Phase", fg='#e67e22')
            else:
                self.phase_label.config(text="Writing Phase", fg='#27ae60')
                
    def stop_slideshow(self):
        """Stop the slideshow"""
        self.is_running = False
        self.is_paused = False
        
        # Reset UI state
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="Pause", bg='#f39c12')
        self.stop_btn.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        
        self.timer_label.config(text="00:00", fg='#2c3e50')
        self.phase_label.config(text="Stopped", fg='#7f8c8d')
        
    def save_current_answer(self):
        """Save the current answer"""
        if self.current_image_index < len(self.images):
            image_name = os.path.basename(self.images[self.current_image_index])
            answer = self.answer_text.get(1.0, tk.END).strip()
            self.answers[image_name] = answer
            messagebox.showinfo("Saved", f"Answer saved for {image_name}")
            
    def clear_current_answer(self):
        """Clear the current answer"""
        self.answer_text.delete(1.0, tk.END)
        
    def export_answers(self):
        """Export all answers to a text file"""
        if not self.answers:
            messagebox.showwarning("No Answers", "No answers to export!")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save TAT Answers"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("TAT Practice Session Answers\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for image_name, answer in self.answers.items():
                        f.write(f"Image: {image_name}\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"{answer}\n\n")
                        
                messagebox.showinfo("Exported", f"Answers exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not export answers: {e}")
    
    def load_settings(self):
        """Load settings from JSON file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.randomize_enabled = settings.get('randomize_enabled', False)
                    self.display_time = settings.get('display_time', 240)
                    self.preparation_time = settings.get('preparation_time', 30)
                    self.num_images_to_practice = settings.get('num_images_to_practice', None)
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            settings = {
                'randomize_enabled': self.randomize_enabled,
                'display_time': self.display_time,
                'preparation_time': self.preparation_time,
                'num_images_to_practice': self.num_images_to_practice
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def toggle_randomize(self):
        """Toggle randomization setting"""
        self.randomize_enabled = self.randomize_var.get()
        self.save_settings()
        if self.randomize_enabled:
            messagebox.showinfo("Randomization", "Images will be randomized in the next session.")
        else:
            messagebox.showinfo("Randomization", "Images will be shown in sequential order.")
    
    def open_image_manager(self):
        """Open the image management window"""
        ImageManagerWindow(self.root, self)

class ImageManagerWindow:
    """Window for managing images in the application"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = tk.Toplevel(parent)
        self.window.title("Image Manager - TATSSB")
        self.window.geometry("900x700")
        self.window.configure(bg='#f0f0f0')
        
        self.image_folder = "images"
        self.selected_image = None
        self.preview_photo = None
        
        self.setup_ui()
        self.refresh_image_list()
    
    def setup_ui(self):
        """Setup the image manager UI"""
        # Title
        title_label = tk.Label(self.window, text="Image Management", 
                              font=('Arial', 16, 'bold'), bg='#34495e', fg='white', pady=10)
        title_label.pack(fill=tk.X)
        
        # Main content frame
        content_frame = tk.Frame(self.window, bg='#f0f0f0')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Image list
        left_frame = tk.Frame(content_frame, bg='#ecf0f1', relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        list_header = tk.Label(left_frame, text="Current Images", 
                              font=('Arial', 12, 'bold'), bg='#34495e', fg='white', pady=5)
        list_header.pack(fill=tk.X)
        
        # Scrollable listbox
        list_scroll_frame = tk.Frame(left_frame, bg='#ecf0f1')
        list_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.image_listbox = tk.Listbox(list_scroll_frame, yscrollcommand=scrollbar.set,
                                       font=('Arial', 10), selectmode=tk.SINGLE)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        scrollbar.config(command=self.image_listbox.yview)
        
        # Control buttons for list
        list_button_frame = tk.Frame(left_frame, bg='#ecf0f1')
        list_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.delete_btn = tk.Button(list_button_frame, text="Delete Selected", 
                                    command=self.delete_image, bg='#e74c3c', fg='white',
                                    font=('Arial', 10), state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=2)
        
        refresh_btn = tk.Button(list_button_frame, text="Refresh List", 
                               command=self.refresh_image_list, bg='#3498db', fg='white',
                               font=('Arial', 10))
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Right panel - Preview and actions
        right_frame = tk.Frame(content_frame, bg='#ecf0f1', relief=tk.RAISED, bd=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        preview_header = tk.Label(right_frame, text="Image Preview", 
                                 font=('Arial', 12, 'bold'), bg='#34495e', fg='white', pady=5)
        preview_header.pack(fill=tk.X)
        
        # Preview area
        self.preview_frame = tk.Frame(right_frame, bg='white', relief=tk.SUNKEN, bd=2)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_label = tk.Label(self.preview_frame, text="Select an image to preview", 
                                     font=('Arial', 12), bg='white', fg='#7f8c8d')
        self.preview_label.pack(expand=True)
        
        # Image info
        self.info_label = tk.Label(right_frame, text="", font=('Arial', 9), 
                                  bg='#ecf0f1', fg='#2c3e50', justify=tk.LEFT)
        self.info_label.pack(fill=tk.X, padx=5)
        
        # Action buttons
        action_frame = tk.Frame(right_frame, bg='#ecf0f1')
        action_frame.pack(fill=tk.X, padx=5, pady=10)
        
        add_btn = tk.Button(action_frame, text="Add New Images", 
                           command=self.add_images, bg='#27ae60', fg='white',
                           font=('Arial', 11, 'bold'), pady=5)
        add_btn.pack(fill=tk.X, pady=2)
        
        # Validation info
        info_text = ("Supported formats: JPG, PNG\n"
                    "Naming convention: image_N.jpg or image_N.png\n"
                    "where N is a number")
        info_display = tk.Label(right_frame, text=info_text, font=('Arial', 9), 
                               bg='#ecf0f1', fg='#7f8c8d', justify=tk.LEFT)
        info_display.pack(padx=5, pady=5)
        
        # Bottom button frame
        bottom_frame = tk.Frame(self.window, bg='#f0f0f0')
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        close_btn = tk.Button(bottom_frame, text="Close", command=self.close_window,
                             bg='#95a5a6', fg='white', font=('Arial', 11), padx=20)
        close_btn.pack(side=tk.RIGHT)
    
    def refresh_image_list(self):
        """Refresh the list of images"""
        self.image_listbox.delete(0, tk.END)
        
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
            return
        
        # Get all image files
        image_files = glob.glob(os.path.join(self.image_folder, "image_*.jpg"))
        image_files.extend(glob.glob(os.path.join(self.image_folder, "image_*.png")))
        
        # Sort by number
        def extract_number(filename):
            try:
                return int(os.path.basename(filename).split('image_')[1].split('.')[0])
            except:
                return 0
        
        image_files.sort(key=extract_number)
        
        for img_file in image_files:
            self.image_listbox.insert(tk.END, os.path.basename(img_file))
    
    def on_image_select(self, event):
        """Handle image selection"""
        selection = self.image_listbox.curselection()
        if not selection:
            self.delete_btn.config(state=tk.DISABLED)
            return
        
        self.delete_btn.config(state=tk.NORMAL)
        index = selection[0]
        filename = self.image_listbox.get(index)
        self.selected_image = os.path.join(self.image_folder, filename)
        
        # Show preview
        self.show_preview(self.selected_image)
    
    def show_preview(self, image_path):
        """Display image preview"""
        try:
            # Load image
            pil_image = Image.open(image_path)
            
            # Get image info
            width, height = pil_image.size
            file_size = os.path.getsize(image_path)
            size_kb = file_size / 1024
            
            info_text = f"Filename: {os.path.basename(image_path)}\n"
            info_text += f"Dimensions: {width} x {height} pixels\n"
            info_text += f"Size: {size_kb:.1f} KB"
            self.info_label.config(text=info_text)
            
            # Resize for preview
            preview_width = 400
            preview_height = 400
            ratio = min(preview_width/width, preview_height/height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(pil_image)
            
            self.preview_label.config(image=self.preview_photo, text="")
            
        except Exception as e:
            self.preview_label.config(image="", text=f"Error loading preview:\n{str(e)}")
            self.info_label.config(text="")
    
    def add_images(self):
        """Add new images to the collection"""
        filenames = filedialog.askopenfilenames(
            title="Select Images to Add",
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        
        if not filenames:
            return
        
        # Get next available number
        existing_images = glob.glob(os.path.join(self.image_folder, "image_*.jpg"))
        existing_images.extend(glob.glob(os.path.join(self.image_folder, "image_*.png")))
        
        max_num = 0
        for img in existing_images:
            try:
                num = int(os.path.basename(img).split('image_')[1].split('.')[0])
                max_num = max(max_num, num)
            except:
                pass
        
        next_num = max_num + 1
        added_count = 0
        errors = []
        
        for filename in filenames:
            try:
                # Validate file is an image
                Image.open(filename).verify()
                
                # Get file extension
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png']:
                    errors.append(f"{os.path.basename(filename)}: Unsupported format")
                    continue
                
                # Normalize extension to .jpg or .png
                if ext == '.jpeg':
                    ext = '.jpg'
                
                # Copy to images folder with proper naming
                dest_filename = f"image_{next_num}{ext}"
                dest_path = os.path.join(self.image_folder, dest_filename)
                
                shutil.copy2(filename, dest_path)
                added_count += 1
                next_num += 1
                
            except Exception as e:
                errors.append(f"{os.path.basename(filename)}: {str(e)}")
        
        # Show results
        message = f"Successfully added {added_count} image(s)."
        if errors:
            message += f"\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                message += f"\n... and {len(errors) - 5} more errors"
        
        if added_count > 0:
            messagebox.showinfo("Images Added", message)
            self.refresh_image_list()
            # Reload images in main app
            self.app.load_images()
        else:
            messagebox.showerror("No Images Added", message)
    
    def delete_image(self):
        """Delete selected image"""
        if not self.selected_image or not os.path.exists(self.selected_image):
            return
        
        filename = os.path.basename(self.selected_image)
        result = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete '{filename}'?\n\nThis action cannot be undone.")
        
        if result:
            try:
                os.remove(self.selected_image)
                messagebox.showinfo("Deleted", f"'{filename}' has been deleted.")
                self.refresh_image_list()
                self.preview_label.config(image="", text="Select an image to preview")
                self.info_label.config(text="")
                self.preview_photo = None
                self.selected_image = None
                self.delete_btn.config(state=tk.DISABLED)
                
                # Reload images in main app
                self.app.load_images()
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete image: {e}")
    
    def close_window(self):
        """Close the image manager window"""
        self.window.destroy()


def main():
    root = tk.Tk()
    app = TATSlideshowApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()