from os.path import join as ojoin

from PyQt5.QtCore import QTime, QDate, QDateTime
from PyQt5.QtGui import QPalette, QColor, QImage, QPixmap

from rclpy.duration import Duration
from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge

#
# Constants
#

GUI_INSTALL_LIB_DIRECTORY = get_package_share_directory("sh_gui")

TRAFFIC_LIGHT_IMAGE_WIDTH  = 200
TRAFFIC_LIGHT_IMAGE_HEIGHT = 500

COLOR_PEAK_COLOR_PREVIEW_IMAGE_HEIGHT = 200
COLOR_PEAK_COLOR_PREVIEW_IMAGE_WIDTH = 200

YOUTUBE_SEARCH_RESULT_COUNT = 10

CV_BRIDGE = CvBridge()

#
# Global functions
#

## Get the full path of some file in this package.
#  @param url_components The remaining/suffix components of the file URL.
#  @return The absolute URL of the desired file.
def get_asset_url(*url_components):
    return ojoin(GUI_INSTALL_LIB_DIRECTORY, *url_components)

## Get the full path of an image in this package.
#  @param url_components The remaining/suffix components of the file URL.
#  @return The absolute URL of the desired image.
def get_image_url(*url_components):
    return get_asset_url("images", *url_components)

## Given a ROS img message, get a corresponding QPixmap.
#  @warning Assumes BGR8 image format.
#  @param img_ros The ROS image message
#  @return The QPixmap.
def get_qpixmap_from_rosimg(img_ros):
    img_cv = CV_BRIDGE.imgmsg_to_cv2(img_ros)
    h, w, _ = img_cv.shape
    return QPixmap.fromImage(QImage(img_cv.data, w, h, 3*w, QImage.Format_BGR888))

## Fill the given label to the given RGB and intensity.
#  @param lbl The label widget to paint.
#  @param r The red channel of the color.
#  @param g The green channel of the color.
#  @param b The blue channel of the color.
#  @param intensity The intensity of the given color (is treated as 100% if unspecified).
def color_label(lbl, r, g, b, intensity=None):
    color = QColor(r,g,b)
    if intensity is not None:
        if (intensity >= 0) and (intensity <= 1):
            color.setHsv(
                color.hue(),
                color.saturation(),
                color.value() * intensity
            )
    pm = QPixmap(lbl.size())
    pm.fill(color)
    lbl.setPixmap(pm)

## Helper function to get the current time.
#  @return The current time.
def curr_time():
    return QTime.currentTime()

## Helper function to get the current date.
#  @return The current date.
def curr_date():
    return QDate.currentDate()

## Helper function to get the current date-time.
#  @return The current date-time.
def curr_date_time():
    return QDateTime.currentDateTime()

## Helper function to set stretches of a layout at specific indices.
#  @param layout The QLayout object to set stretches for
#  @param stretches A variably-lengthed list of relative stretch factors.
def set_layout_stretches(layout, *stretches):
    for stretch in stretches:
        layout.setStretch(*stretch)

## Helper function to get the current time.
#  @param lbl The QWidget object.
#  @param stretches A variably-lengthed list of brushes and corresponding colors to set.
def adjust_palette(lbl, *brushes):
    palette = lbl.palette()
    for role,color in brushes:
        qcolor = QColor(color) if type(color) is str else color
        palette.setColor(role, qcolor)
    lbl.setPalette(palette)

## Helper function to set the text color of a QLabel.
#  @param lbl The QLabel object.
#  @param color The color.
def set_label_text_color(lbl, color):
    adjust_palette(lbl, (QPalette.WindowText, color))

## Truncate the given Q(Date)Time to hours and minutes, ignoring seconds and smaller.
#  @param qval The Q(Date)Time object.
#  @return The truncated value.
def truncate(qval):
    qtype = type(qval)
    if qtype is QTime:
        return QTime(qval.hour(), qval.minute())
    elif qtype is QDateTime:
        return QDateTime(qval.date(), QTime(qval.time().hour(), qval.time().minute()))
    else:
        return None

## Format the given time to a standard, simple format.
#  @param qtime The QTime object.
#  @return The stringified time.
def simply_formatted_time(qtime):
    return qtime.toString("h:mm AP")

## Format the given date-time to a standard, simple format.
#  @param qtime The QDateTime object.
#  @return The stringified date-time.
def simply_formatted_date_time(qdatetime):
    return qdatetime.toString("dd.MM.yyyy h:mm AP")

## Get the number of seconds that a ROS Duration message covers.
#  @param duration_msg The builtin_interfaces Duration msg.
#  @return The number of seconds that the duration covers.
def get_duration_seconds(duration_msg):
    duration = Duration.from_msg(duration_msg)
    return duration.nanoseconds / 1000000000

## Send an async goal to the given action client. If it is connected to its
#  server, return the future of the request response. Otherwise, return null.
#  @param act_cli The action client.
#  @param goal The goal to send to the corresponding action server.
#  @param fb_cb An optional callback for the action's feedback.
#  @return The future of the request response if successful, null otherwise.
def send_action_goal_async(act_cli, goal, fb_cb=None):
    return act_cli.send_goal_async(
        goal,
        feedback_callback=fb_cb
    ) if act_cli.server_is_ready() else None
