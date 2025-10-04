import React, { useState } from "react";
import { CheckCircle } from "lucide-react";

const ExerciseCard = ({ exercise, index }) => {
  const [showAnswer, setShowAnswer] = useState(false);
  
  const getQuestionText = (ex) => {
    return ex.question || ex.problem_description || ex.statement || ex.sentence || "No question text available";
  };

  const getTypeDisplay = (type) => {
    if (!type) return "Exercise";
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ');
  };

  const getTypeColor = (type) => {
    const colors = {
      'mcq': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      'short_answer': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      'true_false': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
      'fill_blank': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
      'math_problem': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
      'coding': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300'
    };
    return colors[type?.toLowerCase()] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
  };

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg space-y-4 border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${getTypeColor(exercise.type)}`}>
            {getTypeDisplay(exercise.type)}
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Question {index + 1}
          </span>
          {exercise._fallback && (
            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full dark:bg-yellow-900 dark:text-yellow-300">
              Fallback
            </span>
          )}
        </div>
        <button
          onClick={() => setShowAnswer(!showAnswer)}
          className="text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
        >
          {showAnswer ? "Hide Answer" : "Show Answer"}
        </button>
      </div>

      {/* Question */}
      <div className="text-gray-700 dark:text-gray-200 text-lg leading-relaxed">
        {getQuestionText(exercise)}
      </div>

      {/* Options for MCQ */}
      {exercise.options && Array.isArray(exercise.options) && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-600 dark:text-gray-400">Options:</h4>
          <ul className="space-y-2">
            {exercise.options.map((option, optIndex) => (
              <li 
                key={optIndex}
                className={`p-3 rounded-lg border ${
                  showAnswer && exercise.correct_answer === String.fromCharCode(65 + optIndex)
                    ? "bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800"
                    : "bg-gray-50 border-gray-200 dark:bg-gray-700/50 dark:border-gray-600"
                }`}
              >
                <span className="font-medium text-gray-700 dark:text-gray-300">
                  {String.fromCharCode(65 + optIndex)}.{" "}
                </span>
                {option}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Solution Steps for Math Problems */}
      {exercise.solution_steps && Array.isArray(exercise.solution_steps) && showAnswer && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-600 dark:text-gray-400">Solution Steps:</h4>
          <ol className="list-decimal list-inside space-y-1 text-gray-700 dark:text-gray-300">
            {exercise.solution_steps.map((step, stepIndex) => (
              <li key={stepIndex}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      {/* Answer Section */}
      {showAnswer && (
        <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <h4 className="font-medium text-green-800 dark:text-green-300 mb-2">
            Answer & Explanation
          </h4>
          {exercise.correct_answer && (
            <p className="text-green-700 dark:text-green-400 mb-2">
              <strong>Correct Answer:</strong> {exercise.correct_answer}
            </p>
          )}
          {exercise.final_answer && (
            <p className="text-green-700 dark:text-green-400 mb-2">
              <strong>Final Answer:</strong> {exercise.final_answer}
            </p>
          )}
          {exercise.explanation && (
            <p className="text-green-700 dark:text-green-400 mb-2">
              <strong>Explanation:</strong> {exercise.explanation}
            </p>
          )}
          {exercise.expected_answer && (
            <p className="text-green-700 dark:text-green-400">
              <strong>Expected Answer:</strong> {exercise.expected_answer}
            </p>
          )}
        </div>
      )}

      {/* Additional Information */}
      {(exercise.hints || exercise.key_points) && showAnswer && (
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <h4 className="font-medium text-blue-800 dark:text-blue-300 mb-2">
            Learning Tips
          </h4>
          {exercise.hints && Array.isArray(exercise.hints) && (
            <div className="mb-2">
              <strong className="text-blue-700 dark:text-blue-400">Hints:</strong>
              <ul className="list-disc list-inside text-blue-700 dark:text-blue-400 ml-2">
                {exercise.hints.map((hint, hintIndex) => (
                  <li key={hintIndex}>{hint}</li>
                ))}
              </ul>
            </div>
          )}
          {exercise.key_points && Array.isArray(exercise.key_points) && (
            <div>
              <strong className="text-blue-700 dark:text-blue-400">Key Points:</strong>
              <ul className="list-disc list-inside text-blue-700 dark:text-blue-400 ml-2">
                {exercise.key_points.map((point, pointIndex) => (
                  <li key={pointIndex}>{point}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Test Cases for Coding Problems */}
      {exercise.test_cases && Array.isArray(exercise.test_cases) && showAnswer && (
        <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
          <h4 className="font-medium text-purple-800 dark:text-purple-300 mb-2">
            Test Cases
          </h4>
          <div className="space-y-2">
            {exercise.test_cases.map((testCase, caseIndex) => (
              <div key={caseIndex} className="text-sm">
                <strong>Input:</strong> {testCase.input}<br/>
                <strong>Expected Output:</strong> {testCase.expected_output}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ExerciseCard;