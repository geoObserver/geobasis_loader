from PyQt5.QtWidgets import QMenu, QWidget, QToolTip, QAction
from PyQt5.QtCore import pyqtSignal, QEvent, QObject, QTimer
from PyQt5.QtGui import QMouseEvent, QCursor
        
class ComplexMenu(QMenu):
    triggered = pyqtSignal()
    menu_data = ""
    
    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(title, parent)
        filter = MenuTooltipFilter(self)
        self.installEventFilter(filter)
    
    # Method doesnt exist on QMenus -> save data of menuAction on click and then retrieve it with this function
    # The same as QAction -> No special cases
    def data(self):
        return self.menu_data
    
    def add_clickable_menu(self, menu: QMenu) -> None:
        self.addMenu(menu)
    
    def onMenuClicked(self, menu: QMenu):
        menu_action = menu.menuAction()
        if not menu_action:
            return
        
        self.menu_data = menu_action.data()
        self.triggered.emit()
    
    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        super().mousePressEvent(a0)
        if not a0:
            return
        
        action = self.actionAt(a0.pos())
        if not action:
            return
        menu = action.menu()
        if menu:
            self.onMenuClicked(menu)
         
class MenuTooltipFilter(QObject):    
    def __init__(self, parent: QMenu):
        super().__init__(parent)
        self._menu = parent
        self._menu.setMouseTracking(True)
        self._hovered_action = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._show_tooltip)        
        
        self.string_name = {}
        for name in vars(QEvent):
            attribute = getattr(QEvent, name)
            if type(attribute) == QEvent.Type:
                self.string_name[attribute] = name
    
    def eventFilter(self, a0, a1):
        if not isinstance(a1, QEvent):
            return super().eventFilter(a0, a1)
        
        # print(self.string_name[a1.type()])
        if a1.type() == QEvent.Type.ToolTip:
            # default tooltip event — let Qt handle it
            return False
        elif a1.type() == QEvent.Type.MouseMove:
            if not isinstance(a1, QMouseEvent):
                return super().eventFilter(a0, a1)
            
            action = self._menu.actionAt(a1.pos())
            if not action:
                action = self._menu.menuAction()
            if action is not self._hovered_action:
                self._hovered_action = action
                self._timer.stop()
                QToolTip.hideText() # Hide any previous tooltip immediately

                # If the new action is valid and has a tooltip, start the timer
                if self._hovered_action and self._hovered_action.toolTip():
                    self._timer.start()
            
        elif a1.type() == QEvent.Type.Hide:
            QToolTip.hideText()
            self._timer.stop()
            self._hovered_action = None
            
        return super().eventFilter(a0, a1)
    
    def _show_tooltip(self):
        """
        This slot is called by the timer after the hover delay.
        It shows the tooltip at the current cursor position.
        """
        if self._hovered_action and self._hovered_action.toolTip():
            # Get the current global mouse position using QCursor.pos()
            global_pos = QCursor.pos()
            QToolTip.showText(global_pos, self._hovered_action.toolTip())