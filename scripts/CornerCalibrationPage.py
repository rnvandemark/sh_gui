from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPalette, QPixmap, QColor

from scripts import GuiUtils
from scripts.Ui_CornerCalibrationPage import Ui_CornerCalibrationPage

## The page encapsulating the screen homography calibration and color preview.
class CornerCalibrationPage(QWidget):

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(CornerCalibrationPage, self).__init__(parent)

        # Build UI object
        self.ui = Ui_CornerCalibrationPage()
        self.ui.setupUi(self)

        # Done
        self.show()

    ## Update the captured image of the screen.
    #  @param self The object pointer.
    #  @param corner A ROS msg image.
    def set_screen_image(self, msg):
        self.ui.screen_image.setPixmap(GuiUtils.get_qpixmap_from_rosimg(msg))

    ## Fill the given label to the given color.
    #  @param self The object pointer.
    #  @param lbl The label to paint.
    #  @param color The ROS msg color.
    def set_generic_peak_image(self, lbl, color):
        r,g,b = color.channels
        GuiUtils.color_label(lbl, r, g, b)

    ## Fill the left color peak preview image to the given color.
    #  @param self The object pointer.
    #  @param color The ROS msg color.
    def set_left_peak_image(self, color):
        self.set_generic_peak_image(self.ui.left_peak_image, color)

    ## Fill the left color peak preview image to the given color.
    #  @param self The object pointer.
    #  @param color The ROS msg color.
    def set_right_peak_image(self, color):
        self.set_generic_peak_image(self.ui.right_peak_image, color)
