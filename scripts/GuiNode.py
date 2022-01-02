from PyQt5.QtCore import QThread

from rclpy import spin as rclpy_spin, shutdown as rclpy_shutdown
from rclpy.node import Node
from std_msgs.msg import Empty, Float32, Header

import sh_common_constants
from sh_common.heartbeat_node import HeartbeatNode
from sh_common_interfaces.msg import ModeChange, ModeChangeRequest, \
    DeviceActivationChange, CountdownState, WaveParticipantLocation, \
    WaveUpdate, Float32Arr, Color, StringArr
from sh_sfp_interfaces.msg import PlaybackCommand, PlaybackUpdate
from sh_scc_interfaces.msg import ColorPeaksTelem
from sh_scc_interfaces.srv import RequestScreenCalibration, \
    SetScreenCalibrationPointsOfHomography

MAX_AUX_DEVICE_COUNT = 32

#
# Class definitions
#

## A very simple QThread to run the ROS spin routine.
class SimpleRosThread(QThread):

    ## The constructor.
    #  @param self The object pointer.
    #  @param node The ROS node to async spin.
    #  @param parent This object's optional Qt parent.
    def __init__(self, node, parent=None):
        super(SimpleRosThread, self).__init__(parent)
        self.node = node

    ## Do the ROS spin routine until ROS has shutdown.
    #  @param self The object pointer.
    def run(self):
        self.node.log_info("Starting ROS spin.")
        rclpy_spin(self.node)
        self.node.log_info("Exiting ROS spin.")

## A class that owns all ROS elements, acting as the means of ROS connectivity for the smart home GUI.
class GuiNode(HeartbeatNode):

    ## The constructor.
    #  @param self The object pointer.
    #  @param qt_parent The Qt object used to interact with the Qt framework.
    def __init__(self, qt_parent):
        super(GuiNode, self).__init__("sh_gui")

        #
        # ROS publishers
        #

        self.mode_change_pub = self.create_publisher(
            ModeChange,
            sh_common_constants.topics.CONFIRMED_MODE_CHANGES,
            1
        )

#        self.device_activation_change_pub = self.create_publisher(
#            DeviceActivationChange,
#            "/smart_home/device_activation_change_chatter",
#            MAX_AUX_DEVICE_COUNT
#        )

        self.intensity_change_pub = self.create_publisher(
            Float32,
            sh_common_constants.topics.INTENSITY_CHANGE_UPDATES,
            1
        )

        self.countdown_state_pub = self.create_publisher(
            CountdownState,
            sh_common_constants.topics.COUNTDOWN_STATE_UPDATES,
            1
        )

        self.start_wave_mode_pub = self.create_publisher(
            Empty,
            sh_common_constants.topics.START_WAVE_MODE,
            1
        )

        self.wave_update_pub = self.create_publisher(
            WaveUpdate,
            sh_common_constants.topics.WAVE_UPDATES,
            MAX_AUX_DEVICE_COUNT
        )

        self.sound_file_playback_command_pub = self.create_publisher(
            PlaybackCommand,
            sh_common_constants.topics.PLAYBACK_COMMANDS,
            10
        )

        self.sound_file_path_list_pub = self.create_publisher(
            StringArr,
            sh_common_constants.topics.REQUESTED_PLAYBACK_FILES,
            10
        )

        #
        # ROS subscribers
        #

        self.mode_change_request_sub = self.create_subscription(
            ModeChangeRequest,
            sh_common_constants.topics.REQUESTED_MODE_CHANGES,
            self.mode_change_request_callback,
            1
        )

        self.countdown_state_sub = self.create_subscription(
            CountdownState,
            sh_common_constants.topics.COUNTDOWN_STATE_UPDATES,
            self.countdown_state_callback,
            1
        )

        self.participant_location_sub = self.create_subscription(
            WaveParticipantLocation,
            sh_common_constants.topics.WAVE_PARTICIPANT_LOCATION,
            self.participant_location_callback,
            MAX_AUX_DEVICE_COUNT
        )

        self.color_peak_left_sub = self.create_subscription(
            Color,
            sh_common_constants.topics.LEFT_COLOR_PEAK,
            self.left_color_peak_callback,
            1
        )

        self.color_peak_right_sub = self.create_subscription(
            Color,
            sh_common_constants.topics.RIGHT_COLOR_PEAK,
            self.right_color_peak_callback,
            1
        )

        self.cap_peaks_telem_sub = self.create_subscription(
            ColorPeaksTelem,
            sh_common_constants.topics.COLOR_PEAKS_TELEM,
            self.color_peaks_telem_callback,
            1
        )

        self.playback_frequencies_sub = self.create_subscription(
            Float32Arr,
            sh_common_constants.topics.PLAYBACK_FREQUENCIES,
            self.playback_frequencies_callback,
            1
        )

        self.cap_peaks_telem_sub = self.create_subscription(
            PlaybackUpdate,
            sh_common_constants.topics.PLAYBACK_UPDATES,
            self.playback_updates_callback,
            1
        )

        #
        # ROS service clients
        #

        self.screen_calibration_request_cli = self.create_client(
            RequestScreenCalibration,
            sh_common_constants.services.REQUEST_SCREEN_COLOR_CALIBRTION
        )

        self.screen_calibration_set_homography_points_cli = self.create_client(
            SetScreenCalibrationPointsOfHomography,
            sh_common_constants.services.SET_SCREEN_COLOR_HOMOG_POINTS
        )

        # Local variable(s)
        self.qt_parent = qt_parent
        self.ros_thread = SimpleRosThread(self, self.qt_parent)
        self.current_mode = None

        # Done
        self.log_info("Started.")

    ## Log info to ROSOUT.
    #  @param self The object pointer.
    #  @param smsg The string message to log.
    def log_info(self, smsg):
        self.get_logger().info(smsg)

    ## Log debug to ROSOUT.
    #  @param self The object pointer.
    #  @param smsg The string message to log.
    def log_debug(self, smsg):
        self.get_logger().debug(smsg)

    ## Log warn to ROSOUT.
    #  @param self The object pointer.
    #  @param smsg The string message to log.
    def log_warn(self, smsg):
        self.get_logger().warn(smsg)

    ## Log err to ROSOUT.
    #  @param self The object pointer.
    #  @param smsg The string message to log.
    def log_err(self, smsg):
        self.get_logger().error(smsg)

    ## Log fatal to ROSOUT.
    #  @param self The object pointer.
    #  @param smsg The string message to log.
    def log_fatal(self, smsg):
        self.get_logger().fatal(smsg)

    ## Log fatal to ROSOUT.
    #  @param self The object pointer.
    #  @param smsg The string message to log.
    def log_fatal(self, smsg):
        self.get_logger().fatal(smsg)

    ## With the node already configured, do any startup operations.
    #  @param self The object pointer.
    def sh_start(self):
        self.ros_thread.start()

    ## With the node running, do any stop operations.
    #  @param self The object pointer.
    def sh_stop(self):
        rclpy_shutdown()
        self.ros_thread.wait()

    ## Repackages and sends out the requested mode type.
    #  @param self The object pointer.
    #  @param msg The ROS message describing the node change request.
    def mode_change_request_callback(self, msg):
        self.set_mode_type(msg.mode_type)
    
    ## The routine to take the provided mode type ROS constant and send a new message.
    #  @param self The object pointer.
    def set_mode_type(self, mode_type):
        mode_change_msg = ModeChange()
        mode_change_msg.mode_type = mode_type
        mode_change_msg.header.stamp = self.get_clock().now().to_msg()
        self.mode_change_pub.publish(mode_change_msg)

        self.current_mode = mode_type

        # If changing to wave mode, advertise to peripheral devices and listen for responses
        if self.current_mode == ModeChange.WAVE:
            self.start_wave_mode_pub.publish(Empty())

        self.qt_parent.mode_type_updated.emit(self.current_mode)
        self.log_info("Set mode to [{0}].".format(self.current_mode))
    
    ## The routine to take the provided countdown state and send a new message.
    #  @param self The object pointer.
    def set_countdown_state(self, countdown_state):
        countdown_state_msg = CountdownState()
        countdown_state_msg.state = countdown_state
        self.countdown_state_pub.publish(countdown_state_msg)
        self.log_info("Set countdown state to [{0}].".format(countdown_state))
    
    ## A handler for countdown state changes.
    #  @param self The object pointer.
    #  @param msg The ROS message describing the updated countdown state.
    def countdown_state_callback(self, msg):
        self.qt_parent.countdown_state_updated.emit(msg)
    
    ## A handler for a wave mode participant's response.
    #  @param self The object pointer.
    #  @param msg The ROS message describing an appliance participating in the wave along with its location.
    def participant_location_callback(self, msg):
        self.qt_parent.wave_participant_responded.emit(msg)
    
    ## A handler for color peak process telemetry. Emits a signal containing the world preview image.
    #  @param self The object pointer.
    #  @param msg The ROS message with the telemetry info.
    def color_peaks_telem_callback(self, msg):
        self.qt_parent.world_image_updated.emit(msg.world_frame_image)
    
    ## Callback to update the left color peak.
    #  @param self The object pointer.
    #  @param msg The ROS color message.
    def left_color_peak_callback(self, msg):
        self.qt_parent.left_color_peak_updated.emit(msg)
    
    ## Callback to update the right color peak.
    #  @param self The object pointer.
    #  @param msg The ROS color message.
    def right_color_peak_callback(self, msg):
        self.qt_parent.right_color_peak_updated.emit(msg)
    
#    ## A helper function to package a device (in)activation request.
#    #  @param self The object pointer.
#    #  @param device_id The coordinated ID for the device that is being requested to be activated or deactivated.
#    #  @param active Whether or not the device is to be activated or otherwise.
#    def send_device_activation_change(self, device_id, active):
#        device_activation_change_msg = DeviceActivationChange()
#        device_activation_change_msg.device_id = device_id
#        device_activation_change_msg.active = active
#        self.device_activation_change_pub.publish(device_activation_change_msg)
#        self.log_info("Set device with ID [{0}] to [{1}ACTIVE].".format(device_id, "" if active else "IN"))
    
    ## Update the individual control intensity.
    #  @param self The object pointer.
    #  @param intensity The new intensity.
    def send_intensity_change(self, intensity):
        intensity_change_msg = Float32()
        intensity_change_msg.data = intensity
        self.intensity_change_pub.publish(intensity_change_msg)
        self.log_info("Set individual control intensity to [{0}].".format(intensity))
    
    ## Update the countdown state.
    #  @param self The object pointer.
    #  @param state The requested updated state.
    def send_countdown_state(self, state):
        countdown_state_msg = CountdownState()
        countdown_state_msg.state = state
        self.countdown_state_pub.publish(countdown_state_msg)
        self.log_info("Set countdown state to [{0}].".format(state))
    
    ## Update the wave mode intensities.
    #  @param self The object pointer.
    #  @param msg The collection of intensities with their corresponding participant ID's.
    def send_wave_update(self, msg):
        self.wave_update_pub.publish(msg)
    
    ## Issue a service request to get currently isolated corners.
    #  @param self The object pointer.
    #  @param max_corners The max corners to find.
    #  @param quality_level The minimal acceptable quality of corners.
    #  @param min_dist Minimum possible Euclidean pixel distance between found corners.
    #  @return The response to the ROS service request.
    def request_screen_calibration(self, max_corners, quality_level, min_dist):
        req = RequestScreenCalibration.Request()
        req.max_corners = max_corners
        req.quality_level = float(quality_level)
        req.min_dist = float(min_dist)
        req.do_blur = True
        req.kh = 5
        req.kw = 5
        return self.screen_calibration_request_cli.call(req)
    
    ## Attempt to use the four selected points for screen calibration homography.
    #  @param self The object pointer.
    #  @param pts The four ROS points of homography.
    #  @return The response to the ROS service request.
    def confirm_screen_calibration(self, pts):
        req = SetScreenCalibrationPointsOfHomography.Request()
        req.pts_of_homog = pts
        result = self.screen_calibration_set_homography_points_cli.call(req)
        if result.successful:
            self.log_info(
                "Homog pts: {0}, {1}, {2}, {3}".format(*["[x={0},y={1}]".format(p.x,p.y) for p in pts])
            )
        else:
            self.log_err("Failed to confirm corner calibration.")
        return result

    ## Publish the given ROS msg playback command.
    #  @param self The object pointer.
    #  @param command The playback command to issue.
    def send_playback_command(self, command):
        self.sound_file_playback_command_pub.publish(command)

    ## Publish the request sound files to queue.
    #  @param self The object pointer.
    #  @param sound_file_paths The absolute paths to the files requested.
    def append_sound_files_for_playback(self, sound_file_paths):
        self.sound_file_path_list_pub.publish(sound_file_paths)

    ## Forward the playback frequencies to callbacks.
    #  @param self The object pointer.
    #  @param msg The array of frequencies.
    def playback_frequencies_callback(self, msg):
        self.qt_parent.playback_frequencies_updated.emit(msg)

    ## Forward the playback update to callbacks.
    #  @param self The object pointer.
    #  @param msg The playback status update, whether or not something is playing.
    def playback_updates_callback(self, msg):
        self.qt_parent.playback_status_updated.emit(msg)
