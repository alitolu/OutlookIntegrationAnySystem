import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from utils.excel_helper import ExcelHelper
from utils.mail_analyzer import MailAnalyzer
from views.main_window import AWBSearchApp  # AWBSearchApp import
from utils.error_handler import ErrorHandler
from utils.logger import Logger

class AWBSearchApp(AWBSearchApp):
    def __init__(self):
        super().__init__()
        self.selected_filter = "all"
def main():
    app = QApplication(sys.argv)
    window = AWBSearchApp()  # AWBSearchApp kullan
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()