from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QFileDialog

from scripts import GuiUtils
from scripts.Ui_SoundFilePlaybackPage import Ui_SoundFilePlaybackPage

from sh_common_interfaces.msg import StringArr
from sh_sfp_interfaces.msg import PlaybackCommand, PlaybackUpdate

## The class encapsulating the display for the app's contents.
class SoundFilePlaybackPage(QWidget):

    #
    # Qt Signal(s)
    #

    ## Emits a soundfile playback command of any type.
    sf_playback_command_requested = pyqtSignal(PlaybackCommand)
    ## Emits a list of absolute file paths to requested sound files.
    sf_files_requested = pyqtSignal(StringArr)

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

        # Build UI object and set layout shapes
        self.ui = Ui_SoundFilePlaybackPage()
        self.ui.setupUi(self)

        # Set to "nothing"
        self.set_null_playback_status()

        #
        # Make Qt connections
        #

        self.ui.play_pause_btn.clicked.connect(lambda: self.request_playback_command(PlaybackCommand.PAUSE if self.playing else PlaybackCommand.RESUME))
        self.ui.stop_btn.clicked.connect(lambda: self.request_playback_command(PlaybackCommand.STOP))
        self.ui.skip_btn.clicked.connect(lambda: self.request_playback_command(PlaybackCommand.SKIP))

        # Done
        self.show()

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
