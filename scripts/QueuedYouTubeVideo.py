from PyQt5.QtWidgets import QWidget

from scripts.Ui_QueuedYouTubeVideo import Ui_QueuedYouTubeVideo

## A simple pair of widgets to label the value of a slider.
class QueuedYouTubeVideo(QWidget):

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(QueuedYouTubeVideo, self).__init__(parent)

        # Build UI object
        self.ui = Ui_QueuedYouTubeVideo()
        self.ui.setupUi(self)

        # Init labels
        self.update_percent_complete(0.0)

        # Done
        self.show()

    ## 
    #  @param self The object pointer.
    #  @param completion
    def update_percent_complete(self, completion):
        # Slider is in the range[0,10000], multiply the percent ([0,100]) for hundredth precision
        self.ui.download_percent_sli.setValue(int(completion*100))
        self.ui.download_percent_lbl.setText("{0}%".format(completion))
