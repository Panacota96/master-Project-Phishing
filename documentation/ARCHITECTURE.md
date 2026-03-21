# Architecture Diagrams

> Phishing awareness training application — En Garde
> See also: [REQUIREMENTS.md](REQUIREMENTS.md) | [README](../README.md)

## Table of Contents

1. [System Overview](#1-system-overview)
2. [AWS Infrastructure](#2-aws-infrastructure)
3. [Flask Software Architecture](#3-flask-software-architecture)
4. [DynamoDB Schema](#4-dynamodb-schema)
5. [CI/CD Pipeline](#5-cicd-pipeline)
6. [Login Flow](#6-login-flow)
7. [Quiz Flow](#7-quiz-flow)
8. [Email Inspector Flow](#8-email-inspector-flow)
9. [QR Self-Registration Flow](#9-qr-self-registration-flow)
10. [Local Development Architecture](#10-local-development-architecture)

---

## 1. System Overview

High-level C4-style context diagram: all actors and AWS services in one view.

```mermaid
graph TB
    subgraph Actors
        Student(["Student"])
        Admin(["Admin"])
        GHA(["GitHub Actions\nCI/CD"])
    end

    subgraph AWS["AWS — eu-west-3"]
        CF["CloudFront\nCDN + HTTPS"]
        APIGW["API Gateway v2\nHTTP API"]
        LambdaApp["Lambda Flask App\nPython 3.12 · 512 MB"]
        LambdaWorker["Lambda Registration Worker\nPython 3.12 · 256 MB"]
        DDB[("DynamoDB\n9 Tables")]
        S3[("S3 Bucket\nEML + Videos")]
        SQS["SQS Queue\nRegistration"]
        SES["SES\nEmail"]
        SNS["SNS\nAlerts + Events"]
        CW["CloudWatch\nAlarms + Dashboard + X-Ray"]
    end

    Student -->|HTTPS| CF
    Admin -->|HTTPS| CF
    CF --> APIGW
    APIGW --> LambdaApp
    LambdaApp --> DDB
    LambdaApp --> S3
    LambdaApp --> SQS
    SQS --> LambdaWorker
    LambdaWorker --> DDB
    LambdaWorker --> SES
    LambdaWorker --> SNS
    LambdaApp --> CW
    SNS --> CW
    GHA -->|Terraform apply| LambdaApp
    GHA -->|S3 sync| S3
    GHA -->|seed_dynamodb.py| DDB
```

---

## 2. AWS Infrastructure

All resources grouped by AWS service with connection direction.

```mermaid
graph LR
    subgraph DNS["Route 53 + ACM (optional)"]
        R53["Route 53\nA record"]
        ACM["ACM Cert\nus-east-1"]
    end

    subgraph CDN["CloudFront"]
        CF["Distribution\nTTL=0 · Compress"]
    end

    subgraph APIGW_["API Gateway v2"]
        APIGW["HTTP API\n$default stage · auto-deploy"]
    end

    subgraph Compute["Lambda"]
        LApp["en-garde-dev-app\n512 MB · 30 s · X-Ray Active"]
        LWorker["en-garde-dev-registration-worker\n256 MB · 60 s"]
    end

    subgraph Storage["S3"]
        S3["en-garde-dev-eu-west-3\nVersioned · AES256"]
    end

    subgraph DB["DynamoDB — 9 tables (PAY_PER_REQUEST)"]
        TUsers["users\nPK: username\nGSI: email, group"]
        TQuizzes["quizzes\nPK: quiz_id"]
        TAttempts["attempts\nPK: username+quiz_id\nGSI: quiz_id, group"]
        TResponses["responses\nPK: username_quiz_id+question_id\nGSI: quiz_question_id"]
        TInspector["inspector-attempts\nPK: username+submitted_at\nGSI: group, email_file"]
        TInspectorAnon["inspector-attempts-anon\nPK: attempt_id+submitted_at"]
        TBugs["bugs\nPK: bug_id"]
        TAnswerKey["answer-key-overrides\nPK: email_file"]
        TCohort["cohort-tokens\nPK: token · TTL: expires_at"]
    end

    subgraph Async["SQS + SES + SNS"]
        SQS["Registration Queue\nDLQ · SSE · 60s visibility"]
        DLQQ["Registration DLQ\n14-day retention"]
        SES["SES Identity\nno-reply@..."]
        SNSReg["SNS Registration Topic"]
        SNSAlerts["SNS Alerts Topic"]
    end

    subgraph Observe["CloudWatch"]
        CWLogs["Log Groups\n/aws/lambda/* · /aws/apigateway/*\n14-day retention"]
        CWAlarms["6 Alarms\nLambda errors/duration/throttles\nAPI GW 4xx/5xx · DynamoDB errors"]
        CWDash["Dashboard\nen-garde-dev-overview"]
    end

    subgraph IAM_["IAM"]
        RoleLambda["lambda-role\nDynamoDB · S3 · SQS · X-Ray"]
        RoleWorker["registration-worker-role\nDynamoDB · SES · SQS · SNS"]
        RoleGHA["github-actions-deploy\nOIDC · broad deploy perms"]
    end

    R53 --> CF
    ACM --> CF
    CF --> APIGW
    APIGW --> LApp
    LApp --> TUsers & TQuizzes & TAttempts & TResponses & TInspector & TInspectorAnon & TBugs & TAnswerKey & TCohort
    LApp --> S3
    LApp --> SQS
    SQS --> LWorker
    SQS --> DLQQ
    LWorker --> TUsers
    LWorker --> SES
    LWorker --> SNSReg
    SNSAlerts --> CWAlarms
    LApp --> CWLogs
    LApp --> CWDash
    RoleLambda --> LApp
    RoleWorker --> LWorker
    RoleGHA --> LApp & LWorker & S3 & DB
```

---

## 3. Flask Software Architecture

App factory, blueprints, models, and DynamoDB table mapping.

```mermaid
graph TD
    subgraph Entry["Entry Points"]
        LH["lambda_handler.py\nMangum + WsgiToAsgi + X-Ray"]
        Run["run.py\nFlask dev server"]
    end

    subgraph Factory["app/__init__.py — create_app()"]
        DynRes["app.dynamodb\nboto3 DynamoDB resource"]
        S3Client["app.s3_client\nboto3 S3 client"]
        SQSClient["app.sqs_client\nboto3 SQS client"]
        CSRF["Flask-WTF CSRF"]
        LoginMgr["Flask-Login\nLoginManager"]
    end

    subgraph Blueprints["Blueprints"]
        Auth["/auth\nlogin · register · logout\nQR · CSV import · password"]
        Quiz["/quiz\nlist · video gate · questions\nfinish · history"]
        Dashboard["/dashboard\nstats · users · bugs\nreports · inspector analytics"]
        Inspector["/inspector\nJSON API — CSRF exempt\nemail pool · detail · submit"]
    end

    subgraph DAL["app/models.py — Data Access Layer"]
        UserModel["User CRUD\nget_user · create_user\nbatch_create · delete_user\nlist_all · by_group · by_email"]
        QuizModel["Quiz CRUD\nget_quiz · list_quizzes\ncreate_quiz"]
        AttemptModel["Attempt CRUD\ncreate_attempt (conditional)\nlist_by_quiz · list_by_group"]
        ResponseModel["Response CRUD\nsave_response · get_responses\nby_question"]
        InspectorModel["Inspector CRUD\ncreate_attempt_anonymous\nlist · count"]
        OverrideModel["Answer Key Overrides\nget_effective_answer_key()\nset · delete override"]
        CohortModel["Cohort Token CRUD\ncreate · get (TTL check)"]
        SQSModel["enqueue_registration()\nsqs_client.send_message()"]
    end

    subgraph Config["config.py — Config class"]
        EnvVars["SECRET_KEY · AWS_REGION\nDYNAMODB_* (9 tables)\nS3_BUCKET · SQS_REGISTRATION_QUEUE_URL\nSES_FROM_EMAIL · APP_LOGIN_URL\nDYNAMODB_ENDPOINT (local dev)"]
    end

    LH --> Factory
    Run --> Factory
    Factory --> DynRes & S3Client & SQSClient & CSRF & LoginMgr
    Factory --> Auth & Quiz & Dashboard & Inspector
    Auth & Quiz & Dashboard & Inspector --> DAL
    DAL --> EnvVars
    Config --> Factory
```

---

## 4. DynamoDB Schema

All 9 tables, primary keys, sort keys, and GSIs.

```mermaid
erDiagram
    USERS {
        string username PK
        string email GSI-email-index
        string group GSI-group-index
        string password_hash
        bool is_admin
        bool quiz_completed
        string class_name
        string academic_year
        string major
        string facility
        string created_at
        list inspector_submitted
        bool inspector_locked
    }

    QUIZZES {
        string quiz_id PK
        string title
        string description
        list questions
        string video_url
        string created_at
    }

    ATTEMPTS {
        string username PK
        string quiz_id SK
        string group GSI-group-index
        string completed_at GSI-quiz-index-range
        number score
        number total
        number percentage
        string class_name
        string academic_year
        string major
    }

    RESPONSES {
        string username_quiz_id PK
        string question_id SK
        string quiz_question_id GSI-quiz-question-index
        string username GSI-quiz-question-index-range
        string selected_answer_id
        bool is_correct
        string answered_at
    }

    INSPECTOR_ATTEMPTS {
        string username PK
        string submitted_at SK
        string group GSI-group-index
        string email_file GSI-email-index
        string classification
        list selected_signals
        string expected_classification
        list expected_signals
        bool is_correct
        string class_name
        string academic_year
        string major
    }

    INSPECTOR_ATTEMPTS_ANON {
        string attempt_id PK
        string submitted_at SK
        string email_file
        string classification
        list selected_signals
        bool is_correct
        string class_name
        string academic_year
        string major
    }

    BUGS {
        string bug_id PK
        string username
        string description
        string page_url
        string status
        string submitted_at
    }

    ANSWER_KEY_OVERRIDES {
        string email_file PK
        string classification
        list signals
        string explanation
    }

    COHORT_TOKENS {
        string token PK
        string class_name
        string academic_year
        string major
        string facility
        string created_by
        string created_at
        number expires_at
    }

    USERS ||--o{ ATTEMPTS : "has"
    USERS ||--o{ RESPONSES : "submits"
    USERS ||--o{ INSPECTOR_ATTEMPTS : "classifies"
    QUIZZES ||--o{ ATTEMPTS : "scored_in"
    QUIZZES ||--o{ RESPONSES : "answered_in"
```

---

## 5. CI/CD Pipeline

Full GitHub Actions pipeline: push to main triggers CI, then deploy to dev.

```mermaid
flowchart TD
    Push["git push to main"] --> CIJob

    subgraph CIJob["ci.yml — CI Job"]
        Lint["make lint\nflake8 app/ --max-line-length=120"]
        Test["make test\npytest tests/ + moto AWS mocks\nJUnit XML report"]
        Lint --> Test
    end

    CIJob --> DeployJob

    subgraph DeployJob["deploy-dev.yml — Deploy Job\n(env: dev · OIDC role)"]
        PipInst["pip install -r requirements.txt"]
        TFSetup["Setup Terraform ~1.9"]
        AWSAuth["AWS OIDC Auth\nsecrets.AWS_DEPLOY_ROLE_ARN"]
        BuildLambda["make lambda\n→ lambda.zip"]
        VerifyZip["test -f lambda.zip"]
        TFInit["terraform init -reconfigure\n-backend-config=backend/dev.hcl"]
        TFVal["terraform validate"]
        WriteTFVars["Write env/dev.tfvars\nregion · env · app_name · secret_key"]
        TFPlan["terraform plan\n-var-file=env/dev.tfvars -out=tfplan"]
        TFApply["terraform apply\n-auto-approve tfplan"]
        CaptureOutputs["Capture tf outputs\ns3_bucket · cloudfront_url\nall DynamoDB table names"]
        SyncEML["aws s3 sync examples/\n→ s3://bucket/eml-samples/"]
        SyncVideos["aws s3 sync app/static/videos/\n→ s3://bucket/videos/"]
        SeedDB["python3 seed_dynamodb.py\n(if not skip_seed)"]
        Summary["Post Job Summary\nApp URL · CloudFront URL"]

        PipInst --> TFSetup --> AWSAuth --> BuildLambda --> VerifyZip
        VerifyZip --> TFInit --> TFVal --> WriteTFVars --> TFPlan --> TFApply
        TFApply --> CaptureOutputs --> SyncEML --> SyncVideos --> SeedDB --> Summary
    end

    subgraph ExtraWF["Other Workflows"]
        ClaudeAction["claude.yml\n@claude mentions in Issues/PRs"]
        ClaudeReview["claude-code-review.yml\nAuto PR review on every PR"]
    end
```

---

## 6. Login Flow

```mermaid
sequenceDiagram
    actor Student
    participant CF as CloudFront
    participant Flask as Flask /auth/login
    participant DDB as DynamoDB users

    Student->>CF: GET /auth/login
    CF->>Flask: Proxy request
    Flask->>Student: Render LoginForm

    Student->>CF: POST /auth/login (username, password)
    CF->>Flask: Proxy POST
    Flask->>Flask: form.validate_on_submit()
    Flask->>DDB: get_item(Key={username})
    DDB-->>Flask: User item (or empty)

    alt User found
        Flask->>Flask: check_password_hash(stored, input)
        alt Password correct
            Flask->>Flask: login_user(user) -- set session cookie
            Flask-->>Student: 302 /quiz/ + "Logged in" flash
        else Wrong password
            Flask-->>Student: 200 re-render form + "Invalid credentials"
        end
    else User not found
        Flask-->>Student: 200 re-render form + "Invalid credentials"
    end
```

---

## 7. Quiz Flow

```mermaid
flowchart TD
    A["GET /quiz/\nlist_quizzes() + get_attempt() per quiz"] --> B["Show quiz list\nwith completed badges"]
    B --> C["User selects quiz\nGET /quiz/quiz_id/start"]
    C --> D{"Already\ncompleted?"}
    D -->|Yes| E["Show results\nalready_completed=True"]
    D -->|No| F{"Video URL\nconfigured?"}
    F -->|Yes| G{"session\nvideo_watched?"}
    G -->|No| H["GET /quiz/quiz_id/video\nRender video player"]
    H --> I["User watches video\nPOST /quiz/quiz_id/video-watched\nset session flag"]
    I --> J
    G -->|Yes| J["Init session:\nscore=0, index=0\nquestion_ids shuffled"]
    F -->|No| J

    J --> K["GET /quiz/question\nRender current question + progress bar"]
    K --> L["User picks answer\nPOST /quiz/question"]
    L --> M["save_response()\n→ DynamoDB responses"]
    M --> N{"More\nquestions?"}
    N -->|Yes| O["Increment index\nShow explanation"]
    O --> K
    N -->|No| P["GET /quiz/finish\ncreate_attempt()\nCondition: attribute_not_exists"]
    P --> Q["mark_quiz_completed()\n→ DynamoDB users"]
    Q --> R["Clear session vars"]
    R --> S["Render results.html\nscore · total · percentage"]
```

---

## 8. Email Inspector Flow

```mermaid
sequenceDiagram
    actor Student
    participant JS as Browser JS
    participant Flask as Flask /inspector
    participant S3 as S3 eml-samples/
    participant DDB as DynamoDB

    Student->>Flask: GET /inspector/
    Flask->>DDB: get_user_inspector_state(username)
    DDB-->>Flask: {submitted:[], locked:false}
    Flask-->>Student: Render inspector.html (SPA)

    JS->>Flask: GET /inspector/api/emails
    Flask->>S3: list_objects eml-samples/
    S3-->>Flask: EML file list
    Flask->>DDB: get_effective_answer_key()
    DDB-->>Flask: static + overrides merged
    Flask->>Flask: Build pool (1-3 spam + phishing = max 8)\nStore in session
    Flask-->>JS: [{fileName, subject, from, date} x8]

    loop For each email (up to 8)
        JS->>Flask: GET /inspector/api/emails/filename.eml
        Flask->>S3: GetObject eml-samples/filename.eml
        S3-->>Flask: Raw EML bytes
        Flask->>Flask: Parse EML, clean placeholders\nExtract headers/body/links/attachments
        Flask->>Flask: requiredSignals = len(answer_key[file].signals)
        Flask-->>JS: {headers, htmlBody, links, requiredSignals, ...}

        JS->>Student: Display email + signal checkboxes
        Student->>JS: Select classification + N signals
        JS->>Flask: POST /inspector/api/submit\n{fileName, classification, signals[]}

        Flask->>Flask: Normalize signals (lowercase alphanumeric)
        Flask->>Flask: Compare to answer key
        Flask->>DDB: create_inspector_attempt_anonymous()\n-- inspector-attempts-anon table
        Flask->>DDB: update_user_inspector_state()\nAppend fileName to inspector_submitted

        alt All 8 submitted
            Flask->>DDB: Set inspector_locked=True
            Flask-->>JS: {completed:true, explanation:"..."}
        else More emails remain
            Flask-->>JS: {completed:false, explanation:"..."}
        end
    end

    JS->>Student: Show "Inspector Complete" screen
```

---

## 9. QR Self-Registration Flow

```mermaid
sequenceDiagram
    actor Admin
    actor Student
    participant Flask as Flask /auth
    participant DDB as DynamoDB
    participant SQS as SQS Registration Queue
    participant Worker as Lambda Registration Worker
    participant SES as SES

    Admin->>Flask: GET /auth/admin/generate-qr
    Flask-->>Admin: Render CohortQRForm

    Admin->>Flask: POST /auth/admin/generate-qr (submit)
    Flask->>Flask: Build register URL: APP_BASE/auth/register
    Flask->>Flask: qrcode.make(register_url)\nEncode PNG as base64
    Flask-->>Admin: Render page with QR image\n+ Download PNG button

    Admin->>Student: Share / print QR code

    Student->>Flask: GET /auth/register (scan QR)
    Flask-->>Student: Render RegistrationForm\n(username, email, class, year, major, facility, password)

    Student->>Flask: POST /auth/register (fill form)
    Flask->>Flask: Validate form fields\nPassword strength check
    Flask->>DDB: get_user(username) -- duplicate check
    Flask->>DDB: get_user_by_email(email) -- duplicate check
    Flask->>Flask: generate_password_hash(password)
    Flask->>SQS: enqueue_registration()\nsend_message({username, email, password_hash, cohort...})
    Flask-->>Student: Render register_pending.html\n"Check your email at {email}"

    SQS->>Worker: Trigger (batch_size=1)
    Worker->>DDB: get_item(username) -- idempotency check
    Worker->>DDB: query email-index -- duplicate email check
    Worker->>DDB: put_item(user)\nCondition: attribute_not_exists(username)
    Worker->>SES: send_email(to=email)\n"Your En Garde account is ready"
    SES-->>Student: Confirmation email with login URL
    Worker->>Worker: publish SNS registration event (optional fan-out)

    Student->>Flask: GET /auth/login (from email link)
    Student->>Flask: POST /auth/login (username, password)
    Flask-->>Student: Logged in -- /quiz/
```

---

## 10. Local Development Architecture

```mermaid
graph TD
    subgraph Host["Developer Machine"]
        Browser["Browser\nlocalhost:80"]
        DotEnv[".env file\nDYNAMODB_ENDPOINT=http://localhost:8766\nAWS_REGION_NAME=eu-west-3\nSECRET_KEY=dev-secret"]
    end

    subgraph DockerCompose["docker-compose.yml"]
        Nginx["nginx:alpine\nPort 80:80\nReverse proxy + static files"]
        Web["web (Gunicorn)\nFlask app · reads .env\ndepends_on: dynamodb-local"]
        DDBLocal["amazon/dynamodb-local\nPort 8766:8000\n-inMemory flag"]
    end

    subgraph Setup["Setup Scripts"]
        SetupDB["python setup_local_db.py\nCreate 9 DynamoDB tables\nvia boto3 to localhost:8766"]
        SeedDB["python seed_dynamodb.py\nSeed admin user + quizzes"]
    end

    subgraph AltRun["Alternative: python run.py"]
        RunPy["Flask dev server\nPort 5000\n(no Docker)"]
    end

    Browser -->|Port 80| Nginx
    Nginx -->|Static files directly| Nginx
    Nginx -->|App routes proxy| Web
    Web --> DDBLocal
    DotEnv --> Web
    SetupDB --> DDBLocal
    SeedDB --> Web
    RunPy -->|Port 5000| Browser
```
