"""Settings management and persistence."""

import json
from pathlib import Path
from typing import Optional


class SettingsManager:
    """Manage application settings."""

    def __init__(self, settingsFile: Optional[str] = None):
        """
        Initialize settings manager.
        
        Args:
            settingsFile: Path to settings JSON file
        """
        if settingsFile is None:
            settingsFile = Path(__file__).parent.parent.parent / "settings.json"

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
            "windowWidth": 1200,
            "windowHeight": 800,
            "splitterPosition": [900, 300],  # Left, Right
            "thumbnailSize": 150,
            "scanSubfolders": False,
            "sortByName": False,
            "filterTags": "",
            "filterName": "",
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

    def setScanSubfolders(self, sort: bool):
        """
        Set scan subfolders preference.

        Args:
            sort: bool flag
        """
        self.settings["scanSubfolders"] = sort
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

    def getFilterTags(self) -> str:
        """Get filter tag preference."""
        return self.settings.get("filterTags", "")

    def getFilterName(self) -> str:
        """Get filter name preference."""
        return self.settings.get("filterName", "")

    def getFilterDescr(self) -> str:
        """Get filter description preference."""
        return self.settings.get("filterDescr", "")

    def setFilters(self, filterTags: str, filterName: str, filterDescr: str):
        """
        Set filters preference.

        Args:
            filterTags: tags filter
            filterName: name filter
            filterDescr: description filter
        """
        self.settings["filterTags"] = filterTags
        self.settings["filterName"] = filterName
        self.settings["filterDescr"] = filterDescr
        self._saveSettings()

    def getWindowGeometry(self) -> tuple:
        """Get window geometry (width, height)."""
        return (
            self.settings.get("windowWidth", 1200),
            self.settings.get("windowHeight", 800)
        )

    def setWindowGeometry(self, width: int, height: int):
        """
        Set window geometry.
        
        Args:
            width: Window width
            height: Window height
        """
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

