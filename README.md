# Blackbox

A real-time screen overlay tool that detects and highlights items using computer vision template matching. Built for tracking in-game inventory items in **ARC Raiders**.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Real-time Detection** — Template matching with color-aware verification using LAB color space
- **Visual Overlay** — Non-intrusive bounding boxes drawn over detected items
- **Sidebar UI** — Dark-themed settings panel with item filtering and search
- **Persistence** — Selected items are saved and restored between sessions
- **Global Hotkeys** — Toggle overlay visibility with keyboard shortcuts
- **Cross-platform** — Runs on Windows and macOS

## Screenshots

*Coming soon*

## Installation

### Requirements

- Python 3.11+
- Windows 10/11 or macOS 12+

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/Blackbox.git
cd Blackbox

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python run_blackbox.py
```

### From Release

Download the latest release from the [Releases](https://github.com/yourusername/Blackbox/releases) page:

- **Windows**: Download `Blackbox-windows.zip`, extract, and run `Blackbox.exe`
- **macOS**: Download `Blackbox-mac.zip`, extract, and run `Blackbox.app`

## Usage

1. **Launch the app** — A sidebar will appear on the right side of your screen
2. **Select items** — Check the items you want to detect from the list
3. **Enable overlay** — Toggle "Enable boxes overlay" to show detection boxes
4. **Adjust threshold** — Use the slider to tune detection sensitivity (higher = stricter matching)

### Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl+Shift+H` | Toggle overlay visibility |

### Sidebar Controls

- **Search** — Filter items by name
- **Show Selected Only** — Display only checked items
- **Show All** — Show all available items
- **Deselect All** — Uncheck all items
- **Threshold Slider** — Adjust detection confidence (0.5 - 1.0)

## Adding Custom Templates

Templates are stored in `assets/templates/` as PNG images.

1. Capture a clean image of the item you want to detect
2. Crop tightly around the item (no extra padding)
3. Save as `item_name.png` in `assets/templates/`
4. Add a corresponding entry in `src/blackbox/catalog.py`:

```python
CatalogItem(id="item_name", name="Item Name", template_labels=["item_name"]),
```

## Project Structure

```
Blackbox/
├── assets/
│   └── templates/          # Template images for detection
├── src/
│   └── blackbox/
│       ├── main.py         # Application entry point
│       ├── catalog.py      # Item definitions
│       ├── settings.py     # Configuration constants
│       ├── capture/        # Screen capture utilities
│       ├── hotkeys/        # Global hotkey handling
│       ├── ui/             # PyQt6 UI components
│       ├── utils/          # Path utilities
│       └── vision/         # Template matching & tracking
├── run_blackbox.py         # Launch script
├── requirements.txt        # Python dependencies
└── Blackbox.spec          # PyInstaller build spec
```

## Building

### Windows

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean Blackbox.spec
```

Output: `dist/Blackbox/Blackbox.exe`

### macOS

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed \
    --name Blackbox \
    --paths src \
    --collect-submodules blackbox \
    --add-data "assets:assets" \
    run_blackbox.py
```

Output: `dist/Blackbox.app`

## Dependencies

| Package | Purpose |
|---------|---------|
| PyQt6 | UI framework |
| OpenCV | Template matching |
| NumPy | Array operations |
| Pillow | Image processing |
| mss | Screen capture |
| pynput | Global hotkeys |

## How It Works

1. **Screen Capture** — Grabs a region of the screen using `mss`
2. **Preprocessing** — Converts to grayscale and LAB color space
3. **Template Matching** — Uses OpenCV's `matchTemplate` with `TM_CCOEFF_NORMED`
4. **Color Verification** — Validates matches using LAB color similarity to reduce false positives
5. **Non-Maximum Suppression** — Filters overlapping detections
6. **Tracking** — Stabilizes detections across frames to reduce flickering
7. **Rendering** — Draws overlay boxes on a transparent PyQt6 window

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License — see [LICENSE](LICENSE) for details.