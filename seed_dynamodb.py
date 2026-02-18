"""Seed DynamoDB tables with admin user and sample quiz data."""

import os
import sys

# Allow running directly: python seed_dynamodb.py
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.models import create_quiz, create_user, get_user

app = create_app()

with app.app_context():
    # Create admin user
    if not get_user('admin'):
        create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_admin=True,
            group='admin',
            class_name='Admin',
            academic_year='2025',
            major='Security',
        )
        print('  - Created admin user: admin / admin123')
    else:
        print('  - Admin user already exists, skipping')

    # Create phishing awareness quiz
    quiz_id = 'quiz-phishing-fundamentals'

    questions = [
        {
            'question_id': 'q1',
            'question_text': 'You receive an email from "security@yourbank-verify.com" asking you to confirm your account details. What should you do?',
            'explanation': 'Legitimate banks never ask for account details via email. The domain "yourbank-verify.com" is not the official bank domain — this is a classic phishing technique using a lookalike domain.',
            'answers': [
                {'answer_id': 'q1a1', 'answer_text': 'Click the link and verify your account immediately', 'is_correct': False},
                {'answer_id': 'q1a2', 'answer_text': 'Ignore the email and contact your bank directly using their official website', 'is_correct': True},
                {'answer_id': 'q1a3', 'answer_text': 'Reply with your account number to verify', 'is_correct': False},
                {'answer_id': 'q1a4', 'answer_text': 'Forward it to your friends for their opinion', 'is_correct': False},
            ],
        },
        {
            'question_id': 'q2',
            'question_text': 'Which of the following URLs is most likely a phishing attempt?',
            'explanation': 'Phishers use subdomains to make URLs look legitimate. "paypal.com.secure-login.net" uses "paypal.com" as a subdomain of "secure-login.net", which is not PayPal\'s real domain.',
            'image_path': '/static/quiz/url-preview.svg',
            'image_alt': 'Email snippet showing a suspicious PayPal URL preview',
            'answers': [
                {'answer_id': 'q2a1', 'answer_text': 'https://www.paypal.com/account/settings', 'is_correct': False},
                {'answer_id': 'q2a2', 'answer_text': 'https://paypal.com.secure-login.net/verify', 'is_correct': True},
                {'answer_id': 'q2a3', 'answer_text': 'https://www.paypal.com/signin', 'is_correct': False},
                {'answer_id': 'q2a4', 'answer_text': 'https://help.paypal.com/contact', 'is_correct': False},
            ],
        },
        {
            'question_id': 'q3',
            'question_text': 'An email claims "Your account will be suspended in 24 hours unless you act now!" What phishing tactic is this?',
            'explanation': 'Creating a false sense of urgency is a common social engineering tactic. Attackers pressure victims into acting quickly without thinking critically about the request.',
            'answers': [
                {'answer_id': 'q3a1', 'answer_text': 'Spear phishing', 'is_correct': False},
                {'answer_id': 'q3a2', 'answer_text': 'Whaling', 'is_correct': False},
                {'answer_id': 'q3a3', 'answer_text': 'Urgency/fear tactics', 'is_correct': True},
                {'answer_id': 'q3a4', 'answer_text': 'Baiting', 'is_correct': False},
            ],
        },
        {
            'question_id': 'q4',
            'question_text': 'You receive an email from your CEO asking you to urgently wire $50,000 to a new vendor. The email address looks slightly different from the usual one. What type of attack is this?',
            'explanation': 'Whaling (or CEO fraud) targets high-value individuals by impersonating executives. Always verify unusual financial requests through a separate communication channel.',
            'answers': [
                {'answer_id': 'q4a1', 'answer_text': 'Vishing', 'is_correct': False},
                {'answer_id': 'q4a2', 'answer_text': 'Whaling / CEO fraud', 'is_correct': True},
                {'answer_id': 'q4a3', 'answer_text': 'Smishing', 'is_correct': False},
                {'answer_id': 'q4a4', 'answer_text': 'Pharming', 'is_correct': False},
            ],
        },
        {
            'question_id': 'q5',
            'question_text': 'What is the safest way to check if an email link is legitimate?',
            'explanation': 'Hovering over (without clicking) a link reveals the actual URL destination. This lets you verify whether it points to the legitimate domain before clicking.',
            'answers': [
                {'answer_id': 'q5a1', 'answer_text': 'Click the link and see where it goes', 'is_correct': False},
                {'answer_id': 'q5a2', 'answer_text': 'Hover over the link to preview the actual URL', 'is_correct': True},
                {'answer_id': 'q5a3', 'answer_text': 'Trust the link if the email looks official', 'is_correct': False},
                {'answer_id': 'q5a4', 'answer_text': 'Copy and paste the link into a new browser tab', 'is_correct': False},
            ],
        },
        {
            'question_id': 'q6',
            'question_text': 'Which email header detail is MOST useful for detecting a spoofed sender?',
            'explanation': 'The "Received" headers and SPF/DKIM/DMARC authentication results in email headers reveal the true origin of an email, even if the "From" address has been spoofed.',
            'answers': [
                {'answer_id': 'q6a1', 'answer_text': 'The subject line', 'is_correct': False},
                {'answer_id': 'q6a2', 'answer_text': 'The "From" display name', 'is_correct': False},
                {'answer_id': 'q6a3', 'answer_text': 'The "Received" headers and authentication results (SPF/DKIM)', 'is_correct': True},
                {'answer_id': 'q6a4', 'answer_text': 'The date and time sent', 'is_correct': False},
            ],
        },
        {
            'question_id': 'q7',
            'question_text': 'A colleague sends you a file called "Q4_Report.pdf.exe" via email. What should you do?',
            'explanation': 'Files with double extensions (like .pdf.exe) are a red flag. The actual file type is determined by the last extension — this is an executable, not a PDF. It could contain malware.',
            'image_path': '/static/quiz/attachment-warning.svg',
            'image_alt': 'Email snippet showing a suspicious attachment filename',
            'answers': [
                {'answer_id': 'q7a1', 'answer_text': 'Open it since it came from a colleague', 'is_correct': False},
                {'answer_id': 'q7a2', 'answer_text': 'Do not open it — the double extension is suspicious and it may be malware', 'is_correct': True},
                {'answer_id': 'q7a3', 'answer_text': 'Rename it to remove the .exe and then open it', 'is_correct': False},
                {'answer_id': 'q7a4', 'answer_text': 'Forward it to IT without any context', 'is_correct': False},
            ],
        },
        {
            'question_id': 'q8',
            'question_text': 'You get a text message saying "Your package delivery failed. Click here to reschedule:" followed by a shortened URL. This is an example of:',
            'explanation': 'Smishing (SMS phishing) uses text messages to trick victims. Shortened URLs hide the true destination. Legitimate delivery services direct you to their official app or website.',
            'answers': [
                {'answer_id': 'q8a1', 'answer_text': 'Vishing', 'is_correct': False},
                {'answer_id': 'q8a2', 'answer_text': 'Phishing', 'is_correct': False},
                {'answer_id': 'q8a3', 'answer_text': 'Smishing', 'is_correct': True},
                {'answer_id': 'q8a4', 'answer_text': 'Pretexting', 'is_correct': False},
            ],
        },
        {
            'question_id': 'q9',
            'question_text': 'What makes spear phishing more dangerous than regular phishing?',
            'explanation': 'Spear phishing uses personal information about the target (name, job role, recent activities) to craft convincing messages, making them much harder to detect than generic phishing emails.',
            'answers': [
                {'answer_id': 'q9a1', 'answer_text': 'It uses more advanced malware', 'is_correct': False},
                {'answer_id': 'q9a2', 'answer_text': 'It targets specific individuals with personalized content', 'is_correct': True},
                {'answer_id': 'q9a3', 'answer_text': 'It only works on mobile devices', 'is_correct': False},
                {'answer_id': 'q9a4', 'answer_text': "It requires physical access to the victim's computer", 'is_correct': False},
            ],
        },
        {
            'question_id': 'q10',
            'question_text': "Your organization's IT department asks everyone to enable Multi-Factor Authentication (MFA). Why does MFA help protect against phishing?",
            'explanation': 'Even if a phishing attack successfully captures your password, MFA requires a second verification factor (like a code from your phone), preventing unauthorized access with stolen credentials alone.',
            'answers': [
                {'answer_id': 'q10a1', 'answer_text': 'It blocks all phishing emails automatically', 'is_correct': False},
                {'answer_id': 'q10a2', 'answer_text': "It encrypts your password so it can't be stolen", 'is_correct': False},
                {'answer_id': 'q10a3', 'answer_text': "It adds an extra layer so stolen passwords alone aren't enough to access accounts", 'is_correct': True},
                {'answer_id': 'q10a4', 'answer_text': 'It makes your password longer and more complex', 'is_correct': False},
            ],
        },
    ]

    create_quiz(
        quiz_id=quiz_id,
        title='Phishing Awareness Fundamentals',
        description='Test your ability to identify phishing attempts, suspicious emails, and social engineering tactics.',
        questions=questions,
    )

    print(f'  - Quiz: "Phishing Awareness Fundamentals" with {len(questions)} questions')
    print('Database seeded successfully!')
