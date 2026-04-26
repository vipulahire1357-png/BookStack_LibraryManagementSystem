# 📚 BookStack — Library Management System

> A full-featured, role-based Library Management System built with **Python Flask** and **SQLite**. Manage books, members, loans, overdue notices, and reports — all from a clean, responsive web interface.

---

## 🖥️ Tech Stack

| Layer       | Technology             |
|-------------|------------------------|
| Backend     | Python 3.8+, Flask     |
| Database    | SQLite (via `sqlite3`) |
| Frontend    | HTML5, CSS3 (Vanilla)  |
| Templating  | Jinja2                 |

No external database server required — SQLite is bundled with Python.

---

## ✨ Features

### 🔐 Authentication & Role-Based Access
- Session-based login/logout
- Two roles: **Librarian** (admin) and **Member** (read-only)
- Route guards via `@login_required` and `@librarian_required` decorators

### 📖 Books Management
- Add, edit, and delete books (librarians only)
- Search books by title, author, or genre
- Track total copies vs. available copies

### 👥 User Management
- Librarians can add and delete member/librarian accounts
- Members can view only their own profile and loan history

### 📋 Loan / Issue System
- Issue books to members with a configurable due date (default: 14 days)
- Return tracking with automatic copy count adjustment
- Loan detail view with overdue day and fine calculation

### ⚠️ Overdue Management
- Automatic overdue status detection on every request
- Send overdue notifications with fine calculation (₹2/day)
- Full notification history log

### 📊 Reports (Librarian Only)
- Top 10 most borrowed books
- Top 10 most active users
- Monthly loan statistics (last 12 months)
- Total outstanding fines

---

## 📁 Project Structure

```
bookstack/
├── app.py                  # Main Flask application (routes, DB logic)
├── database.db             # Auto-generated SQLite database
├── requirements.txt        # Python dependencies
├── static/
│   └── style.css           # Global stylesheet
├── templates/
│   ├── base.html           # Base layout with navigation
│   ├── login.html          # Login page
│   ├── index.html          # Dashboard
│   ├── books.html          # Book catalogue & management
│   ├── users.html          # User list (librarian only)
│   ├── user_detail.html    # Individual user profile & loan history
│   ├── issue.html          # Issue a book to a member
│   ├── loans.html          # All loans (filterable by status)
│   ├── loan_detail.html    # Single loan detail
│   ├── overdue.html        # Overdue loans & notifications
│   └── reports.html        # Analytics & reports
├── SETUP AND RUN.md        # Detailed setup guide
└── README.md               # This file
```

---

## 🗃️ Database Schema

```
books
  book_id, title, author, genre, isbn, total_copies, available_copies, added_date

users
  user_id, name, email, phone, role, password, joined_date

loans
  loan_id, book_id*, user_id*, issue_date, due_date, return_date, status

overdue_notifications
  notif_id, loan_id*, notified_date, message
```

> `*` Foreign key references. `PRAGMA foreign_keys = ON` is enforced at runtime.

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/vipulahire1357-png/BookStack_LibraryManagementSystem.git
cd BookStack_LibraryManagementSystem
```

### 2. Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the App
```bash
python app.py
```

Open **http://localhost:5000** in your browser.  
The database is **auto-created and seeded** on first launch.

---

## 🔐 Default Login Credentials

### Librarian (Full Access)
| Email | Password |
|-------|----------|
| arjun@example.com | admin123 |
| kiran@example.com | admin123 |

### Member (Limited Access)
| Email | Password |
|-------|----------|
| priya@example.com | password123 |
| rahul@example.com | password123 |
| sneha@example.com | password123 |

---

## 🛡️ Role Permissions

| Feature                  | Librarian | Member         |
|--------------------------|:---------:|:--------------:|
| Dashboard                | ✅ All    | ✅ Own only    |
| View & Search Books      | ✅        | ✅             |
| Add / Edit / Delete Books| ✅        | ❌             |
| View All Users           | ✅        | ❌             |
| View Own Profile         | ✅        | ✅             |
| Issue Books              | ✅        | ❌             |
| View All Loans           | ✅        | ❌ (own only)  |
| Mark Books Returned      | ✅        | ❌             |
| Overdue Management       | ✅        | ❌             |
| Reports & Analytics      | ✅        | ❌             |

---

## 🔄 Resetting the Database

```bash
# Delete the existing database
del database.db        # Windows
rm database.db         # macOS / Linux

# Restart the app — DB is re-created and re-seeded automatically
python app.py
```

---

## 🐛 Common Issues

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: flask` | Run `pip install flask` |
| Port 5000 already in use | Change to `app.run(debug=True, port=5001)` in `app.py` |
| PowerShell venv permission error | Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |

---

## 📄 License

This project is intended for **educational / college project** purposes.

---

> 📘 For detailed setup instructions, see [SETUP AND RUN.md](./SETUP%20AND%20RUN.md)
