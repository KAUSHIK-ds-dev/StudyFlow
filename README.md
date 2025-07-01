
🎓 Higher Study Management System

A multi-user web application designed to help students manage and track their higher education applications. This platform allows students to store course/university data, upload necessary documents, and track progress — while administrators manage users and data visibility.

🔧 Features

  1. User Roles: Supports both students and admins with role-based access.
  2. Secure Authentication: Login and registration system with password hashing.
  3. Document Management: Upload and manage SOPs, LORs, and other supporting documents.
  4. University & Course Tracking: Maintain details of target universities, deadlines, and courses.
  5. Interactive Dashboard: View application progress, statuses, and pending items.
  6. Session Management: Uses Flask-Login for user sessions and secure routing.


🛠️ Tech Stack

     Backend  | Flask, Flask-SQLAlchemy, Flask-Login 
     Frontend | HTML, CSS, Bootstrap, Jinja2         
     Database | SQLite (via SQLAlchemy ORM)          
     Others   | WTForms, Werkzeug, Python-Dateutil   

📂 Project Structure

        project/
        ├── app.py               # Main Flask app
        ├── templates/           # HTML templates (Jinja2)
        ├── static/              # Static files: CSS, JS, uploads
        ├── requirements.txt     # Project dependencies
        └── ...

🚀 Setup Instructions

1. Clone the repository
   bash
   git clone <your-repo-url>
   cd project
   
2. Set up a virtual environment
     bash
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies
     bash
     pip install -r requirements.txt

4. Run the app
     bash
     python app.py
   
5. Visit `http://localhost:5000` in your browser.

