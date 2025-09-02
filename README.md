# TATSSB - TAT Image Slideshow Tool

A comprehensive TAT (Thematic Apperception Test) practice application designed for SSB (Services Selection Board) preparation. This tool provides a structured environment for practicing TAT story writing with timed sessions and answer management.

## Features

- **Timed Practice Sessions**: Configurable preparation and writing phases
- **Image Management**: Supports automatic loading of numbered images
- **Story Writing Interface**: Dedicated text area for writing TAT stories
- **Answer Management**: Save, edit, and export all your answers
- **Progress Tracking**: Visual timer and phase indicators
- **User-friendly Interface**: Modern GUI with intuitive controls

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

### 1. Starting a Practice Session
- Ensure images are placed in the `images` folder
- Configure display time and preparation time (default: 30 seconds each)
- Click "Start Test" to begin

### 2. Practice Phases
- **Preparation Phase**: Study the image and plan your story
- **Writing Phase**: Write your TAT story in the text area

### 3. Writing Guidelines
Your TAT story should cover:
- What is happening in the image?
- What led to this situation?
- What are the characters thinking/feeling?
- What will happen next?

### 4. Managing Answers
- **Save Answer**: Save your current story
- **Clear**: Clear the current text area
- **Export All**: Export all saved answers to a text file

### 5. Controls
- **Pause/Resume**: Pause or resume the current session
- **Stop**: Stop the current session
- **Next ?**: Manually move to the next image

## Project Structure
TATSSB/
??? slideshow.py          # Main application file
??? requirements.txt      # Python dependencies
??? Pipfile              # Pipenv configuration
??? Pipfile.lock         # Pipenv lock file
??? README.md            # This file
??? read_data.json       # Configuration/data file
??? images/              # Folder for TAT images (created automatically)
    ??? image_1.jpg
    ??? image_2.jpg
    ??? ...
## Configuration

### Timing Configuration
You can adjust timing settings directly in the application interface:
- **Display Time**: Duration for the writing phase (default: 30 seconds)
- **Preparation Time**: Duration for studying the image (default: 30 seconds)

### Image Requirements
- **Format**: JPG or PNG files
- **Naming**: Must follow the pattern `image_X.jpg` where X is a number
- **Location**: Place all images in the `images` folder
- **Sorting**: Images are automatically sorted numerically

## Troubleshooting

### Common Issues

1. **"No images found" error**:
   - Check that images are in the `images` folder
   - Ensure images follow the naming convention: `image_1.jpg`, `image_2.jpg`, etc.
   - Verify image formats are supported (JPG, PNG)

2. **"Module not found" errors**:
   - Run `pip install -r requirements.txt` to install dependencies
   - For Pipenv users: `pipenv install`

3. **Application won't start**:
   - Ensure Python 3.8+ is installed
   - Check that tkinter is available (usually included with Python)
   - Try running from command line to see error messages

4. **Images not displaying properly**:
   - Check image file integrity
   - Ensure images are not corrupted
   - Try with different image formats

### System Requirements
- **Windows**: Windows 7 or later
- **macOS**: macOS 10.9 or later  
- **Linux**: Most modern distributions
- **RAM**: Minimum 2GB (4GB recommended for large images)
- **Storage**: Depends on image collection size

## Development

### Running in Development Mode# Install development dependencies
pip install -r requirements.txt

# Run the application
python slideshow.py
### Building Executable (Windows)
To create a standalone executable:pip install pyinstaller
pyinstaller --onefile --windowed slideshow.py
## Support

If you encounter any issues or need help:
1. Check the troubleshooting section above
2. Ensure all requirements are properly installed
3. Verify your Python version is 3.8 or higher
4. Make sure images are properly formatted and placed

## License

This project is designed for educational and practice purposes for SSB TAT preparation.
