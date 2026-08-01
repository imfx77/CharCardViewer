"""Character data display panel."""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QFont

from app.models.character_card import CharacterCard
from app.gui.flow_layout import FlowLayout


class CollapsibleWidget(QWidget):
    def __init__(self, title, content_widget):
        super().__init__()
        titleFont = QFont()
        titleFont.setPointSize(12)
        titleFont.setBold(True)

        self.title = QPushButton("△  " + title + "  △")
        self.title.setCheckable(True)
        self.title.setChecked(True)
        self.title.setFont(titleFont)

        self.content = content_widget

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.content)

        self.title.toggled.connect(self.toggle)

    def toggle(self, checked):
        MAX_SIZE = 16777215
        predicted_height = self.height() - self.content.height()
        self.title.setText(self.title.text().replace('▼', '△') if checked else self.title.text().replace('△', '▼'))
        self.content.setMaximumHeight(MAX_SIZE if checked else 0)
        self.setMaximumHeight(MAX_SIZE if checked else predicted_height)

class CollapsibleTextWidget(CollapsibleWidget):
    def __init__(self, title, content):

        content_widget = QLabel(content)
        content_widget.setWordWrap(True)
        content_widget.setStyleSheet("padding: 5px;")
        content_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)

        super().__init__(title, content_widget)

class DataPanel(QWidget):
    """Panel for displaying character card data."""
    
    def __init__(self, parent=None):
        """
        Initialize data panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.currentCard: Optional[CharacterCard] = None
        self.currentGreetingIndex = 0
        
        self._setupUi()
    
    def _setupUi(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header widget
        self.headerWidget = QWidget()
        self.headerLayout = QVBoxLayout()
        self.headerLayout.setSpacing(15)
        self.headerLayout.setContentsMargins(10, 10, 10, 10)
        self.headerWidget.setLayout(self.headerLayout)

        # Content widget
        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout()
        self.contentLayout.setSpacing(15)
        self.contentLayout.setContentsMargins(10, 10, 10, 10)
        self.contentWidget.setLayout(self.contentLayout)

        # Scroll area for content
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidget(self.contentWidget)

        layout.addWidget(self.headerWidget)
        layout.addWidget(self.scrollArea)

        self.setLayout(layout)
        self._showEmptyState()
    
    def _showEmptyState(self):
        """Show empty state when no card is selected."""
        self._clearContent()
        
        label = QLabel("Select a character card to view details")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #888; font-size: 24px;")
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.contentLayout.addWidget(label)
    
    def _clearContent(self):
        """Clear all title widgets."""
        while self.headerLayout.count():
            child = self.headerLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        """Clear all content widgets."""
        while self.contentLayout.count():
            child = self.contentLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def setCard(self, card: Optional[CharacterCard]):
        """
        Set character card to display.
        
        Args:
            card: CharacterCard instance or None
        """
        self.currentCard = card
        self.currentGreetingIndex = 0
        self._updateContent()
    
    def _updateContent(self):
        """Update the displayed content."""
        self._clearContent()
        
        if self.currentCard is None:
            self._showEmptyState()
            return
        
        card = self.currentCard
        
        # File (header)
        fileLabel = QLabel(card.filePath)
        fileLabel.setWordWrap(True)
        fileLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.headerLayout.addWidget(fileLabel)

        # Name (header)
        nameLabel = QLabel(card.name)
        nameFont = QFont()
        nameFont.setPointSize(18)
        nameFont.setBold(True)
        nameLabel.setFont(nameFont)
        nameLabel.setWordWrap(True)
        nameLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.headerLayout.addWidget(nameLabel)

        # Tags (if any) (header)
        if card.tags:
            self._addTagsSection(card.tags)
        
        # Description
        if card.description:
            self._addSection("Description", card.description)
        
        # Personality
        if card.personality:
            self._addSection("Personality", card.personality)
        
        # Scenario
        if card.scenario:
            self._addSection("Scenario", card.scenario)
        
        # First message with navigation
        if card.firstMes or card.alternateGreetings:
            self._addGreetingSection(card)
        
        # Add spacer
        self.contentLayout.addStretch()
    
    def _addSection(self, title: str, content: str):
        """
        Add a section with title and content.
        
        Args:
            title: Section title
            content: Section content
        """
        section = CollapsibleTextWidget(title, content)
        self.contentLayout.addWidget(section)

    def _addTagsSection(self, tags: list):
        """
        Add tags section with styled tag badges.
        
        Args:
            tags: List of tag strings
        """
        # Create a container with flow layout for wrapping tags
        tagsContainer = QWidget()
        tagsLayout = FlowLayout(margin=0, hSpacing=6, vSpacing=6)
        
        for tag in tags:
            if not tag:
                continue
            tagLabel = QLabel(str(tag))
            tagLabel.setStyleSheet("""
                QLabel {
                    background-color: #3a6ea5;
                    color: white;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 14px;
                }
            """)
            tagLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
            tagsLayout.addWidget(tagLabel)
        
        tagsContainer.setLayout(tagsLayout)
        self.headerLayout.addWidget(tagsContainer)
    
    def _addGreetingSection(self, card: CharacterCard):
        """
        Add greeting section with navigation arrows.
        
        Args:
            card: CharacterCard instance
        """

        # Navigation controls
        navLayout = QHBoxLayout()
        navWidget = QWidget()
        navWidget.setLayout(navLayout)

        cardsCount = card.getGreetingCount()

        # PREV
        self.greetingNavPrev = QPushButton("  ◁◁  ")
        self.greetingNavPrev.setEnabled(self.currentGreetingIndex > 0)
        self.greetingNavPrev.clicked.connect(lambda: self._navigateGreeting(-1))
        navLayout.addWidget(self.greetingNavPrev)

        # COUNTER
        navLayout.addStretch()
        self.greetingCounterLabel = QLabel(f"{self.currentGreetingIndex + 1} / {cardsCount}")
        self.greetingCounterLabel.setStyleSheet("color: #888; font-size: 14px;")
        self.greetingCounterLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        navLayout.addWidget(self.greetingCounterLabel)
        navLayout.addStretch()

        # NEXT
        self.greetingNavNext = QPushButton("  ▷▷  ")
        self.greetingNavNext.setEnabled(self.currentGreetingIndex < cardsCount - 1)
        self.greetingNavNext.clicked.connect(lambda: self._navigateGreeting(1))
        navLayout.addWidget(self.greetingNavNext)
        
        # Greetings content
        greetingsLayout = QVBoxLayout()
        greetingsWidget = QWidget()
        greetingsWidget.setLayout(greetingsLayout)
        greetingsLayout.addWidget(navWidget)

        # GREETING CONTAINER
        self.greetingLabel = QLabel(card.getCurrentGreeting(self.currentGreetingIndex))
        self.greetingLabel.setWordWrap(True)
        self.greetingLabel.setStyleSheet("padding: 5px;")
        self.greetingLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        greetingsLayout.addWidget(self.greetingLabel, 1)

        # Greetings Section
        self.greetingsSection = CollapsibleWidget("Greetings", greetingsWidget)
        self.contentLayout.addWidget(self.greetingsSection)

    def _navigateGreeting(self, direction: int):
        """
        Navigate between greetings.
        
        Args:
            direction: -1 for previous, 1 for next
        """
        if self.currentCard is None:
            return
        
        newIndex = self.currentGreetingIndex + direction
        maxIndex = self.currentCard.getGreetingCount() - 1
        
        if 0 <= newIndex <= maxIndex:
            self.currentGreetingIndex = newIndex

            self.greetingNavPrev.setEnabled(self.currentGreetingIndex > 0)
            self.greetingNavNext.setEnabled(self.currentGreetingIndex < maxIndex)

            self.greetingLabel.setText(self.currentCard.getCurrentGreeting(self.currentGreetingIndex))
            self.greetingCounterLabel.setText(f"{self.currentGreetingIndex + 1} / {self.currentCard.getGreetingCount()}")

