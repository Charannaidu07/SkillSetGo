# 🚀 SkillSetGo - Free Online Deployment Guide

This guide will help you deploy **SkillSetGo** online **for 100% free** in less than 5 minutes.

---

## 🌟 Option 1: Render.com (Recommended)
**Render** gives you a free web service with free HTTPS/SSL domain, automatic continuous deployment from GitHub, and seamless static file hosting.

### Step 1: Push Your Code to GitHub
Open your terminal in this project folder and push the latest production configuration to GitHub:

```bash
git add .
git commit -m "Configure project for free cloud deployment"
git push origin main
```

---

### Step 2: Create a Free Render Account
1. Go to **[render.com](https://render.com)**.
2. Sign up or log in using your **GitHub account**.

---

### Step 3: Create a New Web Service
1. On your Render Dashboard, click the blue **"New +"** button at the top right.
2. Select **"Web Service"**.
3. Choose **"Build and deploy from a Git repository"** and click **Next**.
4. Search for your repository: **`SkillSetGo`** (or `Charannaidu07/SkillSetGo`) and click **Connect**.

---

### Step 4: Configure the Service Settings
Fill in the following fields:

| Field | Value |
|---|---|
| **Name** | `skillsetgo` *(or any custom name)* |
| **Region** | Singapore / Frankfurt / Oregon *(choose closest to your users)* |
| **Branch** | `main` |
| **Root Directory** | *(leave blank)* |
| **Runtime** | `Python 3` |
| **Build Command** | `./build.sh` *(or `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`)* |
| **Start Command** | `gunicorn SkillSetGo.wsgi:application` |
| **Instance Type** | **Free** ($0/month) |

---

### Step 5: Add Environment Variables
Scroll down to the **Environment Variables** section and click **Add Environment Variable**:

| Key | Value | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.12.3` | Python runtime version |
| `DEBUG` | `False` | Turn off debug mode for production |
| `SECRET_KEY` | *(Click "Generate" or paste a random string)* | Security key |
| `ALLOWED_HOSTS` | `*` | Allows Render subdomains |
| `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com,http://127.0.0.1,http://localhost` | Fixes CSRF form submission errors |
| `DB_ENGINE` | `sqlite` | Uses built-in SQLite (or provide `DATABASE_URL` for PostgreSQL) |
| `EMAIL_HOST_USER` | `charanedamalapati2005@gmail.com` *(Optional)* | For email notifications |
| `EMAIL_HOST_PASSWORD` | `dowj eafn dwzy lopb` *(Optional)* | Gmail App Password |
| `RAZORPAY_KEY_ID` | `rzp_test_TcizwraHmXHdJg` *(Optional)* | Razorpay test key |
| `RAZORPAY_KEY_SECRET` | `V7iz3wfiLHxVxjZalrERMm4F` *(Optional)* | Razorpay secret |

*(Optional PostgreSQL Database: If you create a free PostgreSQL database on [Render](https://render.com) or [Neon.tech](https://neon.tech), simply add a `DATABASE_URL` environment variable containing the connection string!)*

---

### Step 6: Deploy!
1. Click **"Deploy Web Service"** at the bottom.
2. Render will build your application, install requirements, collect static files, run database migrations, and launch Gunicorn.
3. Once the build finishes (usually ~1-2 minutes), you will see your live URL:
   👉 **`https://skillsetgo.onrender.com`** (or your chosen service name).

---
---

## 🐍 Option 2: PythonAnywhere (No Credit Card Required)

If you prefer a platform specifically designed for Python and MySQL without using Docker/containers:

### Step 1: Create Account
1. Register at **[pythonanywhere.com](https://www.pythonanywhere.com/)** (Free "Beginner" plan).

### Step 2: Open Bash Console
1. In PythonAnywhere, go to the **Consoles** tab and open a **Bash console**.
2. Clone your repository:
   ```bash
   git clone https://github.com/Charannaidu07/SkillSetGo.git
   cd SkillSetGo
   ```
3. Create and activate a virtual environment:
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Run migrations and collect static:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --no-input
   ```

### Step 3: Configure Web App
1. Go to the **Web** tab &rarr; Click **"Add a new web app"**.
2. Select **Manual configuration** &rarr; Select **Python 3.10**.
3. Under **Virtualenv**, enter: `/home/YOUR_USERNAME/SkillSetGo/venv`.
4. Under **Static files**, add:
   - URL: `/static/` &rarr; Directory: `/home/YOUR_USERNAME/SkillSetGo/staticfiles`
   - URL: `/media/` &rarr; Directory: `/home/YOUR_USERNAME/SkillSetGo/media`
5. Click on the **WSGI configuration file** link and replace its contents with:
   ```python
   import os
   import sys

   path = '/home/YOUR_USERNAME/SkillSetGo'
   if path not in sys.path:
       sys.path.append(path)

   os.environ['DJANGO_SETTINGS_MODULE'] = 'SkillSetGo.settings'

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
   *(Replace `YOUR_USERNAME` with your actual PythonAnywhere username)*.
6. Click the green **"Reload <username>.pythonanywhere.com"** button.
7. Your app is live at: `https://<username>.pythonanywhere.com`!

---

## 🎉 Maintenance & Creating an Admin Superuser

To create a superuser for your Django Admin panel on Render:
1. In the Render Dashboard for your web service, click **"Shell"** in the left sidebar.
2. Run:
   ```bash
   python manage.py createsuperuser
   ```
3. Enter your username, email, and password. You can now log into your admin panel at `/admin/`!
