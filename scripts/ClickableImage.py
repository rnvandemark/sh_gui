from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel

## A basic label that emits a signal when clicked.
class ClickableImage(QLabel):

    #
    # Qt Signal(s)
    #

    ## Emits a signal when clicked.
    clicked = pyqtSignal()

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(ClickableImage, self).__init__(parent)
        # Done
        self.show()

    ## Override mouseReleaseEvent to emit a signal.
    #  @param self The object pointer.
    #  @param evt The mouse release event.
    def mouseReleaseEvent(self, evt):
        self.clicked.emit()
