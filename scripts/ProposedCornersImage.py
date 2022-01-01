from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel

from scripts import GuiUtils

## A basic label that emits signals when clicked.
class ProposedCornersImage(QLabel):

    #
    # Qt Signal(s)
    #

    ## Emits the (x,y) coords of a mouse release event when an image is loaded.
    image_clicked = pyqtSignal(int, int)

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(ProposedCornersImage, self).__init__(parent)
        # Local variable(s)
        self.ready = False
        # Done
        self.show()

    ## Override mouseReleaseEvent to emit a signal if an image has been loaded.
    #  @param self The object pointer.
    #  @param evt The mouse release event.
    def mouseReleaseEvent(self, evt):
        if self.ready:
            self.image_clicked.emit(evt.x(), evt.y())

    ## Set this pixel map to the given image.
    #  @param self The object pointer.
    #  @param msg The ROS msg image.
    def set_from_ros_img(self, msg, new_height, new_width):
        self.setFixedSize(new_width, new_height)
        self.setPixmap(GuiUtils.get_qpixmap_from_rosimg(msg).scaled(new_width, new_height))
        self.ready = True
