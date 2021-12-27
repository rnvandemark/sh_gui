from os.path import join as ojoin

from PyQt5.QtCore import QTime, QDate, QDateTime
from PyQt5.QtGui import QPalette, QColor, QImage, QPixmap

from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge
from sh_common_interfaces.msg import ModeChange

#
# Constants
#

GUI_INSTALL_LIB_DIRECTORY = get_package_share_directory("sh_gui")

MODE_LABEL_YELLOW = "#F0E68C"

COLOR_STD_COMPONENT_FG = "#652828"
COLOR_STD_COMPONENT_BG = "#CDCDCD"

COLOR_TRAFFIC_LIGHT_RED = "#F00"
COLOR_TRAFFIC_LIGHT_YLW = "#FF0"
COLOR_TRAFFIC_LIGHT_GRN = "#0A0"

MODES_DICT = {
    ModeChange.FULL_OFF             : ("Full Off",           "#0F2F2F"),
    ModeChange.FULL_ON              : ("Full On",            "#3CCB2C"),
    ModeChange.INDIVIDUAL_CONTROL   : ("Individual Control", MODE_LABEL_YELLOW),
    ModeChange.MORNING_COUNTDOWN    : ("Morning Countdown",  MODE_LABEL_YELLOW),
    ModeChange.FOLLOW_COMPUTER_SOUND: ("Follow Hub",         MODE_LABEL_YELLOW),
    ModeChange.FOLLOW_ROOM_SOUND    : ("Follow Room",        MODE_LABEL_YELLOW),
    ModeChange.WAVE                 : ("Wave",               MODE_LABEL_YELLOW)
}

TRAFFIC_LIGHT_IMAGE_WIDTH  = 200
TRAFFIC_LIGHT_IMAGE_HEIGHT = 500

COLOR_PEAK_COLOR_COORDINATOR_IMAGE_HEIGHT = 480
COLOR_PEAK_COLOR_COORDINATOR_IMAGE_WIDTH = 640
COLOR_PEAK_COLOR_PREVIEW_IMAGE_HEIGHT = 200
COLOR_PEAK_COLOR_PREVIEW_IMAGE_WIDTH = 200

CV_BRIDGE = CvBridge()

#
# Global functions
#

## Given a smart home mode, get a user-friendly name and a color code for it.
#  @param val The key in the dictionary.
#  @return A tuple of the name and color code.
def get_mode_characteristics(val):
    return MODES_DICT[val] if val in MODES_DICT else ("UNDEFINED", "#FF0000")

## Access a resource in the installation library.
#  @param url_suffix The name of the directory and file to access.
#  @return The absolute URL of the desired resource.
def get_resource_url(url_suffix):
    return ojoin(GUI_INSTALL_LIB_DIRECTORY, "images", url_suffix)

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
