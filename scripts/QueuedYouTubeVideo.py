from PyQt5.QtWidgets import QWidget

from scripts.Ui_QueuedYouTubeVideo import Ui_QueuedYouTubeVideo\

from sh_sfp_interfaces.action import AnalyzeSoundFile

ANALYSIS_STATUS_LABELS = {
    AnalyzeSoundFile.Feedback.STATUS_STARTED: "Analysis has started",
    AnalyzeSoundFile.Feedback.STATUS_AUDIO_LOADED: "Audio was successfully loaded, started onset detection",
    AnalyzeSoundFile.Feedback.STATUS_FINISHED_ONSET_DETECTION: "Finished onset detection, started beat detection",
    AnalyzeSoundFile.Feedback.STATUS_FINISHED_BEAT_DETECTION: "Finished beat detection, started pitch detection",
    AnalyzeSoundFile.Feedback.STATUS_FINISHED_PITCH_DETECTION: "Finished pitch detection, finishing up...",
    AnalyzeSoundFile.Feedback.STATUS_FINISHED_ANALYSIS: "Analysis has finished :)"
}

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
        self.update_download_percent_complete(0.0)

        # Done
        self.show()

    ## Update the download slider/progress bar and the corresponding percentage label.
    #  @param self The object pointer.
    #  @param completion The percent complete in the range [0,100].
    def update_download_percent_complete(self, completion):
        # Slider is in the range[0,10000], multiply the percent for hundredth precision
        self.ui.download_percent_sli.setValue(int(completion*100))
        self.ui.download_percent_lbl.setText("{0}%".format(completion))

    ## Update the audio analysis stage completion label.
    #  @param self The object pointer.
    #  @param status The most up-to-date analysis status.
    def update_analysis_status(self, status):
        self.ui.analysis_status_lbl.setText(ANALYSIS_STATUS_LABELS.get(
            status,
            "Analysis state is unknown :("
        ))
