import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls

Window {
    id: bar
    width: 190
    height: 34
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "transparent"
    visible: true

    property var engineRef: null
    signal activated()

    // Park the mini bar just above the taskbar, bottom-right corner.
    Component.onCompleted: {
        var scr = bar.screen
        if (!scr || !scr.availableGeometry) return
        var geo = scr.availableGeometry
        bar.x = Math.max(0, geo.x + geo.width - bar.width - 12)
        bar.y = Math.max(0, geo.y + geo.height - bar.height - 6)
    }

    Rectangle {
        anchors.fill: parent
        radius: 10
        color: "#101a2b"
        border.width: 1
        border.color: "#22314e"

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 9
            anchors.rightMargin: 9
            spacing: 6

            Text { text: "⚡"; font.pixelSize: 11 }

            Text {
                text: (bar.engineRef ? bar.engineRef.totalWatt.toFixed(1) : "0.0")
                color: "#5cc8f5"
                font.pixelSize: 15
                font.bold: true
                font.family: "Consolas"
            }
            Text {
                text: "W"
                color: "#93a4bd"
                font.pixelSize: 9
                font.family: "Segoe UI"
                Layout.alignment: Qt.AlignBottom
                Layout.bottomMargin: 4
            }

            Item { Layout.fillWidth: true }

            Text {
                text: (bar.engineRef ? bar.engineRef.costPerHour : "Rp 0/jam")
                color: "#7ee2a8"
                font.pixelSize: 9
                font.family: "Segoe UI"
            }
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton
            onPressed: function(mouse) { bar.startSystemMove() }
            onClicked: bar.activated()
        }
    }
}