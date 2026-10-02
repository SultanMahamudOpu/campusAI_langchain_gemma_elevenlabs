from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.gemma import get_gemma


# ============================================================
# Gemma LLM
# ============================================================

llm = get_gemma()


# ============================================================
# Helper: Clean Gemma/LangChain Response
# ============================================================

def _content(response: Any) -> str:
    """
    Extract only final user-facing text from a
    Gemma/LangChain response.

    Handles:
    - Normal string responses
    - AIMessage with string content
    - AIMessage with list-based content blocks
    - Thinking/reasoning blocks
    """

    content = response.content if hasattr(response, "content") else response

    # --------------------------------------------------------
    # String response
    # --------------------------------------------------------

    if isinstance(content, str):
        return content.strip()

    # --------------------------------------------------------
    # List-based content
    # --------------------------------------------------------

    if isinstance(content, list):
        text_parts = []

        for block in content:

            if isinstance(block, dict):

                block_type = block.get("type")

                # Ignore hidden reasoning
                if block_type in {
                    "thinking",
                    "reasoning",
                    "analysis",
                }:
                    continue

                if block_type == "text":
                    text = block.get("text", "")

                    if text:
                        text_parts.append(str(text))

                elif "text" in block:
                    text = block.get("text", "")

                    if text:
                        text_parts.append(str(text))

            elif isinstance(block, str):
                text_parts.append(block)

        return "\n".join(text_parts).strip()

    return str(content).strip()


# ============================================================
# Helper: Extract JSON from Gemma response
# ============================================================

def _extract_json(text: str) -> dict:
    """
    Extract JSON object from Gemma response.

    Handles:
    - Pure JSON
    - ```json ... ```
    - Extra text surrounding JSON
    """

    text = text.strip()

    # Remove Markdown code fences
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    # Try direct JSON parsing
    try:
        data = json.loads(text)

        if isinstance(data, dict):
            return data

    except json.JSONDecodeError:
        pass

    # Try finding JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:

        candidate = text[start:end + 1]

        try:
            data = json.loads(candidate)

            if isinstance(data, dict):
                return data

        except json.JSONDecodeError:
            pass

    raise ValueError(
        "Gemma returned an invalid quiz format. "
        "Expected a valid JSON object."
    )


# ============================================================
# Common System Instruction
# ============================================================

COMMON_RULES = """
You are CampusAI, an intelligent academic learning assistant.

You help university students learn more effectively.

General rules:

- Be accurate and educational.
- Be practical and actionable.
- Use clear language.
- Keep responses reasonably concise.
- Avoid unnecessary repetition.
- Do not expose hidden reasoning.
- Do not output chain-of-thought.
- Return only the requested final output.
"""


# ============================================================
# Study Plan Prompt
# ============================================================

study_plan_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        COMMON_RULES
        + """

You are specifically responsible for creating
personalized university study plans.

Create a practical and realistic study plan.

The plan should:

- Prioritize difficult or high-value topics.
- Divide study time realistically.
- Include short breaks.
- Include daily measurable tasks.
- Include revision sessions.
- Include practice or self-testing.
- Avoid unrealistic workloads.
- Consider the student's academic level.
- Provide a clear day-by-day structure.

Return ONLY the final study plan.
"""
    ),

    (
        "human",
        """
Create a {days}-day personalized study plan.

Subject / Goal:
{subject}

Daily study time:
{hours} hours

Academic level:
{level}

Design the schedule for a university student.

Include:

1. Daily study objectives
2. Topics/tasks for each day
3. Study blocks
4. Short breaks
5. Revision
6. Practice/self-testing
7. Final review

Make the plan realistic and easy to follow.
"""
    ),
])


# ============================================================
# AI Tutor Prompt
# ============================================================

explanation_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        COMMON_RULES
        + """

You are CampusAI's university AI tutor.

Explain concepts clearly and accurately according
to the student's academic level.

Structure the response as:

## 1. Simple Explanation

Explain the concept in easy language.

## 2. Intuitive Analogy

Give a simple real-world analogy when appropriate.

## 3. Example

Provide one clear academic or practical example.

## 4. Key Points

List the most important concepts.

## 5. Practice Question

Give one short question to test understanding.

Rules:

- Beginner-friendly language when appropriate.
- Avoid unnecessary technical complexity.
- Use examples whenever helpful.
- Maintain academic accuracy.
- Do not make the answer unnecessarily long.

Return ONLY the final explanation.
"""
    ),

    (
        "human",
        """
Explain this topic:

{topic}

Student level:

{level}

Teach the topic as if you are an excellent
university instructor helping the student understand
both the concept and its practical application.
"""
    ),
])


# ============================================================
# Interactive Quiz Prompt
# ============================================================

quiz_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        COMMON_RULES + """
You are CampusAI's interactive university quiz generator.

Your task is to create a high-quality multiple-choice quiz
for undergraduate university students.

The quiz will be used by an interactive web application.

IMPORTANT OUTPUT RULES:
- Return ONLY valid JSON.
- Do NOT use Markdown.
- Do NOT use code fences.
- Do NOT write explanations outside JSON.
- Do NOT add any text before or after the JSON.
- The JSON must be directly parseable using Python json.loads().

The JSON must follow exactly this structure:

{{
  "title": "Quiz title",
  "topic": "Quiz topic",
  "difficulty": "Difficulty level",
  "questions": [
    {{
      "id": 1,
      "question": "Question text",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct_answer": "A",
      "explanation": "Brief explanation of the correct answer"
    }}
  ]
}}

STRICT QUIZ RULES:

1. Generate exactly the requested number of questions.

2. Every question must have exactly four options:
   A, B, C, and D.

3. Each question must have exactly ONE correct answer.

4. The "correct_answer" field must contain only:
   A, B, C, or D.

5. Every question must include an explanation.

6. The explanation should briefly explain why
   the correct answer is correct.

7. Questions should test:
   - conceptual understanding
   - application
   - reasoning
   - practical knowledge

8. Avoid ambiguous questions.

9. Make incorrect options plausible.

10. Do not make the correct option obviously longer
    than the other options.

11. Do not repeat questions.

12. Questions must match the requested difficulty.

13. Questions must be appropriate for undergraduate
    university students.

14. Do not reveal the answer in the question itself.

15. The answer must exist only in "correct_answer".

16. Do not create a separate answer key.

17. Return valid JSON only.

18. Do not use trailing commas.

19. Make sure all JSON strings use double quotes.

20. Keep the quiz academically meaningful rather than
    relying only on simple memorization.

SECURITY RULE:

The application will initially hide the
"correct_answer" and "explanation" fields from students.

Therefore, keep those fields inside the server-side
quiz data and never expose them in the public quiz response.
"""
    ),
    (
        "human",
        """
Generate exactly {number} multiple-choice questions.

Topic:
{topic}

Difficulty:
{difficulty}

The quiz is intended for university students.

Return ONLY the required JSON object.
Do not include Markdown or any additional text.
"""
    ),
])

# ============================================================
# Chains
# ============================================================

study_plan_chain = study_plan_prompt | llm

explanation_chain = explanation_prompt | llm

quiz_chain = quiz_prompt | llm


# ============================================================
# Generate Study Plan
# ============================================================

def generate_study_plan(
    subject,
    hours,
    days,
    level,
):
    """
    Generate a personalized multi-day study plan.
    """

    response = study_plan_chain.invoke({
        "subject": subject,
        "hours": hours,
        "days": days,
        "level": level,
    })

    return _content(response)


# ============================================================
# Explain Topic
# ============================================================

def explain_topic(
    topic,
    level,
):
    """
    Generate a structured explanation
    of an academic topic.
    """

    response = explanation_chain.invoke({
        "topic": topic,
        "level": level,
    })

    return _content(response)


# ============================================================
# Generate Interactive Quiz
# ============================================================

def generate_quiz(
    topic,
    difficulty,
    count,
):
    """
    Generate a structured interactive quiz.

    Returns:
        {
            "title": "...",
            "topic": "...",
            "difficulty": "...",
            "questions": [
                {
                    "id": 1,
                    "question": "...",
                    "options": {
                        "A": "...",
                        "B": "...",
                        "C": "...",
                        "D": "..."
                    },
                    "correct_answer": "A",
                    "explanation": "..."
                }
            ]
        }
    """

    # --------------------------------------------------------
    # Validate count
    # --------------------------------------------------------

    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 5

    count = max(1, min(count, 20))

    # --------------------------------------------------------
    # Validate topic
    # --------------------------------------------------------

    topic = str(topic or "").strip()

    if not topic:
        raise ValueError("Quiz topic is required.")

    # --------------------------------------------------------
    # Validate difficulty
    # --------------------------------------------------------

    difficulty = str(difficulty or "Medium").strip()

    if not difficulty:
        difficulty = "Medium"

    # --------------------------------------------------------
    # Generate quiz
    # --------------------------------------------------------

    response = quiz_chain.invoke({
        "topic": topic,
        "difficulty": difficulty,
        "number": count,
    })

    raw_text = _content(response)

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    quiz_data = _extract_json(raw_text)

    # --------------------------------------------------------
    # Validate top-level structure
    # --------------------------------------------------------

    if not isinstance(quiz_data, dict):
        raise ValueError("Invalid quiz response.")

    questions = quiz_data.get("questions")

    if not isinstance(questions, list):
        raise ValueError(
            "Quiz response does not contain a valid questions list."
        )

    if len(questions) != count:
        raise ValueError(
            f"Expected {count} questions, "
            f"but Gemma returned {len(questions)}."
        )

    # --------------------------------------------------------
    # Validate each question
    # --------------------------------------------------------

    cleaned_questions = []

    for index, question in enumerate(questions, start=1):

        if not isinstance(question, dict):
            raise ValueError(
                f"Question {index} has an invalid format."
            )

        question_text = str(
            question.get("question", "")
        ).strip()

        options = question.get("options")

        correct_answer = str(
            question.get("correct_answer", "")
        ).strip().upper()

        explanation = str(
            question.get("explanation", "")
        ).strip()

        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------

        if not question_text:
            raise ValueError(
                f"Question {index} is empty."
            )

        if not isinstance(options, dict):
            raise ValueError(
                f"Question {index} has invalid options."
            )

        required_options = ["A", "B", "C", "D"]

        for option_key in required_options:

            if option_key not in options:
                raise ValueError(
                    f"Question {index} is missing option {option_key}."
                )

            if not str(options[option_key]).strip():
                raise ValueError(
                    f"Question {index} has an empty option."
                )

        if correct_answer not in required_options:
            raise ValueError(
                f"Question {index} has invalid correct answer."
            )

        if not explanation:
            raise ValueError(
                f"Question {index} has no explanation."
            )

        # ----------------------------------------------------
        # Clean question
        # ----------------------------------------------------

        cleaned_questions.append({
            "id": index,
            "question": question_text,
            "options": {
                "A": str(options["A"]).strip(),
                "B": str(options["B"]).strip(),
                "C": str(options["C"]).strip(),
                "D": str(options["D"]).strip(),
            },
            "correct_answer": correct_answer,
            "explanation": explanation,
        })

    # --------------------------------------------------------
    # Final quiz object
    # --------------------------------------------------------

    return {
        "title": str(
            quiz_data.get(
                "title",
                f"{topic} Quiz"
            )
        ).strip(),

        "topic": topic,

        "difficulty": difficulty,

        "questions": cleaned_questions,
    }


# ============================================================
# Hide Answers Before Sending Quiz to Frontend
# ============================================================

def get_public_quiz(quiz_data):
    """
    Remove correct answers and explanations.

    This version is safe to send to the frontend
    before the user submits the quiz.
    """

    if not isinstance(quiz_data, dict):
        raise ValueError("Invalid quiz data.")

    public_questions = []

    for question in quiz_data.get("questions", []):

        public_questions.append({
            "id": question["id"],
            "question": question["question"],
            "options": question["options"],
        })

    return {
        "title": quiz_data.get("title", "CampusAI Quiz"),
        "topic": quiz_data.get("topic", ""),
        "difficulty": quiz_data.get("difficulty", ""),
        "questions": public_questions,
    }


# ============================================================
# Grade Interactive Quiz
# ============================================================

def grade_quiz(
    quiz_data,
    user_answers,
):
    """
    Grade an interactive quiz.

    user_answers example:

    {
        "1": "A",
        "2": "C",
        "3": "B"
    }

    Returns score, percentage and detailed review.
    """

    if not isinstance(quiz_data, dict):
        raise ValueError("Invalid quiz data.")

    if not isinstance(user_answers, dict):
        raise ValueError("Invalid submitted answers.")

    questions = quiz_data.get("questions", [])

    if not questions:
        raise ValueError("Quiz contains no questions.")

    results = []

    correct_count = 0

    # --------------------------------------------------------
    # Grade every question
    # --------------------------------------------------------

    for question in questions:

        question_id = str(question["id"])

        user_answer = user_answers.get(
            question_id
        )

        if user_answer is not None:
            user_answer = str(
                user_answer
            ).strip().upper()

        correct_answer = str(
            question["correct_answer"]
        ).strip().upper()

        is_correct = (
            user_answer == correct_answer
        )

        if is_correct:
            correct_count += 1

        results.append({
            "id": question["id"],
            "question": question["question"],
            "options": question["options"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": question["explanation"],
        })

    # --------------------------------------------------------
    # Calculate score
    # --------------------------------------------------------

    total = len(questions)

    percentage = round(
        (correct_count / total) * 100,
        2,
    )

    return {
        "title": quiz_data.get(
            "title",
            "CampusAI Quiz"
        ),

        "topic": quiz_data.get(
            "topic",
            ""
        ),

        "difficulty": quiz_data.get(
            "difficulty",
            ""
        ),

        "score": correct_count,

        "total": total,

        "percentage": percentage,

        "correct": correct_count,

        "incorrect": total - correct_count,

        "results": results,
    }