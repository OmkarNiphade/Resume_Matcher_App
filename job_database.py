import sqlite3

def create_job_table():
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    company TEXT,
                    location TEXT,
                    post_date TEXT
                )''')
    conn.commit()
    conn.close()

def add_job(title, description, company, location, post_date):
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute("INSERT INTO jobs (title, description, company, location, post_date) VALUES (?, ?, ?, ?, ?)",
              (title, description, company, location, post_date))
    conn.commit()
    conn.close()

def get_all_jobs():
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute("SELECT * FROM jobs ORDER BY post_date DESC")
    jobs = c.fetchall()
    conn.close()
    return jobs
