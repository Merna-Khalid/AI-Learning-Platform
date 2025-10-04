// src/components/QuizResults.jsx
import React from "react";
import { Trophy, BarChart3 } from "lucide-react";

const QuizResults = ({ quiz, results, onBack }) => {
  const score = results.final_grade || 0;
  const totalQuestions = quiz.questions?.length || 0;
  const correctAnswers = results.correct_answers || results.answers?.filter(a => a.is_correct)?.length || 0;

  const getPerformanceFeedback = (score) => {
    if (score >= 90) return { text: "Excellent!", color: "text-green-600", bg: "bg-green-50" };
    if (score >= 80) return { text: "Great job!", color: "text-green-500", bg: "bg-green-50" };
    if (score >= 70) return { text: "Good work!", color: "text-blue-600", bg: "bg-blue-50" };
    if (score >= 60) return { text: "Not bad!", color: "text-yellow-600", bg: "bg-yellow-50" };
    return { text: "Keep practicing!", color: "text-red-600", bg: "bg-red-50" };
  };

  const performance = getPerformanceFeedback(score);

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-lg max-w-4xl mx-auto">
      <div className={`text-center p-6 rounded-2xl mb-8 ${performance.bg} dark:bg-gray-700`}>
        <Trophy className={`w-20 h-20 mx-auto mb-4 ${performance.color} dark:text-yellow-400`} />
        <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-2">
          Quiz Complete!
        </h2>
        <div className="text-5xl font-bold text-indigo-600 dark:text-indigo-400 mb-2">
          {score.toFixed(1)}%
        </div>
        <p className={`text-xl font-semibold ${performance.color} dark:text-yellow-300 mb-2`}>
          {performance.text}
        </p>
        <p className="text-gray-600 dark:text-gray-400">
          You got {correctAnswers} out of {totalQuestions} questions correct
        </p>
      </div>

      {/* Score Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
            {correctAnswers}
          </div>
          <div className="text-sm text-green-700 dark:text-green-300">Correct</div>
        </div>
        <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <div className="text-2xl font-bold text-red-600 dark:text-red-400">
            {totalQuestions - correctAnswers}
          </div>
          <div className="text-sm text-red-700 dark:text-red-300">Incorrect</div>
        </div>
        <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {totalQuestions}
          </div>
          <div className="text-sm text-blue-700 dark:text-blue-300">Total</div>
        </div>
        <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {results.time_taken ? `${Math.floor(results.time_taken / 60)}:${(results.time_taken % 60).toString().padStart(2, '0')}` : 'N/A'}
          </div>
          <div className="text-sm text-purple-700 dark:text-purple-300">Time</div>
        </div>
      </div>

      {/* Review Section */}
      <div className="space-y-6">
        <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100 border-b pb-2">
          Detailed Review
        </h3>
        {quiz.questions?.map((question, index) => {
          const userAnswer = results.answers?.find(a => a.question_id === question.id);
          const isCorrect = userAnswer?.is_correct;
          const correctAnswer = question.extra_metadata?.correct_answer;
          const explanation = question.extra_metadata?.explanation;
          
          return (
            <div
              key={question.id}
              className={`p-6 rounded-lg border-2 ${
                isCorrect 
                  ? 'bg-green-50 border-green-300 dark:bg-green-900/20 dark:border-green-700'
                  : 'bg-red-50 border-red-300 dark:bg-red-900/20 dark:border-red-700'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="font-semibold text-gray-800 dark:text-gray-100">
                    Question {index + 1}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    isCorrect 
                      ? 'bg-green-200 text-green-800 dark:bg-green-700 dark:text-green-200'
                      : 'bg-red-200 text-red-800 dark:bg-red-700 dark:text-red-200'
                  }`}>
                    {isCorrect ? '✓ Correct' : '✗ Incorrect'}
                  </span>
                </div>
                <span className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                  {question.type?.toLowerCase().replace('_', ' ')}
                </span>
              </div>
              
              <p className="text-gray-700 dark:text-gray-300 mb-4 font-medium">{question.text}</p>
              
              <div className="space-y-2 text-sm">
                <div className="flex flex-wrap gap-2">
                  <span className="font-semibold">Your answer:</span>
                  <span className={`px-2 py-1 rounded ${
                    isCorrect 
                      ? 'bg-green-200 text-green-800 dark:bg-green-700 dark:text-green-200'
                      : 'bg-red-200 text-red-800 dark:bg-red-700 dark:text-red-200'
                  }`}>
                    {userAnswer?.answer_text || 'No answer provided'}
                  </span>
                </div>
                
                {!isCorrect && correctAnswer && (
                  <div className="flex flex-wrap gap-2">
                    <span className="font-semibold">Correct answer:</span>
                    <span className="px-2 py-1 rounded bg-blue-200 text-blue-800 dark:bg-blue-700 dark:text-blue-200">
                      {correctAnswer}
                    </span>
                  </div>
                )}
                
                {explanation && (
                  <div>
                    <span className="font-semibold">Explanation:</span>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">{explanation}</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="text-center mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={onBack}
          className="px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-semibold"
        >
          Back to Quizzes
        </button>
      </div>
    </div>
  );
};

export default QuizResults;