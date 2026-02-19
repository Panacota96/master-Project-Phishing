"""Seed DynamoDB tables with admin user and sample quiz data."""

import json
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

    data_path = os.path.join(os.path.dirname(__file__), 'data', 'quizzes.json')
    if not os.path.exists(data_path):
        print(f'  - Quiz data not found at {data_path}. Skipping quiz creation.')
    else:
        with open(data_path, 'r', encoding='utf-8') as handle:
            quizzes = json.load(handle)
        created_count = 0
        for quiz in quizzes:
            questions = quiz.get('questions', [])
            if len(questions) != 4:
                raise ValueError(f'Quiz {quiz.get(\"quiz_id\")} must have exactly 4 questions.')
            for question in questions:
                answers = question.get('answers', [])
                if len(answers) != 4:
                    raise ValueError(f'Question {question.get(\"question_id\")} must have 4 answers.')
                correct = [a for a in answers if a.get('is_correct')]
                if len(correct) != 1:
                    raise ValueError(f'Question {question.get(\"question_id\")} must have exactly 1 correct answer.')

            create_quiz(
                quiz_id=quiz['quiz_id'],
                title=quiz['title'],
                description=quiz.get('description', ''),
                video_url=quiz.get('video_url'),
                questions=questions,
            )
            created_count += 1

        print(f'  - Created {created_count} quizzes from data/quizzes.json')
    print('Database seeded successfully!')
