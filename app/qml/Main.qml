import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: root
    width: 470
    height: 726
    minimumWidth: 330
    minimumHeight: 510
    visible: true
    color: "transparent"
    title: backend ? ("WattGauge · " + backend.totalWatt.toFixed(0) + " W") : "WattGauge"
    flags: Qt.Window | Qt.FramelessWindowHint

    property color bg: "#0a0f1a"
    property color card: "#111a2b"
    property color cardHi: "#16223a"
    property color accent: "#38bdf8"
    property color amber: "#f5c451"
    property color text: "#f1f5f9"
    property color muted: "#7b8aa3"
    property color line: "#1e2b45"
    property var backend: null

    // Everything is laid out at the design size (470x726) and scaled as one
    // block, so dragging the corner scales the whole UI instead of clipping it.
    Item {
        id: stage
        width: 470
        height: 726
        anchors.centerIn: parent
        transformOrigin: Item.Center
        scale: Math.min(root.width / width, root.height / height)

    Rectangle {
        id: shell
        anchors.fill: parent
        radius: 14
        color: root.bg
        border.width: 1
        border.color: "#1b2740"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 10

            // ---------- header ----------
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Rectangle {
                    width: 34; height: 34; radius: 9
                    color: "#16324a"
                    Text {
                        anchors.centerIn: parent
                        text: "⚡"
                        font.pixelSize: 16
                    }
                }

                ColumnLayout {
                    spacing: 1
                    Layout.fillWidth: true
                    Text {
                        text: "POWER USAGE & COST"
                        color: root.text
                        font.pixelSize: 12
                        font.bold: true
                        font.letterSpacing: 0.6
                    }
                    Text {
                        text: backend.summaryChips.length > 0 ? backend.summaryChips : "Detecting hardware…"
                        color: root.muted
                        font.pixelSize: 9
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                }

                Rectangle {
                    radius: 9
                    color: "#1d2b1f"
                    border.width: 1
                    border.color: "#2f5a3a"
                    implicitWidth: badgeText.implicitWidth + 14
                    implicitHeight: 20
                    Text {
                        id: badgeText
                        anchors.centerIn: parent
                        text: "● " + backend.sourceLabel
                        color: "#7ee2a8"
                        font.pixelSize: 8
                        font.bold: true
                    }
                }

                Rectangle {
                    width: 24; height: 24; radius: 7
                    color: gearArea.containsMouse ? root.cardHi : "transparent"
                    Text { anchors.centerIn: parent; text: "⚙"; color: root.muted; font.pixelSize: 13 }
                    MouseArea {
                        id: gearArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: settingsLoader.active = true
                    }
                }

                Rectangle {
                    width: 24; height: 24; radius: 7
                    color: closeArea.containsMouse ? "#3a1d24" : "transparent"
                    Text { anchors.centerIn: parent; text: "✕"; color: root.muted; font.pixelSize: 11 }
                    MouseArea {
                        id: closeArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: { backend.shutdown(); Qt.quit() }
                    }
                }
            }

            // ---------- total ----------
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: root.card
                border.width: 1
                border.color: root.line
                implicitHeight: 96

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    radius: 11
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#122036" }
                        GradientStop { position: 1.0; color: "#111a2b" }
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8

                    ColumnLayout {
                        spacing: 0
                        Layout.fillWidth: true
                        Text {
                            text: "TOTAL LIVE CONSUMPTION"
                            color: root.muted
                            font.pixelSize: 8
                            font.letterSpacing: 0.8
                        }
                        RowLayout {
                            spacing: 6
                            Text {
                                text: backend.totalWatt.toFixed(1)
                                color: "#5cc8f5"
                                font.pixelSize: 38
                                font.bold: true
                                font.family: "Consolas"
                            }
                            Text {
                                text: "WATT"
                                color: root.muted
                                font.pixelSize: 9
                                font.bold: true
                                Layout.alignment: Qt.AlignBottom
                                Layout.bottomMargin: 9
                            }
                        }
                        Text {
                            text: backend.uptimeText + " nyala · " + backend.kwhSession.toFixed(2) + " kWh sesi"
                            color: root.muted
                            font.pixelSize: 8
                        }
                    }

                    Rectangle { width: 1; Layout.fillHeight: true; color: root.line }

                    ColumnLayout {
                        spacing: 2
                        Layout.alignment: Qt.AlignRight | Qt.AlignVCenter

                        Text {
                            text: "Tarif PLN"
                            color: root.muted
                            font.pixelSize: 8
                            Layout.alignment: Qt.AlignRight
                        }

                        Rectangle {
                            color: "#0d1524"
                            radius: 6
                            border.width: 1
                            border.color: root.line
                            implicitWidth: 96
                            implicitHeight: 22
                            TextInput {
                                id: tariffInput
                                anchors.fill: parent
                                anchors.margins: 4
                                text: Number(backend.tariff).toFixed(2).replace(".", ",")
                                color: root.text
                                font.pixelSize: 10
                                font.bold: true
                                font.family: "Consolas"
                                horizontalAlignment: TextInput.AlignRight
                                validator: DoubleValidator { bottom: 1; top: 100000; decimals: 2 }
                                onEditingFinished: {
                                    var v = parseFloat(text.replace(/\./g, "").replace(",", "."))
                                    if (!isNaN(v) && v > 0) backend.setTariff(v)
                                }
                            }
                        }
                        Text {
                            text: "Rp/kWh"
                            color: root.muted
                            font.pixelSize: 8
                            Layout.alignment: Qt.AlignRight
                        }
                    }
                }
            }

            // ---------- components ----------
            GridLayout {
                id: grid
                Layout.fillWidth: true
                columns: 2
                columnSpacing: 8
                rowSpacing: 8

                Repeater {
                    model: backend.components

                    delegate: Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 42
                        radius: 9
                        color: root.card
                        border.width: 1
                        border.color: root.line

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            spacing: 6

                            Text {
                                text: modelData.icon
                                font.pixelSize: 11
                                opacity: 0.95
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0
                                Text {
                                    text: modelData.name
                                    color: root.text
                                    font.pixelSize: 9
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Text {
                                    text: (modelData.detail || "") +
                                          (modelData.source === "sensor" ? "  • real" : "")
                                    color: modelData.source === "sensor" ? "#7ee2a8" : root.muted
                                    font.pixelSize: 7
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }
                            Text {
                                text: Number(modelData.watt).toFixed(1) + " W"
                                color: modelData.source === "sensor" ? "#5cc8f5" : "#94a3b8"
                                font.pixelSize: 10
                                font.bold: true
                                font.family: "Consolas"
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 42
                    radius: 9
                    color: root.card
                    border.width: 1
                    border.color: root.line
                    Text {
                        anchors.centerIn: parent
                        text: "+ Tambah Display / Fan / RGB di ⚙ Settings"
                        color: root.muted
                        font.pixelSize: 8
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: settingsLoader.active = true
                    }
                }
            }

            // ---------- history ----------
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: root.card
                border.width: 1
                border.color: root.line
                implicitHeight: 118

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "RIWAYAT JAM PC AKTIF (7 HARI)"
                            color: root.text
                            font.pixelSize: 8
                            font.bold: true
                            font.letterSpacing: 0.5
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: "Rata-rata: " + (backend && backend.avgDailyHours > 0
                                        ? backend.avgDailyHours.toFixed(1) + " Jam/Hari"
                                        : "belum ada data")
                            color: root.accent
                            font.pixelSize: 8
                            font.bold: true
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 4

                        Repeater {
                            model: backend.weekdayStats

                            delegate: ColumnLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 2

                                Item {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    Rectangle {
                                        anchors.bottom: parent.bottom
                                        width: Math.min(18, parent.width * 0.72)
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        radius: 3
                                        height: Math.max(3, Math.min(1.0, modelData.hours / 24.0) * parent.height)
                                        color: modelData.hours >= backend.avgDailyHours ? "#3fa9d8" : "#1d4b66"
                                        Behavior on height { NumberAnimation { duration: 250 } }
                                    }
                                }
                                Text {
                                    text: modelData.day
                                    color: root.muted
                                    font.pixelSize: 7
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Text {
                                    text: modelData.hours.toFixed(1) + "j"
                                    color: "#93a4bd"
                                    font.pixelSize: 7
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                        }
                    }
                }
            }

            // ---------- range + mode ----------
            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Repeater {
                    model: [1, 7, 14, 30]
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 26
                        radius: 7
                        color: backend.selectedDays === modelData ? "#1a5f86" : root.card
                        border.width: 1
                        border.color: backend.selectedDays === modelData ? "#2f9fd0" : root.line
                        Text {
                            anchors.centerIn: parent
                            text: modelData + " Hari"
                            color: backend.selectedDays === modelData ? "#eaf9ff" : root.muted
                            font.pixelSize: 8
                            font.bold: backend.selectedDays === modelData
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: backend.setSelectedDays(modelData)
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 26
                    radius: 7
                    color: "#1a3247"
                    border.width: 1
                    border.color: "#28506f"
                    Text {
                        anchors.centerIn: parent
                        text: "📊 " + backend.modeLabel
                        color: "#bfe6ff"
                        font.pixelSize: 8
                        font.bold: true
                    }
                }

                Rectangle {
                    implicitHeight: 26
                    implicitWidth: 132
                    radius: 7
                    color: backend.useSmartHours ? root.card : "#1a5f86"
                    border.width: 1
                    border.color: backend.useSmartHours ? root.line : "#2f9fd0"
                    Text {
                        anchors.centerIn: parent
                        text: "⚡ 24 Jam Non-Stop"
                        color: backend.useSmartHours ? root.muted : "#eaf9ff"
                        font.pixelSize: 8
                        font.bold: !backend.useSmartHours
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: backend.setUseSmartHours(!backend.useSmartHours)
                    }
                }
            }

            // ---------- cost footer ----------
            Rectangle {
                Layout.fillWidth: true
                radius: 12
                color: "#0e2018"
                border.width: 1
                border.color: "#1d4534"
                implicitHeight: 58

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 10

                    ColumnLayout {
                        spacing: 1
                        Text {
                            text: "Estimasi Biaya (" + backend.selectedDays + " Hari · " + backend.basisNote + ")"
                            color: "#6f8f80"
                            font.pixelSize: 8
                        }
                        Text {
                            text: backend.costText
                            color: "#57e39b"
                            font.pixelSize: 20
                            font.bold: true
                        }
                    }
                    Item { Layout.fillWidth: true }
                    ColumnLayout {
                        spacing: 1
                        Text {
                            text: "Total Energi"
                            color: "#6f8f80"
                            font.pixelSize: 8
                            Layout.alignment: Qt.AlignRight
                        }
                        Text {
                            text: backend.kwhProjected.toFixed(2) + " kWh"
                            color: "#e8fff5"
                            font.pixelSize: 12
                            font.bold: true
                            font.family: "Consolas"
                            Layout.alignment: Qt.AlignRight
                        }
                    }
                }
            }

            Item { Layout.fillHeight: true }
        }

        // drag window by header
        MouseArea {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 56
            acceptedButtons: Qt.LeftButton
            onPressed: function(mouse) { root.startSystemMove() }
        }
    }

    }

    // corner resize grip
    MouseArea {
        id: grip
        width: 20
        height: 20
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        cursorShape: Qt.SizeFDiagCursor
        property real startW: 0
        property real startH: 0
        property point startPt: Qt.point(0, 0)
        onPressed: function(mouse) {
            startW = root.width
            startH = root.height
            startPt = mapToGlobal(mouse.x, mouse.y)
        }
        onPositionChanged: function(mouse) {
            var pt = mapToGlobal(mouse.x, mouse.y)
            root.width = Math.max(root.minimumWidth, startW + (pt.x - startPt.x))
            root.height = Math.max(root.minimumHeight, startH + (pt.y - startPt.y))
        }
        onReleased: if (root.backend) root.backend.saveWindowSize(Math.round(root.width), Math.round(root.height))
        Rectangle {
            width: 10; height: 10; radius: 2
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: 4
            anchors.bottomMargin: 4
            color: grip.containsMouse ? "#38bdf8" : "#2a3a55"
        }
    }

    Shortcut {
        sequence: "Ctrl+,"
        onActivated: settingsLoader.active = true
    }
    Shortcut {
        sequence: "Ctrl+Q"
        onActivated: { if (backend) backend.shutdown(); Qt.quit() }
    }

    Loader {
        id: settingsLoader
        active: false
        source: "Settings.qml"
        onLoaded: item.engineRef = backend
        onActiveChanged: if (active && item) item.show()
    }
}