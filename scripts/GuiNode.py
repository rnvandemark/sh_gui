from PyQt5.QtCore import QThread

from rclpy import spin as rclpy_spin, shutdown as rclpy_shutdown
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import Empty, Float32

from scripts import GuiUtils

import sh_common_constants
from sh_common.heartbeat_node import HeartbeatNode
from sh_common_interfaces.msg import ModeChange, ModeChangeRequest, \
    DeviceActivationChange, CountdownState, WaveParticipantLocation, \
    WaveUpdate, Float32Arr, Color, StringArr
from sh_scc_interfaces.msg import ColorPeaksTelem
from sh_sfp_interfaces.srv import RequestPlaybackCommand
from sh_sfp_interfaces.action import DownloadAudio, PlaySoundFile, \
    AnalyzeSoundFile
from sh_sfp_interfaces.msg import OnsetDetectionAlgorithms, \
    WindowingAlgorithms, RhythmDetectionAlgorithms

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

        self.color_peaks_telem_sub = self.create_subscription(
            ColorPeaksTelem,
            sh_common_constants.topics.COLOR_PEAKS_TELEM,
            self.scc_telemetry_callback,
            1
        )

        #
        # ROS service clients
        #

        self.request_playback_command_cli = self.create_client(
            RequestPlaybackCommand,
            sh_common_constants.services.PLAYBACK_COMMANDS
        )

        #
        # ROS action clients
        #

        self.download_audio_act = ActionClient(
            self,
            DownloadAudio,
            sh_common_constants.actions.DOWNLOAD_AUDIO
        )

        self.analyze_audio_act = ActionClient(
            self,
            AnalyzeSoundFile,
            sh_common_constants.actions.ANALYZE_SOUND_FILE
        )

        self.play_sound_file_act = ActionClient(
            self,
            PlaySoundFile,
            sh_common_constants.actions.REQUEST_PLAY_SOUND_FILE
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
    
    ## Callback to update the telemetry from the color preak calculation pipeline.
    #  @param self The object pointer.
    #  @param msg The ROS color peak calculation telemetry message.
    def scc_telemetry_callback(self, msg):
        self.qt_parent.scc_telemetry_updated.emit(msg)
    
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

    ## Publish the given ROS msg playback command.
    #  @param self The object pointer.
    #  @param command The playback command to issue.
    def send_playback_command(self, command):
        req = RequestPlaybackCommand.Request()
        req.cmd = command
        resp = self.request_playback_command_cli.call(req)
        if resp.success:
            self.log_info("Successfully sent sound playback command [{0}].".format(command))
        else:
            self.log_error("Error sending sound playback command [{0}].".format(command))

    ## Place a request to download a YouTube video with the specified ID.
    #  @param self The object pointer.
    #  @param feedback_callback The callback function to handle feedback from the action server.
    #  @param video_id The unique ID of the YouTube video.
    #  @param quality The desired quality of the downloaded audio.
    #  @param file_formats_data The desired file formats.
    #  @return The future object created for the goal request.
    def queue_youtube_video_for_download(
            self,
            feedback_callback,
            video_id,
            quality=DownloadAudio.Goal.QUALITY_320,
            file_formats_data=["m4a", "wav"]
    ):
        return GuiUtils.send_action_goal_async(
            self.download_audio_act,
            DownloadAudio.Goal(
                video_id=video_id,
                quality=quality,
                file_formats=StringArr(data=file_formats_data)),
            fb_cb=feedback_callback
        )

    ## Place a request to analyze the audio of a sound file at the specified path.
    #  @param self The object pointer.
    #  @param feedback_callback The callback function to handle feedback from the action server.
    #  @param local_url The absolute filename of the sound file saved locally.
    #  @param onset_alg The algorithm to use for onset detection.
    #  @param rhythm_alg The algorithm to use for rhythm/beat detection.
    #  @param window_alg The algorithm to use for windowing.
    #  @return The future object created for the goal request.
    def request_audio_analysis(
            self,
            feedback_callback,
            local_url,
            onset_alg=OnsetDetectionAlgorithms.HFC,
            rhythm_alg=RhythmDetectionAlgorithms.MULTIFEATURE,
            window_alg=WindowingAlgorithms.HAMMING
    ):
        return GuiUtils.send_action_goal_async(
            self.analyze_audio_act,
            AnalyzeSoundFile.Goal(
                local_url=local_url,
                onset=OnsetDetectionAlgorithms(alg=onset_alg),
                rhythm=RhythmDetectionAlgorithms(alg=rhythm_alg),
                window=WindowingAlgorithms(alg=window_alg)),
            fb_cb=feedback_callback
        )

    ## Place a request to play the sound file at the specified path.
    #  @param self The object pointer.
    #  @param feedback_callback The callback function to handle feedback from the action server.
    #  @param local_url The absolute filename of the sound file saved locally.
    #  @return The future object created for the goal request.
    def request_play_sound_file(self, local_url, feedback_callback):
        return GuiUtils.send_action_goal_async(
            self.play_sound_file_act,
            PlaySoundFile.Goal(local_url=local_url),
            fb_cb=feedback_callback
        )
