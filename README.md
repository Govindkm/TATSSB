# TATSSB - TAT Image Slideshow Tool

A comprehensive TAT (Thematic Apperception Test) practice application designed for SSB (Services Selection Board) preparation. This tool provides a structured environment for practicing TAT story writing with timed sessions and answer management.

## Features

### Core Features
- **Timed Practice Sessions**: Configurable preparation and writing phases
- **Story Writing Interface**: Dedicated text area for writing TAT stories
- **Answer Management**: Save, edit, and export all your answers
- **Progress Tracking**: Visual timer and phase indicators
- **User-friendly Interface**: Modern GUI with intuitive controls

### 🆕 New Features (v2.0)
- **🎲 Image Randomization**: Toggle to display images in random order for better practice
- **🖼️ Advanced Image Manager**: Complete interface to add, remove, and preview images
  - Add multiple images at once with automatic numbering
  - Preview images before using them
  - Delete images with confirmation
  - View image details (dimensions, file size)
  - Format validation (JPG, PNG)
- **💾 Settings Persistence**: All preferences saved automatically across sessions
- **✅ Comprehensive Testing**: Full test coverage for reliability

## Requirements

- **Python 3.8+** (Python 3.8 or higher recommended)
- **tkinter** (included with Python standard library)
- **Pillow** (PIL fork for image processing)

## Installation and Setup

### Method 1: Using pip (Recommended)

1. **Clone or download the project**:git clone <repository-url>
cd TATSSB   
   Or download and extract the ZIP file.

2. **Install Python dependencies**:pip install -r requirements.txt
3. **Set up the images folder**:
   - The application will automatically create an `images` folder if it doesn't exist
   - Place your TAT images in the `images` folder
   - Name them in the format: `image_1.jpg`, `image_2.jpg`, `image_3.jpg`, etc.
   - Supported formats: `.jpg`, `.png`

### Method 2: Using Pipenv

1. **Install Pipenv** (if not already installed):pip install pipenv
2. **Clone or download the project**:git clone <repository-url>
cd TATSSB
3. **Install dependencies using Pipenv**:pipenv install
4. **Activate the virtual environment**:pipenv shell
5. **Set up images** (same as Method 1, step 3)

## How to Run the Application

### Using Python directly:python slideshow.py
### Using Pipenv:pipenv run python slideshow.py
### For Windows users:
If available, you can use the `slideshow.exe` file to run the application directly without Python installation.

## Usage Guide

### 1. Managing Images (New!)
**Using the Image Manager**:
- Click the purple **"Manage Images"** button in the main window
- **Add Images**: Click "Add New Images" to upload JPG/PNG files (supports multiple selection)
- **Preview**: Select any image to see a preview and details
- **Delete**: Select an image and click "Delete Selected" (with confirmation)
- All changes apply immediately to your practice sessions

**Quick Tip**: You can still add images manually to the `images` folder using the format `image_N.jpg`

### 2. Randomization Feature (New!)
- Check the **"Randomize Images"** checkbox in the settings panel
- When enabled, images appear in random order (each image shown exactly once)
- Uncheck for sequential order
- Setting is saved automatically for next session

### 3. Starting a Practice Session
- Ensure images are loaded (use Image Manager or place in `images` folder)
- Configure display time and preparation time (default: 240 seconds display, 30 seconds prep)
- Optionally enable randomization
- Click "Start Test" to begin

### 4. Practice Phases
- **Preparation Phase**: Study the image and plan your story
- **Writing Phase**: Image is hidden while you write your TAT story

### 5. Writing Guidelines
Your TAT story should cover:
- What is happening in the image?
- What led to this situation?
- What are the characters thinking/feeling?
- What will happen next?

### 6. Managing Answers
- **Save Answer**: Save your current story
- **Clear**: Clear the current text area
- **Export All**: Export all saved answers to a text file

### 7. Controls
- **Pause/Resume**: Pause or resume the current session
- **Stop**: Stop the current session
- **Next →**: Manually move to the next image
- **Manage Images**: Open the image management window

## Project Structure
TATSSB/
├── slideshow.py              # Main application file (457 lines)
├── requirements.txt          # Python dependencies
├── requirements-dev.txt      # Development dependencies
├── Pipfile                   # Pipenv configuration
├── Pipfile.lock             # Pipenv lock file
├── pytest.ini               # Pytest configuration
├── README.md                # This file
├── IMPLEMENTATION_SUMMARY.md # Detailed feature documentation
├── USER_GUIDE.md            # User guide for new features
├── DEMO_SCRIPT.md           # Demo/presentation guide
├── tatssb_settings.json     # Settings file (auto-created)
├── images/                  # Folder for TAT images (created automatically)
│   ├── image_1.jpg
│   ├── image_2.jpg
│   └── ...
└── tests/                   # Test suite
    └── test_slideshow.py    # Unit and integration tests
## Configuration

### Timing Configuration
You can adjust timing settings directly in the application interface:
- **Display Time**: Duration for the writing phase (default: 240 seconds / 4 minutes)
- **Preparation Time**: Duration for studying the image (default: 30 seconds)
- Settings are automatically saved and restored on restart

### Image Requirements
- **Format**: JPG, JPEG, or PNG files
- **Naming**: Pattern `image_X.jpg` where X is a number (auto-managed by Image Manager)
- **Location**: Place all images in the `images` folder
- **Sorting**: Images are automatically sorted numerically (or randomized if enabled)

### Settings File (New!)
- Automatically created as `tatssb_settings.json`
- Stores: randomization preference, timing settings
- Persists across application restarts
- Can be manually deleted to reset to defaults

## Troubleshooting

### Common Issues

1. **"No images found" error**:
   - Use the **Image Manager** to add images (click "Manage Images" button)
   - Or manually place images in the `images` folder
   - Ensure images follow the naming convention: `image_1.jpg`, `image_2.jpg`, etc.
   - Verify image formats are supported (JPG, JPEG, PNG)

2. **"Module not found" errors**:
   - Run `pip install -r requirements.txt` to install dependencies
   - For Pipenv users: `pipenv install`

3. **Application won't start**:
   - Ensure Python 3.8+ is installed
   - Check that tkinter is available (usually included with Python)
   - Try running from command line to see error messages

4. **Images not displaying properly**:
   - Use Image Manager preview to check image integrity
   - Ensure images are not corrupted
   - Try with different image formats
   - Check file size (very large images may load slowly)

5. **Randomization not working**:
   - Ensure the "Randomize Images" checkbox is checked
   - Start a NEW session (existing sessions continue with current order)
   - Check that `tatssb_settings.json` is not write-protected

6. **Can't add images in Image Manager**:
   - Ensure files are valid JPG/JPEG/PNG images
   - Check that you have write permissions in the application folder
   - Verify images are not corrupted (try opening in image viewer first)

### System Requirements
- **Windows**: Windows 7 or later
- **macOS**: macOS 10.9 or later  
- **Linux**: Most modern distributions
- **RAM**: Minimum 2GB (4GB recommended for large images)
- **Storage**: Depends on image collection size

## Development

### Running in Development Mode
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run the application
python slideshow.py

# Run tests
pytest tests/test_slideshow.py -v

# Run tests with coverage
pytest tests/test_slideshow.py --cov=slideshow --cov-report=html
```

### Testing
The application includes comprehensive unit and integration tests:
- **12 tests** covering all major features
- **55% code coverage** (focused on critical paths)
- Tests for randomization, image loading, timers, answers, and persistence

Run tests with:
```bash
pytest tests/test_slideshow.py -v
```

### Building Executable (Windows)
To create a standalone executable:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed slideshow.py
```

## Recent Updates (v2.0)

### November 3, 2025
- ✅ Added image randomization feature with toggle
- ✅ Implemented comprehensive Image Manager interface
- ✅ Added settings persistence (JSON-based)
- ✅ Enhanced UI with new controls and feedback
- ✅ Added 6 new tests for randomization features
- ✅ Improved image preview and validation
- ✅ Added batch image upload capability
- ✅ All 12 tests passing with 55% coverage

See `IMPLEMENTATION_SUMMARY.md` for detailed information.
## Support

If you encounter any issues or need help:
1. Check the troubleshooting section above
2. Ensure all requirements are properly installed
3. Verify your Python version is 3.8 or higher
4. Make sure images are properly formatted and placed

## License

This project is designed for educational and practice purposes for SSB TAT preparation.
