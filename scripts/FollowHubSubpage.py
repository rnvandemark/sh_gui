from queue import Queue
from math import e

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QColorConstants

from scripts import GuiUtils
from scripts.DoublyLinkedList import DoublyLinkedList
from scripts.Ui_FollowHubSubpage import Ui_FollowHubSubpage

#
# Hardcode some constants for now
#

# The number of elements to manipulate given the playback intensities.
NUM_ELEMS = 7
# The max number of samples in the FFT window to monitor
WINDOW_LENGTH = 450

#
# Class definitions
#

## A container that keeps a linked-list of frequencies that are also pushed/popped in/out
#  of a queue to maintain a sliding window of frequencies.
class FrequencyWindowManager(object):

    ## The constructor.
    #  @param self The object pointer.
    def __init__(self):
        self.ll = DoublyLinkedList()
        self.queue = Queue()
        self.queue_size = 0

    ## Insert a value into the frequency window.
    #  @param self The object pointer.
    #  @param value The frequency to insert into the sliding window.
    def insert(self, value):
        while self.queue_size >= WINDOW_LENGTH:
            self.ll.remove(self.queue.get())
            self.queue.task_done()
            self.queue_size -= 1
        self.queue.put(self.ll.insert(value))
        self.queue_size += 1

    ## Helper function to get the current min and max frequencies of the window.
    #  @param self The object pointer.
    #  @return A tuple of the (min,max) frequency.
    def get_mm(self):
        return self.ll.lmin.parent.value, self.ll.lmax.child.value

## A simple demo for how playback frequencies change light intensity.
class FollowHubSubpage(QWidget):

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(FollowHubSubpage, self).__init__(parent)

        # Build UI object and set layout shapes
        self.ui = Ui_FollowHubSubpage()
        self.ui.setupUi(self)

        # Local variables
        self.freq_manager = FrequencyWindowManager()

        # Set initial label colors
        self.lbl_color_pairs = (
            (self.ui.red_lbl, QColorConstants.Red),
            (self.ui.org_lbl, QColor(255, 128, 0)),
            (self.ui.ylw_lbl, QColorConstants.Yellow),
            (self.ui.grn_lbl, QColorConstants.DarkGreen),
            (self.ui.blu_lbl, QColorConstants.Blue),
            (self.ui.ind_lbl, QColor(75, 0, 130)),
            (self.ui.vlt_lbl, QColorConstants.Magenta)
        )
        self.set_lbl_intensities([1]*NUM_ELEMS)

        # Done
        self.show()

    ## Given the calculated frequencies, calculate the intensities of all visual elements.
    #  @param self The object pointer.
    #  @param freqs The list of calculated frequencies.
    def calc_intensities(self, freqs):
        freq = freqs[0]
        self.freq_manager.insert(freq)
        wmin, wmax = self.freq_manager.get_mm()
        wsize = wmax - wmin
        if abs(wsize) < 0.000001:
            return None
        else:
            step = wsize / (NUM_ELEMS-1)
            return tuple(
                1-pow(e, -3*abs((freq-(step*i)-wmin) / wsize)) for i in range(NUM_ELEMS)
            )

    ## Set the NUM_ELEMS labels to the given intensities (HSV values).
    #  @warning Assumes exactly NUM_ELEMS intensities are given.
    #  @param self The object pointer.
    #  @param intensities The list of intensities to set the color for each respective label.
    def set_lbl_intensities(self, intensities):
        if intensities is not None:
            for i in range(NUM_ELEMS):
                lbl, color = self.lbl_color_pairs[i]
                GuiUtils.color_label(
                    lbl,
                    color.red(),
                    color.green(),
                    color.blue(),
                    intensity=intensities[i]
                )

    ## Set the color intensities given the frequencies of the sound currently playing.
    #  @param self The object pointer.
    #  @param msg The calculated playback frequencies.
    def playback_frequencies_updated(self, msg):
        self.set_lbl_intensities(self.calc_intensities(msg.data))
