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
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .action_manager import ActionManager, PetState
from .animation_manager import AnimationManager
from .git_push import GitPushDialog, GitPushRunner
from .i18n import LANGUAGES, tr
from .interaction import opaque_at
from .schedule import ScheduleDialog
from .settings import SettingsStore

APP_VERSION = "1.4.0"


class ActionMenu(QFrame):
    def __init__(self, trigger, language: str) -> None:
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
        self.language = language
        for key, action in [("action_wave", "wave"), ("action_shake", "shake"), ("action_walk", "walk"), ("action_think", "think"), ("action_jump", "jump"), ("action_food", "food_menu"), ("action_random", "random")]:
            button = QPushButton(tr(language, key))
            button.clicked.connect(lambda checked=False, value=action: trigger(value))
            layout.addWidget(button)

    def set_status(self, care_days: int, hungry: bool) -> None:
        self.care_label.setText(tr(self.language, "care_days", days=care_days))
        self.hunger_label.setText(tr(self.language, "hungry" if hungry else "full"))


class FoodMenu(QFrame):
    def __init__(self, trigger, language: str) -> None:
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("foodMenu")
        self.setStyleSheet("#foodMenu { background: #ffffff; border: 1px solid #e8dfe9; border-radius: 14px; } QPushButton { border: 0; padding: 9px 16px; text-align: left; border-radius: 9px; font-size: 13px; } QPushButton:hover { background: #f6ecf7; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 7, 7, 7)
        for key, action in [("food_cola", "drink_cola"), ("food_burger", "eat_burger"), ("food_cake", "eat_cake"), ("food_coffee", "drink_coffee")]:
            button = QPushButton(tr(language, key))
            button.clicked.connect(lambda checked=False, value=action: trigger(value))
            layout.addWidget(button)


class SettingsDialog(QDialog):
    def __init__(self, current_size: int, preview, language: str, parent: QWidget) -> None:
        super().__init__(parent)
        self.language = language
        self.setWindowTitle(tr(language, "pet_settings"))
        self.setMinimumWidth(300)
        self.original_size = current_size
        self.preview = preview
        self.setStyleSheet("QDialog { background: white; } QLabel { font-size: 13px; } QSlider::groove:horizontal { height: 6px; background: #eadfea; border-radius: 3px; } QSlider::handle:horizontal { width: 18px; margin: -6px 0; background: #8d5b91; border-radius: 9px; }")
        layout = QVBoxLayout(self)
        title = QLabel(tr(language, "pet_size"))
        self.value_label = QLabel()
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(120, 320)
        self.slider.setSingleStep(5)
        self.slider.setPageStep(20)
        self.slider.setValue(current_size)
        self.slider.valueChanged.connect(self._preview_size)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr(language, "ok"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr(language, "cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(title)
        layout.addWidget(self.value_label)
        layout.addWidget(self.slider)
        layout.addWidget(buttons)
        self._preview_size(current_size)

    def _preview_size(self, value: int) -> None:
        self.value_label.setText(tr(self.language, "size_preview", size=value))
        self.preview(value)

    def reject(self) -> None:
        self.preview(self.original_size)
        super().reject()


class AboutDialog(QDialog):
    def __init__(self, care_days: int, language: str, parent: QWidget) -> None:
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
        version = QLabel(f"Version {APP_VERSION}")
        version.setObjectName("meta")
        creator = QLabel(tr(language, "created_by"))
        creator.setObjectName("meta")
        license_label = QLabel(tr(language, "mit_license"))
        license_label.setObjectName("meta")
        care_label = QLabel(tr(language, "together_days", days=care_days))
        care_label.setObjectName("meta")
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr(language, "ok"))
        buttons.accepted.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(version)
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
        if self.settings.language not in LANGUAGES:
            self.settings.language = "zh_CN"
            self.store.save(self.settings)
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
        self.git_push_runner = GitPushRunner(self)
        self.git_push_runner.finished.connect(self._git_push_finished)
        self.git_push_timer = QTimer(self)
        self.git_push_timer.setInterval(30000)
        self.git_push_timer.timeout.connect(self._check_auto_git_push)
        self.git_push_timer.start()
        self.git_push_was_manual = False
        QTimer.singleShot(3000, self._check_auto_git_push)
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
            self.menu = ActionMenu(self._select_action, self.settings.language)
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
            self.food_menu = FoodMenu(self._select_food_action, self.settings.language)
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
        self._build_system_menu().exec(position)

    def _build_system_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background: white; border: 1px solid #e8dfe9; border-radius: 10px; padding: 6px; } QMenu::item { padding: 8px 25px; border-radius: 7px; } QMenu::item:selected { background: #f6ecf7; }")
        reset = QAction(tr(self.settings.language, "menu_reset"), menu)
        reset.triggered.connect(self._reset_position)
        language = self.settings.language
        settings_menu = QMenu(tr(language, "menu_settings"), menu)
        menu.addMenu(settings_menu)
        settings_action = QAction(tr(language, "menu_appearance"), settings_menu)
        settings_action.triggered.connect(self._show_settings)
        about = QAction(tr(language, "menu_version"), settings_menu)
        about.triggered.connect(self._show_about)
        git_push = QAction(tr(language, "menu_git_push"), settings_menu)
        git_push.triggered.connect(self._show_git_push_settings)
        schedule = QAction(tr(language, "menu_schedule"), settings_menu)
        schedule.triggered.connect(self._show_schedule)
        language_menu = QMenu("Language", settings_menu)
        for code, label in LANGUAGES.items():
            language_action = QAction(label, language_menu)
            language_action.setCheckable(True)
            language_action.setChecked(code == language)
            language_action.triggered.connect(lambda checked=False, value=code: self._set_language(value))
            language_menu.addAction(language_action)
        quit_action = QAction(tr(language, "menu_quit"), menu)
        quit_action.triggered.connect(QApplication.quit)
        settings_menu.addAction(settings_action)
        settings_menu.addAction(about)
        settings_menu.addSeparator()
        settings_menu.addAction(schedule)
        settings_menu.addAction(git_push)
        settings_menu.addSeparator()
        settings_menu.addMenu(language_menu)
        menu.addAction(reset)
        care = menu.addAction(tr(language, "menu_care", days=self.care_days(), hungry=tr(language, "menu_hungry_suffix") if self.actions.hungry else ""))
        care.setEnabled(False)
        menu.addSeparator()
        menu.addAction(quit_action)
        return menu

    def _show_settings(self) -> None:
        dialog = SettingsDialog(self.size_px, self.set_pet_size, self.settings.language, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings.size = self.size_px
            self.settings.x, self.settings.y = self.x(), self.y()
            self.store.save(self.settings)

    def _show_about(self) -> None:
        AboutDialog(self.care_days(), self.settings.language, self).exec()

    def _show_git_push_settings(self) -> None:
        dialog = GitPushDialog(self.settings, self, self.settings.language)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        old_schedule = (
            self.settings.git_auto_push_enabled,
            self.settings.git_repo_path,
            self.settings.git_remote_url,
            self.settings.git_push_time,
            self.settings.git_commit_message,
        )
        self.settings.git_auto_push_enabled = dialog.enabled.isChecked()
        self.settings.git_repo_path = dialog.repo_path.text().strip()
        self.settings.git_remote_url = dialog.remote_url.text().strip()
        self.settings.git_push_time = dialog.push_time.time().toString("HH:mm")
        self.settings.git_commit_message = dialog.commit_message.text().strip()
        new_schedule = (
            self.settings.git_auto_push_enabled,
            self.settings.git_repo_path,
            self.settings.git_remote_url,
            self.settings.git_push_time,
            self.settings.git_commit_message,
        )
        if new_schedule != old_schedule:
            self.settings.git_last_attempt_date = None
        self.store.save(self.settings)
        if dialog.run_immediately:
            self._start_git_push(manual=True)

    def _show_schedule(self) -> None:
        dialog = ScheduleDialog(self.settings, self, self.settings.language)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings.calendar_server_url = dialog.server_url.text().strip().rstrip("/")
            self.settings.calendar_person_id = dialog.person_id.text().strip()
            self.store.save(self.settings)

    def _check_auto_git_push(self) -> None:
        if not self.settings.git_auto_push_enabled or self.git_push_runner.running:
            return
        now = datetime.now().astimezone()
        if self.settings.git_last_attempt_date == now.date().isoformat():
            return
        if now.strftime("%H:%M") >= self.settings.git_push_time:
            self._start_git_push(manual=False)

    def _start_git_push(self, manual: bool) -> None:
        if self.git_push_runner.running:
            if manual:
                QMessageBox.information(self, tr(self.settings.language, "git_title"), tr(self.settings.language, "git_busy"))
            return
        self.git_push_was_manual = manual
        self.settings.git_last_attempt_date = datetime.now().astimezone().date().isoformat()
        self.settings.git_last_push_status = tr(self.settings.language, "git_running")
        self.store.save(self.settings)
        self.git_push_runner.start(
            self.settings.git_repo_path,
            self.settings.git_remote_url,
            self.settings.git_commit_message,
            self.settings.language,
        )

    def _git_push_finished(self, success: bool, message: str) -> None:
        now = datetime.now().astimezone()
        self.settings.git_last_push_at = now.isoformat(timespec="seconds")
        self.settings.git_last_push_status = tr(self.settings.language, "status_success" if success else "status_failure") + message
        self.store.save(self.settings)
        if self.git_push_was_manual:
            if success:
                QMessageBox.information(self, tr(self.settings.language, "git_done_title"), message)
            else:
                QMessageBox.warning(self, tr(self.settings.language, "git_failed_title"), message)
        self.git_push_was_manual = False

    def _set_language(self, language: str) -> None:
        if language not in LANGUAGES or language == self.settings.language:
            return
        self.settings.language = language
        self.store.save(self.settings)
        if self.menu is not None:
            self.menu.close()
            self.menu.deleteLater()
            self.menu = None
        if self.food_menu is not None:
            self.food_menu.close()
            self.food_menu.deleteLater()
            self.food_menu = None

    def _reset_position(self) -> None:
        self.settings.x = None
        self.settings.y = None
        self.store.save(self.settings)
        self.show_at_default_position()
