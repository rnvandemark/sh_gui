from PyQt5.QtWidgets import QWidget

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

    ## Fill the given label to the given color.
    #  @param self The object pointer.
    #  @param lbl The label to paint.
    #  @param color The ROS msg color.
    def set_generic_peak_image(self, lbl, color):
        r,g,b = color.channels
        GuiUtils.color_label(lbl, r, g, b)

    ## Update the SCC telemetry on the screen
    #  @param self The object pointer.
    #  @param corner A ROS color peak telemetry message.
    def update_scc_telemetry(self, msg):
        img = msg.image
        if not img.encoding:
            img.encoding = "bgr8"
        self.ui.screen_image.setFixedSize(img.width, img.height)
        self.ui.screen_image.setPixmap(GuiUtils.get_qpixmap_from_rosimg(img))

        self.set_generic_peak_image(self.ui.left_peak_image, msg.left_current_peak)
        self.set_generic_peak_image(self.ui.right_peak_image, msg.right_current_peak)
