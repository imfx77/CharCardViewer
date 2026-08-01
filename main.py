"""Main entry point for Character Card Viewer."""

import os
import sys

# Suppress Qt DirectWrite font warnings on Windows (legacy bitmap fonts)
os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts=false"

from PySide6.QtWidgets import QApplication

from app.gui.main_window import MainWindow


def main():
    """Main application entry point."""
    app = QApplication(sys.argv + ['-platform', 'windows:darkmode=2'])
    app.setStyle('Fusion')
    app.setApplicationName("Character Card Viewer")

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

