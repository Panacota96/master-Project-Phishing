"""Seed the database with sample phishing quiz data."""
from app import create_app, db
from app.models import User, Quiz, Question, Answer

app = create_app()

with app.app_context():
    db.create_all()

    # Create admin user
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)

    # Create phishing awareness quiz
    quiz = Quiz(
        title='Phishing Awareness Fundamentals',
        description='Test your ability to identify phishing attempts, suspicious emails, and social engineering tactics.',
    )
    db.session.add(quiz)
    db.session.flush()

    questions_data = [
        {
            'text': 'You receive an email from "security@yourbank-verify.com" asking you to confirm your account details. What should you do?',
            'explanation': 'Legitimate banks never ask for account details via email. The domain "yourbank-verify.com" is not the official bank domain — this is a classic phishing technique using a lookalike domain.',
            'answers': [
                ('Click the link and verify your account immediately', False),
                ('Ignore the email and contact your bank directly using their official website', True),
                ('Reply with your account number to verify', False),
                ('Forward it to your friends for their opinion', False),
            ],
        },
        {
            'text': 'Which of the following URLs is most likely a phishing attempt?',
            'explanation': 'Phishers use subdomains to make URLs look legitimate. "paypal.com.secure-login.net" uses "paypal.com" as a subdomain of "secure-login.net", which is not PayPal\'s real domain.',
            'answers': [
                ('https://www.paypal.com/account/settings', False),
                ('https://paypal.com.secure-login.net/verify', True),
                ('https://www.paypal.com/signin', False),
                ('https://help.paypal.com/contact', False),
            ],
        },
        {
            'text': 'An email claims "Your account will be suspended in 24 hours unless you act now!" What phishing tactic is this?',
            'explanation': 'Creating a false sense of urgency is a common social engineering tactic. Attackers pressure victims into acting quickly without thinking critically about the request.',
            'answers': [
                ('Spear phishing', False),
                ('Whaling', False),
                ('Urgency/fear tactics', True),
                ('Baiting', False),
            ],
        },
        {
            'text': 'You receive an email from your CEO asking you to urgently wire $50,000 to a new vendor. The email address looks slightly different from the usual one. What type of attack is this?',
            'explanation': 'Whaling (or CEO fraud) targets high-value individuals by impersonating executives. Always verify unusual financial requests through a separate communication channel.',
            'answers': [
                ('Vishing', False),
                ('Whaling / CEO fraud', True),
                ('Smishing', False),
                ('Pharming', False),
            ],
        },
        {
            'text': 'What is the safest way to check if an email link is legitimate?',
            'explanation': 'Hovering over (without clicking) a link reveals the actual URL destination. This lets you verify whether it points to the legitimate domain before clicking.',
            'answers': [
                ('Click the link and see where it goes', False),
                ('Hover over the link to preview the actual URL', True),
                ('Trust the link if the email looks official', False),
                ('Copy and paste the link into a new browser tab', False),
            ],
        },
        {
            'text': 'Which email header detail is MOST useful for detecting a spoofed sender?',
            'explanation': 'The "Received" headers and SPF/DKIM/DMARC authentication results in email headers reveal the true origin of an email, even if the "From" address has been spoofed.',
            'answers': [
                ('The subject line', False),
                ('The "From" display name', False),
                ('The "Received" headers and authentication results (SPF/DKIM)', True),
                ('The date and time sent', False),
            ],
        },
        {
            'text': 'A colleague sends you a file called "Q4_Report.pdf.exe" via email. What should you do?',
            'explanation': 'Files with double extensions (like .pdf.exe) are a red flag. The actual file type is determined by the last extension — this is an executable, not a PDF. It could contain malware.',
            'answers': [
                ('Open it since it came from a colleague', False),
                ('Do not open it — the double extension is suspicious and it may be malware', True),
                ('Rename it to remove the .exe and then open it', False),
                ('Forward it to IT without any context', False),
            ],
        },
        {
            'text': 'You get a text message saying "Your package delivery failed. Click here to reschedule:" followed by a shortened URL. This is an example of:',
            'explanation': 'Smishing (SMS phishing) uses text messages to trick victims. Shortened URLs hide the true destination. Legitimate delivery services direct you to their official app or website.',
            'answers': [
                ('Vishing', False),
                ('Phishing', False),
                ('Smishing', True),
                ('Pretexting', False),
            ],
        },
        {
            'text': 'What makes spear phishing more dangerous than regular phishing?',
            'explanation': 'Spear phishing uses personal information about the target (name, job role, recent activities) to craft convincing messages, making them much harder to detect than generic phishing emails.',
            'answers': [
                ('It uses more advanced malware', False),
                ('It targets specific individuals with personalized content', True),
                ('It only works on mobile devices', False),
                ('It requires physical access to the victim\'s computer', False),
            ],
        },
        {
            'text': 'Your organization\'s IT department asks everyone to enable Multi-Factor Authentication (MFA). Why does MFA help protect against phishing?',
            'explanation': 'Even if a phishing attack successfully captures your password, MFA requires a second verification factor (like a code from your phone), preventing unauthorized access with stolen credentials alone.',
            'answers': [
                ('It blocks all phishing emails automatically', False),
                ('It encrypts your password so it can\'t be stolen', False),
                ('It adds an extra layer so stolen passwords alone aren\'t enough to access accounts', True),
                ('It makes your password longer and more complex', False),
            ],
        },
    ]

    for q_data in questions_data:
        question = Question(
            quiz_id=quiz.id,
            question_text=q_data['text'],
            explanation=q_data['explanation'],
        )
        db.session.add(question)
        db.session.flush()
        for answer_text, is_correct in q_data['answers']:
            answer = Answer(
                question_id=question.id,
                answer_text=answer_text,
                is_correct=is_correct,
            )
            db.session.add(answer)

    db.session.commit()
    print('Database seeded successfully!')
    print(f'  - Admin user: admin / admin123')
    print(f'  - Quiz: "{quiz.title}" with {len(questions_data)} questions')
