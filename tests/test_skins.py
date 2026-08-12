from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from pet.animation_manager import AnimationManager
from pet.i18n import tr


class SkinAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_every_skin_contains_every_configured_frame(self) -> None:
        root = Path(__file__).resolve().parents[1]
        actions = json.loads((root / "config" / "actions.json").read_text(encoding="utf-8"))
        skins = json.loads((root / "config" / "skins.json").read_text(encoding="utf-8"))
        guga_prefix = Path("assets/actions")

        for skin_id, skin in skins.items():
            prefix = Path(skin["assetPrefix"])
            for action_name, action in actions.items():
                for frame in action["frames"]:
                    relative = Path(frame).relative_to(guga_prefix)
                    path = root / prefix / relative
                    self.assertTrue(path.is_file(), f"{skin_id}/{action_name}: missing {path}")

    def test_skin_names_are_localized(self) -> None:
        self.assertEqual(tr("zh_CN", "skin_guga"), "咕嘎")
        self.assertEqual(tr("zh_CN", "skin_phoebe"), "菲比（飞鱼服）")
        self.assertEqual(tr("zh_CN", "skin_author"), "作者")
        self.assertEqual(tr("zh_CN", "skin_guga_eunuch"), "咕嘎（太监）")
        self.assertEqual(tr("en", "skin_guga"), "Guga")
        self.assertEqual(tr("en", "skin_phoebe"), "Phoebe")
        self.assertEqual(tr("en", "skin_author"), "Creator")
        self.assertEqual(tr("en", "skin_guga_eunuch"), "Guga (Eunuch)")
        self.assertEqual(tr("ja", "skin_guga"), "グーガ")
        self.assertEqual(tr("ja", "skin_phoebe"), "フィービー")
        self.assertEqual(tr("ja", "skin_author"), "作者")
        self.assertEqual(tr("ja", "skin_guga_eunuch"), "グーガ（宦官）")

    def test_every_skin_loads_every_animation(self) -> None:
        root = Path(__file__).resolve().parents[1]
        actions = json.loads((root / "config" / "actions.json").read_text(encoding="utf-8"))
        skins = json.loads((root / "config" / "skins.json").read_text(encoding="utf-8"))

        for skin_id in skins:
            manager = AnimationManager(skin_id)
            self.assertEqual(manager.skin, skin_id)
            self.assertEqual(set(manager.animations), set(actions))
            self.assertTrue(
                all(not frame.isNull() for item in manager.animations.values() for frame in item.frames),
                skin_id,
            )

    def test_special_action_is_five_seconds_and_localized(self) -> None:
        root = Path(__file__).resolve().parents[1]
        actions = json.loads((root / "config" / "actions.json").read_text(encoding="utf-8"))
        special = actions["special"]
        self.assertEqual(len(special["frames"]), 15)
        self.assertEqual(special["fps"], 3)
        self.assertEqual(len(special["frames"]) / special["fps"], 5)
        self.assertEqual(tr("zh_CN", "action_special"), "✨  特殊动作")
        self.assertEqual(tr("en", "action_special"), "✨  Special action")
        self.assertEqual(tr("ja", "action_special"), "✨  特別アクション")

    def test_advanced_hunger_actions_are_looping_eight_frame_animations(self) -> None:
        root = Path(__file__).resolve().parents[1]
        actions = json.loads((root / "config" / "actions.json").read_text(encoding="utf-8"))
        self.assertEqual(len(actions["starving"]["frames"]), 8)
        self.assertEqual(actions["starving"]["fps"], 3)
        self.assertTrue(actions["starving"]["loop"])
        self.assertEqual(len(actions["tombstone"]["frames"]), 8)
        self.assertEqual(actions["tombstone"]["fps"], 4)
        self.assertTrue(actions["tombstone"]["loop"])

    def test_every_special_action_has_safe_edges_and_one_baseline(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skins = json.loads((root / "config" / "skins.json").read_text(encoding="utf-8"))
        for skin_id, skin in skins.items():
            action_dir = root / skin["assetPrefix"] / "special"
            frames = sorted(action_dir.glob("*.png"))
            self.assertEqual(len(frames), 15, skin_id)
            bottoms: list[int] = []
            for path in frames:
                frame = QImage(str(path))
                self.assertEqual((frame.width(), frame.height()), (192, 208), str(path))
                edge_pixels = (
                    [(x, y) for x in range(5) for y in range(208)]
                    + [(x, y) for x in range(187, 192) for y in range(208)]
                    + [(x, y) for x in range(192) for y in range(5)]
                    + [(x, y) for x in range(192) for y in range(203, 208)]
                )
                self.assertTrue(
                    all(frame.pixelColor(x, y).alpha() == 0 for x, y in edge_pixels),
                    str(path),
                )
                visible_rows = [
                    y
                    for y in range(208)
                    if any(frame.pixelColor(x, y).alpha() > 24 for x in range(192))
                ]
                self.assertTrue(visible_rows, str(path))
                bottoms.append(visible_rows[-1] + 1)
            self.assertEqual(min(bottoms), max(bottoms), skin_id)

    def test_eunuch_bow_has_no_abrupt_vertical_snap(self) -> None:
        root = Path(__file__).resolve().parents[1]
        action_dir = root / "assets" / "skins" / "guga-eunuch" / "actions" / "special"
        tops: list[int] = []
        for path in sorted(action_dir.glob("*.png")):
            frame = QImage(str(path))
            visible_rows = [
                y
                for y in range(208)
                if any(frame.pixelColor(x, y).alpha() > 24 for x in range(192))
            ]
            tops.append(visible_rows[0])
        largest_step = max(abs(current - previous) for previous, current in zip(tops, tops[1:]))
        self.assertLessEqual(largest_step, 25)

    def test_phoebe_special_action_keeps_one_body_scale(self) -> None:
        root = Path(__file__).resolve().parents[1]
        action_dir = root / "assets" / "skins" / "phoebe" / "actions" / "special"
        skirt_widths: list[int] = []
        for path in sorted(action_dir.glob("*.png")):
            frame = QImage(str(path))
            visible = [x for x in range(192) if frame.pixelColor(x, 180).alpha() > 24]
            self.assertTrue(visible, str(path))
            skirt_widths.append(visible[-1] - visible[0] + 1)
        self.assertLessEqual(
            max(skirt_widths) / min(skirt_widths),
            1.10,
            skirt_widths,
        )

    def test_generated_skin_frames_have_clear_edges_and_a_stable_baseline(self) -> None:
        root = Path(__file__).resolve().parents[1]
        actions = json.loads((root / "config" / "actions.json").read_text(encoding="utf-8"))
        skins = json.loads((root / "config" / "skins.json").read_text(encoding="utf-8"))
        guga_prefix = Path("assets/actions")

        for skin_id, skin in skins.items():
            if skin_id == "guga":
                continue
            prefix = root / Path(skin["assetPrefix"])
            for action_name, action in actions.items():
                bottoms: list[int] = []
                for relative in dict.fromkeys(action["frames"]):
                    path = prefix / Path(relative).relative_to(guga_prefix)
                    frame = QImage(str(path))
                    self.assertFalse(frame.isNull(), str(path))
                    self.assertEqual((frame.width(), frame.height()), (192, 208), str(path))
                    edge_pixels = (
                        [(x, y) for x in range(5) for y in range(208)]
                        + [(x, y) for x in range(187, 192) for y in range(208)]
                        + [(x, y) for x in range(192) for y in range(5)]
                        + [(x, y) for x in range(192) for y in range(203, 208)]
                    )
                    self.assertTrue(
                        all(frame.pixelColor(x, y).alpha() == 0 for x, y in edge_pixels), str(path)
                    )
                    visible_rows = [
                        y
                        for y in range(208)
                        if any(frame.pixelColor(x, y).alpha() > 24 for x in range(192))
                    ]
                    self.assertTrue(visible_rows, str(path))
                    bottoms.append(visible_rows[-1] + 1)

                if action_name != "jump":
                    self.assertLessEqual(
                        max(bottoms) - min(bottoms), 1, f"{skin_id}/{action_name}"
                    )


if __name__ == "__main__":
    unittest.main()
