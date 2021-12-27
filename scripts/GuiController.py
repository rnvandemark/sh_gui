from sys import argv as sargv
from math import cos, pi
from scipy.spatial import cKDTree

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from rclpy import init as rclpy_init
from sensor_msgs.msg import Image
from sh_common_interfaces.msg import ModeChange, CountdownState, WaveUpdate, \
    WaveParticipantLocation, Color, Float32Arr
from sh_sfp_interfaces.msg import PlaybackUpdate

from scripts import GuiUtils
from scripts.GuiNode import GuiNode

#
# Constants
#

_2PI = 2 * pi
WAVE_UPDATE_PERIOD_MS = 10

#
# Class definitions
#

## Data needed to monitor progress for a morning countdown sequence.
class MorningCountdownData(object):

    ## The constructor.
    #  @param self The object pointer.
    #  @param grn The date-time where the green light should turn on.
    #  @param ylw The date-time where the yellow light should turn on.
    #  @param red The date-time where the red light should turn on.
    #  @param end The date-time where the goal/expiration time is reached.
    def __init__(self, grn, ylw, red, end):
        self.grn = grn
        self.ylw = ylw
        self.red = red
        self.end = end
        self.curr_state = None

## Data needed to update the peripheral devices participating in the wave mode.
class WaveUpdateData(object):

    ## The constructor.
    #  @param self The object pointer.
    def __init__(self):
        self.id_location_map = {}
        self.period = None
        self.location = 0.0

    ## Helper function to add a participant given its integer ID and location.
    #  @param self The object pointer.
    #  @param msg The WaveParticipantLocation msg to use to add the participant.
    def add_participant(self, msg):
        self.id_location_map[msg.participant_id] = msg.position

    ## Calculate the intensity at the given location.
    #  @param self The object pointer.
    #  @param other The location to calculate intensity at.
    #  @return The intensity at the other location given the current wave location.
    def calc_intensity_at(self, other):
        return cos(self.location - other)

    ## Calculate the intensity of each peripheral device at the current time.
    #  @param self The object pointer.
    #  @return The WaveUpdate msg containing each intensity and ID's.
    def consume_intensities(self):
        if self.period is None: return None
        msg = WaveUpdate()
        for pId, pLoc in self.id_location_map.items():
            msg.participant_ids.append(pId)
            msg.intensities.data.append(self.calc_intensity_at(self.id_location_map[pId]))
        self.location += ((WAVE_UPDATE_PERIOD_MS / self.period) * _2PI)
        while self.location >= _2PI:
            self.location -= _2PI
        return msg

## Container to identify the current mode and any data used to support this mode.
class ActiveModeData(object):

    ## The constructor.
    #  @param self The object pointer.
    def __init__(self):
        self.reset(None)

    ## Set the mode but nullify any assisting data.
    #  @param self The object pointer.
    #  @param mode The new mode.
    def reset(self, mode):
        self.mode = mode
        self.data = None

## Data needed to calibrate the corners used for homography and calculating color peaks.
class CornerCalibrationData(object):

    ## The constructor.
    #  @param self The object pointer.
    def __init__(self):
        self.detected = None
        self.tree = None
        self.clear_selected()

    ## Clear any selected points.
    #  @param self The object pointer.
    def clear_selected(self):
        self.selected = [None] * 4

    ## Set the detected feature points of the current view and create their binary search tree.
    #  @param self The object pointer.
    #  @param points The detected feature points.
    def set_detected(self, points):
        self.detected = points
        self.tree = cKDTree([(p.x,p.y) for p in self.detected])

    ## If more corners can be selected, find the point closest to the click at [x,y].
    #  @param self The object pointer.
    #  @param self x The click's x-coordinate.
    #  @param self y The click's y-coordinate.
    #  @param self n_jobs How many parallel workers to create when searching, defaults to the
    #  number of available CPU's.
    #  @return The index of the corner set [1,4] and the ROS Point msg describing the position.
    def select_next(self, x, y, n_jobs=-1):
        idx = -1
        corner = None
        if self.detected is not None:
            for i in range(4):
                if self.selected[i] == None:
                    idx = i
                    break
            if idx != -1:
                _, ii = self.tree.query((x,y), k=1, n_jobs=n_jobs)
                corner = self.detected[ii]
                self.selected[idx] = corner
        return idx, corner

## A controller for the smart home hub node, and a utility for the GUI as well.
class GuiController(QObject):

    #
    # Qt Signals
    #

    ## Emits the current mode type's enum value
    mode_type_updated = pyqtSignal(int)
    ## Emits the current morning countdown state
    countdown_state_updated = pyqtSignal(CountdownState)
    ## Emits a wave participant response
    wave_participant_responded = pyqtSignal(WaveParticipantLocation)
    ## Emits the homography's world image telemetry
    world_image_updated = pyqtSignal(Image)
    ## Emits the calculated color peak of the left portion of the region
    left_color_peak_updated = pyqtSignal(Color)
    ## Emits the calculated color peak of the right portion of the region
    right_color_peak_updated = pyqtSignal(Color)
    ## Emits updates on the last set of playback frequencies calculated
    playback_frequencies_updated = pyqtSignal(Float32Arr)
    ## Emits updates on the current sound file playback status
    playback_status_updated = pyqtSignal(PlaybackUpdate)

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(GuiController, self).__init__(parent)

        # Local variables
        self.active_mode_data = ActiveModeData()
        self.corner_calibration_data = CornerCalibrationData()

        self.one_hertz_timer = QTimer(parent=self)
        self.wave_update_timer = QTimer(parent=self)

        # Make Qt connections
        self.one_hertz_timer.timeout.connect(self.check_for_countdown_state_update)
        self.wave_update_timer.timeout.connect(self.wave_mode_update)

        # Init ROS and create node interface
        rclpy_init(args=sargv)
        self.gui_node = GuiNode(self)

    ## Start all peripherals.
    #  @param self The object pointer.
    def start(self):
        self.gui_node.sh_start()
        self.one_hertz_timer.start(1000)

    ## Blocking call to stop all peripherals.
    #  @param self The object pointer.
    def stop(self):
        self.wave_update_timer.stop()
        self.one_hertz_timer.stop()
        self.gui_node.sh_stop()

    ## Calculate if the countdown state has changed since the last time this routine ran.
    #  @param self The object pointer.
    def check_for_countdown_state_update(self):
        # Ignore if not doing the morning countdown routine or if the goal times haven't been set yet
        if self.active_mode_data.mode != ModeChange.MORNING_COUNTDOWN: return
        if not self.active_mode_data.data: return

        curr_state = self.active_mode_data.data.curr_state
        next_state = None

        # First cycle, do start confirmation
        if curr_state == None:
            next_state = CountdownState.CONFIRMATION
        # Ignore if already expired
        elif curr_state != CountdownState.EXPIRED:
            # Get latest countdown state that has been reached
            now = GuiUtils.curr_date_time()
            if (curr_state < CountdownState.EXPIRED) and (self.active_mode_data.data.end <= now):
                next_state = CountdownState.EXPIRED
            elif (curr_state < CountdownState.RED) and (self.active_mode_data.data.red <= now):
                next_state = CountdownState.RED
            elif (curr_state < CountdownState.YELLOW) and (self.active_mode_data.data.ylw <= now):
                next_state = CountdownState.YELLOW
            elif (curr_state < CountdownState.GREEN) and (self.active_mode_data.data.grn <= now):
                next_state = CountdownState.GREEN
            elif curr_state == CountdownState.CONFIRMATION:
                next_state = CountdownState.NONE

        if next_state is not None:
            self.set_countdown_state(next_state)
            self.active_mode_data.data.curr_state = next_state
            self.gui_node.log_info("Advanced to CountdownState {0}".format(next_state))

    ## Send updates to the intensity of each peripheral device if in wave mode.
    #  @param self The object pointer.
    def wave_mode_update(self):
        if self.active_mode_data.mode != ModeChange.WAVE: return
        msg = self.active_mode_data.data.consume_intensities()
        if msg is not None:
            self.gui_node.send_wave_update(msg)

    ## Change the mode type, including publishing a message to inform all devices the mode has changed.
    #  @param self The object pointer.
    #  @param mode_type The enum value of the new mode type.
    def set_mode_type(self, mode_type):
        self.gui_node.set_mode_type(mode_type)
        self.active_mode_data.reset(mode_type)
        if mode_type == ModeChange.WAVE:
            self.active_mode_data.data = WaveUpdateData()
            self.wave_update_timer.start(WAVE_UPDATE_PERIOD_MS)
        else:
            self.wave_update_timer.stop()

    ## Helper function to pass the new countdown state to the ROS node interface.
    #  @param self The object pointer.
    #  @param countdown_state The new countdown state.
    def set_countdown_state(self, countdown_state):
        self.gui_node.set_countdown_state(countdown_state)

    ## Helper function to pass the new individual control intensity to the ROS node interface.
    #  @param self The object pointer.
    #  @param intensity The new intensity.
    def set_individual_control_intensity(self, intensity):
        self.gui_node.send_intensity_change(intensity)

    ## Accept new morning countdown milestones and goal times.
    #  @param self The object pointer.
    #  @param grn The date-time where the green light should turn on.
    #  @param ylw The date-time where the yellow light should turn on.
    #  @param red The date-time where the red light should turn on.
    #  @param end The date-time where the goal/expiration time is reached.
    def set_countdown_goals(self, grn, ylw, red, end):
        if self.active_mode_data.mode != ModeChange.MORNING_COUNTDOWN:
            self.gui_node.log_warn(
                "Ignoring countdown goals! Current mode is {0}".format(
                    self.active_mode_data.mode
            ))
            return
        self.active_mode_data.data = MorningCountdownData(grn, ylw, red, end)
        self.gui_node.log_info(
            "Received countdown goals: green='{0}', yellow='{1}', red='{2}', goal='{3}'".format(
                GuiUtils.simply_formatted_date_time(grn),
                GuiUtils.simply_formatted_date_time(ylw),
                GuiUtils.simply_formatted_date_time(red),
                GuiUtils.simply_formatted_date_time(end)
        ))

    ## Given the current time, get a default display for the objective countdown time.
    #  @param self The object pointer.
    #  @return The start/current time and the default goal time.
    def get_default_countdown_time(self):
        curr_date_time = GuiUtils.curr_date_time()
        curr_min = curr_date_time.time().minute()
        # Get the next minute that is a multiple of 15 and at least 5 whole mins later
        goal_min = ((curr_min + 15) // 15) * 15;
        if goal_min - curr_min < 6:
            goal_min += 15
        # Calculate and return the result as well as the current time used
        return curr_date_time, curr_date_time.addSecs((goal_min - curr_min) * 60)

    ## Handle a response for a peripheral device to participate in the wave.
    #  @param self The object pointer.
    #  @param msg The ROS msg.
    def add_wave_update_participant(self, msg):
        if self.active_mode_data.mode != ModeChange.WAVE: return
        if type(self.active_mode_data.data) is not WaveUpdateData: return
        self.active_mode_data.data.add_participant(msg)
        self.gui_node.log_info("Added participant: [{0},{1}]".format(
            msg.participant_id, msg.position
        ))

    ## Set the revolution period of the wave.
    #  @param self The object pointer.
    #  @param period The period, in milliseconds.
    def set_wave_update_period(self, period):
        if self.active_mode_data.mode != ModeChange.WAVE: return
        if type(self.active_mode_data.data) is not WaveUpdateData: return
        self.active_mode_data.data.period = period

    ## Request to start a new screen calibration by getting the detected feature points. Use
    #  the default parameters specified by that controller unless specified otherwise in this
    #  function's arguments.
    #  @param self The object pointer.
    #  @param max_corners The max corners to find.
    #  @param quality_level The minimal acceptable quality of corners.
    #  @param min_dist Minimum possible Euclidean pixel distance between found corners.
    #  @return The image with each found feature point marked.
    def request_screen_calibration(self, max_corners=-1, quality_level=-1, min_dist=-1):
        result = self.gui_node.request_screen_calibration(max_corners,
                                                          quality_level,
                                                          min_dist)
        if result.corners_found:
            self.corner_calibration_data.set_detected(result.corner_positions)
            return result.marked_image
        else:
            self.gui_node.log_err("Corner detection pipeline failed.")
            return None

    ## Clear all selected screen calibration corners.
    #  @param self The object pointer.
    def clear_selected_corners(self):
        self.corner_calibration_data.clear_selected()

    ## Handle a click that is attempting to selected a screen calibration corner.
    #  @param self The object pointer.
    #  @param self x The click's x-coordinate.
    #  @param self y The click's y-coordinate.
    #  @return The index of the corner set [1,4] and the ROS Point msg describing the position.
    def select_corner_near(self, x, y):
        idx, corner = self.corner_calibration_data.select_next(x,y)
        if idx != -1:
            self.gui_node.log_debug(
                "Proposed image click at [{0},{1}], got [{2},{3}]".format(
                    x, y, corner.x, corner.y
            ))
        return idx, corner

    ## Attempt screen calibration homography given the four currently selected corners.
    #  @param self The object pointer.
    #  @return Whether or not the request to start the routine was successful.
    def confirm_screen_calibration(self):
        result = self.gui_node.confirm_screen_calibration(self.corner_calibration_data.selected)
        return result.successful

    ## Helper function to pass the sound file playback command to the ROS node interface.
    #  @param self The object pointer.
    #  @param command The playback command to issue.
    def send_playback_command(self, command):
        self.gui_node.send_playback_command(command)

    ## Helper function to pass the requested sound file(s) to the ROS node interface.
    #  @param self The object pointer.
    #  @param sound_file_paths The absolute paths to the files requested.
    def append_sound_files_for_playback(self, sound_file_paths):
        self.gui_node.append_sound_files_for_playback(sound_file_paths)
