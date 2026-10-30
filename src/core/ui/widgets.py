from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtCore import Qt


class CustomQMenu(QMenu):
    def __init__(self, title: str, object_name: str, parent=None):
        super().__init__(title, parent)
        self.setObjectName(object_name)
        self.setToolTipsVisible(True)
    
    def mouseReleaseEvent(self, a0):
        if a0 is None:
            return
        
        if a0.button() == Qt.MouseButton.RightButton:
            if hasattr(a0, 'globalPosition'):
                global_pos = a0.globalPosition().toPoint()
            else:
                global_pos = a0.globalPos() # type: ignore
            self._init_context_menu(a0.pos(), global_pos)
            return

        super().mouseReleaseEvent(a0)
    
    def build(self):
        ... # To be implemented in subclasses
    
    def _init_context_menu(self, pos, global_pos=None) -> None:
        action = self.actionAt(pos) or self.menuAction()
        if not action:
            return
        
        if global_pos is None:
            global_pos = self.mapToGlobal(pos)
        
        self._show_context_menu(action, global_pos)
        
    def _show_context_menu(self, action: QAction, global_pos) -> None:
        ... # To be implemented in subclasses