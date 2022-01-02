from sys import exit, argv as sargs
from PyQt5.QtWidgets import QApplication
from scripts import GuiUtils
from scripts.Gui import Gui

## Helper function to split a line at an equal sign.
#  @param line The string to split.
#  @return The left and right parts of the string.
def help_split(line):
    parts = line.split("=")
    return parts[0].strip(), parts[1].strip()

## Main antry point of the GUI.
def main():
    # Get the contents of the stylesheet file, replace select values
    style = None
    with open(GuiUtils.get_asset_url("style", "constants.sass"), "r") as constants_file:
        value_pairs = [help_split(line) for line in constants_file.readlines()]
        with open(GuiUtils.get_asset_url("style", "stylesheet.qss"), "r") as stylesheet_file:
            style = stylesheet_file.read()
            for k,v in value_pairs:
                style = style.replace("${0}".format(k), v)

    # Start the app with our stylesheet
    app = QApplication(sargs)
    app.setStyleSheet(style)
    gui = Gui()
    exit(app.exec_())
