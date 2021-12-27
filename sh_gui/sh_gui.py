from sys import exit, argv as sargs
from PyQt5.QtWidgets import QApplication
from scripts.Gui import Gui

def main():
    app = QApplication(sargs)
    gui = Gui()
    exit(app.exec_())
