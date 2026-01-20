<div align="center">
  <img src="assets/GETOLS%20Logo.png" alt="GETOLS Logo" width="400">
</div>

<div align="center">

![Ubuntu 24.04](https://img.shields.io/badge/Ubuntu-24.04%20LTS-E95420?logo=ubuntu&logoColor=white)
![Debian 12](https://img.shields.io/badge/Debian-12-A81D33?logo=debian&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.x-092E20?logo=django&logoColor=white)
![MariaDB](https://img.shields.io/badge/MariaDB-10.x-003545?logo=mariadb&logoColor=white)
![NGINX](https://img.shields.io/badge/NGINX-Supported-009639?logo=nginx&logoColor=white)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Pre--Release-blue)

</div>

---

# GETOLS  
**Gateway for Extended OLT Services**

---

## 🇮🇩 Deskripsi (Bahasa Indonesia)

**GETOLS** adalah platform gateway open-source yang dirancang untuk menyederhanakan dan menyatukan operasional **OLT dan ONU multi-vendor** melalui satu pintu eksekusi command yang aman dan terkontrol.

GETOLS menggabungkan:
- **Telegram Bot** untuk eksekusi cepat di lapangan  
- **Web Dashboard** untuk manajemen, visualisasi, dan observabilitas  
- **Command abstraction layer** untuk menyamakan perbedaan vendor  
- **Audit & logging eksternal** melalui LeuitLog  

Repository ini merupakan **prerelease publik pertama** dari ide, konsep, arsitektur, dan workflow GETOLS.

> ⚠️ Catatan:  
> Versi ini **belum berisi kode produksi**, dan dipublikasikan untuk mengunci ide serta arah desain GETOLS.

---

## 🧠 Asal Nama GETOLS

Nama **GETOLS** memiliki dua makna yang saling melengkapi: **makna budaya lokal** dan **makna teknis sistem**.

### 🔹 Makna Bahasa Sunda
Dalam bahasa Sunda, kata **getol** berarti:

> **rajin, tekun, konsisten dalam bekerja**

Makna ini mencerminkan filosofi GETOLS sebagai sistem yang:
- Bekerja terus-menerus di belakang layar
- Menangani pekerjaan operasional yang berulang
- Mengurangi beban manual engineer
- Membantu operator fokus pada pengambilan keputusan

### 🔹 Makna Teknis
Secara teknis, **GETOLS** merupakan singkatan dari:

> **Gateway for Extended OLT Services**

Huruf **S** di akhir GETOLS merepresentasikan:
- Multi OLT
- Multi vendor
- Multi layanan

---

## ✨ Fitur Utama (Level Konsep)

- Gateway OLT multi-vendor (Huawei, ZTE, FiberHome, dll)
- Eksekusi command berbasis CLI (SSH / Telnet)
- Discovery ONU berbasis command (`/discover`)
- Bot Telegram dengan otorisasi berbasis **Chat ID**
- Web dashboard untuk:
  - Manajemen OLT
  - Monitoring (SNMP read-only)
- Observabilitas terpisah dari kontrol
- Audit & logging terpusat via **LeuitLog**

---

## 🧠 Status Proyek

- **Status** : Pre-release / Concept Proof  
- **Target User** : NOC Engineer, ISP Operator  
- **Lisensi** : MIT (Freeware)  
- **Stabilitas** : Belum production-ready  

---

## 📐 Arsitektur & Workflow

![GETOLS Workflow](assets/WorkFlow%20Getols.png)

**Prinsip utama:**
- Command (SSH/Telnet) → eksekusi & provisioning
- SNMP → monitoring & visualisasi dashboard
- Logging → sistem eksternal (LeuitLog)

---

## 🤖 Interface yang Didukung

### Telegram Bot
- Discovery ONU
- Provisioning ONU
- Status & quick check
- Audit ringkas
- Keamanan berbasis Chat ID

### Web Dashboard
- Tambah & kelola OLT
- Discovery visual
- Monitoring ONU (SNMP)
- Audit & activity log
- Role-based access

---

## 👤 Penulis & Hak Cipta

Dirancang dan dipublikasikan oleh **Iyankz**  
Pertama kali dipublikasikan: **Januari 2026**

---

---

# 🇬🇧 Description (English)

**GETOLS (Gateway for Extended OLT Services)** is an open-source gateway platform designed to unify and simplify **multi-vendor OLT and ONU operations** through a centralized, secure, and command-driven execution layer.

The name **GETOLS** is inspired by the Sundanese word *getol*, which means **diligent, persistent, and consistently working**—reflecting the philosophy of a system that continuously operates behind the scenes to handle repetitive operational tasks.

GETOLS provides:
- A Telegram Bot for fast operational commands  
- A Web Dashboard for management and observability  
- A vendor-agnostic command abstraction layer  
- Externalized audit and logging via LeuitLog  

This repository represents the **first public prerelease** of the GETOLS concept, architecture, and operational workflow.

> ⚠️ Note:  
> This prerelease does **not contain production-ready code** and is published to establish original authorship and design direction.

---

## 🚀 Project Scope

- Multi-vendor OLT gateway
- Command-first execution model
- Observability separated from control
- Secure, auditable, and extensible design

---

## 📜 License

This project is released as freeware under the **MIT License**.

---

## ⭐ Final Notes

GETOLS is designed to be:
- Practical for real ISP environments
- Secure by default
- Simple for operators
- Extensible for future development

Contributions, ideas, and discussions are welcome once the implementation phase begins.
