"""Thumbnail grid widget for displaying character card images."""
import os
from pathlib import Path
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGridLayout,
    QPushButton, QLabel
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer, QCoreApplication
from PySide6.QtGui import QPixmap, QImage

from app.models.character_card import CharacterCard
from app.utils.image_utils import getThumbnailCache


class ThumbnailItem(QWidget):
    """Individual thumbnail item in the grid."""
    
    selected = Signal(str)  # Emits file path when selected
    
    def __init__(self, app_path : str, filePath: str, card: Optional[CharacterCard], size: int, parent=None):
        """
        Initialize thumbnail item.
        
        Args:
            filePath: Path to image file
            card: CharacterCard instance (may be None)
            size: Thumbnail size in pixels
            parent: Parent widget
        """
        super().__init__(parent)
        self.filePath = filePath
        self.card = card
        self.size = size
        self.isSelected = False
        
        self._setupUi()
        self._loadThumbnail(app_path)
    
    def _setupUi(self):
        """Set up the UI for the thumbnail item."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Thumbnail button
        self.thumbnailButton = QPushButton()
        self.thumbnailButton.setFixedSize(self.size, self.size)
        self.thumbnailButton.setIconSize(QSize(self.size - 10, self.size - 10))
        self.thumbnailButton.clicked.connect(lambda: self.selected.emit(self.filePath))
        self.thumbnailButton.setToolTip(self.filePath
                                        + '\nCreator: ' + (self.card.creator if self.card.creator else '(none)')
                                        + '\nGreetings: ' + str(self.card.getGreetingsCount()))
        self.thumbnailButton.setStyleSheet("""
            QPushButton {
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                border-color: #888;
            }
        """)
        
        # Name label
        name = self.card.name if self.card else Path(self.filePath).stem

        self.nameLabel = QLabel(name)
        self.nameLabel.setAlignment(Qt.AlignCenter)
        self.nameLabel.setWordWrap(True)
        self.nameLabel.setMaximumWidth(self.size)

        layout.addWidget(self.thumbnailButton)
        layout.addWidget(self.nameLabel)

        self.setLayout(layout)
        self.setFixedWidth(self.size + 10)

    def _loadThumbnail(self, app_path : str):
        """Load thumbnail image."""
        thumbnailImagePath = getThumbnailCache(app_path, self.filePath, [self.size - 10, self.size - 10])

        image = QImage(thumbnailImagePath)
        pixmap = QPixmap.fromImage(image)
        self.thumbnailButton.setIcon(pixmap)

    def setSelected(self, selected: bool):
        """
        Set selection state.
        
        Args:
            selected: Whether this item is selected
        """
        self.isSelected = selected
        if selected:
            self.thumbnailButton.setStyleSheet("""
                QPushButton {
                    border: 3px solid #0078d4;
                    border-radius: 5px;
                    background-color: #e3f2fd;
                }
                QPushButton:hover {
                    border-color: #005a9e;
                }
            """)
        else:
            self.thumbnailButton.setStyleSheet("""
                QPushButton {
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                }
                QPushButton:hover {
                    border-color: #888;
                }
            """)


class ThumbnailGrid(QWidget):
    """Scrollable grid of character card thumbnails."""
    
    thumbnailSelected = Signal(str)  # Emits file path when thumbnail is clicked
    refreshStarted = Signal()  # Emitted when grid refresh starts
    refreshFinished = Signal()  # Emitted when grid refresh completes
    
    # Batch size for chunked loading (process this many items then yield to event loop)
    BATCH_SIZE = 5
    
    def __init__(self, app_path : str, parent=None):
        """
        Initialize thumbnail grid.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.app_path = app_path
        self.thumbnailSize = 150
        self.cards: List[CharacterCard] = []
        self.thumbnailItems: List[ThumbnailItem] = []
        self.selectedItem: Optional[ThumbnailItem] = None
        self._resizeTimer: Optional[QTimer] = None
        self._lastWidth = 0
        self._buildIndex = 0
        self._buildIndexCorrector = 0
        self._buildColumns = 1
        self._isBuilding = False
        
        self._setupUi()
    
    def _setupUi(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Gris scroll area
        self.gridScrollArea = QScrollArea()
        self.gridScrollArea.setWidgetResizable(True)
        self.gridScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Grid container
        self.gridWidget = QWidget()
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(10)
        self.gridLayout.setContentsMargins(10, 10, 10, 10)
        self.gridWidget.setLayout(self.gridLayout)
        
        self.gridScrollArea.setWidget(self.gridWidget)
        layout.addWidget(self.gridScrollArea)
        
        self.setLayout(layout)
    
    def setThumbnailSize(self, size: int):
        """
        Set thumbnail size and refresh grid.
        
        Args:
            size: Thumbnail size in pixels
        """
        self.thumbnailSize = max(50, min(500, size))
        self._cancelBuild()
        self._refreshGrid()
    
    def setCards(self, cards: List[CharacterCard]):
        """
        Set character cards to display.
        
        Args:
            cards: List of CharacterCard instances
        """
        self.cards = cards

    def sortCards(self, sortByCreator : bool, sortByName : bool, forceRefresh=False):
        """
        Sort the character cards.

        Args:
            sortByCreator: bool flag
            sortByName: bool flag
        """

        def sortKeyByCreatorAndName(card: CharacterCard):
            return card.creator.strip().casefold(), card.name.strip().casefold()

        def sortKeyByCreator(card: CharacterCard):
            return card.creator.strip().casefold(), card.filePath.count(os.sep), card.filePath.replace('-', '').casefold()

        def sortKeyByName(card: CharacterCard):
            return card.name.strip().casefold()

        def sortKeyByPath(card: CharacterCard):
            return card.filePath.count(os.sep), card.filePath.replace('-', '').casefold()

        if sortByCreator:
            if sortByName:
                sortKey = sortKeyByCreatorAndName
            else:
                sortKey = sortKeyByCreator
        else:
            if sortByName:
                sortKey = sortKeyByName
            else:
                sortKey = sortKeyByPath

        self.cards = sorted(self.cards, key=sortKey)
        if forceRefresh:
            self._cancelBuild()
            self._refreshGrid()

    def filterCards(self, filterName: str, filterCreator: str, filterTags: str, filterDescr: str, forceRefresh: bool = False):
        """
        Filter character cards to display.

        Args:
            filterName: name filter
            filterCreator: creator filter
            filterTags: tags filter
            filterDescr: description filter
        """
        for c in self.cards:
            c.evaluateFilters(filterName, filterCreator, filterTags, filterDescr)
        if forceRefresh:
            self._cancelBuild()
            self._refreshGrid()

    def _cancelBuild(self):
        """Cancel any in-progress thumbnail build."""
        if self._isBuilding:
            self._isBuilding = False
    
    def _refreshGrid(self):
        """Refresh the thumbnail grid using chunked loading for responsiveness."""
        # Prevent concurrent builds
        if self._isBuilding:
            return
        
        self._isBuilding = True
        
        # Emit signal and process events so overlay can show
        self.refreshStarted.emit()
        QCoreApplication.processEvents()
        
        # Clear existing items
        for item in self.thumbnailItems:
            item.deleteLater()
        self.thumbnailItems.clear()
        self.selectedItem = None
        
        # Setup for chunked building
        self._buildColumns = max(1, self.width() // (self.thumbnailSize + 20))
        self._buildIndex = 0
        self._buildIndexCorrector = 0

        # Start building in chunks
        QTimer.singleShot(10, self._buildNextBatch)
    
    def _buildNextBatch(self):
        """Build the next batch of thumbnail items."""
        if not self._isBuilding:
            return
        
        endIndex = min(self._buildIndex + self.BATCH_SIZE, len(self.cards))

        for i in range(self._buildIndex, endIndex):
            card = self.cards[i]
            if card.isFiltered:
                self._buildIndexCorrector += 1
                continue

            col = (i - self._buildIndexCorrector) % self._buildColumns
            rowIndex = (i - self._buildIndexCorrector) // self._buildColumns
            
            item = ThumbnailItem(self.app_path, card.filePath, card, self.thumbnailSize, self.gridWidget)
            item.selected.connect(self._onThumbnailSelected)
            self.gridLayout.addWidget(item, rowIndex, col)
            self.thumbnailItems.append(item)
        
        self._buildIndex = endIndex
        
        # Check if more items to process
        if self._buildIndex < len(self.cards):
            # Schedule next batch, allowing event loop to run (keeps spinner alive)
            QTimer.singleShot(1, self._buildNextBatch)
        else:
            # Done building
            self._isBuilding = False
            self.refreshFinished.emit()
    
    def _onThumbnailSelected(self, filePath: str):
        """
        Handle thumbnail click.
        
        Args:
            filePath: Path to clicked file
        """

        # Deselect previous
        if self.selectedItem:
            self.selectedItem.setSelected(False)
        
        # Select new
        for item in self.thumbnailItems:
            if item.filePath == filePath:
                item.setSelected(True)
                self.selectedItem = item
                break
        
        self.thumbnailSelected.emit(filePath)
    
    def resizeEvent(self, event):
        """Handle resize event to adjust grid columns."""
        super().resizeEvent(event)
        
        # Only refresh if width changed significantly (affects column count)
        newWidth = self.width()
        if abs(newWidth - self._lastWidth) > self.thumbnailSize // 2:
            self._lastWidth = newWidth
            
            # Debounce resize to avoid excessive refreshes
            if self._resizeTimer is not None:
                self._resizeTimer.stop()
            
            self._resizeTimer = QTimer()
            self._resizeTimer.setSingleShot(True)
            self._resizeTimer.timeout.connect(self._onResizeTimeout)
            self._resizeTimer.start(150)  # 150ms debounce
    
    def _onResizeTimeout(self):
        """Handle debounced resize."""
        if self.cards:
            self._refreshGrid()

