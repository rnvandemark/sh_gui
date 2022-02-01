from youtubesearchpython import VideosSearch

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QIcon

from scripts import GuiUtils
from scripts.YouTubeVideoListing import YouTubeVideoListing
from scripts.YouTubeVideoResult import YouTubeVideoResult
from scripts.QueuedYouTubeVideo import QueuedYouTubeVideo
from scripts.Ui_SoundFilePlaybackPage import Ui_SoundFilePlaybackPage

from sh_sfp_interfaces.msg import PlaybackUpdate
from sh_sfp_interfaces.srv import RequestPlaybackCommand

## The class encapsulating the display for the app's contents.
class SoundFilePlaybackPage(QWidget):

    #
    # Qt Signal(s)
    #

    ## Emits a YouTube video listing that the user reuested to download
    audio_download_queue_requested = pyqtSignal(dict)
    ## Emits a soundfile playback command of any type.
    sf_playback_command_requested = pyqtSignal(int)

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(SoundFilePlaybackPage, self).__init__(parent)

        #
        # Local variable(s)
        #

        self.queued_youtube_videos = {}

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
            (0,60),
            (1,40)
        )

        # Set to "nothing"
        self.set_null_playback_status()

        #
        # Make Qt connections
        #

        # Send a value of -1, and allow the GUI controller to decide if this means
        # 'resume' or 'pause', given that it tracks whether playback is currently
        # playing, paused, stopped, etc.
        self.ui.play_pause_btn.clicked.connect(lambda: self.request_playback_command(-1))
        self.ui.stop_btn.clicked.connect(lambda: self.request_playback_command(RequestPlaybackCommand.Request.STOP))
        self.ui.skip_btn.clicked.connect(lambda: self.request_playback_command(RequestPlaybackCommand.Request.SKIP))
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
        self.sf_playback_command_requested.emit(cmd)

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

    ## Queue a video that is confirmed able to start downloading.
    #  @param self The object pointer.
    #  @param youtube_listing_dict The YouTube query result that describes the video.
    def queue_video(self, youtube_listing_dict):
        queued_vid = QueuedYouTubeVideo(self.ui.queued_videos_scroll_area)
        queued_vid.ui.youtube_video_listing.populate(youtube_listing_dict)
        self.ui.queued_videos_layout.addWidget(queued_vid)
        self.queued_youtube_videos[queued_vid.ui.youtube_video_listing.get_video_id()] = queued_vid

    ## Received an update on a video's download by its ID.
    #  @param self The object pointer.
    #  @param video_id The unique ID of the YouTube video.
    #  @param completion The percent complete in the range [0,100].
    def update_download_percent_complete(self, video_id, completion):
        self.queued_youtube_videos[video_id].update_download_percent_complete(completion)

    ## Received an update on an audio's analysis by its ID.
    #  @param self The object pointer.
    #  @param video_id The unique ID of the original YouTube video.
    #  @param status The most up-to-date analysis status.
    def update_analysis_status(self, video_id, status):
        self.queued_youtube_videos[video_id].update_analysis_status(status)

    ## Update UI elements given the current sound file playback status.
    #  @param self The object pointer.
    #  @param update The sound file playback's update.
    #  @param title The title to display for the video.
    #  @param active Whether or not playback is active or has finished.
    def update_playback_status(self, update, title, active):
        self.ui.play_pause_btn.setText("▶" if (not active) or update.is_paused else "⏸")
        if active:
            self.ui.sound_file_name.setText(title)
            curr_total_secs = GuiUtils.get_duration_seconds(update.duration_current)
            total_total_secs = GuiUtils.get_duration_seconds(update.duration_total)
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

    ## 
    #  @param self The object pointer.
    #  @param video_id The unique ID of the YouTube video downloaded.
    def deque_audio_download(self, video_id):
        self.queued_youtube_videos[video_id].deleteLater()
        del self.queued_youtube_videos[video_id]
