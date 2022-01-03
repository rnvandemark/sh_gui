from PyQt5.QtWidgets import QWidget

from scripts.Ui_YouTubeVideoResult import Ui_YouTubeVideoResult

## A simple pair of widgets to label the value of a slider.
class YouTubeVideoResult(QWidget):

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(YouTubeVideoResult, self).__init__(parent)

        # Build UI object
        self.ui = Ui_YouTubeVideoResult()
        self.ui.setupUi(self)

        # Done
        self.show()
