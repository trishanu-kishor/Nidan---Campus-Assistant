# Domain Skill: Information Technology Services (IT)

## Overview & Scope
This skill provides operational knowledge and procedural assistance for campus IT services, network connectivity, software licenses, cybersecurity, workstation labs, and digital identity management.

---

## 1. Campus Network & Connectivity

### 1.1 Eduroam Wi-Fi Setup
- **SSID:** `eduroam` (WPA2/WPA3 Enterprise, EAP-PEAP / MSCHAPv2).
- **Username Format:** `student_id@campus.edu` (e.g., `s104928@campus.edu`). *Do not use just the student ID number.*
- **Password:** Campus Single Sign-On (SSO) password.
- **Certificate Authority:** Trust `Campus-Root-CA-2025` if prompted.
- **Troubleshooting:**
  1. "Forget" the network and reconnect.
  2. Ensure device clock is synced with UTC network time.
  3. Verify that your campus account is active and has no disciplinary or financial suspension blocks.

### 1.2 Guest Wi-Fi (`Campus-Guest`)
- Self-registration via captive portal.
- Active for 24 hours per SMS OTP verification.
- Bandwidth capped at 15 Mbps down / 5 Mbps up.

### 1.3 Campus VPN (GlobalProtect / OpenVPN)
- **Portal URL:** `https://vpn.campus.edu`
- Required for accessing off-campus internal research databases, library journals, and high-performance compute (HPC) clusters.
- **Authentication:** SSO + Duo 2-Factor Authentication (Push or Hardware Token).

---

## 2. Identity & Access Management (SSO)

### 2.1 Password Reset Protocol
- **Self-Service Portal:** `https://identity.campus.edu/reset`
- **Requirements:** Minimum 12 characters, at least 1 uppercase, 1 lowercase, 1 numeric digit, and 1 special symbol. Passwords expire every 180 days.
- **Locked Accounts:** If locked after 5 failed attempts, the lockout lasts 15 minutes. Emergency unlocking requires contacting the IT Helpdesk with official photo ID.

### 2.2 Duo Two-Factor Authentication (2FA)
- New device registration: `https://identity.campus.edu/duo-register`
- Lost phone / Bypass codes: Visit IT Helpdesk in person at Library 1st Floor (Wing B) with student ID card.

---

## 3. Software Licensing & Distribution

| Software Package | Eligibility | Access Method | Notes |
| :--- | :--- | :--- | :--- |
| **Microsoft 365 Enterprise** | All Students & Faculty | `portal.office.com` via SSO | Includes 1 TB OneDrive & Word/Excel/Teams |
| **MATLAB & Simulink** | STEM Students & Researchers | `https://software.campus.edu/matlab` | Campus-wide concurrent license |
| **Adobe Creative Cloud** | Design & Media Majors / Labs | Request via IT Portal Ticket | Free for Media Majors, discounted for others |
| **AutoCAD / Autodesk** | Engineering Students | Autodesk Education Community | Use `.edu` email verification |
| **JetBrains / VS Code Extensions** | Computer Science & IT | JetBrains Student Pack | Annual renewal required |

---

## 4. Hardware & Computer Labs

### 4.1 Lab Workstation Access
- 24/7 Labs located in **Science Hall (Room 304)** and **Engineering Block 2 (Room 110)**.
- Tap student RFID card to unlock door after 10:00 PM.
- Local storage is wiped nightly at 04:00 AM. Always save work to OneDrive or USB.

### 4.2 WebPrint & Campus Printing Quota
- **Portal:** `https://print.campus.edu`
- **Quota:** Every enrolled student receives 250 free black-and-white pages ($12.50 value) per semester.
- Additional credits can be purchased via Campus Card Portal ($0.05/B&W page, $0.20/Color page).

---

## 5. Escalation & Contact Directory

- **IT Helpdesk Physical Desk:** Central Library, Ground Floor, Room 102.
- **Operating Hours:** Mon–Fri: 08:00 AM – 08:00 PM | Sat–Sun: 10:00 AM – 04:00 PM.
- **Email:** `helpdesk@campus.edu`
- **Phone Hotline:** +1 (555) 019-4821 (Emergency Hotline 24/7 for network outages).
- **Ticket Submission:** `https://servicedesk.campus.edu`
