from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

from scripts.Ui_YouTubeVideoResult import Ui_YouTubeVideoResult
from scripts.YouTubeVideoListing import YouTubeVideoListing

## A simple pair of widgets to label the value of a slider.
class YouTubeVideoResult(QWidget):
    #
    # Qt Signal(s)
    #

    ## Emit a signal of the YouTube video's original listing
    queue_requested = pyqtSignal(YouTubeVideoListing)

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(YouTubeVideoResult, self).__init__(parent)

        # Build UI object
        self.ui = Ui_YouTubeVideoResult()
        self.ui.setupUi(self)

        # Make Qt connections
        self.ui.queue_video_btn.clicked.connect(self.request_queue)

        # Done
        self.show()

    ## Attempt to queue the video corresponding to this result.
    #  @param self The object pointer.
    def request_queue(self):
        self.queue_requested.emit(self.ui.youtube_video_listing)
