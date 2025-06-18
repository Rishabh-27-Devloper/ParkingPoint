# 🚗 Parking Point — Smart Parking Management System

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-yellow)
![Android](https://img.shields.io/badge/Android-Companion%20App-green)
![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue)

A smart parking spot reservation platform with an admin dashboard, user bookings, QR-based ticketing, real-time validation via Android app, and Razorpay payment integration.

> 👥 Built for users to **book parking before arrival**, and for admins to **manage slots with analytics and live validation**.

---

## 🌐 Features

### 🔐 User Side
- Email signup with OTP verification
- Login, logout, and forgot/reset password flows
- Book parking spots with:
  - Location, time, vehicle & slot selection
  - Razorpay payment integration
- Auto-generated **QR-coded ticket**
- View & download tickets from profile
- Booking history and vehicle manager
- In-app notifications and preferences

### 🛠 Admin Side
- Secure admin login
- Dashboard with:
  - Total revenue, users, spots, bookings
  - 7-day chart analytics
- Add/manage parking lots with:
  - Location (Leaflet map)
  - Capacity, rate, availability status

### 📱 Android Companion App
- Built with Java + ZXing QR Scanner
- Validate ticket QR codes in real-time via backend
- Perform **entry** and **exit** mark actions
- Popup overlays for success/errors
- Offline input with custom server URL
- Uses `OkHttp` for API communication

---

## 📸 Screenshots

| Web | Admin Dashboard | Android |
|-----|------------------|---------|
| *(Insert images here)* | *(Insert images here)* | *(Insert images here)* |

---

## ⚙️ Tech Stack

| Layer         | Tools / Libraries                                  |
|---------------|----------------------------------------------------|
| Backend       | Flask, SQLite3, Razorpay SDK                       |
| Frontend      | Jinja2 templates, HTML5, CSS3                      |
| Database      | SQLite3 (via custom Python wrapper)                |
| QR Generation | `qrcode` (Python)                                  |
| Email/OTP     | `smtplib`, Brevo SMTP Relay                        |
| Mobile App    | Java (Android), ZXing, OkHttp                      |
| Maps (Admin)  | LeafletJS + OpenStreetMap                          |

---

## 🧾 Database Schema

### Tables:
- `users` — id, username, email, password
- `vehicles` — linked to user, stores vehicle info
- `parkingspots` — name, GPS location, capacity, rate
- `tickets` — QR code bookings with entry/exit flags
- `payments` — transaction status, Razorpay ID, ticket ID
- `notifications` — messages shown in user portal

All managed through `Database.py`, with auto-initialization and query helpers.

---

## 🚀 Getting Started

### 📌 Prerequisites
- Python 3.10+
- pip
- SQLite3 (included in Python)
- Razorpay test keys
- SMTP mail credentials (Brevo or Gmail relay)

---

### ⚙️ Backend Setup

```bash
git clone https://github.com/Rishabh-27-Devloper/ParkingPoint.git
cd ParkingPoint
pip install -r requirements.txt
python main.py
```

- Open in browser: `http://localhost:5000/`
- Admin login: `/admin`
- QR codes saved in: `static/qr_codes/`

---

### 🤖 Android App Setup

1. Open `/Android/` folder in **Android Studio**
2. Build the project and install it on your device
3. Enter backend server IP (e.g. `http://192.168.0.105:5000`)
4. Scan QR → fetch ticket → mark entry/exit

---

## ✅ REST API Endpoints (used by Android)

| Endpoint          | Method | Description             |
|-------------------|--------|-------------------------|
| `/checkTicket`    | POST   | Validate scanned ticket |
| `/makeEntry`      | POST   | Mark vehicle entry      |
| `/makeExit`       | POST   | Mark vehicle exit       |
| `/view_ticket/id` | GET    | Get full ticket details |

---

## 🔐 Security Notes

- Passwords should be hashed securely (use `werkzeug.security`)
- Store keys & credentials in `.env` (not hard-coded)
- Enable HTTPS in deployment
- Validate all incoming data (server & client-side)
- Use secure session settings (`SESSION_COOKIE_SECURE` etc.)

---

## 📄 License

Licensed under the **GNU General Public License v3.0**

See [LICENSE](LICENSE) for full details.

---

## 🤝 Contributing

Contributions are welcome! Fork the repository and open a pull request.

```bash
git checkout -b feature/my-feature
git commit -m "Add new feature"
git push origin feature/my-feature
```

---

## 💡 Credits

- Developed by **Prakhar Shukla**
- Email & QR integration by [Flask & qrcode]
- Android scanning via [ZXing](https://github.com/zxing/zxing)
- Map visualization by [LeafletJS](https://leafletjs.com)
- Payments via [Razorpay](https://razorpay.com)

---

⭐️ Don't forget to **star** this repo if you found it helpful!
