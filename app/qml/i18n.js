.pragma library

var TARIFFS = [
    { group: "household", name: "900 VA (Subsidi)", price: 605.00 },
    { group: "household", name: "900 VA (Nonsubsidi)", price: 1352.00 },
    { group: "household", name: "1.300 VA", price: 1444.70 },
    { group: "household", name: "2.200 VA", price: 1444.70 },
    { group: "household", name: "3.500 VA – 5.500 VA", price: 1699.53 },
    { group: "household", name: "6.600 VA ke atas (R-3)", price: 1699.53 },
    { group: "business", name: "6.600 VA – 200 kVA (B-2 / TR)", price: 1444.70 }
]

var S = {
    en: {
        app_tagline: "POWER USAGE & COST",
        detecting: "Detecting hardware...",
        total_live: "TOTAL LIVE CONSUMPTION",
        watt_unit: "WATT",
        session_line: "{uptime} on · {kwh} kWh session",
        tariff: "PLN Tariff",
        per_kwh: "Rp/kWh",
        add_tile: "+ Add Display / Fan / RGB (open Settings)",
        history_title: "PC ACTIVE HOURS (LAST 7 DAYS)",
        avg_label: "Average:",
        no_data: "no data yet",
        hours_a_day: "{v} h/day",
        days_option: "{n} Days",
        mode_avg: "📊 Average Hours",
        mode_full: "⚡ 24h Non-Stop",
        hours_24: "24 h/day",
        est_smart: "Estimate {days} days × {hours} = ±{total} active hours ({active} active days in last 7 days)",
        est_full: "24h mode: {days} days × 24 h = ±{total} h (PC assumed always on)",
        cost_est: "Estimated Cost ({days} Days · {basis})",
        total_energy: "Total Energy",
        real_tag: "  • real",
        settings_title: "SETTINGS",
        lang_section: "LANGUAGE",
        display_section: "DISPLAY (max watt per monitor)",
        display1_max: "Display 1 max",
        display2_enabled: "Display 2 enabled",
        display2_max: "Display 2 max",
        cpu_section: "CPU (real-time watt, no manual setting)",
        cpu_help: "Read straight from sensors: LibreHardwareMonitor (CPU Package Power) or Intel/AMD RAPL via LHM. When no sensor is available the value is computed from load × TDP and labelled as an estimate.",
        startup_section: "STARTUP",
        autostart_label: "Autostart with Windows",
        autostart_on: "On — WattGauge starts automatically on every boot",
        autostart_off: "Off",
        tariff_section: "PLN TARIFF",
        tariff_credit: "by rezariski",
        tariff_pick: "Choose tariff",
        tariff_custom: "Custom tariff (Rp/kWh)",
        tariff_current: "Current: {name}",
        household: "Household",
        business: "Business",
        price_row: "Rp {price}/kWh",
        fan_section: "FAN & RGB",
        fan_count: "Fan count",
        fan_watt: "Watt per fan",
        pump_label: "AIO pump",
        pump_watt: "Pump watt",
        leds: "RGB LED count",
        led_watt: "Watt per LED",
        topbar_section: "MINI WIDGET & TRAY",
        topbar_show: "Show mini watt widget",
        close_to_tray: "Close button hides to tray (app keeps counting)",
        save: "SAVE",
        about_section: "ABOUT",
        app_version: "WattGauge v{v}",
        about_text: "PC power monitor with PLN cost estimate. Runs in the background so the cost keeps counting after the window is closed.",
        check_update: "Check for update",
        checking: "Checking...",
        up_to_date: "You are on the latest version",
        update_available: "New version {v} available",
        update_failed: "Update check failed",
        open_github: "Open GitHub",
        hours_assumed: "8 h/day assumed",
        hours_active: "{v} h/day active",
        basis_24: "24 h/day",
        basis_assumed: "8 h/day assumed, low data",
        basis_actual: "{v} h/day actual",
        src_estimate: "ESTIMATE",
        src_real: "REAL SENSOR",
        src_partial: "{n}/{m} SENSOR",
        per_hour: "Rp {v}/hr",
        tray_open: "Open WattGauge",
        tray_quit: "Quit",
        tray_show: "Show window",
        tray_hide: "Hide window",
        day0: "Mon", day1: "Tue", day2: "Wed", day3: "Thu",
        day4: "Fri", day5: "Sat", day6: "Sun"
    },
    id: {
        app_tagline: "PEMAKAIAN DAYA & BIAYA",
        detecting: "Mendeteksi hardware...",
        total_live: "TOTAL KONSUMSI REAL-TIME",
        watt_unit: "WATT",
        session_line: "{uptime} nyala · {kwh} kWh sesi",
        tariff: "Tarif PLN",
        per_kwh: "Rp/kWh",
        add_tile: "+ Tambah Display / Fan / RGB (buka Settings)",
        history_title: "RIWAYAT JAM PC AKTIF (7 HARI)",
        avg_label: "Rata-rata:",
        no_data: "belum ada data",
        hours_a_day: "{v} jam/hari",
        days_option: "{n} Hari",
        mode_avg: "📊 Rata-rata Jam",
        mode_full: "⚡ 24 Jam Non-Stop",
        hours_24: "24 jam/hari",
        est_smart: "Estimasi {days} hari x {hours} = ±{total} jam aktif ({active} hari aktif dari 7 hari terakhir)",
        est_full: "Mode 24 Jam: {days} hari x 24 jam = ±{total} jam (PC dianggap nyala terus)",
        cost_est: "Estimasi Biaya ({days} Hari · {basis})",
        total_energy: "Total Energi",
        real_tag: "  • real",
        settings_title: "PENGATURAN",
        lang_section: "BAHASA",
        display_section: "DISPLAY (max watt per monitor)",
        display1_max: "Display 1 maks",
        display2_enabled: "Display 2 aktif",
        display2_max: "Display 2 maks",
        cpu_section: "CPU (watt real-time, tanpa setelan manual)",
        cpu_help: "Dibaca langsung dari sensor: LibreHardwareMonitor (CPU Package Power) atau Intel/AMD RAPL lewat LHM. Kalau sensor tidak tersedia, nilai dihitung dari load × TDP dan diberi label estimasi.",
        startup_section: "STARTUP",
        autostart_label: "Autostart saat Windows nyala",
        autostart_on: "Aktif — WattGauge jalan otomatis tiap booting",
        autostart_off: "Nonaktif",
        tariff_section: "TARIF PLN",
        tariff_credit: "by rezariski",
        tariff_pick: "Pilih tarif",
        tariff_custom: "Tarif custom (Rp/kWh)",
        tariff_current: "Aktif: {name}",
        household: "Rumahan",
        business: "Bisnis",
        price_row: "Rp {price}/kWh",
        fan_section: "FAN & RGB",
        fan_count: "Jumlah fan",
        fan_watt: "Watt per fan",
        pump_label: "AIO pump",
        pump_watt: "Watt pump",
        leds: "Jumlah LED RGB",
        led_watt: "Watt per LED",
        topbar_section: "WIDGET MINI & TRAY",
        topbar_show: "Tampilkan widget watt mini",
        close_to_tray: "Tombol silang menyembunyikan ke tray (aplikasi tetap menghitung)",
        save: "SIMPAN",
        about_section: "TENTANG",
        app_version: "WattGauge v{v}",
        about_text: "Monitor daya PC dengan estimasi biaya PLN. Tetap jalan di background jadi biaya terus dihitung walau jendela ditutup.",
        check_update: "Cek update",
        checking: "Memeriksa...",
        up_to_date: "Sudah versi terbaru",
        update_available: "Versi baru {v} tersedia",
        update_failed: "Gagal cek update",
        open_github: "Buka GitHub",
        hours_assumed: "asumsi 8 j/hari",
        hours_active: "{v} j/hari aktif",
        basis_24: "24 jam/hari",
        basis_assumed: "asumsi 8 jam/hari (data kurang)",
        basis_actual: "{v} jam/hari aktual",
        src_estimate: "ESTIMASI",
        src_real: "SENSOR REAL",
        src_partial: "{n}/{m} SENSOR",
        per_hour: "Rp {v}/jam",
        tray_open: "Buka WattGauge",
        tray_quit: "Keluar",
        tray_show: "Tampilkan jendela",
        tray_hide: "Sembunyikan jendela",
        day0: "Sen", day1: "Sel", day2: "Rab", day3: "Kam",
        day4: "Jum", day5: "Sab", day6: "Min"
    }
}

function money(lang, v) {
    var s = Number(v).toFixed(2)
    var parts = s.split(".")
    var intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, lang === "id" ? "." : ",")
    return intPart + (lang === "id" ? "," : ".") + parts[1]
}

function t(lang, key) {
    var table = S[lang] || S.en
    var value = table[key]
    if (value === undefined)
        value = S.en[key]
    return value === undefined ? key : value
}

function fmt(lang, key, vars) {
    var text = t(lang, key)
    if (!vars)
        return text
    for (var k in vars) {
        if (vars.hasOwnProperty(k))
            text = text.replace(new RegExp("\\{" + k + "\\}", "g"), vars[k])
    }
    return text
}

function day(lang, idx) {
    return t(lang, "day" + idx)
}