from PyQt5.QtCore import pyqtProperty, pyqtSignal
from PyQt5.QtWidgets import QStackedWidget

## A simple stacked widget with a user-friendly name.
class StackedPageGroup(QStackedWidget):

    #
    # Qt Signals
    #

    ## Emits a signal for the updated group name.
    group_name_updated = pyqtSignal(str)

    ## The constructor.
    #  @param self The object pointer.
    #  @param parent This object's optional Qt parent.
    def __init__(self, parent=None):
        # Call base constructor and set local variable
        super(StackedPageGroup, self).__init__(parent)
        self._group_name = None

    ## The group's user-friendly name, a string property.
    #  @param self The object pointer.
    @pyqtProperty(str)
    def groupName(self):
        return self._group_name

    ## The setter for the 'groupName' property.
    #  @param self The object pointer.
    #  @param new_group_name The new value for the group's name.
    def setGroupName(self, new_group_name):
        self._group_name = new_group_name
        self.group_name_updated.emit(self._group_name)
