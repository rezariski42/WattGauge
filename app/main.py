"""WattGauge entry point."""
from __future__ import annotations

import os
import sys
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from PyQt6.QtCore import QTimer, QUrl, Qt
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QFontMetricsF, QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

import config
from engine import PowerEngine


def resource(*parts):
    return os.path.join(APP_DIR, *parts)


def watt_pixmap(total: float, size: int) -> QPixmap:
    """One icon bitmap painted at exact pixel size (crisp digits in tray)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#0b1220"))
    r = max(2.0, size * 0.16)
    p.drawRoundedRect(QRectF(0.5, 0.5, size - 1, size - 1), r, r)
    txt = str(int(round(total))) if total > 0 else "-"
    fs = int(size * 0.78)
    while fs > 5:
        font = QFont("Segoe UI", 1, QFont.Weight.Black)
        font.setPixelSize(fs)
        if QFontMetricsF(font).horizontalAdvance(txt) <= size * 0.86:
            break
        fs -= 1
    p.setFont(font)
    p.setPen(QColor("#7dd3fc"))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, txt)
    p.end()
    return pm


def watt_icon(total: float) -> QIcon:
    """Multi-size tray icon so Windows picks a crisp bitmap at any DPI."""
    icon = QIcon()
    for size in (16, 20, 24, 32, 48, 64):
        icon.addPixmap(watt_pixmap(total, size))
    return icon


def _log(msg: str):
    try:
        with open(os.path.join(config.app_dir(), "wattgauge.log"), "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def main() -> int:
    QApplication.setApplicationName(config.APP_NAME)
    QApplication.setOrganizationName(config.APP_NAME)
    app = QApplication(sys.argv)

    icon_path = resource("assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    engine = PowerEngine()
    engine.ensureAutostart()
    qml = QQmlApplicationEngine()
    qml.warnings.connect(lambda errs: [_log("QML: " + e.toString()) for e in errs])
    qml.rootContext().setContextProperty("engine", engine)
    qml.setInitialProperties({"backend": engine})
    qml.load(QUrl.fromLocalFile(resource("qml", "Main.qml")))
    if not qml.rootObjects():
        _log("QML load failed")
        print("QML load failed", file=sys.stderr)
        return 2

    main_window = qml.rootObjects()[0]
    main_window.setProperty("backend", engine)
    try:
        main_window.setProperty("width", engine.windowWidth)
        main_window.setProperty("height", engine.windowHeight)
    except Exception:
        pass

    def toggle_main():
        try:
            if main_window.isVisible():
                main_window.hide()
            else:
                main_window.show()
                main_window.raise_()
                main_window.requestActivate()
        except Exception:
            pass

    tray = None
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon(), app)
        menu = QMenu()
        show_action = menu.addAction("WattGauge")
        show_action.triggered.connect(toggle_main)
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(app.quit)
        tray.setContextMenu(menu)
        tray.setToolTip("WattGauge")

        def sync_menu():
            try:
                key = "tray_hide" if main_window.isVisible() else "tray_show"
                show_action.setText(engine.label(key))
                quit_action.setText(engine.label("tray_quit"))
            except Exception:
                pass

        tray.activated.connect(
            lambda reason: toggle_main()
            if reason == QSystemTrayIcon.ActivationReason.Trigger else None
        )
        engine.configChanged.connect(sync_menu)
        sync_menu()
        tray.show()

        def refresh_tray():
            try:
                total = engine.totalWatt
                tray.setIcon(watt_icon(total))
                tray.setToolTip(engine.taskbarText)
                sync_menu()
            except Exception:
                pass

        engine.dataChanged.connect(refresh_tray)
        refresh_tray()

    selftest = None
    if "--selftest" in sys.argv:
        idx = sys.argv.index("--selftest")
        if len(sys.argv) > idx + 1:
            selftest = sys.argv[idx + 1]

    if selftest:
        def shoot():
            try:
                engine.tick()
                from PyQt6.QtQuick import QQuickWindow
                win = main_window
                if not isinstance(win, QQuickWindow):
                    from PyQt6 import sip
                    win = sip.cast(win, QQuickWindow)
                img = win.grabWindow()
                img.save(selftest)
                print("saved", selftest)
            except Exception as exc:  # pragma: no cover
                print("grab failed:", exc, file=sys.stderr)
            app.quit()
        QTimer.singleShot(2500, shoot)

    def persist_size():
        try:
            engine.saveWindowSize(int(main_window.width()), int(main_window.height()))
        except Exception:
            pass

    app.aboutToQuit.connect(persist_size)
    app.aboutToQuit.connect(engine.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())