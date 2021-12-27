from PyQt5.QtWidgets import QWidget

from scripts.Ui_LabeledSliderSubpage import Ui_LabeledSliderSubpage

## A simple pair of widgets to label the value of a slider.
class LabeledSliderSubpage(QWidget):

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        super(LabeledSliderSubpage, self).__init__(parent)

        # Build UI object
        self.ui = Ui_LabeledSliderSubpage()
        self.ui.setupUi(self)

        # Done
        self.show()

    ## Set the slider's min, max, and current values.
    #  @param self The object pointer.
    #  @param minimum The new minimum value.
    #  @param maximum The new maximum value.
    #  @param current The new current value.
    def set_slider_state(self, minimum, maximum, value):
        self.ui.slider.setMinimum(minimum)
        self.ui.slider.setMaximum(maximum)
        self.ui.slider.setValue(value)

    ## Set the slider's label with the given text.
    #  @param self The object pointer.
    #  @param text The new text for the label.
    def set_slider_label(self, text):
        self.ui.lbl.setText(text)
