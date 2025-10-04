from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import enum


class SourceType(str, enum.Enum):
    PDF = "pdf"
    VIDEO = "video"
    ARTICLE = "article"
    SLIDES = "slides"
    OTHER = "other"

class QuestionType(str, enum.Enum):
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

class QuizType(str, enum.Enum):
    PRACTICE = "practice"
    EXAM = "exam"
    TIMED_EXAM = "timed_exam"
    EXERCISE = "exercise"

class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class GradingMethod(str, enum.Enum):
    AUTO = "auto"
    MANUAL = "manual"
    PEER = "peer"
    AI_ASSISTED = "ai_assisted"

class SubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    GRADED = "graded"
    REVIEW_PENDING = "review_pending"


class CourseBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    code: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseOut(CourseBase):
    id: int
    date_created: datetime
    num_of_topics: int
    ingestion_status: str = "pending"

    class Config:
        from_attributes = True


class MaterialBase(BaseModel):
    course_id: int
    source_type: SourceType  # PDF, VIDEO, ARTICLE, etc.
    content_type: str = "lecture"  # lecture, tutorial, reference
    filename: str
    extracted_topics: Optional[List[str]] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialOut(MaterialBase):
    id: int
    date_uploaded: datetime
    file_path: str
    ingestion_status: str

    class Config:
        from_attributes = True


class TopicBase(BaseModel):
    course_id: int
    name: str = Field(..., max_length=255)
    description: Optional[str] = None

class TopicCreate(TopicBase):
    pass

class TopicOut(TopicBase):
    id: int

    class Config:
        from_attributes = True


class QuizBase(BaseModel):
    course_id: int
    num_of_questions: int = Field(default=0, ge=0)
    prev_grade: Optional[float] = Field(None, ge=0, le=100)
    quiz_type: QuizType = QuizType.PRACTICE

class QuizCreate(QuizBase):
    topic_ids: List[int]

class QuizOut(QuizBase):
    id: int
    date_created: datetime
    topics: List[TopicOut] = []

    class Config:
        from_attributes = True


class QuizRequest(BaseModel):
    topic_ids: List[int]
    num_questions: int = Field(default=5, ge=1, le=50)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    question_types: Optional[List[QuestionType]] = None


class QuestionBase(BaseModel):
    quiz_id: int
    topic_id: Optional[int] = None
    text: str
    type: QuestionType
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    extra_metadata: Optional[Dict[str, Any]] = None

class QuestionCreate(QuestionBase):
    pass

class QuestionOut(QuestionBase):
    id: int
    diagram_ref: Optional[str] = None
    code_stub: Optional[str] = None

    class Config:
        from_attributes = True


class AttemptBase(BaseModel):
    quiz_id: int
    final_grade: Optional[float] = Field(None, ge=0, le=100)
    grading_notes: Optional[str] = None

class AttemptCreate(AttemptBase):
    pass

class AttemptOut(AttemptBase):
    id: int
    date: datetime
    time_taken: Optional[int] = Field(None, ge=0)

    class Config:
        from_attributes = True


class AnswerBase(BaseModel):
    question_id: int
    attempt_id: int
    answer_text: Optional[str] = None
    is_correct: Optional[bool] = None
    grading_notes: Optional[str] = None

class AnswerCreate(AnswerBase):
    pass

class AnswerOut(AnswerBase):
    id: int

    class Config:
        from_attributes = True


class ProgressBase(BaseModel):
    course_id: int
    num_of_topics_mastered: int = Field(default=0, ge=0)
    num_of_quizzes_taken: int = Field(default=0, ge=0)
    num_of_exercises_completed: int = Field(default=0, ge=0)
    num_of_exams_taken: int = Field(default=0, ge=0)


class ProgressCreate(ProgressBase):
    pass


class ProgressOut(ProgressBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


class ExerciseBase(BaseModel):
    course_id: int
    topic_id: Optional[int] = None
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    question_type: QuestionType
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    question_data: Dict[str, Any]
    solution_data: Optional[Dict[str, Any]] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseOut(ExerciseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExamBase(BaseModel):
    course_id: int
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    exam_type: QuizType = QuizType.TIMED_EXAM
    duration_minutes: int = Field(..., gt=0)
    total_points: int = Field(default=100, gt=0)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    questions_data: List[Dict[str, Any]]
    instructions: Optional[str] = None
    is_published: bool = False


class ExamCreate(ExamBase):
    topic_ids: List[int]


class ExamOut(ExamBase):
    id: int
    created_at: datetime
    updated_at: datetime
    topics: List[TopicOut] = []

    class Config:
        from_attributes = True


class ExerciseSubmissionBase(BaseModel):
    exercise_id: int
    student_id: str = Field(..., max_length=100)
    answers: Dict[str, Any]
    time_spent: int = Field(default=0, ge=0)
    status: SubmissionStatus = SubmissionStatus.SUBMITTED
    auto_feedback: Optional[str] = None
    manual_feedback: Optional[str] = None


class ExerciseSubmissionCreate(ExerciseSubmissionBase):
    pass


class ExerciseSubmissionOut(ExerciseSubmissionBase):
    id: int
    submitted_at: datetime
    exercise: Optional[ExerciseOut] = None

    class Config:
        from_attributes = True


class ExamSubmissionBase(BaseModel):
    exam_id: int
    student_id: str = Field(..., max_length=100)
    answers: Dict[str, Any]
    started_at: datetime
    time_spent: Optional[int] = Field(None, ge=0)
    status: SubmissionStatus = SubmissionStatus.DRAFT
    auto_grade: Optional[float] = Field(None, ge=0, le=100)
    manual_grade: Optional[float] = Field(None, ge=0, le=100)
    final_grade: Optional[float] = Field(None, ge=0, le=100)
    feedback: Optional[str] = None


class ExamSubmissionCreate(ExamSubmissionBase):
    pass


class ExamSubmissionUpdate(BaseModel):
    answers: Optional[Dict[str, Any]] = None
    time_spent: Optional[int] = None
    status: Optional[SubmissionStatus] = None


class ExamSubmissionOut(ExamSubmissionBase):
    id: int
    submitted_at: Optional[datetime] = None
    exam: Optional[ExamOut] = None

    class Config:
        from_attributes = True


class GradeBase(BaseModel):
    score: float = Field(..., ge=0)
    max_score: float = Field(..., ge=0)
    feedback: Optional[str] = None
    detailed_feedback: Optional[Dict[str, Any]] = None
    grading_method: GradingMethod = GradingMethod.AUTO
    graded_by: Optional[str] = Field(None, max_length=100)
    rubrics_used: Optional[Dict[str, Any]] = None


class GradeCreate(GradeBase):
    exercise_submission_id: Optional[int] = None
    exam_submission_id: Optional[int] = None


class GradeOut(GradeBase):
    id: int
    graded_at: datetime
    exercise_submission: Optional[ExerciseSubmissionOut] = None
    exam_submission: Optional[ExamSubmissionOut] = None

    class Config:
        from_attributes = True


class MindMapBase(BaseModel):
    course_id: int
    topic_id: Optional[int] = None
    title: str = Field(..., max_length=255)
    central_topic: str = Field(..., max_length=255)
    map_data: Dict[str, Any]
    generated_prompt: Optional[str] = None


class MindMapCreate(MindMapBase):
    pass


class MindMapOut(MindMapBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CodeTestCaseBase(BaseModel):
    exercise_id: int
    input_data: Optional[str] = None
    expected_output: str
    is_hidden: bool = False
    points: int = Field(default=1, ge=0)
    order_index: int = Field(default=0, ge=0)

class CodeTestCaseCreate(CodeTestCaseBase):
    pass

class CodeTestCaseOut(CodeTestCaseBase):
    id: int

    class Config:
        from_attributes = True


class CodeExecutionResultBase(BaseModel):
    submission_id: int
    test_case_id: int
    actual_output: Optional[str] = None
    passed: bool
    execution_time: Optional[float] = Field(None, ge=0)
    memory_used: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = None

class CodeExecutionResultCreate(CodeExecutionResultBase):
    pass

class CodeExecutionResultOut(CodeExecutionResultBase):
    id: int

    class Config:
        from_attributes = True


class ExerciseGenerationRequest(BaseModel):
    course: str
    topics: List[str]
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    question_types: Optional[List[QuestionType]] = None

class ExerciseGenerationResponse(BaseModel):
    course: str
    topics: List[str]
    exercises: List[Dict[str, Any]]
    generated_at: datetime

class ExamCreationRequest(BaseModel):
    course: str
    topics: List[str]
    duration_minutes: int = Field(..., ge=15, le=240)  # 15 min to 4 hours
    num_questions: int = Field(default=20, ge=5, le=100)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM

class ExamCreationResponse(BaseModel):
    exam_id: str
    course: str
    topics: List[str]
    duration_minutes: int
    total_points: int
    questions: List[Dict[str, Any]]
    instructions: str
    created_at: datetime

class MindMapGenerationRequest(BaseModel):
    course: str
    central_topic: str
    depth: int = Field(default=3, ge=1, le=5)

class MindMapGenerationResponse(BaseModel):
    course: str
    central_topic: str
    mind_map: Dict[str, Any]
    generated_at: datetime

class CodeExecutionRequest(BaseModel):
    language: str = Field(..., pattern="^(python|javascript|java|cpp|go)$")
    code: str
    input_data: Optional[str] = None

class CodeExecutionResponse(BaseModel):
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    success: bool
    execution_time: Optional[float] = None
    error: Optional[str] = None

class GradingRequest(BaseModel):
    submission_id: int
    question_type: QuestionType
    student_answer: str
    reference_answer: str
    question_text: str

class GradingResponse(BaseModel):
    score: float
    max_score: float
    feedback: str
    detailed_feedback: Optional[Dict[str, Any]] = None
    correct: bool

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None