"""Character data display panel."""

from typing import Optional

from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QPushButton, QTextBrowser, QTabWidget, QSizePolicy,
    QApplication
)
from PySide6.QtCore import Qt, QTimer, QUrl, QSize, QEvent, QObject
from PySide6.QtGui import QFont, QImage, QPixmap, QTextOption, QTextDocument, QPainter, QFontMetrics, QTextCursor, \
    QTextCharFormat

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
        self.scroll.setWidget(self.content)

        self.content_widget = content_widget
        self.layout.addWidget(self.content_widget, stretch=1)
        self.layout.addStretch()

        layout.addWidget(self.scroll)
        self.setLayout(layout)

class ScrollableTextWidget(ScrollableWidget):
    def __init__(self, content):

        label = QLabel(content)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        label.setOpenExternalLinks(True)
        label.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)

        super().__init__(label)


class WidthScaledLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None

        # Allow shrinking and expanding
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setPixmap(self, pixmap):
        self.pixmap = pixmap
        self._update_scaled()

    def heightForWidth(self, w):
        """Tell Qt the height depends on the width."""
        if not self.pixmap:
            return super().heightForWidth(w)
        ratio = self.pixmap.height() / self.pixmap.width()
        return int(w * ratio)

    def hasHeightForWidth(self):
        return True

    def minimumSizeHint(self):
        """Remove the image-based minimum size."""
        return QSize(1, 1)

    def resizeEvent(self, event):
        self._update_scaled()
        super().resizeEvent(event)

    def _update_scaled(self):
        if not self.pixmap:
            return

        w = self.width()
        scaled = self.pixmap.scaledToWidth(
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
            html = html.replace(f'<br /><span style=" color:#ff0000;">[Image Failed: ❌ {url}]</span><br />', f'')
            html = html.replace(f'<img src="{url.replace(" ", "%20")}"', f'global_broken_url : {url}')
            html = html.replace(f'<img src="{url}"', f'global_broken_url : {url}')
            html = html.replace(
                f'global_broken_url : {url}',
                f'<br><span style="color:red;">[Image Failed: ❌ {url}]</span><br><img src="{url}"'
            )
        # Replace cached <img src="..."> with text
        for url in RemoteImageBrowser.global_cache:
            html = html.replace(f'<br /><span style=" color:#ffff00;">[Image Loading ... ⏳ {url}]</span><br />', f'')
            html = html.replace(f'<br />[<a href="{url}"><span style=" text-decoration: underline; color:#9b9a99;">{url}</span></a>]<br />', f'')
            if url not in RemoteImageBrowser.global_broken_urls:
                html = html.replace(f'<img src="{url.replace(" ", "%20")}"', f'global_cached_url : {url}')
                html = html.replace(f'<img src="{url}"', f'global_cached_url : {url}')
                html = html.replace(
                    f'global_cached_url : {url}',
                    f'<br>[<a href="{url}"><span style=" text-decoration: underline; color:#9b9a99;">{url}</span></a>]<br><img src="{url}"'
                )
        super().setHtml(html)

    def setMarkdown(self, markdown):
        self.cancelPendingRequests()
        super().setMarkdown(markdown)
        self.setHtml("<style>img { max-width: 100%; height: auto; }</style>" + self.toHtml())  # forces full re-layout


class MouseWheelFilter(QObject):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            modifiers = QApplication.keyboardModifiers()

            if modifiers & Qt.ControlModifier:
                if event.angleDelta().y() > 0:
                    self.controller.onZoomIn()
                else:
                    self.controller.onZoomOut()

        return False


class ZoomController:
    zoom_factor_text = 1.0  # 100%
    zoom_factor_preview = 1.0  # 100%

    def __init__(self):
        self.registered_widgets = []
        self.initial_sizes = {}

    def clear(self):
        self.registered_widgets.clear()
        self.initial_sizes.clear()

    def register_widget(self, widget):
        """Store widget and its initial font size."""
        self.registered_widgets.append(widget)

        if isinstance(widget, RemoteImageBrowser):
            doc = widget.document()
            font = doc.defaultFont()
            self.initial_sizes[widget] = font.pointSizeF()

        elif isinstance(widget, ScrollableTextWidget):
            font = widget.content_widget.font()
            self.initial_sizes[widget] = font.pointSizeF()


    def apply_zoom(self, text_only: bool = False):
        """Apply zoom factor to all registered text widgets."""
        for widget in self.registered_widgets:

            if isinstance(widget, RemoteImageBrowser):
                initial_size = self.initial_sizes[widget]
                new_size = initial_size * self.zoom_factor_text

                doc = widget.document()
                cursor = QTextCursor(doc)

                fmt = QTextCharFormat()
                fmt.setFontPointSize(new_size)

                cursor.select(QTextCursor.Document)
                cursor.mergeCharFormat(fmt)

                widget.update() # Force repaint

            elif isinstance(widget, ScrollableTextWidget):
                initial_size = self.initial_sizes[widget]
                new_size = initial_size * self.zoom_factor_text

                font = widget.content_widget.font()
                font.setPointSizeF(new_size)
                widget.content_widget.setFont(font)

            elif not text_only and (widget, ScrollableWidget):
                if self.zoom_factor_preview == 1.0:
                    widget.scroll.setWidgetResizable(True)
                    widget.content_widget.setPixmap(widget.content_widget.pixmap)
                else:
                    widget.scroll.setWidgetResizable(True)
                    initial_size = widget.content_widget.size()
                    new_size = initial_size * self.zoom_factor_preview

                    widget.scroll.setWidgetResizable(False)
                    widget.content.resize(new_size)
                    widget.content.updateGeometry()

    def zoom_in_text(self):
        ZoomController.zoom_factor_text += 0.10   # +10%
        self.apply_zoom(text_only=True)

    def zoom_out_text(self):
        ZoomController.zoom_factor_text -= 0.10   # -10%
        ZoomController.zoom_factor_text = max(0.50, ZoomController.zoom_factor_text) # limit the zoom out
        self.apply_zoom(text_only=True)

    def zoom_in_preview(self):
        ZoomController.zoom_factor_preview += 0.10   # +10%
        self.apply_zoom()

    def zoom_out_preview(self):
        ZoomController.zoom_factor_preview -= 0.10   # -10%
        ZoomController.zoom_factor_preview = max(0.10, ZoomController.zoom_factor_preview) # limit the zoom out
        self.apply_zoom()


class DataPanel(QWidget):
    """Panel for displaying character card data."""
    last_tab_code = 0
    tab_codes = {
        "Preview" : 0,
        "Tags && Info" : 1,
        "Description" : 2,
        "Personality" : 3,
        "Scenario" : 4,
        "Greetings" : 5,
        "MsgExample" : 6,
        "Notes" : 7,
    }

    def __init__(self, parent=None):
        """
        Initialize data panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.currentCard: Optional[CharacterCard] = None
        self.currentGreetingIndex = 0
        self.selected_tab_code = 0

        self.wheel_filter = MouseWheelFilter(self)
        self.zoomController = ZoomController()

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
        self.tabsWidget.currentChanged.connect(self.onTabChanged)

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

        """Clear text zoom controller."""
        self.zoomController.clear()

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
        DataPanel.last_tab_code = self.selected_tab_code

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

        # Preview
        self._addPreview(card)

        # Tags & Info (if any)
        self._addTagsAndInfo(card)

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
            self._addGreetings(card)
        
        # Message example
        if card.mes_example:
            self._addSection("MsgExample", card.mes_example)

        # Creator notes
        if card.creator_notes:
            self._addNotes(card)

        # Apply current zoom
        self.zoomController.apply_zoom()

        # Attempt to keep the last tab selected
        last_tab_name = None
        for tab_name,tab_code in self.tab_codes.items():
            if tab_code == self.last_tab_code:
                last_tab_name = tab_name
                break

        if last_tab_name:
            for tab_index in range(self.tabsWidget.count()):
                tab_name = self.tabsWidget.tabText(tab_index)
                if tab_name.startswith(last_tab_name):
                    self.tabsWidget.setCurrentIndex(tab_index)
                    break

    def _addPreview(self, card: CharacterCard):
        """
        Add a section with card preview.
        """

        image = QImage(card.filePath)
        pixmap = QPixmap.fromImage(image)

        self.preview = WidthScaledLabel()
        self.preview.setPixmap(pixmap)
        section_widget = ScrollableWidget(self.preview)
        self.zoomController.register_widget(section_widget)
        self.tabsWidget.addTab(section_widget, "Preview")

    def _addNotes(self, card: CharacterCard):
        """
        Add a section with card creator notes.
        """

        self.notesBrowser = RemoteImageBrowser()
        self.notesBrowser.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.notesBrowser.setStyleSheet("padding: 10px;")
        self.notesBrowser.setOpenExternalLinks(True)
        self.notesBrowser.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)

        self.notesBrowser.viewport().installEventFilter(self.wheel_filter)
        self.zoomController.register_widget(self.notesBrowser)

        from app.utils.html_markdown_utils import is_html
        if is_html(card.creator_notes):
            self.notesBrowser.setHtml(card.creator_notes)
        else:
            self.notesBrowser.setMarkdown(card.creator_notes.replace("] (http", "](http"))

        self.tabsWidget.addTab(self.notesBrowser, "Notes")

    def _addSection(self, title: str, content: str):
        """
        Add a section with title and content.

        Args:
            title: Section title
            content: Section content
        """

        section_widget = ScrollableTextWidget(content)
        self.zoomController.register_widget(section_widget)
        self.tabsWidget.addTab(section_widget, title)

    def _addTagsAndInfo(self, card: CharacterCard):
        """
        Add tags section with styled tag badges & info section as text.
        """

        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)

        # Create a container with flow layout for wrapping tags
        if card.tags:
            tagsContainer = QWidget()
            tagsLayout = FlowLayout(margin=0, hSpacing=6, vSpacing=6)
            tagsLayout.setSpacing(15)
            tagsLayout.setContentsMargins(10, 10, 10, 10)

            for tag in card.tags:
                if not tag:
                    continue
                tagLabel = QLabel(str(tag))
                tagLabel.setStyleSheet("""
                    QLabel {
                        background-color: #3a6ea5;
                        color: white;
                        padding: 4px 10px;
                        border-radius: 12px;
                    }
                """)
                tagLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
                tagsLayout.addWidget(tagLabel)

            tagsContainer.setLayout(tagsLayout)
            layout.addWidget(ScrollableWidget(tagsContainer), stretch=1)

        # Compose the card info
        info = "Creator: " + (card.creator if card.creator else "(none)") + "\n"
        if card.spec and card.spec_version:
            info += "Spec: " + card.spec + "  [ " + card.spec_version + " ]\n"
        if card.character_version:
            info += "Character: " + card.character_version + "\n"
        if card.avatar:
            info += "Avatar: " + card.avatar

        infoContainer = ScrollableTextWidget(info)
        self.zoomController.register_widget(infoContainer)
        layout.addWidget(infoContainer, stretch=1)

        # add Tags & Info tab
        self.tabsWidget.addTab(container, "Tags && Info")

    def _addGreetings(self, card: CharacterCard):
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
        self.greetingBrowser.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.greetingBrowser.setOpenExternalLinks(True)
        self.greetingBrowser.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.greetingBrowser.setMarkdown(card.getCurrentGreeting(self.currentGreetingIndex))
        greetingsLayout.addWidget(ScrollableWidget(self.greetingBrowser))

        self.greetingBrowser.viewport().installEventFilter(self.wheel_filter)
        self.zoomController.register_widget(self.greetingBrowser)

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

            self.zoomController.apply_zoom(text_only=True)

    def onNextTab(self):
        if not self.tabsWidget:
            return

        current = self.tabsWidget.currentIndex()
        count = self.tabsWidget.count()
        self.tabsWidget.setCurrentIndex((current + 1) % count)

    def onPreviousTab(self):
        if not self.tabsWidget:
            return

        current = self.tabsWidget.currentIndex()
        count = self.tabsWidget.count()
        self.tabsWidget.setCurrentIndex((current - 1) % count)

    def onZoomIn(self):
        current = self.tabsWidget.currentIndex()
        if current == 0:
            self.zoomController.zoom_in_preview()
        else:
            self.zoomController.zoom_in_text()

    def onZoomOut(self):
        current = self.tabsWidget.currentIndex()
        if current == 0:
            self.zoomController.zoom_out_preview()
        else:
            self.zoomController.zoom_out_text()

    def resizeEvent(self, event):
        self.zoomController.apply_zoom()
        super().resizeEvent(event)

    def onTabChanged(self, index):
        title = self.tabsWidget.tabText(index)
        for tab_name,tab_code in self.tab_codes.items():
            if title.startswith(tab_name):
                self.selected_tab_code = tab_code
                return
        self.selected_tab_code = 0
