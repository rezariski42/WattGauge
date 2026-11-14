import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: bar
    width: 212
    height: 40
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "transparent"
    visible: false

    property var engineRef: null
    property real liveWatt: engineRef ? engineRef.totalWatt : 0
    signal activated()

    onEngineRefChanged: visible = engineRef !== null

    // No frame: just the numbers floating over the desktop, with an outline so
    // they stay readable on any wallpaper.
    RowLayout {
        anchors.fill: parent
        spacing: 5

        Text {
            text: "⚡"
            font.pixelSize: 13
            style: Text.Outline
            styleColor: "#04101c"
        }

        Text {
            text: bar.liveWatt > 0 ? bar.liveWatt.toFixed(1) : "—"
            color: bar.liveWatt > 0 ? "#6fd6ff" : "#8aa0bb"
            font.pixelSize: 24
            font.bold: true
            font.family: "Consolas"
            style: Text.Outline
            styleColor: "#03080f"
        }

        Text {
            text: "W"
            color: "#cfe4f5"
            font.pixelSize: 11
            font.bold: true
            font.family: "Segoe UI"
            style: Text.Outline
            styleColor: "#03080f"
            Layout.alignment: Qt.AlignBottom
            Layout.bottomMargin: 6
        }

        Item { Layout.fillWidth: true }

        Text {
            text: bar.engineRef ? bar.engineRef.costPerHour : "Rp —"
            color: "#7ee2a8"
            font.pixelSize: 11
            font.bold: true
            font.family: "Segoe UI"
            style: Text.Outline
            styleColor: "#02110a"
        }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        cursorShape: Qt.PointingHandCursor
        onPressed: function(mouse) { bar.startSystemMove() }
        onClicked: bar.activated()
    }
}