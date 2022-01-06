from urllib.request import urlopen

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap

from scripts.Ui_YouTubeVideoListing import Ui_YouTubeVideoListing

## A widget for a simple visualization of a YouTube video.
class YouTubeVideoListing(QWidget):

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(YouTubeVideoListing, self).__init__(parent)

        # Build UI object
        self.ui = Ui_YouTubeVideoListing()
        self.ui.setupUi(self)

        # Initialize video content to null
        self.result_dict = None

        # Done
        self.show()

    ## Populate the widgets given data on the YouTube video.
    #  @param self The object pointer.
    #  @param result_dict Properties of the YouTube video.
    def populate(self, result_dict):
        # Capture the results
        self.result_dict = result_dict

        #
        # Populate the UI skeleton given the data in the results dictionary
        #

        # Set the thumbnail image
        thumbnail_pixmap = QPixmap()
        thumbnail_pixmap.loadFromData(urlopen(self.result_dict["thumbnails"][0]["url"]).read())
        self.ui.thumbnail.setPixmap(thumbnail_pixmap.scaledToHeight(150, Qt.SmoothTransformation))

        # Set the title, author, duration, and view count
        self.ui.duration.setText(self.result_dict["duration"])
        self.ui.title.setText(self.result_dict["title"])
        self.ui.author.setText(self.result_dict["channel"]["name"])
        self.ui.views.setText(self.result_dict["viewCount"]["short"])

        # Ensure each column, aside from the thumbnail, has the same width
        for i in range(2, self.ui.overall_layout.columnCount()):
            self.ui.overall_layout.setColumnStretch(i, 1)

    ## Getter for the video's unique ID, returns null if a video is not set.
    #  @param self The object pointer.
    #  @return The video's unique ID.
    def get_video_id(self):
        return self.result_dict["id"] if self.result_dict else None
