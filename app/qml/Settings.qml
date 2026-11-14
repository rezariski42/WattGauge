import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: dlg
    width: 400
    height: 600
    minimumWidth: 340
    minimumHeight: 420
    flags: Qt.Dialog | Qt.FramelessWindowHint
    color: "transparent"
    modality: Qt.ApplicationModal

    property var engineRef: null

    property color bg: "#0a0f1a"
    property color card: "#111a2b"
    property color fieldBg: "#0d1524"
    property color text: "#f1f5f9"
    property color muted: "#7b8aa3"
    property color line: "#1e2b45"
    property color accent: "#38bdf8"
    property string uiFont: "Segoe UI"

    function num(txt, fallback) {
        var v = parseFloat(String(txt).replace(/\./g, "").replace(",", "."))
        return isNaN(v) ? fallback : v
    }

    component DarkField: TextField {
        id: fld
        implicitWidth: 96
        implicitHeight: 28
        color: dlg.text
        font.pixelSize: 10
        font.family: dlg.uiFont
        horizontalAlignment: TextInput.AlignRight
        leftPadding: 8
        rightPadding: 8
        topPadding: 4
        bottomPadding: 4
        selectByMouse: true
        background: Rectangle {
            color: dlg.fieldBg
            radius: 6
            border.width: 1
            border.color: fld.activeFocus ? dlg.accent : "#26354f"
        }
    }

    component DarkCheck: CheckBox {
        id: chk
        implicitHeight: 24
        indicator: Rectangle {
            implicitWidth: 18
            implicitHeight: 18
            radius: 4
            color: chk.checked ? "#1d4ed8" : dlg.fieldBg
            border.width: 1
            border.color: chk.checked ? dlg.accent : "#31425e"
            Text {
                anchors.centerIn: parent
                text: "✓"
                visible: chk.checked
                color: "#eff6ff"
                font.pixelSize: 11
                font.bold: true
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: 14
        color: dlg.bg
        border.width: 1
        border.color: "#1b2740"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "SETTINGS"
                    color: dlg.text
                    font.pixelSize: 12
                    font.bold: true
                    font.family: dlg.uiFont
                    font.letterSpacing: 0.8
                }
                Item { Layout.fillWidth: true }
                Rectangle {
                    width: 24; height: 24; radius: 7
                    color: closeArea.containsMouse ? "#3a1d24" : "transparent"
                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        color: closeArea.containsMouse ? "#fca5a5" : dlg.muted
                        font.pixelSize: 11
                        font.family: dlg.uiFont
                    }
                    MouseArea {
                        id: closeArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: dlg.close()
                    }
                }
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AsNeeded
                    contentItem: Rectangle {
                        implicitWidth: 6
                        radius: 3
                        color: "#33456a"
                    }
                    background: Rectangle { color: "transparent" }
                }

                ColumnLayout {
                    width: dlg.width - 44
                    spacing: 8

                    Text {
                        text: "DISPLAY (max watt per monitor)"
                        color: dlg.muted; font.pixelSize: 8; font.bold: true; font.family: dlg.uiFont
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Display 1 maks"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont; Layout.fillWidth: true }
                        DarkField {
                            id: d1
                            text: engineRef ? Number(engineRef.settings.display1).toFixed(0) : "45"
                            validator: IntValidator { bottom: 5; top: 400 }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Display 2 aktif"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont; Layout.fillWidth: true }
                        DarkCheck { id: d2en; checked: engineRef ? engineRef.settings.display2Enabled : false }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Display 2 maks"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont; Layout.fillWidth: true }
                        DarkField {
                            id: d2
                            text: engineRef ? Number(engineRef.settings.display2).toFixed(0) : "35"
                            validator: IntValidator { bottom: 5; top: 400 }
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: dlg.line }

                    Text {
                        text: "CPU (watt real-time, tanpa setelan manual)"
                        color: dlg.muted; font.pixelSize: 8; font.bold: true; font.family: dlg.uiFont
                    }
                    Text {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: "Dibaca langsung dari sensor: LibreHardwareMonitor (CPU Package Power) " +
                              "atau Intel/AMD RAPL lewat LHM. Kalau sensor tidak tersedia, nilai " +
                              "dihitung dari load × TDP dan diberi label estimasi."
                        color: dlg.muted
                        font.pixelSize: 8
                        font.family: dlg.uiFont
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: dlg.line }

                    Text {
                        text: "STARTUP"
                        color: dlg.muted; font.pixelSize: 8; font.bold: true; font.family: dlg.uiFont
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Text { text: "Autostart saat Windows nyala"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont }
                            Text {
                                text: engineRef && engineRef.settings.autostart
                                      ? "Aktif — WattGauge jalan otomatis tiap booting"
                                      : "Nonaktif"
                                color: engineRef && engineRef.settings.autostart ? "#7ee2a8" : dlg.muted
                                font.pixelSize: 8
                                font.family: dlg.uiFont
                            }
                        }
                        DarkCheck {
                            id: autostartChk
                            checked: engineRef ? engineRef.settings.autostart : true
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: dlg.line }

                    Text {
                        text: "FAN & RGB"
                        color: dlg.muted; font.pixelSize: 8; font.bold: true; font.family: dlg.uiFont
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Jumlah fan"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont; Layout.fillWidth: true }
                        DarkField {
                            id: fanCount
                            text: engineRef ? String(engineRef.settings.fans) : "6"
                            validator: IntValidator { bottom: 0; top: 30 }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Watt per fan"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont; Layout.fillWidth: true }
                        DarkField {
                            id: fanWatt
                            text: engineRef ? Number(engineRef.settings.fanWatt).toFixed(1) : "1.5"
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "AIO pump"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont; Layout.fillWidth: true }
                        DarkCheck { id: pump; checked: engineRef ? engineRef.settings.pump : true }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Watt pump"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont; Layout.fillWidth: true }
                        DarkField {
                            id: pumpWatt
                            text: engineRef ? Number(engineRef.settings.pumpWatt).toFixed(1) : "6.0"
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Jumlah LED RGB"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont; Layout.fillWidth: true }
                        DarkField {
                            id: leds
                            text: engineRef ? String(engineRef.settings.leds) : "24"
                            validator: IntValidator { bottom: 0; top: 400 }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Watt per LED"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont; Layout.fillWidth: true }
                        DarkField {
                            id: ledWatt
                            text: engineRef ? Number(engineRef.settings.ledWatt).toFixed(2) : "0.30"
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: dlg.line }

                    Text {
                        text: "TOP BAR"
                        color: dlg.muted; font.pixelSize: 8; font.bold: true; font.family: dlg.uiFont
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Tampilkan top bar mini"; color: dlg.text; font.pixelSize: 9; font.family: dlg.uiFont; Layout.fillWidth: true }
                        DarkCheck {
                            id: topbar
                            checked: engineRef ? engineRef.settings.topbar : true
                            onToggled: if (engineRef) engineRef.saveTopbar(checked)
                        }
                    }
                }
            }

            Button {
                id: saveBtn
                Layout.fillWidth: true
                implicitHeight: 34
                text: "SIMPAN"
                font.pixelSize: 10
                font.bold: true
                font.family: dlg.uiFont
                contentItem: Text {
                    text: saveBtn.text
                    color: "#eaf6ff"
                    font: saveBtn.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 8
                    color: saveBtn.down ? "#1e40af" : (saveBtn.hovered ? "#1d4ed8" : "#1b3a68")
                    border.width: 1
                    border.color: "#2f5f9e"
                }
                onClicked: {
                    if (!engineRef) { dlg.close(); return }
                    engineRef.saveDisplays(num(d1.text, 45), num(d2.text, 35), d2en.checked)
                    engineRef.savePlatform(num(fanCount.text, 6), num(fanWatt.text, 1.5),
                                           pump.checked, num(pumpWatt.text, 6),
                                           num(leds.text, 24), num(ledWatt.text, 0.3), 18)
                    engineRef.saveAutostart(autostartChk.checked)
                    dlg.close()
                }
            }
        }
    }
}