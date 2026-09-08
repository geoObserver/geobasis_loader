from qgis.PyQt import QtWidgets, QtCore, QtGui
from ... import config

class SearchHighlightItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tokens: tuple[str, ...] = ()
    
    def paint(self, painter, option, index):
        if not self._tokens or painter is None:
            super().paint(painter, option, index)
            return
        
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
        
        icon_mode = QtGui.QIcon.Mode.Normal
        if not (option.state & QtWidgets.QStyle.StateFlag.State_Enabled):
            icon_mode = QtGui.QIcon.Mode.Disabled
        elif option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            icon_mode = QtGui.QIcon.Mode.Selected
        
        if style:
            standard_margin = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_FocusFrameHMargin, option, option.widget)
        else:
            standard_margin = 5
        
        if style:
            text_backup = option.text
            option.text = ""
            style.drawControl(
                QtWidgets.QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget
            )
            option.text = text_backup
        
        state = QtGui.QIcon.State.On if option.state & QtWidgets.QStyle.StateFlag.State_Open else QtGui.QIcon.State.Off
        
        if style:
            icon_rect = style.subElementRect(QtWidgets.QStyle.SubElement.SE_ItemViewItemDecoration, option, option.widget)
        else:
            actual_size = option.icon.actualSize(option.decorationSize, icon_mode, state)
            option.decorationSize = QtCore.QSize(min(option.decorationSize.width(), actual_size.width()), min(option.decorationSize.height(), actual_size.height()))
            icon_rect = QtCore.QRect(QtCore.QPoint(), option.decorationSize)
            icon_rect.moveCenter(option.rect.center())
            icon_rect.setLeft(option.rect.left() + standard_margin)
        
        if not option.icon.isNull():
            option.icon.paint(painter, icon_rect, QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter, icon_mode, state)
        
        if not option.text:
            return
        
        if style:
            # Ask Qt to calculate the exact bounding box for the text of this specific item
            text_rect = style.subElementRect(QtWidgets.QStyle.SubElement.SE_ItemViewItemText, option, option.widget)
        else:
            text_rect = option.rect.adjusted(option.decorationSize.width() + standard_margin, 0, 0, 0)  # Adjust the text rect to account for the icon width
        
        data = index.data(QtCore.Qt.ItemDataRole.UserRole)
        if data is None:  # For the separation item when sorting
            painter.save()
            custom_color: QtGui.QBrush = index.data(QtCore.Qt.ItemDataRole.ForegroundRole)
            if custom_color:
                painter.setPen(custom_color.color())
            else:
                painter.setPen(QtGui.QColor(config.GRAYED_OUT_COLOR))
            painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter, option.text)
            painter.restore()
            return
        
        ranges = self.get_ranges(option.text, self._tokens)
        
        # 1. Prepare fonts
        default_font = option.font
        highlight_font = QtGui.QFont(default_font)
        highlight_font.setBold(True)
        
        # 2. Create the layout with the full, unbroken text
        layout = QtGui.QTextLayout(option.text, default_font)
        
        # 3. Create formatting objects for your different styles
        default_format = QtGui.QTextCharFormat()
        default_format.setFont(default_font)
        
        custom_color = index.data(QtCore.Qt.ItemDataRole.ForegroundRole)
        if custom_color is not None and isinstance(custom_color, QtGui.QColor):
            default_format.setForeground(custom_color)
        else:
            default_format.setForeground(option.palette.color(QtGui.QPalette.ColorRole.Text))
        
        highlight_format = QtGui.QTextCharFormat()
        highlight_format.setFont(highlight_font)
        highlight_format.setForeground(QtGui.QColor(config.SEARCH_HIGHLIGHT_COLOR))
        
        # 4. Build a list of format ranges
        # QTextLayout.FormatRange tells the layout "Apply THIS format from index A to length B"
        format_ranges = []
        
        # Apply default format to the whole string first
        base_range = QtGui.QTextLayout.FormatRange()
        base_range.start = 0
        base_range.length = len(option.text)
        base_range.format = default_format
        format_ranges.append(base_range)
        
        # Add the highlight formats on top
        for start, end in ranges:
            highlight_range = QtGui.QTextLayout.FormatRange()
            highlight_range.start = start
            highlight_range.length = end - start
            highlight_range.format = highlight_format
            format_ranges.append(highlight_range)
        
        # Apply the formats to the layout
        layout.setFormats(format_ranges)
        
        # 5. Tell the layout to calculate its geometry (word wrapping, kerning, etc.)
        layout.beginLayout()
        line = layout.createLine()
        line.setLineWidth(text_rect.width())
        layout.endLayout()
        
        # 6. Draw the layout to the screen
        # We need to calculate the Y offset to keep it vertically centered
        y_offset = text_rect.top() + ((text_rect.height() - layout.boundingRect().height()) / 2)
        draw_position = QtCore.QPointF(text_rect.left(), y_offset)
        
        layout.draw(painter, draw_position)

    def sizeHint(self, option, index) -> QtCore.QSize:
        super_size_hint = super().sizeHint(option, index)
        if not self._tokens:
            return super_size_hint
        
        data = index.data(QtCore.Qt.ItemDataRole.UserRole)
        if data is None:                                        # For the separation item when sorting
            super_size_hint.setHeight(30)                       # Return a fixed height for the separation item
            return super_size_hint
        
        return super_size_hint                                  # Return the default size hint for the item

    def set_search_tokens(self, tokens: tuple[str, ...]) -> None:
        self._tokens = tokens
        self._searching = bool(tokens)
    
    def clear_search_text(self) -> None:
        self.set_search_tokens(())

    def get_ranges(self, text: str, tokens: tuple[str, ...]) -> list[tuple[int, int]]:
        """Returns a list of (start, end) tuples for each occurrence of the tokens in the text."""
        ranges = []
        lower_text = text.lower()
        for token in tokens:
            start = 0
            while True:
                start = lower_text.find(token, start)
                if start == -1:
                    break
                end = start + len(token)
                ranges.append((start, end))
                start = end  # Move past this match
        return ranges
