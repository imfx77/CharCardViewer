<h1 align="center">Character Card Viewer</h1>

<p align="center">
    <a href="https://github.com/imfx77/CharCardViewer/releases">
        <img src="https://img.shields.io/github/v/release/imfx77/CharCardViewer?style=for-the-badge&color=brightgreen" alt="GitHub Latest Release (by date)" title="GitHub Latest Release (by date)">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/blob/master/LICENSE" title="Read License">
        <img src="https://img.shields.io/github/license/imfx77/CharCardViewer?style=for-the-badge" alt="CharCardViewer">
    </a>
</p>
<p align="center">
    <a href="https://github.com/imfx77/CharCardViewer/stargazers" title="View Stargazers">
        <img src="https://img.shields.io/github/stars/imfx77/CharCardViewer?logo=github&style=for-the-badge&color=orange" alt="CharCardViewer">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/releases">
        <img src="https://img.shields.io/github/downloads/imfx77/CharCardViewer/total?style=for-the-badge&color=orange" alt="GitHub All Releases" title="GitHub All Downloads">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/releases">
        <img src="https://img.shields.io/github/directory-file-count/imfx77/CharCardViewer?style=for-the-badge&color=orange" alt="GitHub Repository File Count" title="GitHub Repository File Count">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/releases">
        <img src="https://img.shields.io/github/repo-size/imfx77/CharCardViewer?style=for-the-badge&color=orange" alt="GitHub Repository Size" title="GitHub Repository Size">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/releases">
        <img src="https://img.shields.io/github/languages/code-size/imfx77/CharCardViewer?style=for-the-badge&color=orange" alt="GitHub Code Size" title="GitHub Code Size">
    </a>
</p>
<p align="center">
    <a href="https://github.com/imfx77/CharCardViewer/discussions">
        <img src="https://img.shields.io/github/discussions/imfx77/CharCardViewer?style=for-the-badge&color=blue" alt="GitHub Discussions" title="Read Discussions">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/compare">
        <img src="https://img.shields.io/github/commits-since/imfx77/CharCardViewer/latest?include_prereleases&style=for-the-badge&color=blue" alt="GitHub Commits Since Last Release" title="GitHub Commits Since Last Release">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/compare">
        <img src="https://img.shields.io/github/commit-activity/m/imfx77/CharCardViewer?style=for-the-badge&color=blue" alt="GitHub Commit Monthly Activity" title="GitHub Commit Monthly Activity">
    </a>
</p>

-------
\
A Python desktop application for viewing character cards stored as PNG files with embedded EXIF metadata.
Character card information is typically stored as Base64-encoded JSON in PNG EXIF data, which makes it difficult to browse and view.  

This application provides a user-friendly interface to view collections of character cards by thumbnails and easily explore their character information.  

<img src="https://img.shields.io/badge/⭐-If%20Useful-BC4E99?style=for-the-badge" alt="Star Badge">

\
Browsing and selecting cards to view their metadata:

![Preview0](/images/main0.png)

Using the filters to narrow down the list of cards, previewing multiple greetings with embedded pictures, selecting part of the text to copy it:

![Preview1](/images/main1.png)

Showing very large thumbnails, reviewing card's  Tags & Info:

![Preview2](/images/main2.png)

## Quick Start

**For Windows users**: Download the standalone `CharCardViewer.exe` from [Releases](https://github.com/imfx77/CharCardViewer/releases) — no installation required.

## Features

---
#### Thumbnail Grid View
  - Browse character cards in a scrollable grid with thumbnails
---
#### Resizable Interface
  - Adjustable splitter between thumbnail grid and data panel
---
#### Auto Save Settings
  - The entire window geometry (position, size, splitter) is being auto saved in the settings file, as well as all the options and filters
  - They are automatically restored when the app is started again
---
#### Folder Scanning
  - When a folder is selected its contents can be scanned recursively depending on the checkbox `Scan Subfolders`
---
#### Filtered Display
  - Cards can be filtered by **Name**, **Creator**, **Tags** and **Description**
  - Multiple search substrings are allowed separated by the `|` symbol (for Tags and Description ONLY), thus allowing filtering by multiple tags and co-existing phrases in the descriptions of the cards
---
#### Sorted Display
  - Cards are automatically sorted by character name or by file canonical path depending on `Sort by Name` checkbox
  - When the `Sort by Creator` checkbox is used the cards are grouped and sorted by creator
---
#### Thumbnail Size Control
  - Adjustable thumbnail size with persistent settings, changing the size regenerates thumbnails caches
---
#### Thumbnails Caching
  - Automatically caches and updates thumbnail files for faster loading
  - Look for the `.thumbs_cache` subfolder in the main app folder, it can be manually cleared on demand
---
#### Character Information Display
  - View detailed character data including file path, card name and preview
  - Tags and info are available in a combined tab
  - Separate tabs are available for description, personality, scenario, multiple greetings, message examples, creator notes
---
#### Alternative Greetings Navigation
  - Navigate through multiple greeting messages with arrow buttons in the Greetings tab
  - When greetings have embedded pictures they are loaded asynchronously in the greetings preview and live links to them are provided
---
#### Selecting and Copying Texts
  - All the text sections in the character data panel can be selected by mouse and keyboard for convenient copying of desired data  
---
#### Shortcuts and Customizations
  - Tabs of the data panel can be easily switched by `Ctrl + Tab` and `Ctrl + Shift + Tab` forward and backward
  - The picture in the Preview tab can be zoomed in/out and the texts in all the other tabs can increase/decrease font for convenience of reading by using the keyboard shortcuts `Ctrl + +` and `Ctrl + -` or `Ctrl + Mouse Wheel`
  - The customized zoom and font sizes take scope until the app is closed   
---

## Requirements

- Python 3.12 or later
- Windows (batch scripts provided for Windows)

## Installation

### Option 1: Standalone Executable (Easiest)

Download `CharCardViewer.exe` from [Releases](https://github.com/imfx77/CharCardViewer/releases) and run it directly. No Python or dependencies required.

### Option 2: From Source

1. **Run the installation script**:
   ```batch
   install.bat
   ```

   This script will:
   - Check for `uv` package manager (falls back to `pip` if not available)
   - Create a virtual environment (skipped if active conda env is detected)
   - Install required dependencies (PySide6, Pillow)

2. **(Optional) Manual installation**:
   - Create venv
   - Install Requirements

## Usage

---
1. **Start the application**:
   ```batch
   start.bat
   ```
   or activate venv and run with `python main.py`
---
2. **Select a folder**:
   - Click `Select Folder` button on the main toolbar
   - Choose a directory containing PNG character card files (also, all the subfolders can be scanned recursively if needed)
---
3. **Filter and Sort**
   - Use Name/Creator/Tags/Description filters to reduce the cards count for easier browsing
   - Choose to sort the cards by creator and/or by name depending on which is most useful for you 
---
4. **Browse character cards**:
   - Scroll the grid view and click on any thumbnail to view its character information
   - Use the thumbnail size slider in the main toolbar to adjust thumbnail size as desired
---
5. **Character Data Panel**:
   - Select the tabs to review different parts of the card's metadata
   - Use mouse and keyboard to select and copy any part of the texts 
   - Use arrow buttons in the greetings section to navigate through alternative greetings
   - In greetings click the links to visit the original embedded images (if any)
   - Use keyboard and mouse shortcuts to zoom in/out the preview ot increase/decrease font of texts
---
6. **Adjust the interface**:
   - Adjust the window size and position as necessary
   - Drag the splitter between thumbnails grid and data panel to resize them
   - All the settings are automatically saved
---

## Character Card Format

The application supports character cards in the `chara_card_v2` and `chara_card_v3` format with the following structure:

- **EXIF Tags**: `chara` (primary) or `Ccv3` (fallback)
- **Data Format**: Base64-encoded JSON
- **Required Fields**: creator, tags, name, description, personality, scenario, first_mes
- **Optional Fields**: alternate_greetings, mes_example, creator_notes

## Project Structure

```
CharCardView/
├── main.py                               # Application entry point
├── pyproject.toml                        # Project configuration
├── requirements.txt                      # Python dependencies (for pip fallback)
├── install.bat                           # Installation script
├── start.bat                             # Launch script
├── CharCardViewer.spec                   # pyinstaller build configuration for Windows EXE
├── app/
│   ├── gui/                              # GUI components
│   │   ├── main_window.py                # Main window
│   │   ├── thumbnail_grid.py             # Thumbnail grid widget
│   │   └── data_panel.py                 # Character data display
│   ├── core/                             # Core business logic
│   │   ├── custom_png_exif_extractor.py  # custom EXIF data extraction for PNG
│   │   ├── card_parser.py                # JSON parsing
│   │   └── settings_manager.py           # Settings persistence
│   ├── models/                           # Data models
│   │   └── character_card.py             # Character card model
│   └── utils/                            # Utilities
│   │   ├── html_markdown_utils.py        # Detection of HTML and MD content
│       └── image_utils.py                # Thumbnail generation and caching
└── images/
    ├── icon.ico                          # Icon
    ├── icon.png                          # Icon
    └── main*.png                         # README images
```

## Dependencies

- **PySide6**: GUI framework
- **Pillow**: Image processing and thumbnail generation

## Troubleshooting

#### Application won't start:
- Ensure Python 3.12+ is installed
- Run `install.bat` to set up dependencies
- Check that virtual environment was created successfully

#### No character cards displayed:
- Verify that PNG files contain valid EXIF data with `chara` or `Ccv3` tags
- Check that PNG files are in the selected directory


## Credits

This project was initially forked from the [CharCardView](https://github.com/Deaquay/CharCardView) app and I tried contributing to it for a while.
Eventually, things grew much bigger, this repo was split, and its current code has nothing in common with the original.
Yet, the following credit is mentioned out of courtesy:
* [Deaquay Pekka](https://github.com/Deaquay) (c) 2025-2026
   
## License

* This project is provided as-is for personal use and is distributed under the [MIT License](LICENSE "Read The MIT license")

-------

<p align="center">
    <a href="https://github.com/imfx77/CharCardViewer/stargazers" title="View Stargazers">
        <img src="https://img.shields.io/github/stars/imfx77/CharCardViewer?logo=github&style=flat-square" alt="CharCardViewer">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/forks" title="See Forks">
        <img src="https://img.shields.io/github/forks/imfx77/CharCardViewer?logo=github&style=flat-square" alt="CharCardViewer">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/blob/master/LICENSE" title="Read License">
        <img src="https://img.shields.io/github/license/imfx77/CharCardViewer?style=flat-square" alt="CharCardViewer">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/issues" title="Open Issues">
        <img src="https://img.shields.io/github/issues-raw/imfx77/CharCardViewer?style=flat-square" alt="CharCardViewer">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/issues?q=is%3Aissue+is%3Aclosed" title="Closed Issues">
        <img src="https://img.shields.io/github/issues-closed/imfx77/CharCardViewer?style=flat-square" alt="CharCardViewer">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/discussions" title="Read Discussions">
        <img src="https://img.shields.io/github/discussions/imfx77/CharCardViewer?style=flat-square" alt="CharCardViewer">
    </a>
    <a href="https://github.com/imfx77/CharCardViewer/compare/" title="Latest Commits">
        <img alt="GitHub commits since latest release (by date)" src="https://img.shields.io/github/commits-since/imfx77/CharCardViewer/latest?style=flat-square">
    </a>
</p>
