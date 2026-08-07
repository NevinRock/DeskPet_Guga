from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from PySide6.QtCore import QPoint, QTimer, Qt, QVariantAnimation
from PySide6.QtGui import QAction, QCursor, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QLabel,
    QMenu,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .action_manager import ActionManager, PetState
from .animation_manager import AnimationManager
from .interaction import opaque_at
from .settings import SettingsStore


class ActionMenu(QFrame):
    def __init__(self, trigger) -> None:
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("actionMenu")
        self.setStyleSheet("#actionMenu { background: #ffffff; border: 1px solid #e8dfe9; border-radius: 14px; } QPushButton { border: 0; padding: 9px 16px; text-align: left; border-radius: 9px; font-size: 13px; } QPushButton:hover { background: #f6ecf7; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 7, 7, 7)
        self.care_label = QLabel()
        self.care_label.setStyleSheet("padding: 6px 10px 2px; color: #6f6370; font-size: 12px; font-weight: 600;")
        self.hunger_label = QLabel()
        self.hunger_label.setStyleSheet("padding: 0 10px 6px; color: #b04c63; font-size: 12px;")
        layout.addWidget(self.care_label)
        layout.addWidget(self.hunger_label)
        for label, action in [("👋  挥手", "wave"), ("🐧  摇一摇", "shake"), ("🚶  走两步", "walk"), ("💭  想一想", "think"), ("🕺  跳一跳", "jump"), ("🍴  吃东西  ›", "food_menu"), ("🎲  随机动作", "random")]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, value=action: trigger(value))
            layout.addWidget(button)

    def set_status(self, care_days: int, hungry: bool) -> None:
        self.care_label.setText(f"🐣  已陪伴 Guga {care_days} 天")
        self.hunger_label.setText("🍽️  Guga 饿了，喂点东西吧" if hungry else "🍽️  Guga 现在吃得饱饱的")


class FoodMenu(QFrame):
    def __init__(self, trigger) -> None:
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("foodMenu")
        self.setStyleSheet("#foodMenu { background: #ffffff; border: 1px solid #e8dfe9; border-radius: 14px; } QPushButton { border: 0; padding: 9px 16px; text-align: left; border-radius: 9px; font-size: 13px; } QPushButton:hover { background: #f6ecf7; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 7, 7, 7)
        for label, action in [("🥤  喝可乐", "drink_cola"), ("🍔  吃汉堡", "eat_burger"), ("🍰  吃蛋糕", "eat_cake"), ("☕  喝咖啡", "drink_coffee")]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, value=action: trigger(value))
            layout.addWidget(button)


class SettingsDialog(QDialog):
    def __init__(self, current_size: int, preview, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Guga 设置")
        self.setMinimumWidth(300)
        self.original_size = current_size
        self.preview = preview
        self.setStyleSheet("QDialog { background: white; } QLabel { font-size: 13px; } QSlider::groove:horizontal { height: 6px; background: #eadfea; border-radius: 3px; } QSlider::handle:horizontal { width: 18px; margin: -6px 0; background: #8d5b91; border-radius: 9px; }")
        layout = QVBoxLayout(self)
        title = QLabel("桌宠大小")
        self.value_label = QLabel()
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(120, 320)
        self.slider.setSingleStep(5)
        self.slider.setPageStep(20)
        self.slider.setValue(current_size)
        self.slider.valueChanged.connect(self._preview_size)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(title)
        layout.addWidget(self.value_label)
        layout.addWidget(self.slider)
        layout.addWidget(buttons)
        self._preview_size(current_size)

    def _preview_size(self, value: int) -> None:
        self.value_label.setText(f"{value} px（拖动滑块实时预览）")
        self.preview(value)

    def reject(self) -> None:
        self.preview(self.original_size)
        super().reject()


class AboutDialog(QDialog):
    def __init__(self, care_days: int, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Guga")
        self.setFixedWidth(330)
        self.setStyleSheet(
            "QDialog { background: white; }"
            "QLabel#title { font-size: 22px; font-weight: 700; color: #342b35; }"
            "QLabel#meta { font-size: 13px; color: #6f6370; }"
            "QPushButton { min-width: 80px; padding: 7px 16px; border: 0; "
            "border-radius: 9px; background: #8d5b91; color: white; }"
            "QPushButton:hover { background: #754779; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(9)

        title = QLabel("Guga Desktop Pet")
        title.setObjectName("title")
        creator = QLabel("Created by @Nevin, 2026.")
        creator.setObjectName("meta")
        license_label = QLabel("Licensed under the MIT License.")
        license_label.setObjectName("meta")
        care_label = QLabel(f"Together with you for {care_days} day{'s' if care_days != 1 else ''}.")
        care_label.setObjectName("meta")
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(creator)
        layout.addWidget(license_label)
        layout.addWidget(care_label)
        layout.addSpacing(8)
        layout.addWidget(buttons)


class PetWindow(QWidget):
    DRAG_THRESHOLD = 7
    TOUCH_COOLDOWN_MS = 1500
    HUNGER_INTERVAL = timedelta(minutes=30)
    FOOD_ACTIONS = frozenset({"drink_cola", "eat_burger", "eat_cake", "drink_coffee"})

    def __init__(self) -> None:
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.store = SettingsStore()
        self.settings = self.store.load()
        self._ensure_care_timestamps()
        self.size_px = self.settings.size
        self.setFixedSize(self.size_px, self.size_px)

        self.sprite = QLabel(self)
        self.sprite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sprite.setGeometry(self.rect())
        self.sprite.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.current_pixmap = QPixmap()
        self.animation = AnimationManager()
        self.actions = ActionManager(self.animation)
        self.animation.frame_changed.connect(self._set_frame)
        self.actions.start_idle()
        self.hunger_timer = QTimer(self)
        self.hunger_timer.setInterval(5000)
        self.hunger_timer.timeout.connect(self._update_hunger)
        self.hunger_timer.start()
        self._update_hunger()
        self.press_global: QPoint | None = None
        self.start_pos: QPoint | None = None
        self.dragging = False
        self.last_touch = 0
        self.menu: ActionMenu | None = None
        self.food_menu: FoodMenu | None = None
        self.jump_animation: QVariantAnimation | None = None

    def _set_frame(self, pixmap: QPixmap) -> None:
        self.current_pixmap = pixmap
        self.sprite.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def set_pet_size(self, value: int) -> None:
        bottom_right = self.geometry().bottomRight()
        self.size_px = value
        self.setFixedSize(value, value)
        self.sprite.setGeometry(self.rect())
        if not self.current_pixmap.isNull():
            self._set_frame(self.current_pixmap)
        self.move(bottom_right - QPoint(value - 1, value - 1))

    def show_at_default_position(self) -> None:
        if self.settings.x is not None and self.settings.y is not None:
            self.move(self.settings.x, self.settings.y)
        else:
            screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
            area = screen.availableGeometry()
            self.move(area.right() - self.width() - 20, area.bottom() - self.height() - 20)
        self.show()

    def _inside_pet(self, event: QMouseEvent) -> bool:
        pixmap = self.sprite.pixmap()
        if pixmap is None or pixmap.isNull():
            return False
        # QLabel centers the sprite; map the pointer into the actual scaled image.
        x = event.position().x() - (self.width() - pixmap.width()) / 2
        y = event.position().y() - (self.height() - pixmap.height()) / 2
        return opaque_at(pixmap, QPoint(int(x), int(y)))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.press_global is not None and self.start_pos is not None:
            delta = event.globalPosition().toPoint() - self.press_global
            if delta.manhattanLength() > self.DRAG_THRESHOLD:
                self.dragging = True
                self.actions.dragging(True)
                self.move(self.start_pos + delta)
            return
        if self._inside_pet(event) and self.actions.state is PetState.IDLE and self.last_touch <= 0:
            self.last_touch = self.TOUCH_COOLDOWN_MS
            self.actions.touch()
            QTimer.singleShot(self.TOUCH_COOLDOWN_MS, self._clear_touch_cooldown)

    def _clear_touch_cooldown(self) -> None:
        self.last_touch = 0

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self._inside_pet(event):
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_global = event.globalPosition().toPoint()
            self.start_pos = self.pos()
            self.dragging = False
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_system_menu(event.globalPosition().toPoint())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self.dragging:
            self.settings.x, self.settings.y = self.x(), self.y()
            self.store.save(self.settings)
            self.actions.dragging(False)
        elif self._inside_pet(event):
            self._show_action_menu()
        self.press_global = self.start_pos = None
        self.dragging = False

    def _show_action_menu(self) -> None:
        if self.menu is None:
            self.menu = ActionMenu(self._select_action)
        self.menu.set_status(self.care_days(), self.actions.hungry)
        self.menu.adjustSize()
        self.menu.move(self.pos() + QPoint(self.width() - self.menu.width(), -self.menu.height() - 8))
        self.menu.show()

    def _select_action(self, name: str) -> None:
        if self.menu:
            self.menu.hide()
        if name == "food_menu":
            self._show_food_menu()
            return
        choices = ["wave", "shake", "walk", "think", "jump", "drink_cola", "eat_burger", "eat_cake", "drink_coffee"]
        selected = random.choice(choices) if name == "random" else name
        self._play_action(selected)

    def _play_action(self, selected: str) -> None:
        if selected in self.FOOD_ACTIONS:
            self._mark_fed()
        if selected == "jump":
            self._animate_window_jump()
        self.actions.action(selected)

    def _show_food_menu(self) -> None:
        if self.food_menu is None:
            self.food_menu = FoodMenu(self._select_food_action)
        self.food_menu.adjustSize()
        self.food_menu.move(self.pos() + QPoint(self.width() - self.food_menu.width(), -self.food_menu.height() - 8))
        self.food_menu.show()

    def _select_food_action(self, name: str) -> None:
        if self.food_menu:
            self.food_menu.hide()
        self._play_action(name)

    def _ensure_care_timestamps(self) -> None:
        changed = False
        now = datetime.now(timezone.utc).isoformat()
        if self._parse_timestamp(self.settings.adopted_at) is None:
            self.settings.adopted_at = now
            changed = True
        if self._parse_timestamp(self.settings.last_fed_at) is None:
            self.settings.last_fed_at = now
            changed = True
        if changed:
            self.store.save(self.settings)

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    def care_days(self) -> int:
        adopted = self._parse_timestamp(self.settings.adopted_at) or datetime.now(timezone.utc)
        return max(1, (datetime.now().astimezone().date() - adopted.astimezone().date()).days + 1)

    def _update_hunger(self) -> None:
        last_fed = self._parse_timestamp(self.settings.last_fed_at) or datetime.now(timezone.utc)
        hungry = datetime.now(timezone.utc) - last_fed >= self.HUNGER_INTERVAL
        if hungry != self.actions.hungry:
            self.actions.set_hungry(hungry)

    def _mark_fed(self) -> None:
        self.settings.last_fed_at = datetime.now(timezone.utc).isoformat()
        self.store.save(self.settings)
        self.actions.set_hungry(False, play=False)

    def _animate_window_jump(self) -> None:
        if self.jump_animation is not None:
            self.jump_animation.stop()
        origin = self.pos()
        animation = QVariantAnimation(self)
        animation.setDuration(1000)
        animation.setStartValue(0)
        animation.setKeyValueAt(0.16, 5)
        animation.setKeyValueAt(0.42, -58)
        animation.setKeyValueAt(0.62, -42)
        animation.setKeyValueAt(0.82, -12)
        animation.setEndValue(0)
        animation.valueChanged.connect(lambda offset: self.move(origin + QPoint(0, int(offset))))
        animation.finished.connect(lambda: self.move(origin))
        self.jump_animation = animation
        animation.start()

    def _show_system_menu(self, position: QPoint) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background: white; border: 1px solid #e8dfe9; border-radius: 10px; padding: 6px; } QMenu::item { padding: 8px 25px; border-radius: 7px; } QMenu::item:selected { background: #f6ecf7; }")
        reset = QAction("重置位置", menu)
        reset.triggered.connect(self._reset_position)
        settings_action = QAction("设置", menu)
        settings_action.triggered.connect(self._show_settings)
        about = QAction("关于 Guga", menu)
        about.triggered.connect(self._show_about)
        quit_action = QAction("退出桌宠", menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(settings_action)
        menu.addAction(reset)
        care = menu.addAction(f"已陪伴 Guga {self.care_days()} 天" + (" · 饿了" if self.actions.hungry else ""))
        care.setEnabled(False)
        menu.addSeparator()
        menu.addAction(about)
        menu.addAction(quit_action)
        menu.exec(position)

    def _show_settings(self) -> None:
        dialog = SettingsDialog(self.size_px, self.set_pet_size, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings.size = self.size_px
            self.settings.x, self.settings.y = self.x(), self.y()
            self.store.save(self.settings)

    def _show_about(self) -> None:
        AboutDialog(self.care_days(), self).exec()

    def _reset_position(self) -> None:
        self.settings.x = None
        self.settings.y = None
        self.store.save(self.settings)
        self.show_at_default_position()
