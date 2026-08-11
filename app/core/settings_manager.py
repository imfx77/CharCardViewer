"""Settings management and persistence."""

import json
from pathlib import Path
from typing import Optional


class SettingsManager:
    """Manage application settings."""

    def __init__(self, app_path : Path, settingsFile: Optional[str] = None):
        """
        Initialize settings manager.
        
        Args:
            settingsFile: Path to settings JSON file
        """
        if settingsFile is None:
            settingsFile = app_path.joinpath('settings.json')

        self.settingsFile = Path(settingsFile)
        self.settings = self._loadSettings()

    def _loadSettings(self) -> dict:
        """Load settings from file."""
        if self.settingsFile.exists():
            try:
                with open(self.settingsFile, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "windowPosX": 100,
            "windowPosY": 100,
            "windowWidth": 1200,
            "windowHeight": 800,
            "splitterPosition": [900, 300],  # Left, Right
            "thumbnailSize": 150,
            "scanSubfolders": False,
            "sortByCreator": False,
            "sortByName": False,
            "filterName": "",
            "filterCreator": "",
            "filterTags": "",
            "filterDescr": ""
        }

    def _saveSettings(self):
        """Save settings to file."""
        try:
            with open(self.settingsFile, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass

    def getThumbnailSize(self) -> int:
        """Get thumbnail size preference."""
        return self.settings.get("thumbnailSize", 150)

    def setThumbnailSize(self, size: int):
        """
        Set thumbnail size preference.
        
        Args:
            size: Thumbnail size in pixels
        """
        self.settings["thumbnailSize"] = max(50, min(500, size))
        self._saveSettings()

    def getScanSubfolders(self) -> bool:
        """Get scan subfolders preference."""
        return self.settings.get("scanSubfolders", False)

    def setScanSubfolders(self, recursive: bool):
        """
        Set scan subfolders preference.

        Args:
            recursive: bool flag
        """
        self.settings["scanSubfolders"] = recursive
        self._saveSettings()

    def getSortByCreator(self) -> bool:
        """Get sort by creator preference."""
        return self.settings.get("sortByCreator", False)

    def setSortByCreator(self, sort: bool):
        """
        Set sort by creator preference.

        Args:
            sort: bool flag
        """
        self.settings["sortByCreator"] = sort
        self._saveSettings()

    def getSortByName(self) -> bool:
        """Get sort by name preference."""
        return self.settings.get("sortByName", False)

    def setSortByName(self, sort: bool):
        """
        Set sort by name preference.

        Args:
            sort: bool flag
        """
        self.settings["sortByName"] = sort
        self._saveSettings()

    def getFilterName(self) -> str:
        """Get filter name preference."""
        return self.settings.get("filterName", "")

    def getFilterCreator(self) -> str:
        """Get filter name preference."""
        return self.settings.get("filterCreator", "")

    def getFilterTags(self) -> str:
        """Get filter tag preference."""
        return self.settings.get("filterTags", "")

    def getFilterDescr(self) -> str:
        """Get filter description preference."""
        return self.settings.get("filterDescr", "")

    def setFilters(self, filterName: str, filterCreator: str, filterTags: str, filterDescr: str):
        """
        Set filters preference.

        Args:
            filterName: name filter
            filterCreator: creator filter
            filterTags: tags filter
            filterDescr: description filter
        """
        self.settings["filterName"] = filterName
        self.settings["filterCreator"] = filterCreator
        self.settings["filterTags"] = filterTags
        self.settings["filterDescr"] = filterDescr
        self._saveSettings()

    def getWindowGeometry(self) -> tuple:
        """Get window geometry (width, height)."""
        return (
            self.settings.get("windowPosX", 100),
            self.settings.get("windowPosY", 100),
            self.settings.get("windowWidth", 1200),
            self.settings.get("windowHeight", 800)
        )

    def setWindowGeometry(self, pos_x :int, pos_y : int, width: int, height: int):
        """
        Set window geometry.
        
        Args:
            pos_x: Window position x
            pos_x: Window position y
            width: Window width
            height: Window height
        """
        self.settings["windowPosX"] = pos_x
        self.settings["windowPosY"] = pos_y
        self.settings["windowWidth"] = width
        self.settings["windowHeight"] = height
        self._saveSettings()

    def getSplitterPosition(self) -> list:
        """Get splitter position [left, right]."""
        return self.settings.get("splitterPosition", [900, 300])

    def setSplitterPosition(self, positions: list):
        """
        Set splitter position.
        
        Args:
            positions: List of [left, right] sizes
        """
        self.settings["splitterPosition"] = positions
        self._saveSettings()

    def getLastFolder(self) -> Optional[str]:
        """Get last opened folder path."""
        return self.settings.get("lastFolder", None)

    def setLastFolder(self, folderPath: str):
        """
        Set last opened folder path.
        
        Args:
            folderPath: Path to folder
        """
        self.settings["lastFolder"] = folderPath
        self._saveSettings()

