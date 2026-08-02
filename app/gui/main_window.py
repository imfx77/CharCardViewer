"""Main application window."""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter,
    QFileDialog, QSlider, QLabel, QToolBar, QStatusBar, QPushButton, QCheckBox, QSizePolicy, QWidgetAction, QLineEdit
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QSize
from PySide6.QtGui import QAction, QIcon

from app.models.character_card import CharacterCard
from app.core.custom_png_exif_extractor import CustomPngExifExtractor
from app.core.card_parser import CardParser
from app.core.settings_manager import SettingsManager
from app.gui.thumbnail_grid import ThumbnailGrid
from app.gui.data_panel import DataPanel
from app.gui.loading_overlay import LoadingOverlay


class ExifExtractionWorker(QObject):
    """Worker thread for EXIF extraction."""
    
    finished = Signal(dict)  # Emits {filePath: base64Data}
    error = Signal(str)  # Emits error message
    
    def __init__(self, directoryPath: str, recursive: bool = False):
        """
        Initialize worker.
        
        Args:
            directoryPath: Path to directory containing PNG files
        """
        super().__init__()
        self.directoryPath = directoryPath
        self.recursive = recursive

    def extract(self):
        """Perform EXIF extraction."""
        try:
            extractor = CustomPngExifExtractor()
            result = extractor.extractFromDirectory(self.directoryPath, self.recursive)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.currentDirectory: Optional[str] = None
        self.cards: list[CharacterCard] = []
        self.parser = CardParser()

        # Obtain the base resource path
        try:
            # PyInstaller stores data files in a tmp folder refered to as _MEIPASS
            import sys, os
            self.baseResourcePath = Path(sys._MEIPASS)
            self.baseResourcePath = self.baseResourcePath.joinpath('CharCardViewer')
            self.appPath = Path(os.path.dirname(sys.executable))
        except Exception:
            self.appPath = Path(__file__).parent.parent.parent
            self.baseResourcePath = self.appPath

        self.settings = SettingsManager(self.appPath)

        self._setupUi()
        self._loadWindowSettings()

    def _setupUi(self):
        """Set up the UI."""
        self.setWindowTitle("Character Card Viewer")
        
        # Set window icon
        iconPath = self.baseResourcePath.joinpath('images/icon.ico')
        if iconPath.exists():
            self.setWindowIcon(QIcon(str(iconPath)))
        
        # Central widget
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Thumbnail grid (left)
        self.thumbnailGrid = ThumbnailGrid(str(self.appPath))
        self.thumbnailGrid.thumbnailSelected.connect(self._onThumbnailSelected)
        self.splitter.addWidget(self.thumbnailGrid)
        
        # Data panel (right)
        self.dataPanel = DataPanel()
        self.splitter.addWidget(self.dataPanel)
        
        # Set splitter sizes (75% / 25%)
        splitterPos = self.settings.getSplitterPosition()
        self.splitter.setSizes(splitterPos)
        self.splitter.splitterMoved.connect(self._onSplitterMoved)
        
        layout.addWidget(self.splitter)
        centralWidget.setLayout(layout)
        
        # Toolbar
        self._createToolbars()
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Loading overlay (parent to central widget so it overlays content)
        self.loadingOverlay = LoadingOverlay(centralWidget)
        
        # Connect thumbnail grid signals
        self.thumbnailGrid.refreshStarted.connect(self._onRefreshStarted)
        self.thumbnailGrid.refreshFinished.connect(self._onRefreshFinished)
    
    def _createToolbars(self):
        """Create main toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Select Folder button for thumbnail size
        self.selectFolderButton = QPushButton("  Select Folder  ")
        self.selectFolderButton.clicked.connect(self._onSelectFolder)
        toolbar.addWidget(self.selectFolderButton)
        toolbar.addSeparator()
        toolbar.addSeparator()
        toolbar.addSeparator()
        toolbar.addSeparator()

        # Sort by Name checkbox
        self.scanSubfoldersCheckbox = QCheckBox(" Scan Subfolders  ")
        self.scanSubfoldersCheckbox.clicked.connect(self._onScanSubfolders)
        self.scanSubfoldersCheckbox.setChecked(self.settings.getScanSubfolders())
        toolbar.addWidget(self.scanSubfoldersCheckbox)

        # Sort by Name checkbox
        self.sortByNameCheckbox = QCheckBox(" Sort by Name  ")
        self.sortByNameCheckbox.clicked.connect(self._onSortByName)
        self.sortByNameCheckbox.setChecked(self.settings.getSortByName())
        toolbar.addWidget(self.sortByNameCheckbox)
        toolbar.addSeparator()
        toolbar.addSeparator()
        toolbar.addSeparator()
        toolbar.addSeparator()

        # Thumbnail size slider
        toolbar.addWidget(QLabel("  Thumbnail Size :  "))

        self.thumbnailSlider = QSlider(Qt.Horizontal)
        self.thumbnailSlider.setMinimum(50)
        self.thumbnailSlider.setMaximum(500)
        self.thumbnailSlider.setValue(self.settings.getThumbnailSize())
        self.thumbnailSlider.setTickPosition(QSlider.TicksBelow)
        self.thumbnailSlider.setTickInterval(50)
        self.thumbnailSlider.setFixedWidth(200)
        toolbar.addWidget(self.thumbnailSlider)

        self.sizeLabel = QLabel("  " + str(self.thumbnailSlider.value()) + "  ")
        self.thumbnailSlider.valueChanged.connect(lambda v: self.sizeLabel.setText("  " + str(v) + "  "))
        toolbar.addWidget(self.sizeLabel)

        # Apply button for thumbnail size
        self.applyThumbnailSizeButton = QPushButton("  Apply  ")
        self.applyThumbnailSizeButton.clicked.connect(self._onApplyThumbnailSize)
        toolbar.addWidget(self.applyThumbnailSizeButton)

        # Initialize thumbnail grid with saved size
        self.thumbnailGrid.setThumbnailSize(self.settings.getThumbnailSize())

        self.addToolBarBreak()

        """Create filters toolbar."""
        filters = QToolBar()
        self.addToolBar(filters)

        filters.addWidget(QLabel("  Name :  "))
        self.filterNameInput = QLineEdit()
        self.filterNameInput.setText(self.settings.getFilterName())
        self.filterNameInput.textChanged.connect(self._onFiltersChanged)
        filters.addWidget(self.filterNameInput)
        filters.addSeparator()
        filters.addSeparator()

        filters.addWidget(QLabel("  Creator :  "))
        self.filterCreatorInput = QLineEdit()
        self.filterCreatorInput.setText(self.settings.getFilterCreator())
        self.filterCreatorInput.textChanged.connect(self._onFiltersChanged)
        filters.addWidget(self.filterCreatorInput)
        filters.addSeparator()
        filters.addSeparator()

        filters.addWidget(QLabel("  Tags :  "))
        self.filterTagsInput = QLineEdit()
        self.filterTagsInput.setText(self.settings.getFilterTags())
        self.filterTagsInput.textChanged.connect(self._onFiltersChanged)
        filters.addWidget(self.filterTagsInput)
        filters.addSeparator()
        filters.addSeparator()

        filters.addWidget(QLabel("  Description :  "))
        self.filterDescrInput = QLineEdit()
        self.filterDescrInput.setText(self.settings.getFilterDescr())
        self.filterDescrInput.textChanged.connect(self._onFiltersChanged)
        filters.addWidget(self.filterDescrInput)

    def _loadWindowSettings(self):
        """Load window settings."""
        pos_x, pos_y, width, height = self.settings.getWindowGeometry()
        self.resize(width, height)
        self.move(pos_x, pos_y)

        # Auto-load last folder if available
        lastFolder = self.settings.getLastFolder()
        recursive = self.settings.getScanSubfolders()
        if lastFolder and Path(lastFolder).exists():
            self.setWindowTitle("Character Card Viewer - " + lastFolder)
            self.currentDirectory = lastFolder
            self.statusBar.showMessage("Loading last folder...")
            self._extractAndLoadCards(lastFolder, recursive)
    
    def _onSplitterMoved(self, pos: int, index: int):
        """Handle splitter movement."""
        sizes = self.splitter.sizes()
        self.settings.setSplitterPosition(sizes)
    
    def _onApplyThumbnailSize(self):
        """Handle Apply button click - update thumbnail size."""
        value = self.thumbnailSlider.value()
        self.settings.setThumbnailSize(value)
        self.thumbnailGrid.setThumbnailSize(value)
        self.statusBar.showMessage(f"Thumbnail size set to {value}px")
    
    def _onScanSubfolders(self):
        """Handle ScanSubfolders checkbox click - update subfolders scanning."""
        value = self.scanSubfoldersCheckbox.isChecked()
        self.settings.setScanSubfolders(value)
        self.statusBar.showMessage("Extracting EXIF data...")
        self._extractAndLoadCards(self.currentDirectory, value)

    def _onSortByName(self):
        """Handle SortByName checkbox click - update sorting."""
        value = self.sortByNameCheckbox.isChecked()
        self.settings.setSortByName(value)
        self.thumbnailGrid.sortCards(value, True)
        self.statusBar.showMessage(f"Sort By Name set to {value}")

    def _onFiltersChanged(self):
        """Handle filters change - update filtering."""
        filterName = self.filterNameInput.text()
        filterCreator = self.filterCreatorInput.text()
        filterTags = self.filterTagsInput.text()
        filterDescr = self.filterDescrInput.text()
        self.settings.setFilters(filterName, filterCreator, filterTags, filterDescr)
        self.thumbnailGrid.filterCards(filterName, filterCreator, filterTags, filterDescr, True)
        self.statusBar.showMessage(f"Filters changed to Name=[{filterName}] and Creator=[{filterCreator}] and Tags=[{filterTags}] and Description=[{filterDescr}]")

    def _onSelectFolder(self):
        """Select folder containing character cards."""
        # Use last folder as starting directory if available
        startDir = self.settings.getLastFolder()
        if not startDir or not Path(startDir).exists():
            startDir = str(Path.home())
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Character Cards",
            startDir
        )

        self.dataPanel.setCard(None)

        if directory:
            self.setWindowTitle("Character Card Viewer - " + directory)
            self.currentDirectory = directory
            self.settings.setLastFolder(directory)
            self.statusBar.showMessage("Extracting EXIF data...")
            recursive = self.settings.getScanSubfolders()
            self._extractAndLoadCards(directory, recursive)
    
    def _extractAndLoadCards(self, directoryPath: str, recursive: bool):
        """
        Extract EXIF data and load character cards.
        
        Args:
            directoryPath: Path to directory
        """
        # Show loading overlay
        self.loadingOverlay.showOverlay("Extracting EXIF data...")
        
        # Create worker thread
        self.workerThread = QThread()
        self.worker = ExifExtractionWorker(directoryPath, recursive)
        self.worker.moveToThread(self.workerThread)
        
        self.workerThread.started.connect(self.worker.extract)
        self.worker.finished.connect(self._onExtractionFinished)
        self.worker.error.connect(self._onExtractionError)
        self.worker.finished.connect(self.workerThread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.workerThread.finished.connect(self.workerThread.deleteLater)
        
        self.workerThread.start()
    
    def _onExtractionFinished(self, exifData: dict):
        """Handle EXIF extraction completion."""
        self.loadingOverlay.setMessage("Parsing character data...")
        
        self.cards = []
        
        for filePath, base64Data in exifData.items():
            if base64Data:
                card = self.parser.parseBase64(base64Data, filePath)
                if card:
                    self.cards.append(card)

        # Grid will emit refreshStarted/refreshFinished signals
        self.thumbnailGrid.setCards(self.cards)
        self.thumbnailGrid.sortCards(self.sortByNameCheckbox.isChecked())
        self.thumbnailGrid.filterCards(self.filterNameInput.text(),
                                       self.filterCreatorInput.text(),
                                       self.filterTagsInput.text(),
                                       self.filterDescrInput.text(),
                                       True)
        self.statusBar.showMessage(f"Loaded {len(self.cards)} character cards")
    
    def _onExtractionError(self, errorMsg: str):
        """Handle EXIF extraction error."""
        self.loadingOverlay.hideOverlay()
        self.statusBar.showMessage(f"Error: {errorMsg}")
    
    def _onRefreshStarted(self):
        """Handle thumbnail grid refresh start."""
        self.loadingOverlay.hideOverlay()

    def _onRefreshFinished(self):
        """Handle thumbnail grid refresh completion."""
        self.loadingOverlay.hideOverlay()
    
    def _onThumbnailSelected(self, filePath: str):
        """
        Handle thumbnail click.
        
        Args:
            filePath: Path to clicked file
        """
        # Find card for this file
        card = None
        for c in self.cards:
            if c.filePath == filePath:
                card = c
                break
        
        self.dataPanel.setCard(card)
    
    def _showThumbnailSizeDialog(self):
        """Show thumbnail size dialog (already handled by slider)."""
        self.thumbnailSlider.setFocus()
    
    def resizeEvent(self, event):
        """Handle window resize to update overlay position."""
        super().resizeEvent(event)
        if hasattr(self, "loadingOverlay"):
            self.loadingOverlay.setGeometry(self.centralWidget().rect())
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window geometry
        self.settings.setWindowGeometry(self.x(), self.y(), self.width(), self.height())
        event.accept()

