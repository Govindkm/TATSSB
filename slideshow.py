import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
import os
import glob
import threading
import time

class TATSlideshowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TATSSB - TAT Image Slideshow Tool")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.images = []
        self.current_image_index = 0
        self.timer_seconds = 0
        self.is_running = False
        self.is_paused = False
        self.display_time = 30  # Default 30 seconds per image
        self.preparation_time = 30  # Default 30 seconds preparation
        self.timer_thread = None
        self.current_phase = "preparation"  # "preparation" or "writing"
        
        self.setup_ui()
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
        
        # Settings frame
        settings_frame = tk.Frame(control_frame, bg='#e8e8e8')
        settings_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(settings_frame, text="Display Time (sec):", bg='#e8e8e8', font=('Arial', 10)).pack()
        self.display_time_var = tk.StringVar(value="30")
        display_time_entry = tk.Entry(settings_frame, textvariable=self.display_time_var, width=5)
        display_time_entry.pack()
        
        tk.Label(settings_frame, text="Prep Time (sec):", bg='#e8e8e8', font=('Arial', 10)).pack()
        self.prep_time_var = tk.StringVar(value="30")
        prep_time_entry = tk.Entry(settings_frame, textvariable=self.prep_time_var, width=5)
        prep_time_entry.pack()
        
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
        
    def load_images(self):
        """Load images from the images folder"""
        image_folder = "images"
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)
            messagebox.showwarning("No Images", "Images folder created. Please add images in format: image_1.jpg, image_2.jpg, etc.")
            return
            
        # Load images in numerical order
        image_files = glob.glob(os.path.join(image_folder, "image_*.jpg"))
        image_files.extend(glob.glob(os.path.join(image_folder, "image_*.png")))
        
        if not image_files:
            messagebox.showwarning("No Images", "No images found. Please add images in format: image_1.jpg, image_2.jpg, etc.")
            return
            
        # Sort by number in filename
        def extract_number(filename):
            try:
                return int(filename.split('image_')[1].split('.')[0])
            except:
                return 0
                
        image_files.sort(key=extract_number)
        self.images = image_files
        self.update_image_counter()
        
        if self.images:
            self.image_label.config(text=f"Loaded {len(self.images)} images\nReady to start TAT practice")
            
    def update_image_counter(self):
        """Update the image counter display"""
        total = len(self.images)
        current = self.current_image_index + 1 if self.images else 0
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
        messagebox.showinfo("Complete", f"TAT practice session completed!\nAnswered {len(self.answers)} images.")
        
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

def main():
    root = tk.Tk()
    app = TATSlideshowApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()