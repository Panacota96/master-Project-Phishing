# Software Architecture - Phishing Awareness Training

## System Overview
The Phishing Awareness Training Application is a serverless Flask web application deployed on AWS.

```mermaid
flowchart TD
    subgraph "Frontend (Jinja2 + Bootstrap 5)"
        User[Browser]
    end
    
    subgraph "Backend (Flask)"
        Factory[App Factory app/__init__.py]
        Auth[Auth Blueprint]
        Quiz[Quiz Blueprint]
        Insp[Inspector Blueprint]
        Dash[Dashboard Blueprint]
        Models[Models app/models.py]
    end
    
    subgraph "Database (DynamoDB)"
        DB_Users[Users Table]
        DB_Quizzes[Quizzes Table]
        DB_Attempts[Attempts Table]
        DB_Responses[Responses Table]
        DB_Inspector[Inspector Table]
    end
    
    User <--> Factory
    Factory --> Auth & Quiz & Insp & Dash
    Auth & Quiz & Insp & Dash <--> Models
    Models <--> DB_Users & DB_Quizzes & DB_Attempts & DB_Responses & DB_Inspector
```

## Data Models (Entity Relationships)
The application uses **DynamoDB** as its primary NoSQL database. Logic for data access is centralized in `app/models.py`.

```mermaid
erDiagram
    USER ||--o{ ATTEMPT : completes
    QUIZ ||--o{ ATTEMPT : of
    ATTEMPT ||--o{ RESPONSE : contains
    USER ||--o{ INSPECTOR_ATTEMPT : submits
    
    USER {
        string username PK
        string email
        string password_hash
        string class_name
        string academic_year
        string major
        boolean is_admin
    }
    
    QUIZ {
        string quiz_id PK
        string title
        string description
        list questions
        string video_url
    }
    
    ATTEMPT {
        string username PK, FK
        string quiz_id PK, FK
        number score
        number total
        datetime completed_at
    }
    
    RESPONSE {
        string username_quiz_id PK, FK
        string question_id PK, FK
        string selected_answer_id
        boolean is_correct
    }
```

## Backend Architecture (Flask)
The app uses the Flask Application Factory pattern (`app/__init__.py`). It is adapted for AWS Lambda using the `mangum` adapter (`lambda_handler.py`).

### Blueprints
- **`app/auth`**: Manages user registration, login, and sessions using `Flask-Login`.
- **`app/quiz`**: Handles quiz listing, taking quizzes, and score history.
- **`app/inspector`**: A standalone tool for parsing and analyzing `.eml` files using the Python `email` library.
- **`app/dashboard`**: Provides administrative statistics, charts (Chart.js), and cohort-level analytics.

## Security Features
- **Authentication**: Password hashing with `Werkzeug`.
- **CSRF Protection**: `Flask-WTF` for secure form submission.
- **EML Sandbox**: HTML previews of phishing emails are rendered in an `<iframe>` with restricted permissions.
