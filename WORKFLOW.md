# Workflow GETOLS

## Workflow Bot Telegram (Command-Based)
1. User mengirim perintah
2. GETOLS memvalidasi Chat ID & role
3. Command dimapping sesuai vendor
4. Eksekusi via SSH/Telnet
5. Hasil dikirim ke user
6. Audit dikirim ke LeuitLog

---

## Workflow Discovery
Command `/discover` menggunakan CLI vendor untuk memastikan akurasi data ONU yang belum terdaftar.

---

## Workflow Web Dashboard
- Eksekusi command menggunakan engine yang sama dengan Telegram
- Monitoring & visualisasi menggunakan SNMP (read-only)

---

---

# GETOLS Workflow

## Telegram Bot Workflow
1. User sends command
2. GETOLS validates Chat ID and role
3. Vendor command mapping
4. Execution via SSH/Telnet
5. Result returned to user
6. Audit sent to LeuitLog
