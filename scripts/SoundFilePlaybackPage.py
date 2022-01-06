from youtubesearchpython import VideosSearch

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtGui import QIcon

from scripts import GuiUtils
from scripts.YouTubeVideoListing import YouTubeVideoListing
from scripts.YouTubeVideoResult import YouTubeVideoResult
from scripts.Ui_SoundFilePlaybackPage import Ui_SoundFilePlaybackPage

from sh_common_interfaces.msg import StringArr
from sh_sfp_interfaces.msg import PlaybackCommand, PlaybackUpdate

## The class encapsulating the display for the app's contents.
class SoundFilePlaybackPage(QWidget):

    #
    # Qt Signal(s)
    #

    ## 
    audio_download_queue_requested = pyqtSignal(YouTubeVideoListing)
    ## Emits a soundfile playback command of any type.
    sf_playback_command_requested = pyqtSignal(PlaybackCommand)

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(SoundFilePlaybackPage, self).__init__(parent)

        #
        # Local variable(s)
        #

        self.playing = True

        #
        # Basic UI/cosmetics
        #

        # Build UI object
        self.ui = Ui_SoundFilePlaybackPage()
        self.ui.setupUi(self)

        # Set YouTube search buttons
        self.ui.clear_youtube_search_btn.setIcon(QIcon(GuiUtils.get_image_url("clear_search.png")))
        self.ui.clear_youtube_search_btn.setIconSize(0.9 * self.ui.clear_youtube_search_btn.size())
        self.ui.youtube_search_btn.setIcon(QIcon(GuiUtils.get_image_url("search_youtube.png")))
        self.ui.youtube_search_btn.setIconSize(0.9 * self.ui.youtube_search_btn.size())

        # Split page contents
        GuiUtils.set_layout_stretches(
            self.ui.overall_layout,
            (0,50),
            (1,50)
        )

        # Set to "nothing"
        self.set_null_playback_status()

        #
        # Make Qt connections
        #

        self.ui.play_pause_btn.clicked.connect(lambda: self.request_playback_command(PlaybackCommand.PAUSE if self.playing else PlaybackCommand.RESUME))
        self.ui.stop_btn.clicked.connect(lambda: self.request_playback_command(PlaybackCommand.STOP))
        self.ui.skip_btn.clicked.connect(lambda: self.request_playback_command(PlaybackCommand.SKIP))
        self.ui.clear_youtube_search_btn.clicked.connect(self.clear_youtube_search)
        self.ui.youtube_search_btn.clicked.connect(self.search_youtube)

        # Done
        self.show()

    ## Clear the YouTube search text and the video results.
    #  @param self The object pointer.
    def purge_search_results(self):
        for i in reversed(range(self.ui.search_results_layout.count())):
            self.ui.search_results_layout.itemAt(i).widget().deleteLater()

    ## Emit a signal that passes along the requested command.
    #  @param self The object pointer.
    #  @param cmd The playback command to populate the message with.
    def request_playback_command(self, cmd):
        msg = PlaybackCommand()
        msg.cmd = cmd
        self.sf_playback_command_requested.emit(msg)

#    ## Open a file dialog to queue one or more sound files for playback.
#    #  @param self The object pointer.
#    def load_sound_files(self):
#        sound_file_paths, _ = QFileDialog.getOpenFileNames(
#            self,
#            "Select one or more sound files to open",
#            "/home",
#            "MP3s or WAVs (*.mp3 *.wav)"
#        )
#        if len(sound_file_paths) > 0:
#            sound_files_msg = StringArr()
#            sound_files_msg.data = sound_file_paths
#            self.sf_files_requested.emit(sound_files_msg)

    ## Update UI elements to "nothing".
    #  @param self The object pointer.
    def set_null_playback_status(self):
        self.ui.sound_file_name.setText("")
        self.ui.playback_time.setText("--:-- / --:--")
        self.ui.sound_file_playback_status.setValue(0)

    ## Clear the YouTube search text and the video results.
    #  @param self The object pointer.
    def clear_youtube_search(self):
        self.ui.youtube_search_bar.setText("")
        self.purge_search_results()

    ## Clear the YouTube search text and the video results.
    #  @param self The object pointer.
    def search_youtube(self):
        query = self.ui.youtube_search_bar.text()
        if query:
            self.purge_search_results()
            search_results = VideosSearch(
                query,
                limit=GuiUtils.YOUTUBE_SEARCH_RESULT_COUNT
            ).result()["result"]
            for n in range(len(search_results)):
                vid_result = YouTubeVideoResult(self.ui.search_results_scroll_area)
                vid_result.ui.youtube_video_listing.populate(search_results[n])
                vid_result.queue_requested.connect(self.audio_download_queue_requested)
                self.ui.search_results_layout.addWidget(vid_result)

    ## Update UI elements given the current sound file playback status.
    #  @param self The object pointer.
    #  @param msg The message containing all information related to sound file playback.
    def update_playback_status(self, msg):
        prev_playing = self.playing
        self.playing = msg.status == PlaybackUpdate.PLAYING
        if self.playing != prev_playing:
            self.ui.play_pause_btn.setText("⏸" if self.playing else "▶")
        if self.playing:
            self.ui.sound_file_name.setText(msg.name)
            curr_total_secs = msg.duration_current.to_sec()
            total_total_secs = msg.duration_total.to_sec()
            curr_min, curr_sec = divmod(curr_total_secs, 60)
            total_min, total_sec = divmod(total_total_secs, 60)
            self.ui.playback_time.setText("{0}:{1} / {2}:{3}".format(
                int(curr_min),
                "{:02d}".format(int(curr_sec)),
                int(total_min),
                "{:02d}".format(int(total_sec))
            ))
            self.ui.sound_file_playback_status.setValue(
                int((curr_total_secs / total_total_secs) * self.ui.sound_file_playback_status.maximum())
            )
        else:
            self.set_null_playback_status()
