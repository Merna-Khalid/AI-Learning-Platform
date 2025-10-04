from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    Enum,
    JSON,
    Table,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class SourceType(enum.Enum):
    PDF = "pdf"
    VIDEO = "video"
    ARTICLE = "article"
    SLIDES = "slides"
    OTHER = "other"

    def __str__(self):
        return self.value

class QuestionType(enum.Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    CODING = "coding"
    FILL_BLANK = "fill_blank"
    DIAGRAM = "diagram"
    TRUE_FALSE = "true_false"
    MATH_PROBLEM = "math_problem"
    MATCHING = "matching"
    ESSAY = "essay"

    def __str__(self):
        return self.value

class QuizType(enum.Enum):
    PRACTICE = "practice"
    EXAM = "exam"
    TIMED_EXAM = "timed_exam"
    EXERCISE = "exercise"

    def __str__(self):
        return self.value

class DifficultyLevel(enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

    def __str__(self):
        return self.value

class GradingMethod(enum.Enum):
    AUTO = "auto"
    MANUAL = "manual"
    PEER = "peer"
    AI_ASSISTED = "ai_assisted"

    def __str__(self):
        return self.value

class SubmissionStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    GRADED = "graded"
    REVIEW_PENDING = "review_pending"

    def __str__(self):
        return self.value


# =========================
# LINKING TABLES
# =========================
quiz_topics = Table(
    "quiz_topics",
    Base.metadata,
    Column("quiz_id", ForeignKey("quiz.id"), primary_key=True),
    Column("topic_id", ForeignKey("topic.id"), primary_key=True),
)

material_topics = Table(
    "material_topics",
    Base.metadata,
    Column("material_id", ForeignKey("material.id"), primary_key=True),
    Column("topic_id", ForeignKey("topic.id"), primary_key=True),
)

exam_topics = Table(
    "exam_topics",
    Base.metadata,
    Column("exam_id", ForeignKey("exam.id"), primary_key=True),
    Column("topic_id", ForeignKey("topic.id"), primary_key=True),
)


# =========================
# MAIN TABLES
# =========================

class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String(50), nullable=True)
    date_created = Column(DateTime, default=datetime.utcnow)
    num_of_topics = Column(Integer, default=0)
    ingestion_status = Column(String, default="pending")

    materials = relationship("Material", back_populates="course", cascade="all, delete")
    topics = relationship("Topic", back_populates="course", cascade="all, delete")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete")
    exams = relationship("Exam", back_populates="course", cascade="all, delete")
    exercises = relationship("Exercise", back_populates="course", cascade="all, delete")
    progress = relationship("Progress", back_populates="course", uselist=False)


class Material(Base):
    __tablename__ = "material"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    date_uploaded = Column(DateTime, default=datetime.utcnow)
    source_type = Column(
        Enum(SourceType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    content_type = Column(String(50), default="lecture")  # lecture, tutorial, reference
    file_path = Column(String(500), nullable=False)
    extracted_topics = Column(JSON, nullable=True)
    ingestion_status = Column(String, default="pending")

    course = relationship("Course", back_populates="materials")
    topics = relationship("Topic", secondary=material_topics, back_populates="materials")


class Topic(Base):
    __tablename__ = "topic"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    course = relationship("Course", back_populates="topics")
    quizzes = relationship("Quiz", secondary=quiz_topics, back_populates="topics")
    exams = relationship("Exam", secondary=exam_topics, back_populates="topics")
    materials = relationship("Material", secondary=material_topics, back_populates="topics")
    questions = relationship("Question", back_populates="topic")
    exercises = relationship("Exercise", back_populates="topic")


class Quiz(Base):
    __tablename__ = "quiz"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    num_of_questions = Column(Integer, default=0)
    prev_grade = Column(Float, nullable=True)
    quiz_type = Column(
        Enum(QuizType, values_callable=lambda obj: [e.value for e in obj]),
        default=QuizType.PRACTICE,
    )
 
    date_created = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="quizzes")
    topics = relationship("Topic", secondary=quiz_topics, back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete")
    attempts = relationship("Attempt", back_populates="quiz", cascade="all, delete")


class Question(Base):
    __tablename__ = "question"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quiz.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topic.id"), nullable=True)
    text = Column(Text, nullable=False)
    type = Column(
        Enum(QuestionType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    diagram_ref = Column(String(500), nullable=True)
    code_stub = Column(Text, nullable=True)
    # Enhanced fields for exercise generation
    difficulty = Column(
        Enum(DifficultyLevel, values_callable=lambda obj: [e.value for e in obj]),
        default=DifficultyLevel.MEDIUM,
    )
    extra_metadata = Column(JSON, nullable=True)  # For storing additional data like options, answers, etc.

    quiz = relationship("Quiz", back_populates="questions")
    topic = relationship("Topic", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete")


class Attempt(Base):
    __tablename__ = "attempt"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quiz.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    time_taken = Column(Integer, nullable=True)  # seconds
    final_grade = Column(Float, nullable=True)
    grading_notes = Column(Text, nullable=True)

    quiz = relationship("Quiz", back_populates="attempts")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete")


class Answer(Base):
    __tablename__ = "answer"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("question.id"), nullable=False)
    attempt_id = Column(Integer, ForeignKey("attempt.id"), nullable=False)
    answer_text = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    grading_notes = Column(Text, nullable=True)

    question = relationship("Question", back_populates="answers")
    attempt = relationship("Attempt", back_populates="answers")


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    num_of_topics_mastered = Column(Integer, default=0)
    num_of_quizzes_taken = Column(Integer, default=0)
    num_of_exercises_completed = Column(Integer, default=0)
    num_of_exams_taken = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course", back_populates="progress")

class Exercise(Base):
    __tablename__ = "exercise"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topic.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    question_type = Column(
        Enum(QuestionType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    difficulty = Column(
        Enum(DifficultyLevel, values_callable=lambda obj: [e.value for e in obj]),
        default=DifficultyLevel.MEDIUM,
    )

    question_data = Column(JSON, nullable=False)  # Full question data including options, answers, etc.
    solution_data = Column(JSON, nullable=True)   # Reference solutions and explanations
    extra_metadata = Column(JSON, nullable=True)        # Additional metadata like tags, learning objectives
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course", back_populates="exercises")
    topic = relationship("Topic", back_populates="exercises")
    submissions = relationship("ExerciseSubmission", back_populates="exercise", cascade="all, delete")


class Exam(Base):
    __tablename__ = "exam"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    exam_type = Column(
        Enum(QuizType, values_callable=lambda obj: [e.value for e in obj]),
        default=QuizType.TIMED_EXAM,
    )
    duration_minutes = Column(Integer, nullable=False)  # Exam duration in minutes
    total_points = Column(Integer, default=100)
    difficulty = Column(
        Enum(DifficultyLevel, values_callable=lambda obj: [e.value for e in obj]),
        default=DifficultyLevel.MEDIUM,
    )
    questions_data = Column(JSON, nullable=False)  # Array of question objects or IDs
    instructions = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course", back_populates="exams")
    topics = relationship("Topic", secondary=exam_topics, back_populates="exams")
    submissions = relationship("ExamSubmission", back_populates="exam", cascade="all, delete")


class ExerciseSubmission(Base):
    __tablename__ = "exercise_submission"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercise.id"), nullable=False)
    student_id = Column(String(100), nullable=False)  # Could be ForeignKey to User table if you have one
    answers = Column(JSON, nullable=False)  # Student's answers
    submitted_at = Column(DateTime, default=datetime.utcnow)
    time_spent = Column(Integer, default=0)  # Time spent in seconds
    status = Column(
        Enum(SubmissionStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=SubmissionStatus.DRAFT,
    )
    auto_feedback = Column(Text, nullable=True)  # AI-generated feedback
    manual_feedback = Column(Text, nullable=True)  # Teacher feedback

    exercise = relationship("Exercise", back_populates="submissions")
    grades = relationship("Grade", back_populates="exercise_submission", cascade="all, delete")


class ExamSubmission(Base):
    __tablename__ = "exam_submission"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exam.id"), nullable=False)
    student_id = Column(String(100), nullable=False)
    answers = Column(JSON, nullable=False)  # All exam answers
    started_at = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime, nullable=True)  # Null if still in progress
    time_spent = Column(Integer, nullable=True)  # Total time spent in seconds
    status = Column(
        Enum(SubmissionStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=SubmissionStatus.DRAFT,
    )
    auto_grade = Column(Float, nullable=True)  # Auto-calculated grade
    manual_grade = Column(Float, nullable=True)  # Teacher-adjusted grade
    final_grade = Column(Float, nullable=True)  # Final grade after review
    feedback = Column(Text, nullable=True)

    exam = relationship("Exam", back_populates="submissions")
    grades = relationship("Grade", back_populates="exam_submission", cascade="all, delete")


class Grade(Base):
    __tablename__ = "grade"

    id = Column(Integer, primary_key=True, index=True)
    # Flexible foreign key - can be linked to either exercise or exam submission
    exercise_submission_id = Column(Integer, ForeignKey("exercise_submission.id"), nullable=True)
    exam_submission_id = Column(Integer, ForeignKey("exam_submission.id"), nullable=True)
    
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    detailed_feedback = Column(JSON, nullable=True)  # Structured feedback per question
    grading_method = Column(
        Enum(GradingMethod, values_callable=lambda obj: [e.value for e in obj]),
        default=GradingMethod.AUTO,
    )
    graded_by = Column(String(100), nullable=True)  # "auto", teacher_id, or "peer"
    graded_at = Column(DateTime, default=datetime.utcnow)
    rubrics_used = Column(JSON, nullable=True)  # Grading rubrics applied

    exercise_submission = relationship("ExerciseSubmission", back_populates="grades")
    exam_submission = relationship("ExamSubmission", back_populates="grades")


class MindMap(Base):
    __tablename__ = "mind_map"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topic.id"), nullable=True)
    title = Column(String(255), nullable=False)
    central_topic = Column(String(255), nullable=False)
    map_data = Column(JSON, nullable=False)  # Structured mind map data
    generated_prompt = Column(Text, nullable=True)  # The prompt used to generate the mind map
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course")
    topic = relationship("Topic")


class CodeTestCase(Base):
    __tablename__ = "code_test_case"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercise.id"), nullable=False)
    input_data = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=False)
    is_hidden = Column(Boolean, default=False)  # Hidden test cases for grading
    points = Column(Integer, default=1)
    order_index = Column(Integer, default=0)

    exercise = relationship("Exercise")


class CodeExecutionResult(Base):
    __tablename__ = "code_execution_result"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("exercise_submission.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("code_test_case.id"), nullable=False)
    actual_output = Column(Text, nullable=True)
    passed = Column(Boolean, nullable=False)
    execution_time = Column(Float, nullable=True)  # Time in seconds
    memory_used = Column(Integer, nullable=True)  # Memory in bytes
    error_message = Column(Text, nullable=True)

    submission = relationship("ExerciseSubmission")
    test_case = relationship("CodeTestCase")