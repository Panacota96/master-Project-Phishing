# Adding a New Quiz

This guide covers the end-to-end process for adding a new quiz module to the platform.

---

## Step 1: Edit `data/quizzes.json`

Add a new entry to the quizzes array. Each quiz requires:

```json
{
  "quiz_id": "quiz-your-topic",
  "title": "Your Quiz Title",
  "description": "One-sentence description shown on the quiz list page.",
  "video_url": "https://phishing-app-dev-eu-west-3.s3.eu-west-3.amazonaws.com/videos/your-video.mp4",
  "questions": [
    {
      "question_id": "q1",
      "text": "Question text here?",
      "choices": [
        {"id": "a", "text": "Choice A"},
        {"id": "b", "text": "Choice B"},
        {"id": "c", "text": "Choice C"},
        {"id": "d", "text": "Choice D"}
      ],
      "correct_answer": "b",
      "explanation": "Explanation shown after the student answers."
    }
  ]
}
```

**Rules:**
- `quiz_id` must be unique across all quizzes (use lowercase kebab-case, e.g. `quiz-ceo-fraud`)
- Each quiz must have exactly 4 choices per question
- `correct_answer` must match one of the choice `id` values

---

## Step 2: Upload the Training Video

Videos are stored in S3 and served via direct S3 URL (not through Lambda).

```bash
# Upload to dev
aws s3 cp your-video.mp4 \
  s3://phishing-app-dev-eu-west-3/videos/your-video.mp4 \
  --region eu-west-3

# Upload to prod
aws s3 cp your-video.mp4 \
  s3://phishing-app-prod-eu-west-3/videos/your-video.mp4 \
  --region eu-west-3
```

Set `video_url` in `data/quizzes.json` to the corresponding S3 URL.

---

## Step 3: Seed DynamoDB

Push the updated quiz definitions to DynamoDB:

```bash
python seed_dynamodb.py
```

For deployed environments, the `deploy-dev.yml` workflow seeds automatically on push to `main` (unless `skip_seed=true`).

---

## Step 4: Verify

1. Log in as a student and confirm the new quiz appears in the quiz list.
2. Verify the video gate loads and the video plays.
3. Complete the quiz and check that the results page shows the correct score and rank badge.

---

## Existing Quizzes (Reference)

| Quiz ID | Title |
|---|---|
| `quiz-what-is-phishing` | What Is Phishing? |
| `quiz-spot-fake-link` | Spot the Fake Link |
| `quiz-imposter-email` | The Imposter Email |

Add your new quiz below these in `data/quizzes.json` to control display order.
