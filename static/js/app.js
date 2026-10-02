/* =========================================================
   CAMPUSAI — FRONTEND APPLICATION
   ========================================================= */

/* =========================================================
   PAGE CONFIGURATION
   ========================================================= */

const pageTitles = {
    dashboard: "Learn smarter. Plan better.",
    planner: "Build your personalized study plan.",
    tutor: "Learn difficult topics with AI.",
    quiz: "Practice with an AI-generated quiz."
};


/* =========================================================
   GLOBAL ELEMENTS
   ========================================================= */

const pages = document.querySelectorAll(".page");
const navItems = document.querySelectorAll(".nav-item");
const pageButtons = document.querySelectorAll("[data-page]");
const pageTitle = document.getElementById("pageTitle");
const themeToggle = document.getElementById("themeToggle");


/* =========================================================
   QUIZ STATE
   ========================================================= */

let currentQuiz = null;
let currentQuestionIndex = 0;
let selectedAnswers = {};
let quizSubmitting = false;


/* =========================================================
   PAGE NAVIGATION
   ========================================================= */

function showPage(pageName) {
    const targetPage = document.getElementById(pageName);

    if (!targetPage) {
        console.warn(`Page "${pageName}" was not found.`);
        return;
    }

    pages.forEach((page) => {
        page.classList.toggle("active", page.id === pageName);
    });

    navItems.forEach((button) => {
        button.classList.toggle(
            "active",
            button.dataset.page === pageName
        );
    });

    if (pageTitle) {
        pageTitle.textContent =
            pageTitles[pageName] || pageTitles.dashboard;
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


pageButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const page = button.dataset.page;

        if (page) {
            showPage(page);
        }
    });
});


/* =========================================================
   DARK MODE
   ========================================================= */

function updateThemeButton() {
    if (!themeToggle) {
        return;
    }

    const darkMode = document.body.classList.contains("dark");

    themeToggle.textContent = darkMode
        ? "☀️ Light Mode"
        : "🌙 Dark Mode";
}


function initializeTheme() {
    const savedTheme = localStorage.getItem("campusai-theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark");
    }

    updateThemeButton();
}


initializeTheme();


if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        document.body.classList.toggle("dark");

        const mode = document.body.classList.contains("dark")
            ? "dark"
            : "light";

        localStorage.setItem(
            "campusai-theme",
            mode
        );

        updateThemeButton();
    });
}


/* =========================================================
   HTML ESCAPING
   ========================================================= */

function escapeHtml(text) {
    return String(text ?? "").replace(
        /[&<>"']/g,
        (character) => {
            const entities = {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"
            };

            return entities[character];
        }
    );
}


/* =========================================================
   BASIC AI RESPONSE FORMATTER
   ========================================================= */

function formatResult(text) {
    let safe = escapeHtml(text);

    safe = safe.replace(
        /^### (.*)$/gm,
        "<h4>$1</h4>"
    );

    safe = safe.replace(
        /^## (.*)$/gm,
        "<h3>$1</h3>"
    );

    safe = safe.replace(
        /^# (.*)$/gm,
        "<h2>$1</h2>"
    );

    safe = safe.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );

    safe = safe.replace(
        /\n/g,
        "<br>"
    );

    return safe;
}


/* =========================================================
   TOAST NOTIFICATION
   ========================================================= */

function showToast(message, type = "info") {
    let container = document.getElementById(
        "toastContainer"
    );

    if (!container) {
        container = document.createElement("div");
        container.id = "toastContainer";
        container.className = "toast-container";

        document.body.appendChild(container);
    }

    const toast = document.createElement("div");

    toast.className = `toast toast-${type}`;

    toast.innerHTML = `
        <span class="toast-message">
            ${escapeHtml(message)}
        </span>
    `;

    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.add("show");
    });

    setTimeout(() => {
        toast.classList.remove("show");

        setTimeout(() => {
            toast.remove();
        }, 250);
    }, 3000);
}


/* =========================================================
   LOADING STATE
   ========================================================= */

function showLoading(target, message = "CampusAI is thinking...") {
    if (!target) {
        return;
    }

    target.innerHTML = `
        <div class="empty-state loading-state">
            <div class="loading">
                <div class="spinner"></div>

                <div class="loading-text">
                    <strong>${escapeHtml(message)}</strong>
                    <span>Please wait a moment...</span>
                </div>
            </div>
        </div>
    `;
}


/* =========================================================
   EMPTY STATE
   ========================================================= */

function renderEmptyState(
    target,
    icon = "✨",
    title = "Ready when you are",
    description = "Start using CampusAI to begin learning."
) {
    if (!target) {
        return;
    }

    target.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">
                ${icon}
            </div>

            <h3>
                ${escapeHtml(title)}
            </h3>

            <p>
                ${escapeHtml(description)}
            </p>
        </div>
    `;
}


/* =========================================================
   ERROR STATE
   ========================================================= */

function renderError(target, message) {
    if (!target) {
        return;
    }

    target.innerHTML = `
        <div class="empty-state error-state">
            <div class="empty-icon">
                ⚠️
            </div>

            <h3>
                Something went wrong
            </h3>

            <p>
                ${escapeHtml(
                    message || "An unexpected error occurred."
                )}
            </p>

            <button
                type="button"
                class="secondary-button"
                onclick="location.reload()"
            >
                ↻ Try Again
            </button>
        </div>
    `;
}


/* =========================================================
   AI RESULT RENDERING
   ========================================================= */

function renderResult(target, result) {
    if (!target) {
        return;
    }

    target.innerHTML = `
        <div class="result-top">
            <div>
                <span class="eyebrow">
                    AI RESPONSE
                </span>

                <h3>
                    CampusAI
                </h3>
            </div>

            <button
                class="voice-button"
                type="button"
                onclick="speakResponse(this)"
            >
                🎙️ Listen
            </button>
        </div>

        <div class="result-content">
            ${formatResult(result)}
        </div>

        <div class="audio-slot"></div>
    `;
}


/* =========================================================
   GENERIC AI REQUEST
   ========================================================= */

async function submitAI(feature, payload, target) {
    if (!target) {
        console.error("Result element not found.");
        return;
    }

    showLoading(target);

    try {
        const response = await fetch(
            "/api/generate",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    feature: feature,
                    payload: payload
                })
            }
        );

        let data;

        try {
            data = await response.json();
        } catch (jsonError) {
            throw new Error(
                "The server returned an invalid response."
            );
        }

        if (!response.ok) {
            throw new Error(
                data.error ||
                `Server returned ${response.status}.`
            );
        }

        if (
            data.result === undefined ||
            data.result === null ||
            data.result === ""
        ) {
            throw new Error(
                "The AI returned an empty response."
            );
        }

        renderResult(
            target,
            data.result
        );

        showToast(
            "AI response generated successfully.",
            "success"
        );
    } catch (error) {
        console.error(
            "AI request error:",
            error
        );

        renderError(
            target,
            error.message
        );

        showToast(
            error.message || "AI request failed.",
            "error"
        );
    }
}


/* =========================================================
   STUDY PLANNER
   ========================================================= */

const plannerForm =
    document.getElementById("plannerForm");


if (plannerForm) {
    plannerForm.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();

            const subjectElement =
                document.getElementById("subject");

            const hoursElement =
                document.getElementById("hours");

            const daysElement =
                document.getElementById("days");

            const levelElement =
                document.getElementById("plannerLevel");

            const target =
                document.getElementById("plannerResult");

            const subject =
                subjectElement
                    ? subjectElement.value.trim()
                    : "";

            const hours =
                hoursElement
                    ? hoursElement.value
                    : "";

            const days =
                daysElement
                    ? daysElement.value
                    : "";

            const level =
                levelElement
                    ? levelElement.value
                    : "Beginner";

            if (!subject) {
                renderError(
                    target,
                    "Please enter your subjects or topics."
                );

                return;
            }

            if (!hours || Number(hours) <= 0) {
                renderError(
                    target,
                    "Please enter a valid daily study time."
                );

                return;
            }

            if (!days || Number(days) <= 0) {
                renderError(
                    target,
                    "Please enter a valid number of days."
                );

                return;
            }

            await submitAI(
                "study_planner",
                {
                    subject: subject,
                    hours: hours,
                    days: days,
                    level: level
                },
                target
            );
        }
    );
}


/* =========================================================
   AI TUTOR
   ========================================================= */

const tutorForm =
    document.getElementById("tutorForm");


if (tutorForm) {
    tutorForm.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();

            const topicElement =
                document.getElementById("topic");

            const levelElement =
                document.getElementById("tutorLevel");

            const target =
                document.getElementById("tutorResult");

            const topic =
                topicElement
                    ? topicElement.value.trim()
                    : "";

            const level =
                levelElement
                    ? levelElement.value
                    : "Beginner";

            if (!topic) {
                renderError(
                    target,
                    "Please enter a topic."
                );

                return;
            }

            await submitAI(
                "tutor",
                {
                    topic: topic,
                    level: level
                },
                target
            );
        }
    );
}


/* =========================================================
   SMART QUIZ — START
   ========================================================= */

const quizForm =
    document.getElementById("quizForm");


if (quizForm) {
    quizForm.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();

            const topicElement =
                document.getElementById("quizTopic");

            const difficultyElement =
                document.getElementById("difficulty");

            const countElement =
                document.getElementById("count");

            const target =
                document.getElementById("quizResult");

            const topic =
                topicElement
                    ? topicElement.value.trim()
                    : "";

            const difficulty =
                difficultyElement
                    ? difficultyElement.value
                    : "Medium";

            let count =
                countElement
                    ? Number(countElement.value)
                    : 5;

            count = Math.max(
                1,
                Math.min(count || 5, 20)
            );

            if (!topic) {
                renderError(
                    target,
                    "Please enter a quiz topic."
                );

                return;
            }

            await startQuiz(
                topic,
                difficulty,
                count,
                target
            );
        }
    );
}


/* =========================================================
   START QUIZ API REQUEST
   ========================================================= */

async function startQuiz(
    topic,
    difficulty,
    count,
    target
) {
    if (!target) {
        console.error(
            "Quiz result element not found."
        );

        return;
    }

    showLoading(
        target,
        "Gemma is creating your quiz..."
    );

    try {
        const response = await fetch(
            "/api/quiz/start",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    topic: topic,
                    difficulty: difficulty,
                    count: count
                })
            }
        );

        let data;

        try {
            data = await response.json();
        } catch (jsonError) {
            throw new Error(
                "The server returned an invalid quiz response."
            );
        }

        if (!response.ok) {
            throw new Error(
                data.error ||
                `Quiz generation failed (${response.status}).`
            );
        }

        if (!data.success) {
            throw new Error(
                data.error ||
                "Could not create the quiz."
            );
        }

        if (!data.quiz) {
            throw new Error(
                "The server returned no quiz data."
            );
        }

        currentQuiz = data.quiz;

        currentQuestionIndex = 0;

        selectedAnswers = {};

        quizSubmitting = false;

        renderQuiz();

        showToast(
            "Your quiz is ready! Good luck 🎯",
            "success"
        );

    } catch (error) {
        console.error(
            "Quiz start error:",
            error
        );

        renderError(
            target,
            error.message
        );

        showToast(
            error.message || "Quiz generation failed.",
            "error"
        );
    }
}


/* =========================================================
   QUIZ VALIDATION
   ========================================================= */

function isValidQuiz(quiz) {
    if (!quiz || typeof quiz !== "object") {
        return false;
    }

    if (
        !Array.isArray(quiz.questions) ||
        quiz.questions.length === 0
    ) {
        return false;
    }

    return quiz.questions.every(
        (question) => {
            return (
                question &&
                question.question &&
                question.options &&
                ["A", "B", "C", "D"].every(
                    (key) =>
                        question.options[key]
                )
            );
        }
    );
}


/* =========================================================
   QUIZ RENDERING
   ========================================================= */

function renderQuiz() {
    const target =
        document.getElementById("quizResult");

    if (!target) {
        return;
    }

    if (!isValidQuiz(currentQuiz)) {
        renderError(
            target,
            "The quiz format is invalid."
        );

        return;
    }

    const total =
        currentQuiz.questions.length;

    const question =
        currentQuiz.questions[currentQuestionIndex];

    const progress =
        ((currentQuestionIndex + 1) / total) * 100;

    const selected =
        selectedAnswers[String(question.id)] || "";

    const isLastQuestion =
        currentQuestionIndex === total - 1;

    target.innerHTML = `
        <div class="quiz-container">

            <div class="quiz-header">

                <div>
                    <span class="eyebrow">
                        AI GENERATED QUIZ
                    </span>

                    <h3>
                        ${escapeHtml(
                            currentQuiz.title ||
                            "CampusAI Quiz"
                        )}
                    </h3>

                    <div class="quiz-meta">
                        <span>
                            📚 ${escapeHtml(
                                currentQuiz.topic || ""
                            )}
                        </span>

                        <span>
                            🎯 ${escapeHtml(
                                currentQuiz.difficulty || ""
                            )}
                        </span>
                    </div>
                </div>

                <div class="quiz-counter">
                    Question
                    <strong>
                        ${currentQuestionIndex + 1}
                    </strong>
                    /
                    ${total}
                </div>

            </div>


            <div class="quiz-progress">

                <div class="quiz-progress-track">
                    <div
                        class="quiz-progress-bar"
                        style="width: ${progress}%"
                    ></div>
                </div>

                <div class="quiz-progress-info">
                    <span>
                        Progress
                    </span>

                    <strong>
                        ${Math.round(progress)}%
                    </strong>
                </div>

            </div>


            <div class="quiz-question-card">

                <div class="question-number">
                    Question ${currentQuestionIndex + 1}
                </div>

                <h4 class="quiz-question">
                    ${escapeHtml(
                        question.question
                    )}
                </h4>


                <div class="quiz-options">

                    ${renderQuizOption(
                        question,
                        "A",
                        selected
                    )}

                    ${renderQuizOption(
                        question,
                        "B",
                        selected
                    )}

                    ${renderQuizOption(
                        question,
                        "C",
                        selected
                    )}

                    ${renderQuizOption(
                        question,
                        "D",
                        selected
                    )}

                </div>

            </div>


            <div class="quiz-navigation">

                <button
                    type="button"
                    class="secondary-button"
                    id="quizPreviousButton"
                    ${currentQuestionIndex === 0
                        ? "disabled"
                        : ""}
                >
                    ← Previous
                </button>


                <button
                    type="button"
                    class="primary-button"
                    id="quizNextButton"
                >
                    ${isLastQuestion
                        ? "Submit Quiz ✓"
                        : "Next Question →"}
                </button>

            </div>

        </div>
    `;


    attachQuizEvents();
}


/* =========================================================
   QUIZ OPTION
   ========================================================= */

function renderQuizOption(
    question,
    key,
    selected
) {
    const isSelected =
        selected === key;

    return `
        <button
            type="button"
            class="quiz-option ${
                isSelected
                    ? "selected"
                    : ""
            }"
            data-option="${key}"
        >

            <span class="option-letter">
                ${key}
            </span>

            <span class="option-text">
                ${escapeHtml(
                    question.options[key]
                )}
            </span>

            <span class="option-check">
                ${
                    isSelected
                        ? "✓"
                        : ""
                }
            </span>

        </button>
    `;
}


/* =========================================================
   QUIZ EVENT HANDLERS
   ========================================================= */

function attachQuizEvents() {
    const optionButtons =
        document.querySelectorAll(
            ".quiz-option"
        );

    optionButtons.forEach(
        (button) => {
            button.addEventListener(
                "click",
                () => {
                    selectQuizAnswer(
                        button.dataset.option
                    );
                }
            );
        }
    );


    const previousButton =
        document.getElementById(
            "quizPreviousButton"
        );

    const nextButton =
        document.getElementById(
            "quizNextButton"
        );


    if (previousButton) {
        previousButton.addEventListener(
            "click",
            () => {
                previousQuizQuestion();
            }
        );
    }


    if (nextButton) {
        nextButton.addEventListener(
            "click",
            () => {
                nextQuizQuestion();
            }
        );
    }
}


/* =========================================================
   SELECT QUIZ ANSWER
   ========================================================= */

function selectQuizAnswer(option) {
    if (!currentQuiz) {
        return;
    }

    const question =
        currentQuiz.questions[
            currentQuestionIndex
        ];

    if (!question) {
        return;
    }

    if (
        !["A", "B", "C", "D"].includes(option)
    ) {
        return;
    }

    selectedAnswers[
        String(question.id)
    ] = option;

    renderQuiz();
}


/* =========================================================
   NEXT QUIZ QUESTION
   ========================================================= */

function nextQuizQuestion() {
    if (!currentQuiz) {
        return;
    }

    const question =
        currentQuiz.questions[
            currentQuestionIndex
        ];

    const selected =
        selectedAnswers[
            String(question.id)
        ];


    if (!selected) {
        showToast(
            "Please select an answer first.",
            "warning"
        );

        return;
    }


    if (
        currentQuestionIndex <
        currentQuiz.questions.length - 1
    ) {
        currentQuestionIndex++;

        renderQuiz();

        return;
    }


    submitQuiz();
}


/* =========================================================
   PREVIOUS QUIZ QUESTION
   ========================================================= */

function previousQuizQuestion() {
    if (
        !currentQuiz ||
        currentQuestionIndex <= 0
    ) {
        return;
    }

    currentQuestionIndex--;

    renderQuiz();
}


/* =========================================================
   SUBMIT QUIZ
   ========================================================= */

async function submitQuiz() {
    if (!currentQuiz) {
        return;
    }

    if (quizSubmitting) {
        return;
    }

    const unanswered =
        currentQuiz.questions.filter(
            (question) => {
                return !selectedAnswers[
                    String(question.id)
                ];
            }
        );


    if (unanswered.length > 0) {
        showToast(
            `Please answer all questions. ${unanswered.length} remaining.`,
            "warning"
        );

        const firstUnansweredIndex =
            currentQuiz.questions.findIndex(
                (question) =>
                    !selectedAnswers[
                        String(question.id)
                    ]
            );

        if (firstUnansweredIndex >= 0) {
            currentQuestionIndex =
                firstUnansweredIndex;

            renderQuiz();
        }

        return;
    }


    quizSubmitting = true;


    const target =
        document.getElementById("quizResult");


    showLoading(
        target,
        "Checking your answers..."
    );


    try {
        const response = await fetch(
            "/api/quiz/submit",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    quiz_id:
                        currentQuiz.quiz_id,
                    answers:
                        selectedAnswers
                })
            }
        );


        let data;

        try {
            data = await response.json();
        } catch (jsonError) {
            throw new Error(
                "The server returned an invalid result."
            );
        }


        if (!response.ok) {
            throw new Error(
                data.error ||
                `Quiz submission failed (${response.status}).`
            );
        }


        if (!data.success || !data.result) {
            throw new Error(
                data.error ||
                "Could not grade the quiz."
            );
        }


        renderQuizResults(
            data.result
        );


        showToast(
            "Quiz submitted successfully! 🎉",
            "success"
        );

    } catch (error) {
        console.error(
            "Quiz submission error:",
            error
        );

        renderError(
            target,
            error.message
        );

        showToast(
            error.message ||
            "Quiz submission failed.",
            "error"
        );

    } finally {
        quizSubmitting = false;
    }
}


/* =========================================================
   QUIZ RESULT
   ========================================================= */

function renderQuizResults(result) {
    const target =
        document.getElementById("quizResult");

    if (!target) {
        return;
    }


    const percentage =
        Number(result.percentage || 0);

    const score =
        Number(result.score || 0);

    const total =
        Number(result.total || 0);

    const correct =
        Number(result.correct || 0);

    const incorrect =
        Number(result.incorrect || 0);


    let scoreMessage;

    if (percentage >= 90) {
        scoreMessage = "Excellent work! 🌟";
    } else if (percentage >= 75) {
        scoreMessage = "Great job! Keep it up! 🎉";
    } else if (percentage >= 50) {
        scoreMessage = "Good effort. Keep practicing! 💪";
    } else {
        scoreMessage = "Keep learning and try again! 📚";
    }


    target.innerHTML = `
        <div class="quiz-results">

            <div class="results-header">

                <span class="eyebrow">
                    QUIZ COMPLETED
                </span>

                <h3>
                    ${escapeHtml(
                        result.title ||
                        "Quiz Results"
                    )}
                </h3>

                <p>
                    ${escapeHtml(
                        scoreMessage
                    )}
                </p>

            </div>


            <div class="score-card">

                <div class="score-circle">

                    <div class="score-value">
                        ${percentage}%
                    </div>

                    <div class="score-label">
                        Score
                    </div>

                </div>


                <div class="score-details">

                    <div class="score-item">
                        <span>Correct</span>
                        <strong>
                            ${correct}
                        </strong>
                    </div>

                    <div class="score-item">
                        <span>Incorrect</span>
                        <strong>
                            ${incorrect}
                        </strong>
                    </div>

                    <div class="score-item">
                        <span>Total</span>
                        <strong>
                            ${total}
                        </strong>
                    </div>

                </div>

            </div>


            <div class="quiz-result-actions">

                <button
                    type="button"
                    class="secondary-button"
                    id="quizTryAgain"
                >
                    ↻ Try Again
                </button>

                <button
                    type="button"
                    class="primary-button"
                    id="quizNewQuiz"
                >
                    ✨ New Quiz
                </button>

            </div>


            <div class="review-header">

                <span class="eyebrow">
                    DETAILED REVIEW
                </span>

                <h3>
                    Review your answers
                </h3>

                <p>
                    Learn from each answer and understand why it is correct.
                </p>

            </div>


            <div class="quiz-review-list">

                ${
                    Array.isArray(result.results)
                        ? result.results
                            .map(
                                (
                                    item,
                                    index
                                ) =>
                                    renderQuizReview(
                                        item,
                                        index
                                    )
                            )
                            .join("")
                        : ""
                }

            </div>

        </div>
    `;


    const tryAgainButton =
        document.getElementById(
            "quizTryAgain"
        );

    const newQuizButton =
        document.getElementById(
            "quizNewQuiz"
        );


    if (tryAgainButton) {
        tryAgainButton.addEventListener(
            "click",
            () => {
                restartQuiz();
            }
        );
    }


    if (newQuizButton) {
        newQuizButton.addEventListener(
            "click",
            () => {
                resetQuiz();
            }
        );
    }
}


/* =========================================================
   QUIZ REVIEW ITEM
   ========================================================= */

function renderQuizReview(
    item,
    index
) {
    const isCorrect =
        Boolean(item.is_correct);

    const userAnswer =
        item.user_answer
            ? item.user_answer
            : "Not answered";

    const correctAnswer =
        item.correct_answer || "";


    const userAnswerText =
        item.options &&
        item.options[userAnswer]
            ? item.options[userAnswer]
            : userAnswer;


    const correctAnswerText =
        item.options &&
        item.options[correctAnswer]
            ? item.options[correctAnswer]
            : correctAnswer;


    return `
        <div
            class="review-item ${
                isCorrect
                    ? "review-correct"
                    : "review-incorrect"
            }"
        >

            <div class="review-status">
                ${
                    isCorrect
                        ? "✓ Correct"
                        : "✕ Incorrect"
                }
            </div>


            <div class="review-question">
                <strong>
                    Q${index + 1}.
                </strong>

                ${escapeHtml(
                    item.question
                )}
            </div>


            <div class="review-answer-grid">

                <div class="review-answer user-answer">

                    <span>
                        Your answer
                    </span>

                    <strong>
                        ${escapeHtml(
                            userAnswer
                        )}
                        —
                        ${escapeHtml(
                            userAnswerText
                        )}
                    </strong>

                </div>


                <div class="review-answer correct-answer">

                    <span>
                        Correct answer
                    </span>

                    <strong>
                        ${escapeHtml(
                            correctAnswer
                        )}
                        —
                        ${escapeHtml(
                            correctAnswerText
                        )}
                    </strong>

                </div>

            </div>


            <div class="review-explanation">

                <span>
                    💡 Explanation
                </span>

                <p>
                    ${escapeHtml(
                        item.explanation ||
                        "No explanation available."
                    )}
                </p>

            </div>

        </div>
    `;
}


/* =========================================================
   RESTART CURRENT QUIZ
   ========================================================= */

function restartQuiz() {
    if (!currentQuiz) {
        return;
    }

    currentQuestionIndex = 0;

    selectedAnswers = {};

    quizSubmitting = false;

    renderQuiz();

    showToast(
        "Quiz restarted. Give it another try! 🚀",
        "info"
    );
}


/* =========================================================
   RESET QUIZ
   ========================================================= */

function resetQuiz() {
    currentQuiz = null;

    currentQuestionIndex = 0;

    selectedAnswers = {};

    quizSubmitting = false;


    const target =
        document.getElementById("quizResult");


    if (target) {
        renderEmptyState(
            target,
            "🧠",
            "Ready for a new challenge?",
            "Choose a topic, difficulty, and number of questions to generate your next AI quiz."
        );
    }


    showToast(
        "Ready to create a new quiz.",
        "info"
    );
}


/* =========================================================
   ELEVENLABS TEXT-TO-SPEECH
   ========================================================= */

async function speakResponse(button) {
    if (!button) {
        return;
    }

    const panel =
        button.closest(".result-panel");


    if (!panel) {
        console.error(
            "Result panel not found."
        );

        return;
    }


    const resultElement =
        panel.querySelector(
            ".result-content"
        );


    const audioSlot =
        panel.querySelector(
            ".audio-slot"
        );


    if (
        !resultElement ||
        !audioSlot
    ) {
        console.error(
            "Result content/audio slot not found."
        );

        return;
    }


    const text =
        resultElement.innerText.trim();


    if (!text) {
        showToast(
            "There is no text to convert to speech.",
            "warning"
        );

        return;
    }


    button.disabled = true;

    button.textContent =
        "⏳ Generating...";


    try {
        const response =
            await fetch(
                "/api/tts",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        text: text
                    })
                }
            );


        if (!response.ok) {
            let errorMessage =
                "Voice generation failed.";


            try {
                const data =
                    await response.json();

                errorMessage =
                    data.error ||
                    errorMessage;

            } catch (jsonError) {
                console.error(
                    "Could not parse TTS error:",
                    jsonError
                );
            }


            throw new Error(
                errorMessage
            );
        }


        const audioBlob =
            await response.blob();


        if (!audioBlob.size) {
            throw new Error(
                "ElevenLabs returned empty audio data."
            );
        }


        const audioUrl =
            URL.createObjectURL(
                audioBlob
            );


        audioSlot.innerHTML = `
            <audio
                controls
                autoplay
                src="${audioUrl}"
            >
            </audio>
        `;


        button.textContent =
            "🔊 Generated";


        showToast(
            "Voice generated successfully.",
            "success"
        );

    } catch (error) {
        console.error(
            "TTS error:",
            error
        );

        button.textContent =
            "🎙️ Listen";


        showToast(
            error.message ||
            "Voice generation failed.",
            "error"
        );

    } finally {
        button.disabled = false;
    }
}


/* =========================================================
   KEYBOARD SUPPORT FOR QUIZ
   ========================================================= */

document.addEventListener(
    "keydown",
    (event) => {
        if (!currentQuiz) {
            return;
        }

        const activePage =
            document.querySelector(
                ".page.active"
            );

        if (
            !activePage ||
            activePage.id !== "quiz"
        ) {
            return;
        }


        const key =
            event.key.toUpperCase();


        if (
            ["A", "B", "C", "D"].includes(key)
        ) {
            selectQuizAnswer(key);
        }


        if (event.key === "ArrowRight") {
            nextQuizQuestion();
        }


        if (event.key === "ArrowLeft") {
            previousQuizQuestion();
        }
    }
);


/* =========================================================
   INITIAL QUIZ STATE
   ========================================================= */

function initializeQuiz() {
    const target =
        document.getElementById(
            "quizResult"
        );

    if (!target) {
        return;
    }


    renderEmptyState(
        target,
        "🧠",
        "Ready to test yourself?",
        "Generate an AI-powered quiz and challenge your understanding."
    );
}


initializeQuiz();


/* =========================================================
   GLOBAL FUNCTIONS
   ========================================================= */

window.showPage = showPage;
window.speakResponse = speakResponse;
window.startQuiz = startQuiz;
window.restartQuiz = restartQuiz;
window.resetQuiz = resetQuiz;


/* =========================================================
   DEBUG
   ========================================================= */

console.log(
    "🎓 CampusAI frontend loaded successfully."
);