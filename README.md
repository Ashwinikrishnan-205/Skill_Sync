<h1 align="center">Skill Sync – Online Learning & Task Management System</h1>

<p align="center">
A role-based learning and task management platform built using <strong>Python (Streamlit)</strong> and <strong>MySQL</strong>.  
Designed to support students in learning, experts in mentoring, and administrators in managing the platform efficiently.
</p>

---

## Key Features

### Student Panel
- User registration and login
- Browse and enroll in courses
- Submit tasks with text or file upload
- View expert feedback and ratings
- Personal dashboard with learning analytics

### Expert Panel
- Create and manage tasks for assigned courses
- Review student submissions
- Provide feedback and ratings
- View course engagement analytics

### Admin Panel
- Manage users and courses
- Assign experts to courses
- Delete users and courses with complete data cascading
- View platform-wide analytics and insights

---

## Technology Stack

| Layer | Technology |
|------|-----------|
| Frontend | Streamlit (Python) |
| Backend | Python |
| Database | MySQL |
| Data Handling | Pandas |
| Data Visualization | Matplotlib |

---

## Database Schema (ER Model Summary)

| Table | Description |
|------|------------|
| `users` | Stores student, expert, and admin information |
| `courses` | Course details |
| `enrollments` | Student-to-course relationship |
| `tasks` | Tasks created by experts for courses |
| `submissions` | Student submissions |
| `feedback` | Expert reviews and ratings |

Designed with referential integrity using `ON DELETE CASCADE` and `SET NULL`.

---

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Ashwinikrishnan-205/Skill_Sync.git
cd Skill_Sync
