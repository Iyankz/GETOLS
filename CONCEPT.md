# Konsep GETOLS

## Mengapa GETOLS Dibuat
Tim NOC dan ISP sering mengelola banyak vendor OLT dengan perbedaan command, workflow, dan model akses. Hal ini menimbulkan kompleksitas, human error, dan inefisiensi.

GETOLS hadir sebagai **gerbang operasional tunggal** untuk menstandarkan interaksi dengan OLT.

---

## Apa Itu GETOLS
- Gateway eksekusi command
- Lapisan abstraksi multi-vendor
- Interface operasional yang aman (Telegram & Web)

---

## Apa BUKAN GETOLS
- Bukan pengganti OLT
- Bukan sistem OSS/BSS
- Bukan platform monitoring murni

---

## Prinsip Desain
- Command-first execution
- Observabilitas terpisah dari kontrol
- Logging & audit eksternal
- Arsitektur vendor-neutral

---

---

# GETOLS Concept

## Why GETOLS Exists
NOC and ISP teams often operate multiple OLT vendors with different command syntax, workflows, and access models, leading to operational friction and human error.

GETOLS is designed as a **single operational gateway** that standardizes OLT interactions.
