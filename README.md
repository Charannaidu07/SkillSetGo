# 🛠️ SkillSetGo — Premium On-Demand Home Services Platform

[![Live Production](https://img.shields.io/badge/Live%20Website-skillsetgo--1--x9e7.onrender.com-success?style=for-the-badge&logo=render)](https://skillsetgo-1-x9e7.onrender.com/)
[![Django 5.1](https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

> **Live Website URL**: **[https://skillsetgo-1-x9e7.onrender.com/](https://skillsetgo-1-x9e7.onrender.com/)**

**SkillSetGo** is a full-stack, on-demand home service marketplace designed with an Urban Company–inspired user experience. It connects verified technicians and service professionals with homeowners through transparent price negotiation, zero-advance escrow payments, automated PDF ID/Invoice generation, and geolocation-based service discovery.

---

## 🌐 Quick Links
- 🏠 **Live Home Page**: [https://skillsetgo-1-x9e7.onrender.com/](https://skillsetgo-1-x9e7.onrender.com/)
- 📝 **Create Account / Sign Up**: [https://skillsetgo-1-x9e7.onrender.com/accounts/signup/](https://skillsetgo-1-x9e7.onrender.com/accounts/signup/)
- 🔐 **Sign In**: [https://skillsetgo-1-x9e7.onrender.com/accounts/login/](https://skillsetgo-1-x9e7.onrender.com/accounts/login/)
- 🛠️ **Service Categories**: [https://skillsetgo-1-x9e7.onrender.com/services/](https://skillsetgo-1-x9e7.onrender.com/services/)
- 🎁 **Refer & Earn Rewards**: [https://skillsetgo-1-x9e7.onrender.com/rewards/](https://skillsetgo-1-x9e7.onrender.com/rewards/)

---

## ✨ Core Platform Highlights

### 1. 🤝 Transparent Price Negotiation Engine
- Customers submit an initial expected budget for service jobs (Plumbing, Electrical, Carpentry, AC Repair, Cleaning).
- Service professionals review job details and counter-offer in real time with interactive bidding.
- Mutual price agreement locks the booking before any service commences.

### 2. 🛡️ Zero-Advance Escrow Protection
- Integrated payment gateway using Razorpay test/live checkout.
- Funds are safely held in escrow until the service is marked complete via customer OTP verification.

### 3. 🆔 Digital Verifiable ID Cards & Invoices
- Automated dynamic PDF generation for verified service partners (with QR codes, hologram styling, and tamper-resistant serials).
- Instant downloadable tax invoices upon booking completion.

### 4. 📍 Geolocation & OpenCage Integration
- Reverse geocoding of customer locations to map nearby active service providers.

---

## 🏗️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Django 5.1 (Python 3.12) |
| **WSGI / Web Server** | Gunicorn + WhiteNoise (Brotli static caching) |
| **Authentication** | Django Allauth (Custom User Model & Role Segmenting) |
| **Frontend UI** | HTML5, Vanilla CSS3 (Custom Urban Design System), Bootstrap 5, FontAwesome 6 |
| **Database** | SQLite (Production/Dev Fallback), PostgreSQL / MySQL ready |
| **Payments** | Razorpay SDK |
| **PDF & Asset Engine** | ReportLab, Pillow, QRCode |
| **Hosting & CI/CD** | Render.com with automated GitHub Webhooks |

---

## 💻 Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Charannaidu07/SkillSetGo.git
   cd SkillSetGo
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables** (`.env` file):
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   SITE_URL=https://skillsetgo-1-x9e7.onrender.com
   DB_ENGINE=sqlite
   ```

5. **Run migrations and start server**:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000` in your browser!

---

## 🚀 Cloud Deployment

The repository is pre-configured with [`render.yaml`](render.yaml), [`build.sh`](build.sh), and [`Procfile`](Procfile) for zero-config continuous deployment on Render.

Whenever you push to the `main` branch:
```bash
git add .
git commit -m "Your update description"
git push origin main
```
Render automatically rebuilds, compiles static assets with WhiteNoise, applies migrations, and restarts the live service with zero downtime!

---

## 📄 License
This project is licensed under the MIT License.