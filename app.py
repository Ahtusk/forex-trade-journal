from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import timedelta
import sqlite3

app = Flask(__name__)

app.secret_key = "forex_secret_key"

# Login 30 days tak save rahega
app.permanent_session_lifetime = timedelta(days=30)


# ---------- Database ----------
def init_db():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # Trades table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trades(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        trade_date TEXT,
        pair_name TEXT,
        trade_type TEXT,
        mistake TEXT,
        amount REAL
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------- Login ----------
@app.route("/", methods=["GET", "POST"])
def login():

    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cur.fetchone()

        conn.close()

        if user:

            session["user"] = email
            session.permanent = True

            return redirect(url_for("dashboard"))

        else:

            flash("Invalid Email or Password")

    return render_template("login.html")


# ---------- Register ----------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        try:

            conn = sqlite3.connect("database.db")
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO users(email,password) VALUES(?,?)",
                (email, password)
            )

            conn.commit()
            conn.close()

            flash("Account Created Successfully!")

            return redirect(url_for("login"))

        except:

            flash("Email already exists!")

    return render_template("register.html")


# ---------- Forgot Password ----------
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]
        new_password = request.form["new_password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cur.fetchone()

        if user:

            cur.execute(
                "UPDATE users SET password=? WHERE email=?",
                (new_password, email)
            )

            conn.commit()

            flash("Password Updated Successfully!")

        else:

            flash("Email not found!")

        conn.close()

        return redirect(url_for("login"))

    return render_template("forgot_password.html")


# ---------- Dashboard ----------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Total Trades
    cur.execute(
        "SELECT COUNT(*) FROM trades WHERE user_email=?",
        (user_email,)
    )

    total_trades = cur.fetchone()[0]

    # Winning Trades
    cur.execute(
        "SELECT COUNT(*) FROM trades WHERE user_email=? AND amount > 0",
        (user_email,)
    )

    winning_trades = cur.fetchone()[0]

    # Losing Trades
    cur.execute(
        "SELECT COUNT(*) FROM trades WHERE user_email=? AND amount < 0",
        (user_email,)
    )

    losing_trades = cur.fetchone()[0]

    # Total Profit
    cur.execute(
        "SELECT SUM(amount) FROM trades WHERE user_email=?",
        (user_email,)
    )

    result = cur.fetchone()[0]

    total_profit = result if result else 0

    conn.close()

    # Win Rate
    if total_trades > 0:

        win_rate = round(
            (winning_trades / total_trades) * 100,
            1
        )

    else:

        win_rate = 0

    return render_template(
        "dashboard.html",
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        total_profit=total_profit,
        win_rate=win_rate
    )


# ---------- Trade Journal ----------
@app.route("/journal", methods=["GET", "POST"])
def journal():

    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":

        trade_date = request.form["trade_date"]
        pair_name = request.form["pair_name"]
        trade_type = request.form["trade_type"]
        mistake = request.form["mistake"]
        amount = float(request.form["amount"])

        cur.execute(
            """
            INSERT INTO trades
            (user_email, trade_date, pair_name, trade_type, mistake, amount)
            VALUES(?,?,?,?,?,?)
            """,
            (
                user_email,
                trade_date,
                pair_name,
                trade_type,
                mistake,
                amount
            )
        )

        conn.commit()

    # User ke trades show karo
    cur.execute(
        """
        SELECT trade_date,
               pair_name,
               trade_type,
               mistake,
               amount
        FROM trades
        WHERE user_email=?
        ORDER BY id DESC
        """,
        (user_email,)
    )

    trades = cur.fetchall()

    conn.close()

    return render_template("journal.html", trades=trades)


# ---------- Logout ----------
@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect(url_for("login"))


# ---------- Run App ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)