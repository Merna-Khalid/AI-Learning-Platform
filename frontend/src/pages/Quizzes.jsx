// src/pages/Quizzes.jsx
import React, { useState, useEffect } from "react";
import { Trophy } from "lucide-react";
import api from "../api/api";
import QuizControlPanel from "../components/quizzes/QuizControlPanel";
import QuizCard from "../components/quizzes/QuizCard";
import QuizInterface from "../components/quizzes/QuizInterface";
import GenerationStats from "../components/GenerationStats";
import DebugInfo from "../components/exercises/DebugInfo";

const Quizzes = ({ selectedCourse }) => {
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [allTopics, setAllTopics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingTopics, setLoadingTopics] = useState(false);
  const [quizzes, setQuizzes] = useState([]);
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [quizResults, setQuizResults] = useState(null);
  const [difficulty, setDifficulty] = useState("medium");
  const [numQuestions, setNumQuestions] = useState(20);
  const [quizType, setQuizType] = useState("practice");
  const [error, setError] = useState(null);
  const [generationStats, setGenerationStats] = useState(null);

  // Fetch topics from materials when course changes
  useEffect(() => {
    const fetchTopicsFromMaterials = async () => {
      if (!selectedCourse?.id) {
        setAllTopics([]);
        return;
      }

      try {
        setLoadingTopics(true);
        setError(null);
        
        const materialsResponse = await api.get(`/courses/${selectedCourse.id}/materials`);
        const materials = materialsResponse.data || [];
        
        // Extract and flatten all topics from all materials
        const allExtractedTopics = new Set();
        
        materials.forEach(material => {
          if (material.extracted_topics) {
            try {
              let topics = material.extracted_topics;
              if (typeof topics === 'string') {
                topics = JSON.parse(topics);
              }
              if (Array.isArray(topics)) {
                topics.forEach(topic => {
                  if (topic && topic.trim()) {
                    allExtractedTopics.add(topic.trim());
                  }
                });
              }
            } catch (parseError) {
              console.error('Error parsing topics for material:', material.id, parseError);
            }
          }
        });
        
        const uniqueTopics = Array.from(allExtractedTopics).sort();
        setAllTopics(uniqueTopics);
        
      } catch (err) {
        console.error("Error fetching materials/topics:", err);
        setError("Failed to load topics. Please try again.");
        setAllTopics([]);
      } finally {
        setLoadingTopics(false);
      }
    };

    fetchTopicsFromMaterials();
  }, [selectedCourse]);

  // Fetch existing quizzes for this course
  useEffect(() => {
    const fetchQuizzes = async () => {
      if (!selectedCourse?.id) return;
      
      try {
        const response = await api.get(`/quiz/${selectedCourse.id}`);
        setQuizzes(response.data || []);
      } catch (err) {
        console.error("Error fetching quizzes:", err);
      }
    };

    fetchQuizzes();
  }, [selectedCourse]);

  const handleTopicToggle = (topic) => {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  };

  const generateQuiz = async () => {
    setLoading(true);
    setError(null);
    setActiveQuiz(null);
    setQuizResults(null);
    setGenerationStats(null);

    if (!selectedCourse) {
      setError("Please select a course first.");
      setLoading(false);
      return;
    }
    if (selectedTopics.length === 0) {
      setError("Please select at least one topic.");
      setLoading(false);
      return;
    }

    try {
      const startTime = Date.now();
      const response = await api.post("/quiz/generate", {
        course_id: selectedCourse.id,
        topic_names: selectedTopics,
        num_questions: numQuestions,
        difficulty: difficulty,
        quiz_type: quizType
      });
      
      const endTime = Date.now();
      const generationTime = (endTime - startTime) / 1000;
      
      if (response.data.error) {
        setError(response.data.error);
      } else {
        setActiveQuiz(response.data);
        setGenerationStats({
          time: generationTime,
          count: response.data.questions?.length || 0
        });
        // Refresh quizzes list
        const quizzesResponse = await api.get(`/quiz/${selectedCourse.id}`);
        setQuizzes(quizzesResponse.data || []);
      }
    } catch (err) {
      console.error("Error generating quiz:", err);
      setError("Failed to generate quiz. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const startQuiz = (quiz) => {
    setActiveQuiz(quiz);
    setQuizResults(null);
  };

  const submitQuiz = async (answers) => {
    try {
      const response = await api.post(`/quiz/${activeQuiz.id}/attempt`, {
        answers: answers,
        time_taken: 0
      });
      setQuizResults(response.data);
    } catch (err) {
      console.error("Error submitting quiz:", err);
      setError("Failed to submit quiz. Please try again.");
    }
  };

  const clearSelection = () => {
    setSelectedTopics([]);
    setActiveQuiz(null);
    setQuizResults(null);
    setError(null);
    setGenerationStats(null);
  };

  const selectAllTopics = () => {
    setSelectedTopics([...allTopics]);
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center space-x-3 mb-2">
          <Trophy className="w-8 h-8 text-indigo-600" />
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">
            Quizzes & Assessments
          </h1>
        </div>
        {selectedCourse && (
          <p className="text-gray-600 dark:text-gray-400">
            For course:{" "}
            <span className="font-semibold text-indigo-500">
              {selectedCourse.name}
            </span>
          </p>
        )}
      </div>

      {!activeQuiz ? (
        <>
          {/* Control Panel */}
          <QuizControlPanel
            selectedCourse={selectedCourse}
            allTopics={allTopics}
            selectedTopics={selectedTopics}
            onTopicToggle={handleTopicToggle}
            onSelectAll={selectAllTopics}
            onClearAll={clearSelection}
            quizType={quizType}
            onQuizTypeChange={(e) => setQuizType(e.target.value)}
            difficulty={difficulty}
            onDifficultyChange={(e) => setDifficulty(e.target.value)}
            numQuestions={numQuestions}
            onNumQuestionsChange={(e) => setNumQuestions(parseInt(e.target.value, 10))}
            onGenerate={generateQuiz}
            loading={loading}
            loadingTopics={loadingTopics}
            error={error}
          />

          {/* Generation Stats */}
          <GenerationStats stats={generationStats} />

          {/* Debug info */}
          {/* <DebugInfo 
            selectedCourse={selectedCourse}
            allTopics={allTopics}
            selectedTopics={selectedTopics}
          /> */}

          {/* Previous Quizzes */}
          {quizzes.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
                Previous Quizzes
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {quizzes.map((quiz) => (
                  <QuizCard 
                    key={quiz.id} 
                    quiz={quiz}
                    onStart={() => startQuiz(quiz)}
                  />
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        /* Quiz Taking Interface */
        <QuizInterface 
          quiz={activeQuiz}
          onSubmit={submitQuiz}
          results={quizResults}
          onBack={() => setActiveQuiz(null)}
        />
      )}
    </div>
  );
};

export default Quizzes;