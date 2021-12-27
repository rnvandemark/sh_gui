from PyQt5.QtCore import Qt, QCoreApplication, pyqtSignal
from PyQt5.QtGui import QPixmap, QPalette, QColor, QBrush, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow

from scripts import GuiUtils
from scripts.GuiController import GuiController
from scripts.Ui_Gui import Ui_Gui

from sh_common_interfaces.msg import ModeChange

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
            (3,5),
            (4,5),
            (5,4),
            (6,23),
            (7,23)
        )

        # Set application-wide settings for widgets
        std_font = QFont("MSGothic", pointSize=28)
        std_font.setBold(True)
        QApplication.setFont(std_font, "QLabel")
        QApplication.setFont(std_font, "QPushButton")
        QApplication.setFont(std_font, "QRadioButton")
        std_palette = QPalette()
        std_palette.setBrush(QPalette.WindowText, QColor(GuiUtils.COLOR_STD_COMPONENT_FG))
        QApplication.setPalette(std_palette, "QLabel")
        QApplication.setPalette(std_palette, "QPushButton")
        QApplication.setPalette(std_palette, "QRadioButton")

        # Set background image
        self.screen_size = QApplication.instance().primaryScreen().size()
        bg_palette = QPalette()
        bg_palette.setBrush(
            QPalette.Window,
            QBrush(QPixmap(GuiUtils.get_resource_url("kyoto.png")).scaled(
                self.screen_size,
                Qt.IgnoreAspectRatio))
        )
        self.setPalette(bg_palette)

        #
        # Set dynamic/miscellaneous values
        #

        # Populate available mode type dropdown
        self.ui.curr_mode_dropdown.addItems(v[0] for v in GuiUtils.MODES_DICT.values())
        self.ui.curr_mode_dropdown.setFont(std_font)
        # Set this text here because it's easier to do so than in the .ui file
        self.ui.prev_page_btn.setText("<<")
        self.ui.next_page_btn.setText(">>")
        # Set single-slider subpage slider states
        self.ui.individual_control_subpage.set_slider_state(1, 1000, 500)
        self.ui.wave_subpage.set_slider_state(1, 6000, 1000)
        # TODO: fix colors
        GuiUtils.adjust_palette(
            self.ui.curr_mode_dropdown,
            (QPalette.Text, GuiUtils.COLOR_STD_COMPONENT_FG),
            (QPalette.WindowText, GuiUtils.COLOR_STD_COMPONENT_FG),
            (QPalette.Window, GuiUtils.COLOR_STD_COMPONENT_BG),
            (QPalette.Base, GuiUtils.COLOR_STD_COMPONENT_BG)
        )

        #
        # Make Qt connections
        #

        self.ui.curr_mode_dropdown.currentIndexChanged.connect(self.request_mode_change)
        self.ui.prev_page_btn.pressed.connect(self.go_to_prev_page)
        self.ui.next_page_btn.pressed.connect(self.go_to_next_page)
        self.gui_controller.one_hertz_timer.timeout.connect(self.handle_date_time_update)
        self.mode_type_requested.connect(self.gui_controller.set_mode_type)
        self.gui_controller.mode_type_updated.connect(self.handle_mode_update)
        self.ui.individual_control_subpage.ui.slider.valueChanged.connect(self.individual_control_intensity_update)
        self.ui.morning_countdown_subpage.countdown_goal_updated.connect(self.gui_controller.set_countdown_goals)
        self.gui_controller.countdown_state_updated.connect(self.ui.morning_countdown_subpage.update_countdown_state)
        self.ui.wave_subpage.ui.slider.valueChanged.connect(self.handle_wave_update_period_update)
        self.gui_controller.wave_participant_responded.connect(self.gui_controller.add_wave_update_participant)
        self.ui.corner_calibration_page.ui.reset_btn.released.connect(self.gui_controller.clear_selected_corners)
        self.ui.corner_calibration_page.ui.request_calibration_btn.released.connect(self.handle_corner_calibration_request)
        self.ui.corner_calibration_page.ui.proposed_corners_image.image_clicked.connect(self.handle_proposed_corner_selection)
        self.ui.corner_calibration_page.ui.confirm_btn.released.connect(self.gui_controller.confirm_screen_calibration)
        self.gui_controller.world_image_updated.connect(self.ui.corner_calibration_page.set_world_image)
        self.gui_controller.left_color_peak_updated.connect(self.ui.corner_calibration_page.set_left_peak_image)
        self.gui_controller.right_color_peak_updated.connect(self.ui.corner_calibration_page.set_right_peak_image)
        self.ui.sound_file_playback_page.sf_playback_command_requested.connect(self.gui_controller.send_playback_command)
        self.ui.sound_file_playback_page.sf_files_requested.connect(self.gui_controller.append_sound_files_for_playback)
        self.gui_controller.playback_frequencies_updated.connect(self.ui.follow_hub_subpage.playback_frequencies_updated)
        self.gui_controller.playback_status_updated.connect(self.ui.sound_file_playback_page.update_playback_status)

        #
        # Any immediately-prior initialization
        #

        # Set initial values for date-time label
        self.handle_date_time_update()
        # Start controller then initialize current mode
        self.gui_controller.start()
        self.request_mode_change(self.ui.curr_mode_dropdown.currentIndex())
        
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

    ## The callback to updating the current mode label.
    #  @param self The object pointer.
    #  @param new_mode The enum of the new mode being entered.
    def handle_mode_update(self, new_mode):
        if self.app_is_closing: return
        # Set label at top-right corner of screen
        text, color = GuiUtils.get_mode_characteristics(new_mode)
        self.ui.curr_mode_lbl.setText(text)
        GuiUtils.set_label_text_color(self.ui.curr_mode_lbl, color)
        # Select the proper widget out of the two stacks
        self.ui.mode_stacked_content.setCurrentIndex(new_mode - ModeChange.META_BEGIN)
        self.ui.all_stacked_content.setCurrentIndex(0)

        # Handle any special requirements to start each type of mode
        if new_mode == ModeChange.MORNING_COUNTDOWN:
            curr_date_time, goal_date_time = self.gui_controller.get_default_countdown_time()
            self.ui.morning_countdown_subpage.set_goal_time(curr_date_time, goal_date_time)
        elif new_mode == ModeChange.INDIVIDUAL_CONTROL:
            self.individual_control_intensity_update()
        elif new_mode == ModeChange.WAVE:
            self.handle_wave_update_period_update()

    ## Places a request to set the mode type given the dropdown index.
    #  @param self The object pointer.
    #  @param index The index in the dropdown menu of the mode change requested.
    def request_mode_change(self, index):
        if self.app_is_closing or (index < 0): return
        # Only bother changing mode if it's different than the current one
        new_mode = ModeChange.META_BEGIN + index
        if new_mode != self.gui_controller.gui_node.current_mode:
            self.mode_type_requested.emit(new_mode)

    ## Traverse the given number of pages.
    #  @param self The object pointer.
    #  @param diff The number of indices to translate by.
    def translate_page(self, diff):
        self.ui.all_stacked_content.setCurrentIndex(
            (self.ui.all_stacked_content.currentIndex() + diff) % self.ui.all_stacked_content.count()
        )

    ## The callback to decrement the window page index.
    #  @param self The object pointer.
    def go_to_prev_page(self):
        self.translate_page(-1)

    ## The callback to increment the window page index.
    #  @param self The object pointer.
    def go_to_next_page(self):
        self.translate_page(+1)

    ## The callback to changing the individual control intensity slider.
    #  @param self The object pointer.
    def individual_control_intensity_update(self):
        slider = self.ui.individual_control_subpage.ui.slider
        intensity = slider.value() / (slider.maximum() - slider.minimum() + 1)
        self.ui.individual_control_subpage.set_slider_label(str(round(intensity, 3)))
        self.gui_controller.set_individual_control_intensity(intensity)

    ## The callback to changing the wave update period slider.
    #  @param self The object pointer.
    def handle_wave_update_period_update(self):
        slider = self.ui.wave_subpage.ui.slider
        period_ms = 60000 * slider.value() // (slider.maximum() - slider.minimum() + 1)
        self.ui.wave_subpage.set_slider_label("{0} seconds".format(round(period_ms/1000, 3)))
        self.gui_controller.set_wave_update_period(period_ms)

    ## The callback to changing the wave update period slider.
    #  @param self The object pointer.
    def handle_corner_calibration_request(self):
        img = self.gui_controller.request_screen_calibration()
        if img is not None:
            self.ui.corner_calibration_page.ui.proposed_corners_image.set_from_ros_img(img)

    ## The callback to the user clicking on the proposed homography points image.
    #  @param self The object pointer.
    #  @param x The click's x-coordinate.
    #  @param y The click's y-coordinate.
    def handle_proposed_corner_selection(self, x, y):
        idx, corner = self.gui_controller.select_corner_near(x, y)
        if (idx >= 0) and (idx <= 3):
            self.ui.corner_calibration_page.corner_update_at(idx, corner)
