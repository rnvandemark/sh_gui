from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QPalette, QBrush
from PyQt5.QtWidgets import QApplication, QMainWindow

from scripts import GuiUtils
from scripts.GuiController import GuiController
from scripts.Ui_Gui import Ui_Gui

## The class encapsulating the display for the app's contents.
class Gui(QMainWindow):

    #
    # Qt Signal(s)
    #

    ## Emits the enum value of a requested mode change
    mode_type_requested = pyqtSignal(int)

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(Gui, self).__init__(parent)

        #
        # Local variable(s)
        #

        # Flag to track if the application is shutting down
        self.app_is_closing = False
        # Create the smart home controller and therefore the ROS node interface
        self.gui_controller = GuiController(parent=self)

        #
        # Basic UI/cosmetics
        #

        # Build UI object and set layout shapes
        self.ui = Ui_Gui()
        self.ui.setupUi(self)
        GuiUtils.set_layout_stretches(
            self.ui.overall_layout,
            (0,15),
            (1,85)
        )
        GuiUtils.set_layout_stretches(
            self.ui.menu_layout,
            (0,16),
            (1,16),
            (2,4),
            (3,40),
            (4,4),
            (5,10),
            (6,10)
        )

        # Set background image
        self.screen_size = QApplication.instance().primaryScreen().size()
        bg_palette = QPalette()
        bg_palette.setBrush(
            QPalette.Window,
            QBrush(QPixmap(GuiUtils.get_image_url("kyoto.png")).scaled(
                self.screen_size,
                Qt.IgnoreAspectRatio))
        )
        self.setPalette(bg_palette)

        #
        # Set dynamic/miscellaneous values
        #

        # Populate available page groups dropdown then navigate to the page it
        # points to by default
        self.ui.curr_stacked_group_dropdown.addItems(
            self.ui.stacked_page_groups.widget(i).groupName for i in range(self.ui.stacked_page_groups.count())
        )
        self.change_stacked_group(self.ui.curr_stacked_group_dropdown.currentIndex())

        # Set this text here because it's easier to do so than in the .ui file
        self.ui.prev_page_btn.setText("<<")
        self.ui.next_page_btn.setText(">>")

        #
        # Make Qt connections
        #

        self.ui.curr_stacked_group_dropdown.currentIndexChanged.connect(self.change_stacked_group)
        self.ui.prev_page_btn.pressed.connect(self.go_to_prev_page)
        self.ui.next_page_btn.pressed.connect(self.go_to_next_page)
        self.gui_controller.one_hertz_timer.timeout.connect(self.handle_date_time_update)
        self.ui.morning_countdown_subpage.countdown_goal_updated.connect(self.gui_controller.set_countdown_goals)
        self.gui_controller.countdown_state_updated.connect(self.ui.morning_countdown_subpage.update_countdown_state)
        self.gui_controller.wave_participant_responded.connect(self.gui_controller.add_wave_update_participant)
        self.gui_controller.scc_telemetry_updated.connect(self.ui.screen_color_coordination_page.update_scc_telemetry)
        self.ui.sound_file_playback_page.audio_download_queue_requested.connect(self.gui_controller.queue_youtube_video_for_download)
        self.gui_controller.audio_download_queue_confirmed.connect(self.ui.sound_file_playback_page.queue_video)
        self.gui_controller.audio_download_completion_updated.connect(self.ui.sound_file_playback_page.update_download_percent_complete)
        self.gui_controller.audio_analysis_status_updated.connect(self.ui.sound_file_playback_page.update_analysis_status)
        self.gui_controller.starting_sound_file_playback.connect(self.ui.sound_file_playback_page.deque_audio_download)
        self.ui.sound_file_playback_page.sf_playback_command_requested.connect(self.gui_controller.send_playback_command)
        self.gui_controller.playback_status_updated.connect(self.ui.sound_file_playback_page.update_playback_status)

        #
        # Any immediately-prior initialization
        #

        # Set initial values for date-time label
        self.handle_date_time_update()
        # Finally, start the controller
        self.gui_controller.start()
        
        # Done
        self.show()

    ## Override key press event to safely quit the app on pressing ESCAPE.
    #  @param self The object pointer.
    #  @param evt The key-press event.
    def keyPressEvent(self, evt):
        if evt.key() == Qt.Key_Escape:
            self.app_is_closing = True
            self.gui_controller.stop()
            self.close()

    ## The callback to updating the current time label.
    #  @param self The object pointer.
    def handle_date_time_update(self):
        if self.app_is_closing: return
        self.ui.curr_time_lbl.setText(
            GuiUtils.curr_date_time().toString("ddd MMM d, yy\nhh:mm:ss ap")
        )

    ## Changes the active stacked page group.
    #  @param self The object pointer.
    #  @param new_index The index in the dropdown menu of the group selected.
    def change_stacked_group(self, new_index):
        if self.app_is_closing or (new_index < 0): return
        self.ui.stacked_page_groups.setCurrentIndex(new_index)

    ## Traverse the given number of pages within the current page group.
    #  @param self The object pointer.
    #  @param diff The number of indices to translate by.
    def translate_page(self, diff):
        curr_group = self.ui.stacked_page_groups.currentWidget()
        if None != curr_group:
            curr_group.setCurrentIndex(
                (curr_group.currentIndex() + diff) % curr_group.count()
            )

    ## The callback to decrement the window page index.
    #  @param self The object pointer.
    def go_to_prev_page(self):
        self.translate_page(-1)

    ## The callback to increment the window page index.
    #  @param self The object pointer.
    def go_to_next_page(self):
        self.translate_page(+1)
