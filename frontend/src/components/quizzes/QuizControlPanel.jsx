import React from "react";
import { BookOpen, Loader, AlertCircle, Zap } from "lucide-react";
import TopicSelector from "./../TopicSelector";

const QuizControlPanel = ({
  selectedCourse,
  allTopics,
  selectedTopics,
  onTopicToggle,
  onSelectAll,
  onClearAll,
  quizType,
  onQuizTypeChange,
  difficulty,
  onDifficultyChange,
  numQuestions,
  onNumQuestionsChange,
  onGenerate,
  loading,
  loadingTopics,
  error
}) => {
  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-lg space-y-6">
      {/* Topic Selection */}
      <TopicSelector
        topics={allTopics}
        selectedTopics={selectedTopics}
        onTopicToggle={onTopicToggle}
        onSelectAll={onSelectAll}
        onClearAll={onClearAll}
        loading={loadingTopics}
      />

      {/* Quiz Configuration */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="block text-gray-700 dark:text-gray-300 mb-2 font-medium">
            Quiz Type
          </label>
          <select
            value={quizType}
            onChange={onQuizTypeChange}
            className="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-800 dark:text-gray-100"
          >
            <option value="practice">Practice</option>
            <option value="assessment">Assessment</option>
            <option value="exam">Exam</option>
          </select>
        </div>
        <div>
          <label className="block text-gray-700 dark:text-gray-300 mb-2 font-medium">
            Difficulty Level
          </label>
          <select
            value={difficulty}
            onChange={onDifficultyChange}
            className="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-800 dark:text-gray-100"
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
        <div>
          <label className="block text-gray-700 dark:text-gray-300 mb-2 font-medium">
            Number of Questions
          </label>
          <div className="flex items-center space-x-2">
            <input
              type="range"
              value={numQuestions}
              onChange={onNumQuestionsChange}
              min="5"
              max="50"
              step="5"
              className="flex-1"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 w-12 text-center">
              {numQuestions}
            </span>
          </div>
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>5</span>
            <span>25</span>
            <span>50</span>
          </div>
        </div>
      </div>

      {/* Generation Info */}
      <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-center space-x-2 text-blue-700 dark:text-blue-300 mb-2">
          <Zap className="w-4 h-4" />
          <span className="font-medium">Interactive Quizzes</span>
        </div>
        <p className="text-sm text-blue-600 dark:text-blue-400">
          Generate comprehensive quizzes with automatic grading, progress tracking, and detailed feedback.
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-3">
        <button
          onClick={onGenerate}
          disabled={!selectedCourse || selectedTopics.length === 0 || loading}
          className="flex-1 bg-indigo-600 text-white font-medium py-3 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          {loading ? (
            <Loader className="w-5 h-5 animate-spin" />
          ) : (
            <BookOpen className="w-5 h-5" />
          )}
          <span>{loading ? "Generating..." : "Generate New Quiz"}</span>
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <div className="flex items-center space-x-2 text-red-700 dark:text-red-300">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuizControlPanel;