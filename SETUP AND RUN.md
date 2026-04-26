# ⚙️ BookStack — Setup & Run Guide

> Complete instructions to get BookStack running on your local machine.

---

## Prerequisites

| Tool | Minimum Version | Check Command |
|------|----------------|---------------|
| Python | 3.8+ | `python --version` |
| pip | Latest | `pip --version` |

No database installation required — BookStack uses **SQLite**, built into Python.

---

## Step 1 — Extract the Project

```bash
unzip bookstack.zip
cd bookstack
```

Your folder structure:

```
bookstack/
├── app.py
├── requirements.txt
├── static/
│   └── style.css
└── templates/
    ├── login.html        ← NEW
    ├── base.html
    ├── index.html
    ├── books.html
    ├── users.html
    ├── issue.html
    ├── loans.html
    ├── loan_detail.html
    ├── overdue.html
    └── reports.html
```

---

## Step 2 — Create a Virtual Environment (Recommended)

### macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows (Command Prompt):
```cmd
python -m venv venv
venv\Scripts\activate
```

### Windows (PowerShell):
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

Installs only **Flask**.

---

## Step 4 — Run the Application

```bash
python app.py
```

Output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

---

## Step 5 — Open in Browser & Log In

Navigate to: **http://localhost:5000**

You will be redirected to the **Login page**.

---

## 🔐 Login Accounts

### Librarian (Full Access)
| Field | Value |
|-------|-------|
| Email | arjun@example.com |
| Password | admin123 |

Also: `kiran@example.com` / `admin123`

### Member (Read-Only Access)
| Field | Value |
|-------|-------|
| Email | priya@example.com |
| Password | password123 |

Also: `rahul@example.com` / `password123`, `sneha@example.com` / `password123`

---

## 🛡️ Role-Based Access

| Feature | Librarian | Member |
|---------|-----------|--------|
| Dashboard | ✅ All loans & alerts | ✅ Own loans only |
| Books (view & search) | ✅ | ✅ |
| Books (add/edit/delete) | ✅ | ❌ |
| Users list | ✅ | ❌ |
| Issue Book | ✅ | ❌ |
| All Loans | ✅ | ❌ (own only) |
| Overdue Management | ✅ | ❌ |
| Reports | ✅ | ❌ |

---

## Resetting the Database

```bash
rm database.db        # macOS / Linux
del database.db       # Windows

python app.py
```

The database is re-created and re-seeded automatically on next launch.

---

## Troubleshooting

**Port already in use:**
```bash
# Edit app.py last line:
app.run(debug=True, port=5001)
```

**ModuleNotFoundError: flask:**
```bash
pip install flask
```

**Permission denied on venv (Windows PowerShell):**
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
