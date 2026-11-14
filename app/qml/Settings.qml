import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "i18n.js" as I18N

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
    property string lang: engineRef ? engineRef.language : "en"
    property bool tariffOpen: false

    property color bg: "#0a0f1a"
    property color card: "#111a2b"
    property color fieldBg: "#0d1524"
    property color text: "#f1f5f9"
    property color muted: "#7b8aa3"
    property color line: "#1e2b45"
    property color accent: "#38bdf8"
    property string uiFont: "Segoe UI"

    function num(txt, fallback) {
        var s = String(txt).replace(/\s/g, "")
        if (s === "") return fallback
        if (s.indexOf(",") >= 0)
            s = s.replace(/\./g, "").replace(",", ".")
        var v = parseFloat(s)
        return isNaN(v) ? fallback : v
    }

    function priceLabel(v) {
        return "Rp " + I18N.money(dlg.lang, v)
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

    component SectionLabel: Text {
        color: dlg.muted
        font.pixelSize: 8
        font.bold: true
        font.family: dlg.uiFont
    }

    component RowLabel: Text {
        color: dlg.text
        font.pixelSize: 9
        font.family: dlg.uiFont
        Layout.fillWidth: true
    }

    component FlatButton: Button {
        id: btn
        property bool active: false
        property color activeColor: "#1a5f86"
        implicitHeight: 26
        font.pixelSize: 9
        font.family: dlg.uiFont
        font.bold: true
        contentItem: Text {
            text: btn.text
            color: btn.active ? "#eaf9ff" : dlg.muted
            font: btn.font
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 7
            color: btn.active ? btn.activeColor : (btn.hovered ? "#16223a" : dlg.card)
            border.width: 1
            border.color: btn.active ? "#2f9fd0" : dlg.line
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
                    text: I18N.t(dlg.lang, "settings_title")
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

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                Flickable {
                    id: flick
                    anchors.fill: parent
                    clip: true
                    contentWidth: width
                    contentHeight: contentCol.implicitHeight + 16
                    boundsBehavior: Flickable.StopAtBounds
                    flickableDirection: Flickable.VerticalFlick
                    focus: true
                    activeFocusOnTab: true
                    Component.onCompleted: forceActiveFocus()

                    Keys.onDownPressed: contentY = Math.min(contentHeight - height,
                                                            contentY + 40)
                    Keys.onUpPressed: contentY = Math.max(0, contentY - 40)
                    Keys.onPressed: function(ev) {
                        if (ev.key === Qt.Key_PageDown) {
                            contentY = Math.min(contentHeight - height, contentY + height * 0.8)
                            ev.accepted = true
                        } else if (ev.key === Qt.Key_PageUp) {
                            contentY = Math.max(0, contentY - height * 0.8)
                            ev.accepted = true
                        }
                    }

                    ScrollBar.vertical: ScrollBar {
                        id: vsb
                        policy: ScrollBar.AlwaysOn
                        width: 14
                        padding: 3
                        minimumSize: 0.08
                        active: true
                        contentItem: Rectangle {
                            implicitWidth: 7
                            radius: 3.5
                            color: vsb.pressed ? "#7dd3fc" : (vsb.hovered ? "#5ec9f5" : "#4a6a96")
                        }
                        background: Rectangle {
                            implicitWidth: 9
                            radius: 4.5
                            color: "#101b2c"
                            border.width: 1
                            border.color: "#22344f"
                        }
                    }

                    ColumnLayout {
                        id: contentCol
                        y: 4
                        width: flick.width - 18
                        spacing: 8

                        SectionLabel { text: I18N.t(dlg.lang, "lang_section") }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            FlatButton {
                                Layout.fillWidth: true
                                text: "English"
                                active: dlg.lang === "en"
                                onClicked: if (engineRef) engineRef.setLanguage("en")
                            }
                            FlatButton {
                                Layout.fillWidth: true
                                text: "Bahasa Indonesia"
                                active: dlg.lang === "id"
                                onClicked: if (engineRef) engineRef.setLanguage("id")
                            }
                        }

                        Rectangle { Layout.fillWidth: true; height: 1; color: dlg.line }

                        SectionLabel { text: I18N.t(dlg.lang, "display_section") }

                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "display1_max") }
                            DarkField {
                                id: d1
                                text: engineRef ? Number(engineRef.settings.display1).toFixed(0) : "45"
                                validator: IntValidator { bottom: 5; top: 400 }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "display2_enabled") }
                            DarkCheck { id: d2en; checked: engineRef ? engineRef.settings.display2Enabled : false }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "display2_max") }
                            DarkField {
                                id: d2
                                text: engineRef ? Number(engineRef.settings.display2).toFixed(0) : "35"
                                validator: IntValidator { bottom: 5; top: 400 }
                            }
                        }

                        Rectangle { Layout.fillWidth: true; height: 1; color: dlg.line }

                        SectionLabel { text: I18N.t(dlg.lang, "cpu_section") }
                        Text {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: I18N.t(dlg.lang, "cpu_help")
                            color: dlg.muted
                            font.pixelSize: 8
                            font.family: dlg.uiFont
                        }

                        Rectangle { Layout.fillWidth: true; height: 1; color: dlg.line }

                        RowLayout {
                            Layout.fillWidth: true
                            SectionLabel { text: I18N.t(dlg.lang, "tariff_section") }
                            Item { Layout.fillWidth: true }
                            Text {
                                text: I18N.t(dlg.lang, "tariff_credit")
                                color: "#4f7ea8"
                                font.pixelSize: 8
                                font.family: dlg.uiFont
                            }
                        }

                        Button {
                            id: tariffBtn
                            Layout.fillWidth: true
                            implicitHeight: 30
                            text: engineRef && engineRef.tariffPresetName !== ""
                                  ? engineRef.tariffPresetName
                                  : I18N.t(dlg.lang, "tariff_custom")
                            font.pixelSize: 9
                            font.family: dlg.uiFont
                            contentItem: RowLayout {
                                spacing: 6
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                Text {
                                    Layout.fillWidth: true
                                    text: tariffBtn.text
                                    color: "#eaf6ff"
                                    font: tariffBtn.font
                                    elide: Text.ElideRight
                                }
                                Text {
                                    text: engineRef ? dlg.priceLabel(engineRef.tariff) : "Rp —"
                                    color: "#7ee2a8"
                                    font.pixelSize: 9
                                    font.bold: true
                                    font.family: "Consolas"
                                }
                                Text { text: "▾"; color: dlg.accent; font.pixelSize: 9 }
                            }
                            background: Rectangle {
                                radius: 7
                                color: tariffBtn.hovered || dlg.tariffOpen ? "#16223a" : dlg.fieldBg
                                border.width: 1
                                border.color: dlg.tariffOpen ? dlg.accent : "#26354f"
                            }
                            onClicked: dlg.tariffOpen = !dlg.tariffOpen
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "tariff_custom") }
                            DarkField {
                                id: tariffField
                                text: engineRef ? I18N.money(dlg.lang, engineRef.tariff) : "1444.70"
                                validator: DoubleValidator { bottom: 1; top: 100000; decimals: 2 }
                            }
                        }

                        Rectangle { Layout.fillWidth: true; height: 1; color: dlg.line }

                        SectionLabel { text: I18N.t(dlg.lang, "startup_section") }
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                RowLabel { text: I18N.t(dlg.lang, "autostart_label") }
                                Text {
                                    text: engineRef && engineRef.settings.autostart
                                          ? I18N.t(dlg.lang, "autostart_on")
                                          : I18N.t(dlg.lang, "autostart_off")
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

                        SectionLabel { text: I18N.t(dlg.lang, "fan_section") }
                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "fan_count") }
                            DarkField {
                                id: fanCount
                                text: engineRef ? String(engineRef.settings.fans) : "6"
                                validator: IntValidator { bottom: 0; top: 16 }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "fan_watt") }
                            DarkField {
                                id: fanWatt
                                text: engineRef ? Number(engineRef.settings.fanWatt).toFixed(1) : "1.5"
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "pump_label") }
                            DarkCheck { id: pump; checked: engineRef ? engineRef.settings.pump : true }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "pump_watt") }
                            DarkField {
                                id: pumpWatt
                                text: engineRef ? Number(engineRef.settings.pumpWatt).toFixed(1) : "6.0"
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "leds") }
                            DarkField {
                                id: leds
                                text: engineRef ? String(engineRef.settings.leds) : "24"
                                validator: IntValidator { bottom: 0; top: 150 }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "led_watt") }
                            DarkField {
                                id: ledWatt
                                text: engineRef ? Number(engineRef.settings.ledWatt).toFixed(2) : "0.30"
                            }
                        }

                        Rectangle { Layout.fillWidth: true; height: 1; color: dlg.line }

                        SectionLabel { text: I18N.t(dlg.lang, "topbar_section") }
                        RowLayout {
                            Layout.fillWidth: true
                            RowLabel { text: I18N.t(dlg.lang, "topbar_show") }
                            DarkCheck {
                                id: topbar
                                checked: engineRef ? engineRef.settings.topbar : true
                                onToggled: if (engineRef) engineRef.saveTopbar(checked)
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                RowLabel { text: I18N.t(dlg.lang, "close_to_tray") }
                            }
                            DarkCheck {
                                id: closeTray
                                checked: engineRef ? engineRef.settings.closeToTray : true
                                onToggled: if (engineRef) engineRef.saveCloseToTray(checked)
                            }
                        }

                        Rectangle { Layout.fillWidth: true; height: 1; color: dlg.line }

                        SectionLabel { text: I18N.t(dlg.lang, "about_section") }
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                Layout.fillWidth: true
                                text: I18N.fmt(dlg.lang, "app_version",
                                               { v: engineRef ? engineRef.appVersion : "" })
                                color: dlg.text
                                font.pixelSize: 9
                                font.bold: true
                                font.family: dlg.uiFont
                            }
                            Text {
                                text: I18N.t(dlg.lang, "tariff_credit")
                                color: "#4f7ea8"
                                font.pixelSize: 8
                                font.family: dlg.uiFont
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: I18N.t(dlg.lang, "about_text")
                            color: dlg.muted
                            font.pixelSize: 8
                            font.family: dlg.uiFont
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            FlatButton {
                                Layout.fillWidth: true
                                text: I18N.t(dlg.lang, "check_update")
                                onClicked: if (engineRef) engineRef.checkUpdate()
                            }
                            FlatButton {
                                Layout.fillWidth: true
                                text: I18N.t(dlg.lang, "open_github")
                                onClicked: if (engineRef) engineRef.openUrl(engineRef.githubUrl)
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: text !== ""
                            text: engineRef ? engineRef.updateStatus : ""
                            color: "#7ee2a8"
                            font.pixelSize: 8
                            font.family: dlg.uiFont
                        }
                        Item { width: 1; height: 6 }
                    }
                }
            }

            Button {
                id: saveBtn
                Layout.fillWidth: true
                implicitHeight: 34
                text: I18N.t(dlg.lang, "save")
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
                    var custom = num(tariffField.text, -1)
                    if (custom > 0 && Math.abs(custom - engineRef.tariff) > 0.001)
                        engineRef.setTariff(custom)
                    dlg.close()
                }
            }
        }

        // ---------- tariff picker (overlay) ----------
        Rectangle {
            id: tariffOverlay
            anchors.fill: parent
            z: 90
            visible: dlg.tariffOpen
            color: "#00000099"

            MouseArea {
                anchors.fill: parent
                onClicked: dlg.tariffOpen = false
            }

            Rectangle {
                id: tariffPanel
                width: 260
                height: tariffList.implicitHeight + 14
                anchors.centerIn: parent
                radius: 10
                color: "#0c1524"
                border.width: 1
                border.color: "#2b3d5c"

                Column {
                    id: tariffList
                    anchors.fill: parent
                    anchors.margins: 7
                    spacing: 0

                    Item {
                        width: tariffList.width
                        height: 22
                        Text {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            text: I18N.t(dlg.lang, "tariff_section")
                            color: "#8fb0d0"
                            font.pixelSize: 8
                            font.bold: true
                            font.letterSpacing: 0.5
                        }
                        Text {
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            text: I18N.t(dlg.lang, "tariff_credit")
                            color: "#4f7ea8"
                            font.pixelSize: 7
                        }
                    }

                    Repeater {
                        model: I18N.TARIFFS

                        delegate: Column {
                            width: tariffList.width
                            spacing: 0
                            property bool showHeader: index === 0
                                                      || I18N.TARIFFS[index - 1].group !== modelData.group
                            property bool isActive: engineRef
                                                    && Math.abs(engineRef.tariff - modelData.price) < 0.01
                                                    && engineRef.tariffPresetName === modelData.name

                            Item {
                                width: parent.width
                                height: showHeader ? 18 : 0
                                Text {
                                    anchors.left: parent.left
                                    anchors.bottom: parent.bottom
                                    text: modelData.group === "business"
                                          ? I18N.t(dlg.lang, "business")
                                          : I18N.t(dlg.lang, "household")
                                    color: "#5f7a96"
                                    font.pixelSize: 7
                                    font.bold: true
                                    font.letterSpacing: 0.6
                                }
                            }

                            Rectangle {
                                width: parent.width
                                height: 26
                                radius: 5
                                color: isActive ? "#14314a" : (rowHover.containsMouse ? "#16223a" : "transparent")

                                Row {
                                    anchors.fill: parent
                                    anchors.leftMargin: 8
                                    anchors.rightMargin: 8
                                    spacing: 6
                                    Text {
                                        width: parent.width - priceText.width - 10
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: modelData.name
                                        color: isActive ? "#bfe6ff" : "#dbe7f5"
                                        font.pixelSize: 9
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        id: priceText
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: "Rp " + I18N.money(dlg.lang, modelData.price)
                                        color: "#7ee2a8"
                                        font.pixelSize: 9
                                        font.family: "Consolas"
                                    }
                                }

                                MouseArea {
                                    id: rowHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (engineRef)
                                            engineRef.setTariffPreset(modelData.name, modelData.price)
                                        tariffField.text = Number(modelData.price).toFixed(2)
                                        dlg.tariffOpen = false
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}