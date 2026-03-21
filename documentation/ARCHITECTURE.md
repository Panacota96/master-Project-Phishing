# Architecture Diagrams

> Phishing awareness training application
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
        S3[("S3 Bucket\nEML + Videos + Reports")]
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

![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?logo=awslambda&logoColor=white)
![DynamoDB](https://img.shields.io/badge/DynamoDB-4053D6?logo=amazondynamodb&logoColor=white)
![Amazon S3](https://img.shields.io/badge/Amazon_S3-569A31?logo=amazons3&logoColor=white)
![Amazon SQS](https://img.shields.io/badge/Amazon_SQS-FF4F8B?logo=amazonsqs&logoColor=white)
![Amazon SES](https://img.shields.io/badge/Amazon_SES-232F3E?logo=amazonaws&logoColor=white)
![CloudFront](https://img.shields.io/badge/CloudFront-232F3E?logo=amazonaws&logoColor=white)
![API Gateway](https://img.shields.io/badge/API_Gateway-FF4F8B?logo=amazonaws&logoColor=white)
![CloudWatch](https://img.shields.io/badge/CloudWatch-FF4F8B?logo=amazonaws&logoColor=white)

All resources grouped by AWS service with connection direction.

```mermaid
graph LR
    subgraph DNS["Route 53 + ACM (optional)"]
        R53["Route 53\nA record"]
        ACM["ACM Cert\nus-east-1"]
    end

    subgraph CDN["CloudFront"]
        CF["Distribution\nTTL=0 · Compress\nredirect-to-https"]
    end

    subgraph APIGW_["API Gateway v2"]
        APIGW["HTTP API\n$default stage · auto-deploy\nStructured access logs"]
    end

    subgraph Compute["Lambda"]
        LApp["phishing-app-{env}-app\n512 MB · 30 s · X-Ray Active"]
        LWorker["phishing-app-{env}-registration-worker\n256 MB · 60 s"]
    end

    subgraph Storage["S3"]
        S3["phishing-app-{env}-eu-west-3\nVersioned · AES256\nPublic read: videos/* (dev only)\nPrivate: eml-samples/ reports/"]
    end

    subgraph DB["DynamoDB — 9 tables (PAY_PER_REQUEST)"]
        TUsers["users\nPK: username\nGSI: email-index, group-index"]
        TQuizzes["quizzes\nPK: quiz_id"]
        TAttempts["attempts\nPK: username+quiz_id\nGSI: quiz-index, group-index"]
        TResponses["responses\nPK: username_quiz_id+question_id\nGSI: quiz-question-index"]
        TInspector["inspector-attempts\nPK: username+submitted_at\nGSI: group-index, email-index"]
        TInspectorAnon["inspector-attempts-anon\nPK: attempt_id+submitted_at"]
        TBugs["bugs\nPK: bug_id"]
        TAnswerKey["answer-key-overrides\nPK: email_file"]
        TCohort["cohort-tokens\nPK: token · TTL: expires_at (90 days)"]
    end

    subgraph Async["SQS + SES + SNS"]
        SQS["Registration Queue\nDLQ · SSE · 60s visibility · 1-day retention"]
        DLQQ["Registration DLQ\n14-day retention · maxReceiveCount=4"]
        SES["SES Email Identity\nno-reply@..."]
        SNSReg["SNS Registration Topic\nFuture fan-out"]
        SNSAlerts["SNS Alerts Topic\n+ Email subscription (optional)"]
    end

    subgraph Observe["CloudWatch"]
        CWLogs["Log Groups\n/aws/lambda/{app,worker} · /aws/apigateway/*\n14-day retention"]
        CWAlarms["6 Alarms\nLambda errors(>=5)/duration-p95(>=25s)/throttles(>=1)\nAPI GW 4xx(>=50)/5xx(>=3) · DynamoDB SystemErrors(>=1)"]
        CWDash["Dashboard\nphishing-app-{env}-overview\n3 rows: Lambda · API GW · DynamoDB"]
    end

    subgraph IAM_["IAM"]
        RoleLambda["phishing-app-{env}-lambda-role\nDynamoDB (9 tables+GSIs) · S3 · SQS:SendMessage · X-Ray"]
        RoleWorker["phishing-app-{env}-registration-worker-role\nDynamoDB:users · SES:SendEmail · SQS:Receive+Delete · SNS:Publish"]
        RoleGHA["phishing-app-{env}-github-actions-deploy\nOIDC · Lambda · IAM · DynamoDB · S3 · API GW\nCloudFront · CloudWatch · SNS · SQS · SES · X-Ray · ACM · Route53"]
        OIDC["OIDC Provider\ntoken.actions.githubusercontent.com\nrepo: Panacota96/master-Project-Phishing:*"]
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
    LWorker --> CWLogs
    APIGW --> CWLogs
    RoleLambda --> LApp
    RoleWorker --> LWorker
    OIDC --> RoleGHA
```

---

## 3. Flask Software Architecture

App factory, blueprints, models, and DynamoDB table mapping.

```mermaid
graph TD
    subgraph Entry["Entry Points"]
        LH["lambda_handler.py\nMangum + WsgiToAsgi + X-Ray"]
        Run["run.py\nFlask dev server (port 5000)"]
    end

    subgraph Factory["app/__init__.py — create_app()"]
        DynRes["app.dynamodb\nboto3 DynamoDB resource"]
        S3Client["app.s3_client\nboto3 S3 client"]
        SQSClient["app.sqs_client\nboto3 SQS client"]
        CSRF["Flask-WTF CSRF\n(WTF_CSRF_SSL_STRICT=False for CloudFront)"]
        LoginMgr["Flask-Login\nLoginManager · login_view=auth.login"]
    end

    subgraph Blueprints["Blueprints"]
        Auth["/auth\nlogin · register · logout\nchange-password\nadmin/generate-qr · admin/import-users"]
        Quiz["/quiz\nlist · video-gate · video-watched\ntake-question · finish · history"]
        Dashboard["/dashboard\nstats · api/stats · api/threat-feed\nusers (list/add/delete)\nbugs · report-bug\nreports · reports/generate\ninspector-analytics · inspector/generate\nanswer-key · answer-key/edit · answer-key/reset\nrisk · inspector/reset-user · reset-bulk"]
        Inspector["/inspector\nJSON API — CSRF exempt\napi/emails · api/emails/<file> · api/submit"]
    end

    subgraph DAL["app/models.py — Data Access Layer"]
        UserModel["User CRUD\nget_user · get_user_by_email\ncreate_user · batch_create_users · delete_user\nlist_all · list_by_group · count\nmark_quiz_completed · update_user_password\nget/update/reset_user_inspector_state\nget_distinct_groups/cohorts/facilities"]
        QuizModel["Quiz CRUD\nget_quiz · list_quizzes · create_quiz"]
        AttemptModel["Attempt CRUD\ncreate_attempt (conditional)\nget_attempt · list_by_quiz · list_by_group\nlist_all · list_by_user"]
        ResponseModel["Response CRUD\nsave_response · get_responses\nget_responses_by_question"]
        InspectorModel["Inspector CRUD\ncreate_attempt_anonymous\nlist · count · list_anonymous\nlist_by_group · list_by_email"]
        OverrideModel["Answer Key Overrides\nget_effective_answer_key() — merges static + DDB\nget_answer_key_overrides()\nset_answer_key_override()\ndelete_answer_key_override()"]
        CohortModel["Cohort Token CRUD\ncreate_cohort_token() — 90-day TTL\nget_cohort_token() — TTL guard"]
        BugModel["Bug Report CRUD\ncreate_bug_report · list_bug_reports"]
        SQSModel["enqueue_registration()\nsqs_client.send_message()"]
    end

    subgraph Config["config.py — Config class"]
        EnvVars["SECRET_KEY · AWS_REGION · WTF_CSRF_SSL_STRICT\nDYNAMODB_USERS · DYNAMODB_QUIZZES · DYNAMODB_ATTEMPTS\nDYNAMODB_RESPONSES · DYNAMODB_INSPECTOR · DYNAMODB_INSPECTOR_ANON\nDYNAMODB_BUGS · DYNAMODB_ANSWER_KEY_OVERRIDES · DYNAMODB_COHORT_TOKENS\nS3_BUCKET · SQS_REGISTRATION_QUEUE_URL\nSES_FROM_EMAIL · APP_LOGIN_URL\nDYNAMODB_ENDPOINT · S3_ENDPOINT (local dev)"]
    end

    LH --> Factory
    Run --> Factory
    Factory --> DynRes & S3Client & SQSClient & CSRF & LoginMgr
    Factory --> Auth & Quiz & Dashboard & Inspector
    Auth & Quiz & Dashboard & Inspector --> DAL
    DAL --> EnvVars
    Config --> Factory
```

### Blueprint Routing Table

| Blueprint | Prefix | Key Routes |
|-----------|--------|------------|
| `app/auth` | `/auth` | `GET/POST /auth/login`, `GET /auth/logout`, `GET/POST /auth/register`, `GET/POST /auth/change-password`, `GET/POST /auth/admin/generate-qr`, `GET/POST /auth/admin/import-users` |
| `app/quiz` | `/quiz` | `GET /quiz/`, `GET /quiz/<id>/start`, `GET /quiz/<id>/video`, `POST /quiz/<id>/video-watched`, `GET/POST /quiz/question`, `GET /quiz/finish`, `GET /quiz/history` |
| `app/dashboard` | `/dashboard` | `GET /dashboard/`, `GET /dashboard/api/stats`, `GET /dashboard/api/threat-feed`, `GET /dashboard/users`, `POST /dashboard/users/add`, `POST /dashboard/users/delete/<u>`, `GET /dashboard/bugs`, `POST /dashboard/report-bug`, `GET /dashboard/risk`, `GET /dashboard/reports`, `POST /dashboard/reports/generate`, `GET /dashboard/inspector`, `POST /dashboard/reports/inspector/generate`, `GET /dashboard/inspector/answer-key`, `POST /dashboard/inspector/answer-key/edit`, `POST /dashboard/inspector/answer-key/reset`, `POST /dashboard/inspector/reset-user`, `POST /dashboard/inspector/reset-bulk` |
| `app/inspector` | `/inspector` | `GET /inspector/`, `GET /inspector/api/emails`, `GET /inspector/api/emails/<filename>`, `POST /inspector/api/submit` |

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
        string completed_at GSI-quiz-index-SK
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
        string username GSI-quiz-question-index-SK
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
        string expected_classification
        list expected_signals
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

![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=github-actions&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white)

Full GitHub Actions pipeline across all workflow files.

```mermaid
flowchart TD
    Push["git push to any branch\nor PR to main"] --> CIJob

    subgraph CIJob["ci.yml — CI (runs on all branches + PRs)"]
        Lint["make lint\nflake8 app/ --max-line-length=120"]
        ValidEML["make validate-eml\nEML realism checks"]
        Test["make test\npytest tests/ + moto AWS mocks\nJUnit XML report → report.xml artifact"]
        Build["make lambda + make registration-worker\nlambda.zip + registration_worker.zip → artifact"]
        Lint --> ValidEML --> Test --> Build
    end

    CIJob -->|on push to main| PlanJob

    subgraph PlanJob["deploy-dev.yml — plan_dev job\n(env: dev · OIDC role)"]
        IAMBootstrap["Bootstrap IAM permissions\nImport OIDC provider + GHA role if orphaned\nApply github_actions_deploy policy only\nSleep 20s for IAM propagation"]
        TFInit["terraform init -reconfigure\n-backend-config=backend/dev.hcl"]
        TFVal["terraform validate"]
        WriteTFVars["Write env/dev.tfvars\nregion · env · app_name · secret_key"]
        TFPlan["terraform plan\n-var-file=env/dev.tfvars -out=tfplan\nUpload tfplan artifact"]
        IAMBootstrap --> TFInit --> TFVal --> WriteTFVars --> TFPlan
    end

    PlanJob --> DeployJob

    subgraph DeployJob["deploy-dev.yml — deploy_dev job\n(env: dev · OIDC role)"]
        TFApply["terraform apply -auto-approve tfplan"]
        CaptureOutputs["Capture tf outputs\ns3_bucket · cloudfront_url · app_url\nall 9 DynamoDB table names"]
        SyncEML["aws s3 sync examples/\n→ s3://bucket/eml-samples/ (*.eml)"]
        SyncVideos["aws s3 sync app/static/videos/\n→ s3://bucket/videos/ (*.mp4)"]
        SeedDB["python3 seed_dynamodb.py\n(if not skip_seed input)"]
        Summary["Post Job Summary\nApp URL · CloudFront URL"]
        TFApply --> CaptureOutputs --> SyncEML --> SyncVideos --> SeedDB --> Summary
    end

    subgraph ManualWF["Manual / Other Workflows"]
        DeployProd["deploy-prod.yml\nworkflow_dispatch only\nbuild → plan_prod → deploy_prod\n(env: prod · requires prod environment approval)"]
        DestroyWF["destroy.yml\nworkflow_dispatch\nChoose env: dev or prod\nOptional: empty S3 versioned bucket\nRemoves IAM from state before destroy"]
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
    G -->|Yes| J["Init session:\nscore=0, index=0\nquestion_ids list"]
    F -->|No| J

    J --> K["GET /quiz/question\nRender current question + progress bar"]
    K --> L["User picks answer\nPOST /quiz/question"]
    L --> M["save_response()\n→ DynamoDB responses"]
    M --> N{"More\nquestions?"}
    N -->|Yes| O["Increment index\nShow explanation"]
    O --> K
    N -->|No| P["GET /quiz/finish\ncreate_attempt()\nCondition: attribute_not_exists(username AND quiz_id)"]
    P --> Q["mark_quiz_completed()\n→ DynamoDB users"]
    Q --> R["Clear session vars\n(quiz_score, quiz_total, quiz_id, question_ids, current_index)"]
    R --> S["Render results.html\nscore · total · percentage\nrank badge: Novice / Trainee / Defender / Cyber Sentinel"]
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
    Flask-->>Student: Render inspector.html (SPA shell)

    JS->>Flask: GET /inspector/api/emails
    Flask->>S3: list_objects_v2 eml-samples/
    S3-->>Flask: EML file list
    Flask->>DDB: get_effective_answer_key()\n(static ANSWER_KEY merged with DDB overrides)
    DDB-->>Flask: merged answer key
    Flask->>Flask: Build pool (1–3 spam + phishing, max 8)\nStore in session['inspector_email_pool']
    Flask-->>JS: [{fileName, subject, from, date} x≤8]

    loop For each email (up to 8)
        JS->>Flask: GET /inspector/api/emails/filename.eml
        Flask->>S3: GetObject eml-samples/filename.eml
        S3-->>Flask: Raw EML bytes (or JSON-formatted EML)
        Flask->>Flask: Parse EML stdlib / JSON path\nclean_placeholders()\nExtract headers/body/links/attachments/warnings
        Flask->>Flask: requiredSignals = len(answer_key[file].signals)\n(0 for Spam)
        Flask-->>JS: {summary, headers, htmlBody, links,\nattachments, warnings, requiredSignals}

        JS->>Student: Display email + signal checkboxes
        Student->>JS: Select classification + N signals
        JS->>Flask: POST /inspector/api/submit\n{fileName, classification, signals[]}

        Flask->>Flask: Validate: classification in (Spam,Phishing)\nlen(signals) == requiredSignals\nfilename in pool + not already submitted
        Flask->>Flask: Normalize signals (lowercase alphanumeric)\nCompare to effective answer key
        Flask->>DDB: create_inspector_attempt_anonymous()\n→ inspector-attempts-anon table
        Flask->>DDB: update_user_inspector_state()\nAppend fileName to inspector_submitted

        alt All pool emails submitted (non-admin)
            Flask->>DDB: Set inspector_locked=True
            Flask->>Flask: session.pop('inspector_email_pool')
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
    Flask->>Flask: Build register URL from APP_LOGIN_URL config\nqrcode.make(register_url) → base64 PNG
    Flask-->>Admin: Render page with QR image + Download PNG button

    Admin->>Student: Share / print QR code

    Student->>Flask: GET /auth/register (scan QR)
    Flask-->>Student: Render RegistrationForm\n(username, email, class, year, major, facility, password)

    Student->>Flask: POST /auth/register (fill form)
    Flask->>Flask: Validate form fields
    Flask->>DDB: get_user(username) — duplicate check
    Flask->>DDB: get_user_by_email(email) — duplicate check
    Flask->>Flask: generate_password_hash(password)
    Flask->>SQS: enqueue_registration()\nsend_message({username, email, password_hash,\nclass_name, academic_year, major, facility, group})
    Flask-->>Student: Render register_pending.html\n"Check your email at {email}"

    SQS->>Worker: Trigger (batch_size=1)
    Worker->>DDB: get_item(username) — idempotency check
    Worker->>DDB: query email-index — duplicate email check
    Worker->>DDB: put_item(user)\nCondition: attribute_not_exists(username)
    Worker->>SES: send_email(to=email)\n"Your En Garde account is ready" + login URL
    SES-->>Student: Confirmation email with login URL
    Worker->>Worker: sns.publish() to SNS registration topic (future fan-out)

    Student->>Flask: GET /auth/login (from email link)
    Student->>Flask: POST /auth/login (username, password)
    Flask-->>Student: Logged in — /quiz/
```

---

## 10. Local Development Architecture

```mermaid
graph TD
    subgraph Host["Developer Machine"]
        Browser["Browser\nlocalhost:80 (Docker) or\nlocalhost:5000 (run.py)"]
        DotEnv[".env file\nDYNAMODB_ENDPOINT=http://localhost:8766\nAWS_REGION_NAME=eu-west-3\nSECRET_KEY=dev-secret\nDYNAMODB_* table names\nS3_BUCKET=phishing-app-dev-eu-west-3"]
    end

    subgraph DockerCompose["docker-compose.yml (recommended)"]
        Nginx["nginx:alpine\nPort 80:80\nReverse proxy + static files"]
        Web["web (Gunicorn)\nFlask app · reads .env\ndepends_on: dynamodb-local"]
        DDBLocal["amazon/dynamodb-local\nPort 8766:8000 (-inMemory)"]
    end

    subgraph Setup["Setup Scripts"]
        SetupDB["python setup_local_db.py\nCreate 9 DynamoDB tables\nvia boto3 to localhost:8766"]
        SeedDB["python seed_dynamodb.py\nSeed admin user + quizzes\n(uses Flask app context)"]
    end

    subgraph AltRun["Alternative: python run.py"]
        RunPy["Flask dev server\nPort 5000\n(no Docker needed)"]
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
