import sqlite3
import os
from datetime import date, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, g, session

app = Flask(__name__)
app.secret_key = 'bookstack_secret_2026'

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            book_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT NOT NULL,
            author        TEXT NOT NULL,
            genre         TEXT,
            isbn          TEXT UNIQUE,
            total_copies  INTEGER DEFAULT 1,
            available_copies INTEGER DEFAULT 1,
            added_date    TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            phone         TEXT,
            role          TEXT DEFAULT 'member',
            password      TEXT DEFAULT 'password123',
            joined_date   TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS loans (
            loan_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id       INTEGER NOT NULL,
            user_id       INTEGER NOT NULL,
            issue_date    TEXT DEFAULT (date('now')),
            due_date      TEXT NOT NULL,
            return_date   TEXT,
            status        TEXT DEFAULT 'active',
            FOREIGN KEY (book_id) REFERENCES books(book_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS overdue_notifications (
            notif_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id       INTEGER NOT NULL,
            notified_date TEXT DEFAULT (date('now')),
            message       TEXT,
            FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
        );
    """)
    db.commit()

    # Seed if empty
    count = db.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if count == 0:
        today = date.today()
        past_14 = (today - timedelta(days=14)).isoformat()
        past_20 = (today - timedelta(days=20)).isoformat()
        past_5  = (today - timedelta(days=5)).isoformat()
        past_30 = (today - timedelta(days=30)).isoformat()
        past_10 = (today - timedelta(days=10)).isoformat()
        due_past_5  = (today - timedelta(days=5)).isoformat()
        due_past_3  = (today - timedelta(days=3)).isoformat()
        due_future7 = (today + timedelta(days=7)).isoformat()
        due_future3 = (today + timedelta(days=3)).isoformat()
        returned_date = (today - timedelta(days=2)).isoformat()

        books = [
            ("The Name of the Wind", "Patrick Rothfuss", "Fiction", "978-0756404741", 3, 2),
            ("Sapiens: A Brief History", "Yuval Noah Harari", "History", "978-0062316097", 2, 2),
            ("Clean Code", "Robert C. Martin", "Technology", "978-0132350884", 4, 3),
            ("Cosmos", "Carl Sagan", "Science", "978-0345331359", 2, 1),
            ("Dune", "Frank Herbert", "Fiction", "978-0441013593", 3, 3),
            ("A Brief History of Time", "Stephen Hawking", "Science", "978-0553380163", 2, 2),
            ("The Pragmatic Programmer", "Andrew Hunt", "Technology", "978-0201616224", 3, 2),
            ("Guns, Germs and Steel", "Jared Diamond", "History", "978-0393317558", 2, 2),
            ("1984", "George Orwell", "Fiction", "978-0451524935", 5, 4),
            ("The Design of Everyday Things", "Don Norman", "Technology", "978-0465050659", 2, 2),
        ]
        db.executemany(
            "INSERT INTO books (title, author, genre, isbn, total_copies, available_copies) VALUES (?,?,?,?,?,?)",
            books
        )

        # Seeded users with passwords
        # librarian: arjun@example.com / admin123
        # members:   priya@example.com / password123  etc.
        users = [
            ("Arjun Mehta",  "arjun@example.com",  "9876543210", "librarian", "admin123"),
            ("Priya Sharma", "priya@example.com",  "9123456780", "member",    "password123"),
            ("Rahul Verma",  "rahul@example.com",  "9988776655", "member",    "password123"),
            ("Sneha Patil",  "sneha@example.com",  "9001122334", "member",    "password123"),
            ("Kiran Desai",  "kiran@example.com",  "9876001234", "librarian", "admin123"),
        ]
        db.executemany(
            "INSERT INTO users (name, email, phone, role, password) VALUES (?,?,?,?,?)",
            users
        )

        loans = [
            (1, 2, past_14, due_past_5, None, "overdue"),
            (3, 3, past_20, due_past_3, None, "overdue"),
            (7, 4, past_10, due_future7, None, "active"),
            (9, 5, past_30, (today - timedelta(days=10)).isoformat(), returned_date, "returned"),
            (4, 2, past_5, due_future3, None, "active"),
        ]
        db.executemany(
            "INSERT INTO loans (book_id, user_id, issue_date, due_date, return_date, status) VALUES (?,?,?,?,?,?)",
            loans
        )

        notifs = [
            (1, past_5, "Reminder: 'The Name of the Wind' is overdue by 5 days. Please return immediately."),
            (2, past_5, "Reminder: 'Clean Code' is overdue by 3 days. Please return immediately."),
        ]
        db.executemany(
            "INSERT INTO overdue_notifications (loan_id, notified_date, message) VALUES (?,?,?)",
            notifs
        )
        db.commit()

def update_overdue_status():
    db = get_db()
    today = date.today().isoformat()
    db.execute("""
        UPDATE loans SET status = 'overdue'
        WHERE status = 'active' AND due_date < ?
    """, (today,))
    db.commit()

@app.before_request
def before_request():
    init_db()

# ─── AUTH HELPERS ─────────────────────────────────────────────────────────────

def login_required(f):
    """Redirect to login if not logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def librarian_required(f):
    """Restrict to librarians only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        if session.get('role') != 'librarian':
            flash('Access denied — librarians only.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# ─── LOGIN / LOGOUT ──────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email    = request.form['email'].strip().lower()
        password = request.form['password']
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE LOWER(email)=? AND password=?", (email, password)
        ).fetchone()
        if user:
            session['user_id'] = user['user_id']
            session['name']    = user['name']
            session['role']    = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    update_overdue_status()
    db = get_db()
    total_books   = db.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    total_users   = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active_loans  = db.execute("SELECT COUNT(*) FROM loans WHERE status='active'").fetchone()[0]
    overdue_loans = db.execute("SELECT COUNT(*) FROM loans WHERE status='overdue'").fetchone()[0]

    # Members only see their own recent loans
    if session['role'] == 'member':
        recent_loans = db.execute("""
            SELECT l.loan_id, b.title, u.name, l.issue_date, l.due_date, l.status
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            JOIN users u ON l.user_id = u.user_id
            WHERE l.user_id = ?
            ORDER BY l.loan_id DESC LIMIT 10
        """, (session['user_id'],)).fetchall()
        overdue_alerts = db.execute("""
            SELECT l.loan_id, b.title, u.name, l.due_date,
                   CAST(julianday('now') - julianday(l.due_date) AS INTEGER) AS days_overdue
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            JOIN users u ON l.user_id = u.user_id
            WHERE l.status = 'overdue' AND l.user_id = ?
            ORDER BY days_overdue DESC
        """, (session['user_id'],)).fetchall()
    else:
        recent_loans = db.execute("""
            SELECT l.loan_id, b.title, u.name, l.issue_date, l.due_date, l.status
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            JOIN users u ON l.user_id = u.user_id
            ORDER BY l.loan_id DESC LIMIT 10
        """).fetchall()
        overdue_alerts = db.execute("""
            SELECT l.loan_id, b.title, u.name, l.due_date,
                   CAST(julianday('now') - julianday(l.due_date) AS INTEGER) AS days_overdue
            FROM loans l
            JOIN books b ON l.book_id = b.book_id
            JOIN users u ON l.user_id = u.user_id
            WHERE l.status = 'overdue'
            ORDER BY days_overdue DESC
        """).fetchall()

    return render_template('index.html',
        total_books=total_books, total_users=total_users,
        active_loans=active_loans, overdue_loans=overdue_loans,
        recent_loans=recent_loans, overdue_alerts=overdue_alerts)

# ─── BOOKS ────────────────────────────────────────────────────────────────────

@app.route('/books', methods=['GET', 'POST'])
@login_required
def books():
    db = get_db()
    if request.method == 'POST':
        # Only librarians can add/edit/delete
        if session['role'] != 'librarian':
            flash('Access denied.', 'error')
            return redirect(url_for('books'))
        action = request.form.get('action')
        if action == 'add':
            title   = request.form['title'].strip()
            author  = request.form['author'].strip()
            genre   = request.form.get('genre', '').strip()
            isbn    = request.form.get('isbn', '').strip() or None
            total   = int(request.form.get('total_copies', 1))
            try:
                db.execute(
                    "INSERT INTO books (title, author, genre, isbn, total_copies, available_copies) VALUES (?,?,?,?,?,?)",
                    (title, author, genre, isbn, total, total)
                )
                db.commit()
                flash(f'Book "{title}" added successfully!', 'success')
            except sqlite3.IntegrityError:
                flash('ISBN already exists in the database.', 'error')
        elif action == 'edit':
            book_id = request.form['book_id']
            title   = request.form['title'].strip()
            author  = request.form['author'].strip()
            genre   = request.form.get('genre', '').strip()
            isbn    = request.form.get('isbn', '').strip() or None
            total   = int(request.form.get('total_copies', 1))
            try:
                db.execute(
                    "UPDATE books SET title=?, author=?, genre=?, isbn=?, total_copies=? WHERE book_id=?",
                    (title, author, genre, isbn, total, book_id)
                )
                db.commit()
                flash('Book updated successfully!', 'success')
            except sqlite3.IntegrityError:
                flash('ISBN already exists in the database.', 'error')
        elif action == 'delete':
            book_id = request.form['book_id']
            active = db.execute(
                "SELECT COUNT(*) FROM loans WHERE book_id=? AND status IN ('active','overdue')", (book_id,)
            ).fetchone()[0]
            if active > 0:
                flash('Cannot delete book with active/overdue loans.', 'error')
            else:
                db.execute("DELETE FROM books WHERE book_id=?", (book_id,))
                db.commit()
                flash('Book deleted successfully.', 'success')
        return redirect(url_for('books'))

    q = request.args.get('q', '').strip()
    if q:
        like = f'%{q}%'
        all_books = db.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR genre LIKE ? ORDER BY title",
            (like, like, like)
        ).fetchall()
    else:
        all_books = db.execute("SELECT * FROM books ORDER BY title").fetchall()

    return render_template('books.html', books=all_books, q=q)

# ─── USERS ────────────────────────────────────────────────────────────────────

@app.route('/users', methods=['GET', 'POST'])
@librarian_required
def users():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name     = request.form['name'].strip()
            email    = request.form['email'].strip()
            phone    = request.form.get('phone', '').strip()
            role     = request.form.get('role', 'member')
            password = request.form.get('password', 'password123').strip() or 'password123'
            try:
                db.execute(
                    "INSERT INTO users (name, email, phone, role, password) VALUES (?,?,?,?,?)",
                    (name, email, phone, role, password)
                )
                db.commit()
                flash(f'User "{name}" added successfully!', 'success')
            except sqlite3.IntegrityError:
                flash('Email already registered.', 'error')
        elif action == 'delete':
            user_id = request.form['user_id']
            if int(user_id) == session['user_id']:
                flash('You cannot delete your own account.', 'error')
            else:
                active = db.execute(
                    "SELECT COUNT(*) FROM loans WHERE user_id=? AND status IN ('active','overdue')", (user_id,)
                ).fetchone()[0]
                if active > 0:
                    flash('Cannot delete user with active/overdue loans.', 'error')
                else:
                    db.execute("DELETE FROM users WHERE user_id=?", (user_id,))
                    db.commit()
                    flash('User deleted successfully.', 'success')
        return redirect(url_for('users'))

    all_users = db.execute("SELECT * FROM users ORDER BY name").fetchall()
    return render_template('users.html', users=all_users)

@app.route('/users/<int:user_id>')
@login_required
def user_detail(user_id):
    # Members can only see their own profile
    if session['role'] == 'member' and session['user_id'] != user_id:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('users'))
    loan_history = db.execute("""
        SELECT l.*, b.title, b.author
        FROM loans l JOIN books b ON l.book_id=b.book_id
        WHERE l.user_id=?
        ORDER BY l.loan_id DESC
    """, (user_id,)).fetchall()
    return render_template('user_detail.html', user=user, loan_history=loan_history)

# ─── ISSUE BOOK ───────────────────────────────────────────────────────────────

@app.route('/issue', methods=['GET', 'POST'])
@librarian_required
def issue():
    db = get_db()
    if request.method == 'POST':
        book_id  = request.form['book_id']
        user_id  = request.form['user_id']
        due_date = request.form['due_date']

        book = db.execute("SELECT * FROM books WHERE book_id=?", (book_id,)).fetchone()
        if not book or book['available_copies'] < 1:
            flash('Book is not available for issue.', 'error')
            return redirect(url_for('issue'))

        db.execute(
            "INSERT INTO loans (book_id, user_id, issue_date, due_date, status) VALUES (?,?,date('now'),?,'active')",
            (book_id, user_id, due_date)
        )
        db.execute("UPDATE books SET available_copies = available_copies - 1 WHERE book_id=?", (book_id,))
        db.commit()
        flash(f'Book "{book["title"]}" issued successfully! Due: {due_date}', 'success')
        return redirect(url_for('loans'))

    default_due = (date.today() + timedelta(days=14)).isoformat()
    all_users = db.execute("SELECT * FROM users ORDER BY name").fetchall()
    available_books = db.execute(
        "SELECT * FROM books WHERE available_copies > 0 ORDER BY title"
    ).fetchall()
    return render_template('issue.html', users=all_users, books=available_books, default_due=default_due)

# ─── LOANS ────────────────────────────────────────────────────────────────────

@app.route('/loans', methods=['GET', 'POST'])
@login_required
def loans():
    update_overdue_status()
    db = get_db()
    if request.method == 'POST':
        if session['role'] != 'librarian':
            flash('Access denied.', 'error')
            return redirect(url_for('loans'))
        loan_id = request.form['loan_id']
        loan = db.execute("SELECT * FROM loans WHERE loan_id=?", (loan_id,)).fetchone()
        if loan and loan['status'] in ('active', 'overdue'):
            db.execute(
                "UPDATE loans SET status='returned', return_date=date('now') WHERE loan_id=?",
                (loan_id,)
            )
            db.execute(
                "UPDATE books SET available_copies = available_copies + 1 WHERE book_id=?",
                (loan['book_id'],)
            )
            db.commit()
            flash('Book marked as returned successfully!', 'success')
        else:
            flash('Loan not found or already returned.', 'error')
        return redirect(url_for('loans'))

    status_filter = request.args.get('status', 'all')
    query = """
        SELECT l.loan_id, b.title, b.author, u.name, u.email,
               l.issue_date, l.due_date, l.return_date, l.status
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        JOIN users u ON l.user_id = u.user_id
    """
    # Members see only their own loans
    if session['role'] == 'member':
        base_where = f" WHERE l.user_id = {session['user_id']}"
        if status_filter in ('active', 'returned', 'overdue'):
            all_loans = db.execute(query + base_where + " AND l.status=? ORDER BY l.loan_id DESC", (status_filter,)).fetchall()
        else:
            all_loans = db.execute(query + base_where + " ORDER BY l.loan_id DESC").fetchall()
        uid = session['user_id']
        counts = {
            'all':      db.execute("SELECT COUNT(*) FROM loans WHERE user_id=?", (uid,)).fetchone()[0],
            'active':   db.execute("SELECT COUNT(*) FROM loans WHERE status='active' AND user_id=?", (uid,)).fetchone()[0],
            'returned': db.execute("SELECT COUNT(*) FROM loans WHERE status='returned' AND user_id=?", (uid,)).fetchone()[0],
            'overdue':  db.execute("SELECT COUNT(*) FROM loans WHERE status='overdue' AND user_id=?", (uid,)).fetchone()[0],
        }
    else:
        if status_filter in ('active', 'returned', 'overdue'):
            all_loans = db.execute(query + " WHERE l.status=? ORDER BY l.loan_id DESC", (status_filter,)).fetchall()
        else:
            all_loans = db.execute(query + " ORDER BY l.loan_id DESC").fetchall()
        counts = {
            'all':      db.execute("SELECT COUNT(*) FROM loans").fetchone()[0],
            'active':   db.execute("SELECT COUNT(*) FROM loans WHERE status='active'").fetchone()[0],
            'returned': db.execute("SELECT COUNT(*) FROM loans WHERE status='returned'").fetchone()[0],
            'overdue':  db.execute("SELECT COUNT(*) FROM loans WHERE status='overdue'").fetchone()[0],
        }
    return render_template('loans.html', loans=all_loans, status_filter=status_filter, counts=counts)

@app.route('/loans/<int:loan_id>', methods=['GET', 'POST'])
@login_required
def loan_detail(loan_id):
    db = get_db()
    if request.method == 'POST':
        if session['role'] != 'librarian':
            flash('Access denied.', 'error')
            return redirect(url_for('loan_detail', loan_id=loan_id))
        loan = db.execute("SELECT * FROM loans WHERE loan_id=?", (loan_id,)).fetchone()
        if loan and loan['status'] in ('active', 'overdue'):
            db.execute(
                "UPDATE loans SET status='returned', return_date=date('now') WHERE loan_id=?",
                (loan_id,)
            )
            db.execute(
                "UPDATE books SET available_copies = available_copies + 1 WHERE book_id=?",
                (loan['book_id'],)
            )
            db.commit()
            flash('Book returned successfully!', 'success')
        return redirect(url_for('loan_detail', loan_id=loan_id))

    loan = db.execute("""
        SELECT l.*, b.title, b.author, b.genre, b.isbn,
               u.name AS user_name, u.email, u.phone, u.role
        FROM loans l
        JOIN books b ON l.book_id=b.book_id
        JOIN users u ON l.user_id=u.user_id
        WHERE l.loan_id=?
    """, (loan_id,)).fetchone()
    if not loan:
        flash('Loan not found.', 'error')
        return redirect(url_for('loans'))

    # Members can only view their own loan details
    if session['role'] == 'member' and loan['user_id'] != session['user_id']:
        flash('Access denied.', 'error')
        return redirect(url_for('loans'))

    today = date.today().isoformat()
    days_overdue = 0
    if loan['status'] == 'overdue':
        from datetime import datetime
        due = datetime.strptime(loan['due_date'], '%Y-%m-%d').date()
        days_overdue = (date.today() - due).days
    return render_template('loan_detail.html', loan=loan, today=today, days_overdue=days_overdue)

# ─── OVERDUE ──────────────────────────────────────────────────────────────────

@app.route('/overdue', methods=['GET', 'POST'])
@librarian_required
def overdue():
    update_overdue_status()
    db = get_db()
    if request.method == 'POST':
        loan_id = request.form['loan_id']
        loan = db.execute("""
            SELECT l.*, b.title, u.name
            FROM loans l JOIN books b ON l.book_id=b.book_id
            JOIN users u ON l.user_id=u.user_id
            WHERE l.loan_id=?
        """, (loan_id,)).fetchone()
        if loan:
            from datetime import datetime
            due = datetime.strptime(loan['due_date'], '%Y-%m-%d').date()
            days = (date.today() - due).days
            fine = days * 2
            msg = (f"Overdue Notice: '{loan['title']}' borrowed by {loan['name']} "
                   f"is {days} day(s) overdue. Fine: ₹{fine}.")
            db.execute(
                "INSERT INTO overdue_notifications (loan_id, notified_date, message) VALUES (?, date('now'), ?)",
                (loan_id, msg)
            )
            db.commit()
            flash(f'Notification sent for loan #{loan_id}.', 'success')
        return redirect(url_for('overdue'))

    overdue_loans = db.execute("""
        SELECT l.loan_id, b.title, u.name, u.email, l.due_date,
               CAST(julianday('now') - julianday(l.due_date) AS INTEGER) AS days_overdue,
               CAST((julianday('now') - julianday(l.due_date)) * 2 AS INTEGER) AS fine
        FROM loans l
        JOIN books b ON l.book_id=b.book_id
        JOIN users u ON l.user_id=u.user_id
        WHERE l.status='overdue'
        ORDER BY days_overdue DESC
    """).fetchall()

    notifications = db.execute("""
        SELECT n.*, b.title, u.name
        FROM overdue_notifications n
        JOIN loans l ON n.loan_id=l.loan_id
        JOIN books b ON l.book_id=b.book_id
        JOIN users u ON l.user_id=u.user_id
        ORDER BY n.notif_id DESC
    """).fetchall()

    return render_template('overdue.html', overdue_loans=overdue_loans, notifications=notifications)

# ─── REPORTS ─────────────────────────────────────────────────────────────────

@app.route('/reports')
@librarian_required
def reports():
    db = get_db()
    top_books = db.execute("""
        SELECT b.title, b.author, COUNT(l.loan_id) AS borrow_count
        FROM books b LEFT JOIN loans l ON b.book_id=l.book_id
        GROUP BY b.book_id ORDER BY borrow_count DESC LIMIT 10
    """).fetchall()

    top_users = db.execute("""
        SELECT u.name, u.email, u.role, COUNT(l.loan_id) AS loan_count
        FROM users u LEFT JOIN loans l ON u.user_id=l.user_id
        GROUP BY u.user_id ORDER BY loan_count DESC LIMIT 10
    """).fetchall()

    monthly_stats = db.execute("""
        SELECT strftime('%Y-%m', issue_date) AS month, COUNT(*) AS total,
               SUM(CASE WHEN status='returned' THEN 1 ELSE 0 END) AS returned,
               SUM(CASE WHEN status='overdue' THEN 1 ELSE 0 END) AS overdue_count
        FROM loans
        GROUP BY month ORDER BY month DESC LIMIT 12
    """).fetchall()

    overdue_count = db.execute("SELECT COUNT(*) FROM loans WHERE status='overdue'").fetchone()[0]
    total_fine = db.execute("""
        SELECT COALESCE(SUM(CAST(julianday('now') - julianday(due_date) AS INTEGER) * 2), 0)
        FROM loans WHERE status='overdue'
    """).fetchone()[0]

    return render_template('reports.html',
        top_books=top_books, top_users=top_users,
        monthly_stats=monthly_stats,
        overdue_count=overdue_count, total_fine=total_fine)

if __name__ == '__main__':
    app.run(debug=True)
