# PixelBead Grid Helper

Pixel bead grid helper tool for quickly adding, editing, and exporting grid lines on bead embroidery patterns.

## Table of Contents

- [Project Introduction](#project-introduction)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Usage Guide](#detailed-usage-guide)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Tech Stack](#tech-stack)
- [Development](#development)
- [License](#license)

## Project Introduction

PixelBead Grid Helper is an auxiliary tool for pixel bead (perler bead) pattern design. It provides an intuitive interface that allows you to quickly add, edit, and manage grid lines on images, helping you precisely locate and plan your bead patterns.

## Features

### 🎨 Interface Themes
- **Four theme styles**: Dark Standard, Light Standard, Dark Pixel, Light Pixel
- Real-time theme switching for different use cases

### 🔍 View Control
- **Zoom functions**:
  - Zoom in/out buttons
  - 100% view (original size)
  - Fit to screen (auto-adjust to window size)
  - Mouse wheel zoom (centered at mouse position)
  - Zoom range: 10% - 500%
- **Pan functions**:
  - Space + left mouse button drag
  - Middle mouse button drag
  - Scrollbars automatically shown when canvas exceeds window

### 📏 Grid Line Management
- **Add lines**:
  - Add horizontal and vertical lines
  - Click anywhere on the image to add
- **Edit lines**:
  - Drag to adjust position after selection
  - Delete selected lines (button or Delete key)
- **Batch fill**:
  - Auto-fill horizontal/vertical lines at equal intervals
  - Boundary leave-empty principle
  - Auto-copy all properties of original line (color, thickness, style)
- **Crop function**:
  - Drag to draw selection box
  - Only delete parts inside selection box
  - Keep both sides of lines

### ✏️ Line Properties
- **Thickness adjustment**:
  - Slider control (1-10px)
  - Real-time preview
- **Custom color**:
  - Built-in color picker
  - Supports RGB/HEX input
  - Batch modify multiple lines
- **Style switching**:
  - Solid line
  - Dashed line
  - Dotted line

### 🎯 Selection System
- **Single select**: Click single line to select
- **Multi select**: Shift + click
- **Box select**: Use box select tool to drag and select multiple lines
- **Select all/Deselect all**: Ctrl+A / Ctrl+Shift+A
- **Selected state display**:
  - Highlighted (red)
  - Control points at both ends and middle

### 📏 Distance Calculation
- **Calculate distance between two parallel lines**:
  - Click "Calculate Distance" button
  - Select two parallel lines in sequence
  - Display distance (in pixels)
  - Auto-verify if lines are parallel

### ⏪ Undo/Redo
- Supports Ctrl+Z / Ctrl+Y keyboard shortcuts
- Up to 50 history operations recorded

### 📷 Export Function
- Export image + grid lines
- Supports PNG and JPG formats
- Default save to `output` folder in project root
- Auto-create output folder

## Directory Structure

```
pixelbead-grid-helper/
├── src/                      # Source code directory
│   ├── __init__.py
│   ├── main.py              # Program entry
│   ├── model.py             # Data model
│   ├── view.py              # Interface view
│   └── controller.py        # Logic controller
├── assets/                   # Resource files (icons, etc.)
├── output/                   # Output folder (auto-created)
├── requirements.txt           # Dependency list
├── project_rule.md           # Project rules document
├── README.md                # Chinese documentation
├── README_EN.md             # English documentation
└── LICENSE                  # License
```

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Installation Steps

1. **Clone or download the project**

   ```bash
   git clone <repository-url>
   cd pixelbead-grid-helper
   ```

2. **Create virtual environment (recommended)**

   Windows:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   Linux/Mac:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the program**

   ```bash
   python src/main.py
   ```

## Quick Start

1. **Open image**: Click "Open" button in toolbar, select image to add grid lines to
2. **Add grid lines**: Click "Add Horizontal" or "Add Vertical", then click position on image
3. **Edit lines**: Select lines and drag to adjust position, or press Delete to remove
4. **Adjust properties**: Use controls in right panel to adjust line thickness, color, and style
5. **Export image**: Click "Export" button, save image+grid lines to `output` folder

## Detailed Usage Guide

### 1. Opening Images

- Click "Open" button in toolbar
- Select image file in file dialog
- Supported formats: PNG, JPG, JPEG, BMP, GIF, WEBP
- Image will automatically fit to screen size

### 2. Adding Grid Lines

#### Adding Horizontal Lines
1. Click "Add Horizontal" button in toolbar or right panel
2. Button will highlight to indicate add mode
3. Click position on image where you want to add horizontal line
4. Horizontal line will be added at clicked y-coordinate

#### Adding Vertical Lines
1. Click "Add Vertical" button in toolbar or right panel
2. Button will highlight to indicate add mode
3. Click position on image where you want to add vertical line
4. Vertical line will be added at clicked x-coordinate

### 3. Selecting and Editing Lines

#### Selecting Lines
- **Single select**: Directly click single line
- **Multi select**: Hold Shift key, click multiple lines in sequence
- **Box select**:
  1. Click "Box Select" button
  2. Drag on image to draw selection box
  3. Release mouse, all lines inside box will be selected
- **Select all**: Press Ctrl+A or click "Select All" button in toolbar
- **Deselect**:
  - Click on empty space
  - Press Ctrl+Shift+A
  - Press Esc key

#### Editing Lines
- **Move position**: After selecting lines, hold left mouse button and drag
- **Delete lines**:
  - Select lines and press Delete key
  - Click "Delete Selected" button in right panel
  - Click "Delete" button in toolbar

### 4. Adjusting Line Properties

#### Setting Default Properties
- When no lines are selected, adjusting property controls modifies default values
- Next line added will use these default properties

#### Modifying Properties of Selected Lines
- After selecting one or more lines, adjusting property controls modifies all selected lines in real-time
- Supports batch modification

#### Thickness Adjustment
- Use "Thickness" slider in right panel
- Range: 1-10 pixels
- Current value displayed on right

#### Color Adjustment
1. Click "Color" button in right panel (shows current color preview)
2. Select color in popup color picker
3. Supports RGB, HEX, HSV color modes

#### Style Adjustment
- Use "Style" dropdown in right panel
- Options:
  - Solid (default)
  - Dashed
  - Dotted

### 5. Batch Filling Grid Lines

1. Select one horizontal or vertical line
2. Set "Spacing" value in right panel (in pixels)
3. Click "Fill Horizontal" or "Fill Vertical" button
4. System will auto-fill all lines at equal intervals
5. New lines will copy all properties of original line (color, thickness, style)

**Fill Rules**:
- Based on selected line, copy upwards/downwards (horizontal) or leftwards/rightwards (vertical) at equal intervals
- Boundary leave-empty: Do not exceed image boundaries
- Skip existing positions

### 6. Cropping Grid Lines

1. Click "Crop" button in toolbar
2. Button will highlight to indicate crop mode
3. Drag on image to draw crop box
4. Release mouse, parts intersecting with crop box will be deleted
5. Both sides of lines will be kept
6. Press Esc to cancel crop mode

### 7. Calculating Distance Between Two Parallel Lines

1. Click "Calculate Distance" button in toolbar
2. Button will highlight to indicate calculation mode
3. Click first line (horizontal or vertical)
4. Click second line (must be same direction as first)
5. Popup dialog shows:
   - Position of first line
   - Position of second line
   - Distance between two lines (in pixels)
6. Click "OK" to close dialog

### 8. View Control

#### Zooming Canvas
- **Button control**:
  - Zoom in: Click "Zoom In" button, 1.2x each time
  - Zoom out: Click "Zoom Out" button, 0.8x each time
  - 100%: Click "100%" button, restore original size
  - Fit to screen: Click "Fit to Screen" button, auto-adjust to window size
- **Mouse wheel**:
  - Scroll up: Zoom in
  - Scroll down: Zoom out
  - Zoom centered at mouse position

#### Panning Canvas
- **Space + left button**:
  1. Hold Space key
  2. Mouse changes to "hand"
  3. Hold left button and drag to pan
  4. Release Space to exit pan mode
- **Middle mouse button**: Directly hold middle button and drag to pan

### 9. Undo and Redo

- **Undo**:
  - Press Ctrl+Z
  - Click "Undo" button in toolbar
  - Up to 50 undo steps
- **Redo**:
  - Press Ctrl+Y
  - Click "Redo" button in toolbar

### 10. Exporting Images

1. Click "Export" button in toolbar
2. In save dialog select:
   - Save location (default in `output` folder in project root)
   - File name
   - File format (PNG or JPG)
3. Click "Save"
4. Image will be saved at original image size, including all grid lines

### 11. Switching Themes

- Select theme from "Theme" dropdown in toolbar
- Options:
  - Dark Standard (default)
  - Light Standard
  - Dark Pixel
  - Light Pixel
- Theme will be immediately applied to entire interface

## Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| Ctrl+Z | Undo operation |
| Ctrl+Y | Redo operation |
| Ctrl+A | Select all lines |
| Ctrl+Shift+A | Deselect all |
| Delete | Delete selected lines |
| Esc | Cancel operation/exit mode |
| Space | Hold + left button drag to pan canvas |
| Middle Mouse | Drag to pan canvas |
| Mouse Wheel | Zoom canvas |

## Tech Stack

- **Python 3.x** - Programming language
- **PyQt6** - GUI framework
- **Pillow** - Image processing library

## Architecture Design

Project uses classic **MVC (Model-View-Controller)** architecture:

### Model (model.py)
- `ImageModel`: Manages image and grid line data
- `GridLine`: Grid line data class
- Maintains operation history, supports undo/redo

### View (view.py)
- `MainWindow`: Main window
- `CanvasWidget`: Custom canvas component
- `HelpDialog`: Help dialog
- `DistanceDialog`: Distance calculation dialog
- Four theme style definitions

### Controller (controller.py)
- Connects Model and View
- Handles user interaction logic
- Implements business functions

## Development

### Project Rules

Detailed project rules can be found in `project_rule.md` file.

### Dependency Management

Project dependencies are listed in `requirements.txt`:
- PyQt6
- Pillow

### Code Standards

- Use type annotations
- Follow PEP 8 code style
- MVC architecture separation
- All keyboard shortcuts implemented with QShortcut

## License

MIT License

See LICENSE file for details.

## Contributing

Issues and Pull Requests are welcome!

## Contact

For questions or suggestions, please submit an Issue.
