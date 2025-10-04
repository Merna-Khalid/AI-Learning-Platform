import React from "react";
import { Play, Trophy } from "lucide-react";

const QuizCard = ({ quiz, onStart }) => {
  const getTypeDisplay = (type) => {
    const types = {
      'practice': 'Practice',
      'assessment': 'Assessment', 
      'exam': 'Exam'
    };
    return types[type] || type;
  };

  const getTypeColor = (type) => {
    const colors = {
      'practice': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      'assessment': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
      'exam': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
    };
    return colors[type] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
  };

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${getTypeColor(quiz.quiz_type)}`}>
          {getTypeDisplay(quiz.quiz_type)}
        </span>
        {quiz.prev_grade && (
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {quiz.prev_grade}%
          </span>
        )}
      </div>
      
      <h3 className="font-semibold text-gray-800 dark:text-gray-100 mb-2">
        {quiz.questions?.length || 0} Questions
      </h3>
      
      <div className="text-sm text-gray-600 dark:text-gray-400 mb-4 space-y-1">
        <div>Created: {new Date(quiz.date_created).toLocaleDateString()}</div>
        {quiz.topics && quiz.topics.length > 0 && (
          <div>Topics: {quiz.topics.slice(0, 2).map(t => t.name).join(', ')}{quiz.topics.length > 2 && '...'}</div>
        )}
      </div>
      
      <button
        onClick={onStart}
        className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors flex items-center justify-center space-x-2"
      >
        <Play className="w-4 h-4" />
        <span>Start Quiz</span>
      </button>
    </div>
  );
};

export default QuizCard;