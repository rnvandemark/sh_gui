from PyQt5.QtCore import QTime, QDateTime, pyqtSignal
from PyQt5.QtWidgets import QWidget, QButtonGroup
from PyQt5.QtGui import QPixmap, QPalette

from scripts import GuiUtils
from scripts.Ui_MorningCountdownSubpage import Ui_MorningCountdownSubpage

from sh_common_interfaces.msg import CountdownState

## A subpage to handle all widgets needed to control the morning countdown traffic light.
class MorningCountdownSubpage(QWidget):

    #
    # Qt Signals
    #

    ## Emits a signal for the four date-time values that describes a countdown sequence.
    countdown_goal_updated = pyqtSignal(QDateTime, QDateTime, QDateTime, QDateTime)

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(MorningCountdownSubpage, self).__init__(parent)

        # Build UI object and set layout shape
        self.ui = Ui_MorningCountdownSubpage()
        self.ui.setupUi(self)

        # Bind AM and PM buttons into a group, select AM button by default
        self.btn_group = QButtonGroup(parent=self)
        self.btn_group.setExclusive(True)
        self.btn_group.addButton(self.ui.am_radio_btn)
        self.btn_group.addButton(self.ui.pm_radio_btn)
        self.ui.am_radio_btn.click()

        # Set individual styles
        GuiUtils.adjust_palette(
            self.ui.red_slider,
            (QPalette.Button, GuiUtils.COLOR_TRAFFIC_LIGHT_RED),
            (QPalette.Highlight, GuiUtils.COLOR_TRAFFIC_LIGHT_RED)
        )
        GuiUtils.adjust_palette(
            self.ui.yellow_slider,
            (QPalette.Button, GuiUtils.COLOR_TRAFFIC_LIGHT_YLW),
            (QPalette.Highlight, GuiUtils.COLOR_TRAFFIC_LIGHT_YLW)
        )
        GuiUtils.adjust_palette(
            self.ui.green_slider,
            (QPalette.Button, GuiUtils.COLOR_TRAFFIC_LIGHT_GRN),
            (QPalette.Highlight, GuiUtils.COLOR_TRAFFIC_LIGHT_GRN)
        )
        GuiUtils.set_label_text_color(self.ui.red_lbl, GuiUtils.COLOR_TRAFFIC_LIGHT_RED)
        GuiUtils.set_label_text_color(self.ui.yellow_lbl, GuiUtils.COLOR_TRAFFIC_LIGHT_YLW)
        GuiUtils.set_label_text_color(self.ui.green_lbl, GuiUtils.COLOR_TRAFFIC_LIGHT_GRN)

        # Init each traffic light image
        for i,state in enumerate(["none", "green", "yellow", "red", "all"]):
            self.ui.traffic_light_images.widget(i).setPixmap(QPixmap(
                GuiUtils.get_image_url("traffic_lights", "traffic_light_{0}.png".format(state))
            ).scaled(GuiUtils.TRAFFIC_LIGHT_IMAGE_WIDTH, GuiUtils.TRAFFIC_LIGHT_IMAGE_HEIGHT))

        # Make Qt connections
        self.ui.green_slider.valueChanged.connect(self.update_green_slider)
        self.ui.yellow_slider.valueChanged.connect(self.update_yellow_slider)
        self.ui.red_slider.valueChanged.connect(self.update_red_slider)
        self.ui.hour_slider.valueChanged.connect(self.update_generic_time_slider)
        self.ui.minute_slider.valueChanged.connect(self.update_generic_time_slider)
        self.ui.am_radio_btn.released.connect(self.update_generic_time_button)
        self.ui.pm_radio_btn.released.connect(self.update_generic_time_button)
        self.ui.confirm_goal_time_btn.released.connect(self.confirm_countdown_goal)

        # Init other required data
        self.do_set_value = True
        self.init_date_time = None
        self.secs_to_goal_date_time = None

        # Done
        self.show()

    ## Helper function to update R/Y/G sliders so their values are ordered properly.
    #  @param self The object pointer.
    #  @param new_value The value to potentially set the slider to.
    #  @param slider The slider object whose value is potentially being set.
    #  @param lbl The label to set the date-time to.
    #  @param slider_before The slider whose value must become before this slider.
    #  @param slider_after The slider whose value must become after this slider.
    def update_generic_stage_slider(self, new_value, slider, lbl, slider_before, slider_after):
        if self.do_set_value:
            slider.setValue(new_value)
        lbl.setText(GuiUtils.simply_formatted_time(self.init_date_time.addSecs(new_value).time()))
        if slider_before:
            if slider_before.value() > new_value:
                slider_before.setValue(new_value)
        if slider_after:
            if slider_after.value() < new_value:
                slider_after.setValue(new_value)

    ## Update the red slider to a new value.
    #  @param self The object pointer.
    #  @param new_value The value to set the slider to.
    def update_red_slider(self, new_value):
        self.update_generic_stage_slider(
            new_value,
            self.ui.red_slider,
            self.ui.red_lbl,
            self.ui.yellow_slider,
            None
        )

    ## Update the yellow slider to a new value.
    #  @param self The object pointer.
    #  @param new_value The value to set the slider to.
    def update_yellow_slider(self, new_value):
        self.update_generic_stage_slider(
            new_value,
            self.ui.yellow_slider,
            self.ui.yellow_lbl,
            self.ui.green_slider,
            self.ui.red_slider)

    ## Update the green slider to a new value.
    #  @param self The object pointer.
    #  @param new_value The value to set the slider to.
    def update_green_slider(self, new_value):
        self.update_generic_stage_slider(
            new_value,
            self.ui.green_slider,
            self.ui.green_lbl,
            None,
            self.ui.yellow_slider
        )

    ## Set the start and goal times, setting the goal-time widgets and defaulting the
    #  R/Y/G sliders to cut the remaining time into equal fourths.
    #  @param self The object pointer.
    #  @param curr_date_time The current date-time.
    #  @param curr_date_time The objective date-time.
    def set_goal_time(self, curr_date_time, goal_date_time):
        # Add an additional second because there are likely more than 0 milliseconds as
        # a part of the current time, so missing one extra full second
        self.init_date_time = curr_date_time
        self.secs_to_goal_date_time = self.init_date_time.secsTo(goal_date_time) + 1
        goal_time = goal_date_time.time()

        # Set the goal time sliders
        self.ui.hour_slider.setValue(goal_time.hour() % 12)
        self.ui.minute_slider.setValue(goal_time.minute())
        self.ui.goal_time_lbl.setText(GuiUtils.simply_formatted_time(goal_time))
        if goal_time.hour() < 12:
            self.ui.am_radio_btn.click()
        else:
            self.ui.pm_radio_btn.click()

        # Set the range and positions of each stage slider
        for slider in [self.ui.green_slider, self.ui.yellow_slider, self.ui.red_slider]:
            slider.setMaximum(self.secs_to_goal_date_time)
        secs_each = self.secs_to_goal_date_time / 4
        self.do_set_value = not self.do_set_value
        self.update_red_slider(secs_each*3)
        self.update_yellow_slider(secs_each*2)
        self.update_green_slider(secs_each)
        self.do_set_value = not self.do_set_value

    ## Handle updating any one of the goal-time widgets.
    #  @param self The object pointer.
    def update_generic_time_widget(self):
        if not self.do_set_value: return
        # Calculate the goal time given the widget inputs
        curr_date_time = GuiUtils.curr_date_time()
        goal_minute = self.ui.minute_slider.value()
        goal_hour = self.ui.hour_slider.value()
        if self.btn_group.checkedButton() == self.ui.pm_radio_btn:
            goal_hour += 12
        # Make the goal date the next day if the goal time passes midnight
        goal_time = QTime(goal_hour, goal_minute)
        goal_date = GuiUtils.curr_date()
        if goal_time < curr_date_time.time():
            goal_date = goal_date.addDays(1)
        # Set goal time and stage sliders
        self.do_set_value = False
        self.set_goal_time(
            curr_date_time,
            QDateTime(goal_date, goal_time)
        )
        self.do_set_value = True

    ## Handle updating any one of the goal-time sliders.
    #  @param self The object pointer.
    #  @param unused An unused value.
    def update_generic_time_slider(self, unused):
        self.update_generic_time_widget()

    ## Handle updating any one of the goal-time AP/PM buttons.
    #  @param self The object pointer.
    def update_generic_time_button(self):
        self.update_generic_time_widget()

    ## Send the four date-time values of interest to an hour&minute precision given the
    #  current values of the four sliders.
    #  @param self The object pointer.
    def confirm_countdown_goal(self):
        self.countdown_goal_updated.emit(
            GuiUtils.truncate(self.init_date_time.addSecs(self.ui.green_slider.value())),
            GuiUtils.truncate(self.init_date_time.addSecs(self.ui.yellow_slider.value())),
            GuiUtils.truncate(self.init_date_time.addSecs(self.ui.red_slider.value())),
            GuiUtils.truncate(self.init_date_time.addSecs(self.secs_to_goal_date_time))
        )

    ## Update the traffic light image given an update on the current countdown state.
    #  @param self The object pointer.
    #  @param msg The countdown state ROS msg.
    def update_countdown_state(self, msg):
        state = msg.state
        if (state >= CountdownState.NONE) and (state <= CountdownState.EXPIRED):
            self.ui.traffic_light_images.setCurrentIndex(state - CountdownState.NONE)
