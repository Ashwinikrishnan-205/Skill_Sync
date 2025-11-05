import streamlit as st
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import date

# Database connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  
        password="Ashwini205@",  
        database="skill_sync"
    )
# Helper Functions
def run_query(query, params=(), fetch=False):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, params)
    data = cur.fetchall() if fetch else None
    conn.commit()
    cur.close()
    conn.close()
    return data

def run_one(query, params=()):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, params)
    data = cur.fetchone()
    cur.close()
    conn.close()
    return data

def register_user(name, email, password, role, bio):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, email, password, role, bio) VALUES (%s,%s,%s,%s,%s)",
                (name, email, password, role, bio))
    conn.commit()
    cur.close()
    conn.close()

def login_user(email, password):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_all_courses():
    return run_query("SELECT * FROM courses", fetch=True)

def get_enrolled_courses(student_id):
    return run_query("""SELECT c.title, c.category, c.duration 
                        FROM enrollments e 
                        JOIN courses c ON e.course_id=c.course_id 
                        WHERE e.student_id=%s""", (student_id,), fetch=True)

def get_tasks_for_student(student_id):
    return run_query("""SELECT t.task_id, t.title AS task_title, c.title AS course_title, t.due_date 
                        FROM tasks t 
                        JOIN courses c ON t.course_id=c.course_id 
                        JOIN enrollments e ON e.course_id=c.course_id 
                        WHERE e.student_id=%s""", (student_id,), fetch=True)

def get_submissions_for_expert(expert_id):
    return run_query("""SELECT s.submission_id, s.text_answer, s.file_name, s.submission_date,
                        t.title AS task_title, c.title AS course_title, u.name AS student_name
                        FROM submissions s
                        JOIN tasks t ON s.task_id=t.task_id
                        JOIN courses c ON t.course_id=c.course_id
                        JOIN users u ON s.student_id=u.user_id
                        WHERE c.expert_id=%s ORDER BY s.submission_date DESC""",
                     (expert_id,), fetch=True)


def wrap_labels(labels, max_width):
    return ['\n'.join([label[i:i+max_width] for i in range(0, len(label), max_width)]) for label in labels]

# Page Config and CSS

st.set_page_config(page_title="Skill Sync", layout="wide")

st.markdown("""
<style>
body {font-family: 'Segoe UI', sans-serif;}
.header {text-align:center; font-size:38px; font-weight:700; color:#0b5ed7; margin-bottom:4px;}
.subheader {text-align:center; font-size:18px; color:#555; margin-bottom:25px;}
.section-title {font-size:22px; color:#0b5ed7; margin-top:20px; margin-bottom:12px; font-weight:600;}
.card {background-color:#f8f9fa; padding:15px; border-radius:10px; margin-bottom:10px; box-shadow:0px 2px 5px rgba(0,0,0,0.1);}
.metric {display:inline-block; text-align:center; margin:10px; padding:10px 20px; background:#f8f9fa; border-radius:8px; font-weight:600; font-size:16px;}
.small {font-size:13px; color:#666;}
</style>
""", unsafe_allow_html=True)

# Student Dashboard

def student_dashboard(user):
    uid = user["user_id"]
    menu = ["Browse Courses", "My Courses", "Submit Task", "View Feedback", "Analytics"]
    choice = st.sidebar.radio("Student Menu", menu)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if choice == "Browse Courses":
        st.markdown("<div class='section-title'>Available Courses</div>", unsafe_allow_html=True)
        courses = get_all_courses()
        if not courses:
            st.info("No courses available yet.")
        else:
            for c in courses:
                st.markdown(f"<div class='card'><b>{c['title']}</b><div class='small'>Category: {c['category']} • Duration: {c['duration']} days • ₹{c['price']}</div>"
                            f"<div style='margin-top:8px'>{c['description'] or ''}</div></div>", unsafe_allow_html=True)
                enrolled = run_one("SELECT 1 FROM enrollments WHERE student_id=%s AND course_id=%s", (uid, c["course_id"]))
                if enrolled:
                    if st.button(f"Unenroll — {c['title']}", key=f"unenroll_{c['course_id']}"):
                        cur.execute("DELETE FROM enrollments WHERE student_id=%s AND course_id=%s", (uid, c["course_id"]))
                        conn.commit()
                        st.success(f"Unenrolled from {c['title']}")
                        try: st.rerun()
                        except: st.experimental_rerun()
                else:
                    if st.button(f"Enroll — {c['title']}", key=f"enroll_{c['course_id']}"):
                        cur.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s,%s)", (uid, c["course_id"]))
                        conn.commit()
                        st.success(f"Enrolled in {c['title']}")
                        try: st.rerun()
                        except: st.experimental_rerun()

    elif choice == "My Courses":
        st.markdown("<div class='section-title'>My Courses</div>", unsafe_allow_html=True)
        rows = get_enrolled_courses(uid)
        if not rows:
            st.info("You have not enrolled in any courses yet.")
        else:
            df = pd.DataFrame(rows)
            st.table(df[["title", "category", "duration"]])

    elif choice == "Submit Task":
        st.markdown("<div class='section-title'>Submit Task</div>", unsafe_allow_html=True)
        tasks = get_tasks_for_student(uid)
        if not tasks:
            st.info("No tasks available for your courses.")
        else:
            labels = [f"{t['task_title']} — {t['course_title']} (Due: {t['due_date']})" for t in tasks]
            sel = st.selectbox("Select Task", labels)
            task = tasks[labels.index(sel)]
            text_ans = st.text_area("Answer or paste link")
            uploaded = st.file_uploader("Attach file (optional)")
            if st.button("Submit"):
                if (not text_ans.strip()) and not uploaded:
                    st.warning("Please provide an answer or attach a file.")
                else:
                    fname = None
                    if uploaded:
                        os.makedirs("uploads", exist_ok=True)
                        fname = uploaded.name
                        with open(os.path.join("uploads", fname), "wb") as f:
                            f.write(uploaded.getbuffer())
                    cur.execute("INSERT INTO submissions (student_id, task_id, text_answer, file_name, submission_date) VALUES (%s,%s,%s,%s,%s)",
                                (uid, task["task_id"], text_ans.strip() or None, fname, date.today()))
                    conn.commit()
                    st.success("Submission saved.")
                    try: st.rerun()
                    except: st.experimental_rerun()

    elif choice == "View Feedback":
        st.markdown("<div class='section-title'>Feedback Received</div>", unsafe_allow_html=True)
        rows = run_query("""SELECT c.title AS course, t.title AS task, f.feedback_text, f.rating, f.feedback_date
                             FROM feedback f
                             JOIN submissions s ON f.submission_id=s.submission_id
                             JOIN tasks t ON s.task_id=t.task_id
                             JOIN courses c ON t.course_id=c.course_id
                             WHERE s.student_id=%s ORDER BY f.feedback_date DESC""", (uid,), fetch=True)
        if not rows:
            st.info("No feedback yet.")
        else:
            for r in rows:
                st.markdown(f"<div class='card'><b>{r['task']}</b> — <div class='small'>{r['course']} • {r['feedback_date']}</div>"
                            f"<div style='margin-top:6px'>{r['feedback_text'] or ''}</div><div style='margin-top:8px'><b>Rating:</b> {r['rating']}/5</div></div>", unsafe_allow_html=True)

    elif choice == "Analytics":
        st.markdown("<div class='section-title'>My Analytics</div>", unsafe_allow_html=True)

        total_courses = run_one("SELECT COUNT(*) AS c FROM enrollments WHERE student_id=%s", (uid,)).get('c', 0)
        total_tasks = run_one("""SELECT COUNT(t.task_id) AS c FROM tasks t 
                             JOIN enrollments e ON t.course_id=e.course_id 
                             WHERE e.student_id=%s""", (uid,)).get('c', 0)
        total_sub = run_one("SELECT COUNT(*) AS c FROM submissions WHERE student_id=%s", (uid,)).get('c', 0)

        progress = round(min((total_sub / total_tasks) * 100, 100), 1) if total_tasks > 0 else 0.0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Courses", total_courses)
        col2.metric("Tasks", total_tasks)
        col3.metric("Submitted", total_sub)
        col4.metric("Progress", f"{progress}%")

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(["Assigned", "Submitted"], [total_tasks, total_sub], color=['#0b5ed7', '#6c757d'])
        ax.set_ylabel("Count")
        ax.set_title("Task Progress")
        for i, v in enumerate([total_tasks, total_sub]):
            ax.text(i, v + 0.02, str(v), ha='center')
        plt.tight_layout()
        st.pyplot(fig)
        
# Expert Dashboard

def expert_dashboard(user):
    uid = user["user_id"]
    menu = ["Manage Tasks", "Review Submissions", "Analytics"]
    if "expert_menu" not in st.session_state:
        st.session_state["expert_menu"] = menu[0]
    choice = st.sidebar.radio("Expert Menu", menu, index=menu.index(st.session_state["expert_menu"]))
    st.session_state["expert_menu"] = choice

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if choice == "Manage Tasks":
        st.markdown("<div class='section-title'>Create Task</div>", unsafe_allow_html=True)
        courses = run_query("SELECT course_id, title FROM courses WHERE expert_id=%s", (uid,), fetch=True)
        if not courses:
            st.info("No courses assigned.")
        else:
            mapping = {c['title']: c['course_id'] for c in courses}
            sel = st.selectbox("Select Course", list(mapping.keys()))
            title = st.text_input("Task Title", key="task_title_expert")
            desc = st.text_area("Task Description", key="task_desc_expert")
            due = st.date_input("Due Date")

            if st.button("Add Task", key="add_task_btn"):
                if not title.strip():
                    st.warning("Provide a task title.")
                else:
                    run_query("INSERT INTO tasks (course_id, title, description, due_date) VALUES (%s,%s,%s,%s)",
                          (mapping[sel], title.strip(), desc.strip(), due))
                    st.success("Task added successfully.")
                    st.experimental_rerun() 

            tasks = run_query("SELECT task_id, title FROM tasks WHERE course_id=%s", (mapping[sel],), fetch=True)
            if tasks:
                st.markdown("### Existing Tasks")
                for t in tasks:
                    st.markdown(f"- {t['title']}")
                    if st.button(f"Delete — {t['title']}", key=f"del_task_{t['task_id']}"):
                        run_query("DELETE FROM tasks WHERE task_id=%s", (t['task_id'],))
                        st.success(f"Deleted task: {t['title']}")
                        st.experimental_rerun() 

    elif choice == "Review Submissions":
        st.markdown("<div class='section-title'>Review Submissions</div>", unsafe_allow_html=True)
        subs = get_submissions_for_expert(uid)
        if not subs:
            st.info("No submissions yet.")
        else:
            sel_label = st.selectbox(
              "Select Submission", 
              [f"{s['student_name']} — {s['task_title']}" for s in subs]
            )
            s = subs[[f"{x['student_name']} — {x['task_title']}" for x in subs].index(sel_label)]
        
            st.markdown(
                f"<div class='card'><b>{s['task_title']}</b><div class='small'>Course: {s['course_title']}</div>"
                f"<div style='margin-top:8px'>{s['text_answer'] or ''}</div>"
                f"<div class='small'>File: {s['file_name'] or '—'}</div></div>", 
                unsafe_allow_html=True
            )
       
            fb = st.text_area("Feedback", key=f"fb_{s['submission_id']}")
            rating = st.slider("Rating (1-5)", 1, 5, 4, key=f"rt_{s['submission_id']}")

            if st.button("Save Feedback", key=f"savefb_{s['submission_id']}"):
                run_query("DELETE FROM feedback WHERE submission_id=%s", (s['submission_id'],))
                run_query(
                    "INSERT INTO feedback (submission_id, expert_id, feedback_text, rating, feedback_date) VALUES (%s,%s,%s,%s,%s)",
                    (s['submission_id'], uid, fb.strip() or None, rating, date.today())
                )
                st.success("Feedback saved successfully.")
                st.experimental_rerun()  
            if st.button("Delete Submission", key=f"del_{s['submission_id']}"):
                run_query("DELETE FROM submissions WHERE submission_id=%s", (s['submission_id'],))
                st.success("Submission deleted.")
                st.experimental_rerun()

    elif choice == "Analytics":
        st.markdown("<div class='section-title'>Expert Analytics</div>", unsafe_allow_html=True)
        data = run_query("""SELECT c.title, COUNT(e.student_id) AS students
                            FROM courses c LEFT JOIN enrollments e ON c.course_id=e.course_id
                            WHERE c.expert_id=%s
                            GROUP BY c.course_id""", (uid,), fetch=True)
        if not data:
            st.info("No analytics yet.")
        else:
            df = pd.DataFrame(data)
            df.columns = ["title", "students"]
            st.table(df)
            fig, ax = plt.subplots(figsize=(7, max(3, len(df)*0.5)))
            ax.barh(wrap_labels(df['title'], 30), df['students'], color='#0b5ed7')
            ax.set_xlabel("Students")
            ax.set_title("Students per Course")
            plt.tight_layout()
            st.pyplot(fig)

    cur.close()
    conn.close()

# Admin Dashboard

def admin_dashboard(user):
    uid = user["user_id"]
    menu = ["Manage Users", "Manage Courses", "Analytics Overview"]
    if "admin_menu" not in st.session_state:
        st.session_state["admin_menu"] = menu[0]
    choice = st.sidebar.radio("Admin Menu", menu, index=menu.index(st.session_state["admin_menu"]))
    st.session_state["admin_menu"] = choice

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if choice == "Manage Users":
        st.markdown("<div class='section-title'>Manage Users</div>", unsafe_allow_html=True)
        users = run_query("SELECT user_id, name, email, role FROM users", fetch=True)
        if users:
            df = pd.DataFrame(users)
            df.columns = ["user_id", "name", "email", "role"]
            st.table(df[["user_id", "name", "email", "role"]])

            uid_del = st.number_input("Enter User ID to delete", min_value=1, step=1)
            if st.button("Delete User"):
                run_query("DELETE FROM feedback WHERE expert_id=%s", (uid_del,))
                subs = run_query("SELECT submission_id FROM submissions WHERE student_id=%s", (uid_del,), fetch=True)
                for s in subs:
                    run_query("DELETE FROM feedback WHERE submission_id=%s", (s["submission_id"],))
                run_query("DELETE FROM submissions WHERE student_id=%s", (uid_del,))
                run_query("DELETE FROM enrollments WHERE student_id=%s", (uid_del,))
                courses = run_query("SELECT course_id FROM courses WHERE expert_id=%s", (uid_del,), fetch=True)
                for c in courses:
                    run_query("DELETE FROM enrollments WHERE course_id=%s", (c["course_id"],))
                    tasks = run_query("SELECT task_id FROM tasks WHERE course_id=%s", (c["course_id"],), fetch=True)
                    for t in tasks:
                        run_query("DELETE FROM feedback WHERE submission_id IN (SELECT submission_id FROM submissions WHERE task_id=%s)", (t["task_id"],))
                        run_query("DELETE FROM submissions WHERE task_id=%s", (t["task_id"],))
                    run_query("DELETE FROM tasks WHERE course_id=%s", (c["course_id"],))
                    run_query("DELETE FROM courses WHERE course_id=%s", (c["course_id"],))
                run_query("DELETE FROM users WHERE user_id=%s", (uid_del,))
                st.success("User and related data deleted successfully.")
                st.rerun()
        else:
            st.info("No users found.")
    elif choice == "Manage Courses":
        st.markdown("<div class='section-title'>Manage Courses</div>", unsafe_allow_html=True)
        courses = run_query("SELECT course_id, title, category FROM courses", fetch=True)
        if courses:
            df = pd.DataFrame(courses)
            df.columns = ["course_id", "title", "category"]
            st.table(df[["course_id", "title", "category"]])

            del_id = st.number_input("Enter Course ID to delete", min_value=1, step=1)
            if st.button("Delete Course"):
                run_query("DELETE FROM courses WHERE course_id=%s", (del_id,))
                st.success("Course deleted successfully.")
                st.rerun()
        else:
            st.info("No courses found.")

        st.markdown("<div class='section-title'>Add New Course</div>", unsafe_allow_html=True)
        title = st.text_input("Course Title")
        desc = st.text_area("Description")
        cat = st.text_input("Category")
        dur = st.number_input("Duration (days)", min_value=1, step=1)
        price = st.number_input("Price (₹)", min_value=0.0, step=0.5)

        experts = run_query("SELECT user_id, name FROM users WHERE role='expert'", fetch=True)
        if experts:
            mapping = {e["name"]: e["user_id"] for e in experts}
            sel = st.selectbox("Assign Expert", list(mapping.keys()))
            if st.button("Add Course"):
                run_query(
                    "INSERT INTO courses (title, description, category, duration, price, expert_id) VALUES (%s,%s,%s,%s,%s,%s)",
                    (title.strip(), desc.strip(), cat.strip(), int(dur), float(price), mapping[sel])
                )
                st.success("Course added successfully.")
                st.rerun()
        else:
            st.info("No experts available to assign courses.")
    elif choice == "Analytics Overview":
        st.markdown("<div class='section-title'>Platform Analytics</div>", unsafe_allow_html=True)
    
        students = run_one("SELECT COUNT(*) AS c FROM users WHERE role='student'")["c"]
        experts = run_one("SELECT COUNT(*) AS c FROM users WHERE role='expert'")["c"]
        courses = run_one("SELECT COUNT(*) AS c FROM courses")["c"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Students", students)
        col2.metric("Experts", experts)
        col3.metric("Courses", courses)
        fig, ax = plt.subplots()
        ax.bar(["Students", "Experts", "Courses"], [students, experts, courses],
               color=["#0b5ed7", "#6c757d", "#0b5ed7"])
        ax.set_ylabel("Count")
        ax.set_title("Platform Overview")
        st.pyplot(fig)

    cur.close()
    conn.close()

# Login / Register Page

def login_register_page():
    choice = st.radio("Select Option", ["Login", "Register"], horizontal=True)

    if choice == "Login":
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login"):
            user = login_user(email, password)
            if user:
                st.session_state["user"] = {
                    "user_id": user["user_id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                    "bio": user.get("bio", "")
                }
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")
    else:
        st.subheader("Register")
        name = st.text_input("Full Name", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pw")
        role = st.selectbox("Role", ["student", "expert", "admin"], key="reg_role")
        bio = st.text_area("Short Bio (optional)", key="reg_bio")
        if st.button("Register"):
            if not (name.strip() and email.strip() and password.strip()):
                st.warning("Please fill in all required fields.")
            else:
                try:
                    register_user(name.strip(), email.strip(), password.strip(), role, bio.strip())
                    st.success("Account created successfully. Please login.")
                    st.rerun()
                except mysql.connector.IntegrityError:
                    st.error("Email already exists. Please use a different email.")

def main():
    st.markdown("<div style='text-align:center'><h1 class='header'>Skill Sync</h1><div class='subheader'>Empowering Learners & Experts through Skill Development</div></div>", unsafe_allow_html=True)

    if "user" not in st.session_state:
        st.session_state["user"] = None

    if st.session_state["user"]:
        user = st.session_state["user"]
        st.sidebar.markdown("### Account")
        st.sidebar.write(f"{user['name']}")
        st.sidebar.write(f"Role: {user['role'].capitalize()}")
        if st.sidebar.button("Logout"):
            st.session_state["user"] = None
            st.rerun()

        if user["role"] == "student":
            student_dashboard(user)
        elif user["role"] == "expert":
            expert_dashboard(user)
        elif user["role"] == "admin":
            admin_dashboard(user)

    else:
        login_register_page()


if __name__ == "__main__":
    main()