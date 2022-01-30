from sys import argv as sargv
from math import cos, pi
from collections import OrderedDict

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from rclpy import init as rclpy_init
from sh_common_interfaces.msg import ModeChange, CountdownState, WaveUpdate, \
    WaveParticipantLocation, Float32Arr
from sh_scc_interfaces.msg import ColorPeaksTelem
from sh_sfp_interfaces.msg import PlaybackUpdate
from sh_sfp_interfaces.srv import RequestPlaybackCommand

from scripts import GuiUtils
from scripts.GuiNode import GuiNode
from scripts.YouTubeVideoListing import YouTubeVideoListing

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

## A class used to pipe data back and forth from the audio download action server.
class AudioDownloadManager(object):

    ## The constructor.
    #  @param self The object pointer.
    #  @param controller The GUI controller.
    def __init__(self, controller):
        self.video_id = None
        self.controller = controller
        self.send_audio_download_goal_future = None
        self.audio_download_result_future = None

    ## Send a goal to the action server to start a download.
    #  @param self The object pointer.
    #  @param video_id The unique video ID according to YouTube.
    def send_goal(self, video_id):
        self.video_id = video_id
        self.send_audio_download_goal_future = self.controller.gui_node.queue_youtube_video_for_download(
            self.handle_feedback,
            self.video_id
        )
        if self.send_audio_download_goal_future:
            self.send_audio_download_goal_future.add_done_callback(self.handle_request_response)
            return True
        else:
            return False

    ## Callback for the download request's result (accepted or rejected?).
    #  @param self The object pointer.
    #  @param future The finished future object containing the response.
    def handle_request_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.controller.gui_node.log_err(
                "Audio download request was rejected: '{0}'".format(self.video_id)
            )
        else:
            self.audio_download_result_future = goal_handle.get_result_async()
            self.audio_download_result_future.add_done_callback(self.handle_result)

    ## Callback for a download's feedback updates.
    #  @param self The object pointer.
    #  @param feedback The download's feedback.
    def handle_feedback(self, feedback):
        completion = feedback.feedback.completion
        self.controller.audio_download_completion_updated.emit(self.video_id, completion)
        self.controller.gui_node.log_debug(
            "Download of '{0}' {1}% complete.".format(self.video_id, completion)
        )

    ## Callback for a download's result.
    #  @param self The object pointer.
    #  @param future The finished future object containing the result's value.
    def handle_result(self, future):
        result = future.result().result
        self.controller.handle_completed_video_download(
            self.video_id,
            result.local_urls.data
        )

## A class to describe a downloaded sound file.
class DownloadedAudio(object):

    ## The constructor.
    #  @param self The object pointer.
    #  @param youtube_listing_dict The result from the original YouTube query.
    def __init__(self, youtube_listing_dict, local_url=None):
        self.youtube_listing_dict = youtube_listing_dict
        self.local_url = local_url

## A class used to pipe data back and forth from the sound file player action server.
class SoundFilePlayerManager(object):

    ## The constructor.
    #  @param self The object pointer.
    #  @param controller The GUI controller.
    def __init__(self, controller):
        self.controller = controller
        self.reset()

    ## Reset to an 'initial' state.
    #  @param self The object pointer.
    def reset(self):
        self.video_id = None
        self.local_url = None
        self.active = False
        self.paused = False
        self.stopped = False
        self.send_sound_file_playback_goal_future = None
        self.sound_file_playback_result_future = None

    ## Send a goal to the action server to start playback of a sound file.
    #  @param self The object pointer.
    #  @param video_id The unique video ID according to YouTube that was audio was downloaded from.
    #  @param local_url The absolute filename of the sound file saved locally.
    def send_goal(self, video_id, local_url):
        self.reset()
        self.video_id = video_id
        self.local_url = local_url
        self.active = True
        self.send_sound_file_playback_goal_future = self.controller.gui_node.request_play_sound_file(
            self.local_url,
            self.handle_feedback
        )
        if self.send_sound_file_playback_goal_future:
            self.send_sound_file_playback_goal_future.add_done_callback(self.handle_request_response)
            return True
        else:
            return False

    ## Callback for the play request's result (accepted or rejected?).
    #  @param self The object pointer.
    #  @param future The finished future object containing the response.
    def handle_request_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.active = False
            self.controller.gui_node.log_err(
                "Request to play sound file was rejected: '{0}'".format(self.local_url)
            )
        else:
            self.sound_file_playback_result_future = goal_handle.get_result_async()
            self.sound_file_playback_result_future.add_done_callback(self.handle_result)

    ## Callback for a playback's feedback updates.
    #  @todo Implement playback title.
    #  @param self The object pointer.
    #  @param feedback The playback's feedback.
    def handle_feedback(self, feedback):
        update = feedback.feedback.update
        self.paused = update.is_paused
        self.controller.playback_status_updated.emit(
            update,
            "",
            self.active
        )

    ## Callback for a play request's result.
    #  @param self The object pointer.
    #  @param future The finished future object containing the result's value.
    def handle_result(self, future):
        result = future.result().result
        self.controller.gui_node.log_info(
            "Finished playing '{0}' (originally from {1}).".format(self.video_id, self.local_url)
        )
        self.active = False
        self.stopped = result.was_stopped
        self.controller.handle_completed_sound_file_playback(self.video_id)

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
    ## Emits the screen color coordinator's telemetry
    scc_telemetry_updated = pyqtSignal(ColorPeaksTelem)
    ## Emits a signal that a video reuested to be downloaded was confirmed
    audio_download_queue_confirmed = pyqtSignal(dict)
    ## Emits the audio download's latest progress for the corresponding video
    audio_download_completion_updated = pyqtSignal(str, float)
    ## Emits the video ID of a queued sound that is about to start playing
    starting_sound_file_playback = pyqtSignal(str)
    ## Emits updates on the current sound file playback status
    playback_status_updated = pyqtSignal(PlaybackUpdate, str, bool)

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(GuiController, self).__init__(parent)

        # Local variables
        self.active_mode_data = ActiveModeData()

        self.one_hertz_timer = QTimer(parent=self)
        self.wave_update_timer = QTimer(parent=self)

        self.audio_download_managers = {}
        self.downloaded_audios = OrderedDict()
        self.sound_file_player_manager = SoundFilePlayerManager(self)

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

    ## Helper function to pass the sound file playback command to the ROS node interface.
    #  @param self The object pointer.
    #  @param command The playback command to issue.
    def send_playback_command(self, command):
        if -1 == command:
            if self.sound_file_player_manager.paused or self.sound_file_player_manager.stopped:
                command = RequestPlaybackCommand.Request.RESUME
            else:
                command = RequestPlaybackCommand.Request.PAUSE
        if (
            (not self.sound_file_player_manager.active)
            and (command == RequestPlaybackCommand.Request.RESUME)
        ):
            self.check_for_next_playback(True)
        self.gui_node.send_playback_command(command)

    ## Handle the user's request to queue a new YouTube video for sound file playback.
    #  If the listing is not set, simply ignore the request.
    #  @param self The object pointer.
    #  @param youtube_listing_dict The YouTube query result that describes the video.
    def queue_youtube_video_for_download(self, youtube_listing_dict):
        video_id = youtube_listing_dict["id"]
        if video_id:
            audio_download_manager = AudioDownloadManager(self)
            if audio_download_manager.send_goal(video_id):
                self.audio_download_queue_confirmed.emit(youtube_listing_dict)
                self.audio_download_managers[video_id] = audio_download_manager
                self.downloaded_audios[video_id] = DownloadedAudio(youtube_listing_dict)
            else:
                self.gui_node.log_err("Failed to send audio download request.")

    ## Handle a YouTube video download having been completed.
    #  @param self The object pointer.
    #  @param video_id The unique YouTube video ID.
    #  @param local_urls The list of local file URLs that the download(s) were saved to.
    def handle_completed_video_download(self, video_id, local_urls):
        self.gui_node.log_info(
            "Video with id '{0}' saved locally to {1}.".format(
                video_id,
                local_urls
        ))
        # TODO: improve this, for now assume local_urls[1] is the WAV file
        self.downloaded_audios[video_id].local_url = local_urls[1]
        del self.audio_download_managers[video_id]
        self.check_for_next_playback(False)

    ## Handle a sound file's playback having finished.
    #  @param self The object pointer.
    #  @param video_id The unique YouTube video ID.
    def handle_completed_sound_file_playback(self, video_id):
        self.playback_status_updated.emit(
            PlaybackUpdate(),
            "",
            False
        )
        del self.downloaded_audios[video_id]
        self.check_for_next_playback(False)

    ## Check if the next queued downloaded sound file, if any, should be started.
    #  If any should, the request is sent. If not, this does nothing.
    #  @param self The object pointer.
    #  @param ignore_stopped Whether or not the next playback should proceed
    #  even though playback is currently stopped.
    def check_for_next_playback(self, ignore_stopped):
        if (
            (not self.sound_file_player_manager.active)
            and (ignore_stopped or (not self.sound_file_player_manager.stopped))
            and self.downloaded_audios
        ):
            video_id = next(iter(self.downloaded_audios))
            local_url = self.downloaded_audios[video_id].local_url
            if local_url:
                self.sound_file_player_manager.send_goal(
                    video_id,
                    local_url
                )
                self.starting_sound_file_playback.emit(video_id)
