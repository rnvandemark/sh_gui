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

        # Set other UI elements
        # TODO: fix colors
        GuiUtils.adjust_palette(
            self.ui.reset_btn,
            (QPalette.Text, "00A"),
            (QPalette.WindowText, "00A"),
            (QPalette.Window, "00A"),
            (QPalette.Base, "00A"),
            (QPalette.Highlight, "00A")
        )

        # Local data
        self.corner_lbl_list = [
            self.ui.tl_lbl,
            self.ui.tr_lbl,
            self.ui.bl_lbl,
            self.ui.br_lbl
        ]
        self.reset_corners()

        # Make Qt connections
        self.ui.reset_btn.released.connect(self.reset_corners)

        # Done
        self.show()

    ## Reset the corner labels to null.
    #  @param self The object pointer.
    def reset_corners(self):
        for i in range(4):
            self.corner_update_at(i, None)

    ## Update the label for the corner at the given index with the given value.
    #  @param self The object pointer.
    #  @param idx The index of the corner to set (top/bottom, left/right).
    #  @param corner A ROS msg 2D point.
    def corner_update_at(self, idx, corner):
        self.corner_lbl_list[idx].setText(
            "<None>" if corner is None else "[{0},{1}]".format(corner.x, corner.y)
        )
        self.ui.confirm_btn.setEnabled((idx == 3) and (corner is not None))

    ## Update the homography world image.
    #  @param self The object pointer.
    #  @param corner A ROS msg image.
    def set_world_image(self, msg):
        self.ui.world_image.setPixmap(GuiUtils.get_qpixmap_from_rosimg(msg))

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
