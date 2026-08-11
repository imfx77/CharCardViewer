"""Character data display panel."""

from typing import Optional

from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QPushButton, QTextBrowser, QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QUrl, QSize
from PySide6.QtGui import QFont, QImage, QPixmap, QTextOption, QTextDocument, QPainter, QFontMetrics

from app.models.character_card import CharacterCard
from app.gui.flow_layout import FlowLayout


class ScrollableWidget(QWidget):
    def __init__(self, content_widget):
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Content widget
        self.content = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.content.setLayout(self.layout)

        # Scroll area for content
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.content)

        self.layout.addWidget(content_widget, stretch=1)
        self.layout.addStretch()

        layout.addWidget(self.scroll)
        self.setLayout(layout)

class ScrollableTextWidget(ScrollableWidget):
    def __init__(self, content):

        content_widget = QLabel(content)
        content_widget.setWordWrap(True)
        content_widget.setStyleSheet("padding: 5px;")
        content_widget.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)

        super().__init__(content_widget)


class WidthScaledLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None

        # Allow shrinking and expanding
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        super().setPixmap(pixmap)
        self.update_scaled()

    def heightForWidth(self, w):
        """Tell Qt the height depends on the width."""
        if not self._pixmap:
            return super().heightForWidth(w)
        ratio = self._pixmap.height() / self._pixmap.width()
        return int(w * ratio)

    def hasHeightForWidth(self):
        return True

    def minimumSizeHint(self):
        """Remove the image-based minimum size."""
        return QSize(1, 1)

    def resizeEvent(self, event):
        self.update_scaled()
        super().resizeEvent(event)

    def update_scaled(self):
        if not self._pixmap:
            return

        w = self.width()
        scaled = self._pixmap.scaledToWidth(
            w,
            Qt.SmoothTransformation
        )
        super().setPixmap(scaled)


class RemoteImageBrowser(QTextBrowser):
    # Global cache shared by all instances
    global_cache = {}  # url → QImage
    global_pending_urls = set()
    global_canceled_urls = set() # url → currently canceled
    global_broken_urls = set()  # url → failed permanently

    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self._replyFinished)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Instance-level pending replies
        self.pending_replies = {}

    def loadResource(self, type, name):
        if type == QTextDocument.ImageResource:
            url = name.toString()

            if url.startswith("http"):

                # If broken, return the broken placeholder
                if url in RemoteImageBrowser.global_broken_urls:
                    return RemoteImageBrowser.global_cache[url]

                # If cached, return cached image
                if url in RemoteImageBrowser.global_cache:
                    return RemoteImageBrowser.global_cache[url]

                # If already downloading, do nothing
                if url in RemoteImageBrowser.global_pending_urls:
                    return None

                # Start new download
                RemoteImageBrowser.global_canceled_urls.discard(url)
                RemoteImageBrowser.global_pending_urls.add(url)
                reply = self.manager.get(QNetworkRequest(QUrl(url)))
                self.pending_replies[reply] = url
                QTimer.singleShot(100, lambda: self.setHtml("<style>img { max-width: 100%; height: auto; }</style>" + self.toHtml()))  # forces full re-layout
                return None

        return super().loadResource(type, name)

    def _replyFinished(self, reply):
        url = self.pending_replies.pop(reply, None)
        if url is None:
            return

        RemoteImageBrowser.global_pending_urls.discard(url)

        data = reply.readAll()
        img = QImage.fromData(data)
        if img.isNull():
            if url not in RemoteImageBrowser.global_canceled_urls:
                self._handleImageFailure(url)
            return

        # Store globally
        RemoteImageBrowser.global_cache[url] = img

        # Insert into document
        doc = self.document()
        doc.addResource(QTextDocument.ImageResource, QUrl(url), img)
        doc.markContentsDirty(0, doc.characterCount())
        self.setHtml("<style>img { max-width: 100%; height: auto; }</style>" + self.toHtml())  # forces full re-layout

    def _handleImageFailure(self, url):

        # Create a small image with the URL written inside
        font = QFont("Arial", 10)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(url)
        text_height = metrics.height()

        w = text_width + 10
        h = text_height + 10

        img = QImage(w, h, QImage.Format_ARGB32)
        img.fill(Qt.white)

        painter = QPainter(img)
        painter.setPen(Qt.red)
        painter.setFont(font)
        painter.drawText(5, text_height, url)
        painter.end()

        # Mark URL as broken
        RemoteImageBrowser.global_broken_urls.add(url)

        # Store placeholder in cache
        RemoteImageBrowser.global_cache[url] = img

        # Insert into document
        doc = self.document()
        doc.addResource(QTextDocument.ImageResource, QUrl(url), img)
        doc.markContentsDirty(0, doc.characterCount())
        self.setHtml("<style>img { max-width: 100%; height: auto; }</style>" + self.toHtml())  # forces full re-layout

        QTimer.singleShot(10, lambda: self.setMinimumHeight(40 + self.document().size().height()))

    def cancelPendingRequests(self):
        # Abort all active network replies
        for reply in list(self.pending_replies.keys()):
            url = self.pending_replies.pop(reply, None)
            RemoteImageBrowser.global_canceled_urls.add(url)
            RemoteImageBrowser.global_pending_urls.discard(url)
            reply.abort()
            reply.deleteLater()

        # Clear tracking structures
        self.pending_replies.clear()

    def setHtml(self, html):
        # Replace pending <img src="..."> with text
        for url in RemoteImageBrowser.global_pending_urls:
            html = html.replace(f'<br /><span style=" color:#ffff00;">[Image Loading ... ⏳ {url}]</span><br />', f'')
            html = html.replace(f'<img src="{url.replace(" ", "%20")}"', f'global_pending_url : {url}')
            html = html.replace(f'<img src="{url}"', f'global_pending_url : {url}')
            html = html.replace(
                f'global_pending_url : {url}',
                f'<br><span style="color:yellow;">[Image Loading ... ⏳ {url}]</span><br><img src="{url}"'
            )
        # Replace broken <img src="..."> with text
        for url in RemoteImageBrowser.global_broken_urls:
            html = html.replace(f'<br /><span style=" color:#ffff00;">[Image Loading ... ⏳ {url}]</span><br />', f'')
            html = html.replace(f'<img src="{url.replace(" ", "%20")}"', f'global_broken_url : {url}')
            html = html.replace(f'<img src="{url}"', f'global_broken_url : {url}')
            html = html.replace(
                f'global_broken_url : {url}',
                f'<br><span style="color:red;">[Image Failed: ❌ {url}]</span><br><img src="{url}"'
            )
        # Replace cached <img src="..."> with text
        for url in RemoteImageBrowser.global_cache:
            html = html.replace(f'<br /><span style=" color:#ffff00;">[Image Loading ... ⏳ {url}]</span><br />', f'')
            if url not in RemoteImageBrowser.global_broken_urls:
                html = html.replace(f'<img src="{url.replace(" ", "%20")}"', f'global_cached_url : {url}')
                html = html.replace(f'<img src="{url}"', f'global_cached_url : {url}')
                html = html.replace(
                    f'global_cached_url : {url}',
                    f'<br><span>[{url}]</span><br><img src="{url}"'
                )
        super().setHtml(html)

    def setMarkdown(self, markdown):
        self.cancelPendingRequests()
        super().setMarkdown(markdown)
        self.setHtml("<style>img { max-width: 100%; height: auto; }</style>" + self.toHtml())  # forces full re-layout


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

        # Tabs widget
        self.tabsWidget = QTabWidget()

        layout.addWidget(self.headerWidget)
        layout.addWidget(self.tabsWidget)

        self.setLayout(layout)
        self._showEmptyState()
    
    def _showEmptyState(self):
        """Show empty state when no card is selected."""
        self._clearContent()

        label = QLabel("Select a character card to view details")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #888; font-size: 24px;")
        self.headerLayout.addWidget(label)

    def _clearContent(self):
        """Clear all title widgets."""
        while self.headerLayout.count():
            child = self.headerLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        """Clear all tabs widgets."""
        while self.tabsWidget.count() > 0:
            self.tabsWidget.removeTab(0)

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

        # Preview
        self._addPreview(card)

        # Card Info
        self._addCardInfo(card)

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
        if card.first_mes or card.alternate_greetings:
            self._addGreetingSection(card)
        
        # Message example
        if card.mes_example:
            self._addSection("MsgExample", card.mes_example)

        # Creator notes
        if card.creator_notes:
            self._addSection("Notes", card.creator_notes)

    def _addPreview(self, card: CharacterCard):
        """
        Add a section with card preview.
        """

        image = QImage(card.filePath)
        pixmap = QPixmap.fromImage(image)

        self.preview = WidthScaledLabel()
        self.preview.setPixmap(pixmap)
        self.tabsWidget.addTab(ScrollableWidget(self.preview), "Preview")

    def _addCardInfo(self, card: CharacterCard):
        """
        Add a section with card info.
        """
        info: str = ""

        if card.spec and card.spec_version:
            info += "Spec: " + card.spec + "  [ " + card.spec_version + " ]\n"
        if card.creator:
            info += "Creator: " + card.creator + "\n"
        if card.character_version:
            info += "Character: " + card.character_version + "\n"
        if card.avatar:
            info += "Avatar: " + card.avatar

        if info:
            self._addSection("Info", info)

    def _addSection(self, title: str, content: str):
        """
        Add a section with title and content.

        Args:
            title: Section title
            content: Section content
        """

        self.tabsWidget.addTab(ScrollableTextWidget(content), title)

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

        greetingsCount = card.getGreetingsCount()

        # PREV
        self.greetingNavPrev = QPushButton("  ◁◁  ")
        self.greetingNavPrev.setEnabled(self.currentGreetingIndex > 0)
        self.greetingNavPrev.clicked.connect(lambda: self._navigateGreeting(-1))
        navLayout.addWidget(self.greetingNavPrev)

        # COUNTER
        navLayout.addStretch()
        self.greetingCounterLabel = QLabel(f"{self.currentGreetingIndex + 1} / {greetingsCount}")
        self.greetingCounterLabel.setStyleSheet("color: #888; font-size: 14px;")
        self.greetingCounterLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        navLayout.addWidget(self.greetingCounterLabel)
        navLayout.addStretch()

        # NEXT
        self.greetingNavNext = QPushButton("  ▷▷  ")
        self.greetingNavNext.setEnabled(self.currentGreetingIndex < greetingsCount - 1)
        self.greetingNavNext.clicked.connect(lambda: self._navigateGreeting(1))
        navLayout.addWidget(self.greetingNavNext)
        
        # Greetings content
        greetingsLayout = QVBoxLayout()
        greetingsWidget = QWidget()
        greetingsWidget.setLayout(greetingsLayout)
        greetingsLayout.addWidget(navWidget)

        # GREETING CONTAINER
        self.greetingBrowser = RemoteImageBrowser()
        self.greetingBrowser.setOpenExternalLinks(True)
        self.greetingBrowser.setStyleSheet("padding: 5px;")
        self.greetingBrowser.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.greetingBrowser.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.greetingBrowser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.greetingBrowser.setMarkdown(card.getCurrentGreeting(self.currentGreetingIndex))
        greetingsLayout.addWidget(ScrollableWidget(self.greetingBrowser))

        self.tabsWidget.addTab(greetingsWidget, f"Greetings ({greetingsCount})")

    def _navigateGreeting(self, direction: int):
        """
        Navigate between greetings.
        
        Args:
            direction: -1 for previous, 1 for next
        """
        if self.currentCard is None:
            return

        greetingsCount = self.currentCard.getGreetingsCount()
        newIndex = self.currentGreetingIndex + direction
        maxIndex = greetingsCount - 1
        
        if 0 <= newIndex <= maxIndex:
            self.currentGreetingIndex = newIndex

            self.greetingNavPrev.setEnabled(self.currentGreetingIndex > 0)
            self.greetingNavNext.setEnabled(self.currentGreetingIndex < maxIndex)

            self.greetingCounterLabel.setText(f"{self.currentGreetingIndex + 1} / {greetingsCount}")
            self.greetingBrowser.setMarkdown(self.currentCard.getCurrentGreeting(self.currentGreetingIndex))

