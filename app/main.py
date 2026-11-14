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
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

import config
from engine import PowerEngine


def resource(*parts):
    return os.path.join(APP_DIR, *parts)


def watt_icon(total: float) -> QPixmap:
    """Tray/live icon painted with the current watt number."""
    size = 64
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor("#38bdf8"), 4))
    p.setBrush(QColor("#0b1220"))
    p.drawRoundedRect(QRectF(3, 3, 58, 58), 14, 14)
    txt = str(int(round(total)))
    fs = 30 if len(txt) <= 2 else (23 if len(txt) == 3 else 17)
    p.setFont(QFont("Segoe UI", fs, QFont.Weight.Bold))
    p.setPen(QColor("#7dd3fc"))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, txt)
    p.end()
    return pm


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

    topbar_holder = {"window": None}

    def apply_topbar():
        enabled = bool(engine.cfg.get("topbar", "enabled", default=True))
        if enabled and topbar_holder["window"] is None:
            tb = QQmlApplicationEngine(qml)
            tb.load(QUrl.fromLocalFile(resource("qml", "TopBar.qml")))
            if tb.rootObjects():
                win = tb.rootObjects()[0]
                win.engineRef = engine
                win.activated.connect(main_window.show)
                topbar_holder["window"] = win
                topbar_holder["engine"] = tb
        elif not enabled and topbar_holder["window"] is not None:
            topbar_holder["window"].close()
            topbar_holder["window"] = None

    apply_topbar()
    engine.configChanged.connect(apply_topbar)

    tray = None
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon(), app)
        menu = QMenu()
        show_action = menu.addAction("Buka WattGauge")
        show_action.triggered.connect(main_window.show)
        quit_action = menu.addAction("Keluar")
        quit_action.triggered.connect(app.quit)
        tray.setContextMenu(menu)
        tray.setToolTip("WattGauge")
        tray.show()

        def refresh_tray():
            try:
                total = engine.totalWatt
                tray.setIcon(QIcon(watt_icon(total)))
                tray.setToolTip(engine.taskbarText)
                main_window.setTitle(engine.taskbarText)
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