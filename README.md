# Skill Sync – Online Learning & Task Management System

Skill Sync is a learning platform built using Python, Streamlit, and MySQL.  
It allows students to enroll in courses, complete tasks, and receive expert feedback, while experts and admins manage the platform.

---

## Features

### Student
- Register and log in
- Browse and enroll in courses
- Submit tasks with text or file
- View expert feedback and ratings
- Performance analytics dashboard

### Expert
- Manage and create tasks for assigned courses
- Review student submissions
- Give feedback and ratings
- Analytics on course engagement

### Admin
- Manage users and courses
- View platform-wide analytics and engagement statistics

---

## Tech Stack

| Component | Technology |
|----------|------------|
Frontend | Streamlit (Python)
Backend | Python
Database | MySQL
Data Handling | Pandas
Visualization | Matplotlib

---

## Database Structure (ER Model Summary)

**Tables:**
- `users` — stores student, expert, and admin details
- `courses` — course information
- `enrollments` — student-to-course mapping
- `tasks` — tasks assigned to courses
- `submissions` — student submissions
- `feedback` — expert feedback on submissions

---

## Installation & Setup

### 1. Clone the repository
```sh
git clone https://github.com/Ashwinikrishnan-205/Skill_Sync.git
cd Skill_Sync
