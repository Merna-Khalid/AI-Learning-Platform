import React from "react";
import { AlertCircle } from "lucide-react";

const QuizQuestion = ({ 
  question, 
  questionNumber, 
  totalQuestions, 
  answer, 
  onAnswer 
}) => {
  // Get options for MCQ questions
  const getQuestionType = (question) => {
    const declaredType = question.type?.toUpperCase();
    const metadata = question.extra_metadata || {};
    
    if (metadata.expected_answer && !metadata.options) {
      return 'SHORT_ANSWER';
    }
    
    if (metadata.correct_answer && 
        (metadata.correct_answer.toLowerCase() === 'true' || 
        metadata.correct_answer.toLowerCase() === 'false')) {
      return 'TRUE_FALSE';
    }
    
    return declaredType || 'MCQ';
  };

  const getOptions = (question) => {
    if (!question.extra_metadata) return [];
    return question.extra_metadata.options || question.extra_metadata.choices || [];
  };

  const actualType = getQuestionType(question);
  const options = getOptions(question);

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
        {question.text}
      </h3>

      {(() => {
        switch(actualType) {
          case 'MCQ':
            return (
              <div className="space-y-3">
                {options.length > 0 ? (
                  options.map((option, index) => {
                    const optionLetter = String.fromCharCode(65 + index);
                    
                    return (
                      <label
                        key={index}
                        className={`flex items-start space-x-3 p-4 rounded-lg border cursor-pointer transition-all ${
                          answer === optionLetter
                            ? 'bg-indigo-50 border-indigo-300 dark:bg-indigo-900/20 dark:border-indigo-700'
                            : 'bg-gray-50 border-gray-200 dark:bg-gray-700/50 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-400'
                        }`}
                        onClick={() => onAnswer(question.id, optionLetter)}
                      >
                        <input
                          type="radio"
                          name={`question-${question.id}`}
                          value={optionLetter}
                          checked={answer === optionLetter}
                          onChange={(e) => onAnswer(question.id, e.target.value)}
                          className="mt-1 text-indigo-600 focus:ring-indigo-500"
                        />
                        <div className="flex items-start space-x-3 flex-1">
                          <span className="font-medium text-gray-700 dark:text-gray-300 min-w-6">
                            {optionLetter}.
                          </span>
                          <span className="text-gray-700 dark:text-gray-300 flex-1">{option}</span>
                        </div>
                      </label>
                    );
                  })
                ) : (
                  <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                    <AlertCircle className="w-6 h-6 mx-auto mb-2" />
                    <p>No options available for this MCQ question.</p>
                  </div>
                )}
              </div>
            );

          case 'SHORT_ANSWER':
            return (
              <div className="space-y-2">
                <textarea
                  value={answer || ''}
                  onChange={(e) => onAnswer(question.id, e.target.value)}
                  placeholder="Type your detailed answer here..."
                  className="w-full h-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-vertical"
                />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Provide a detailed answer. Your response will be evaluated based on key concepts.
                </p>
              </div>
            );

          case 'TRUE_FALSE':
            return (
              <div className="grid grid-cols-2 gap-4">
                {['true', 'false'].map((option) => (
                  <label
                    key={option}
                    className={`flex-1 text-center p-6 rounded-lg border cursor-pointer transition-all ${
                      answer === option
                        ? 'bg-indigo-50 border-indigo-300 dark:bg-indigo-900/20 dark:border-indigo-700'
                        : 'bg-gray-50 border-gray-200 dark:bg-gray-700/50 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-400'
                    }`}
                  >
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      value={option}
                      checked={answer === option}
                      onChange={(e) => onAnswer(question.id, e.target.value)}
                      className="hidden"
                    />
                    <span className="font-medium text-gray-700 dark:text-gray-300 text-lg">
                      {option.charAt(0).toUpperCase() + option.slice(1)}
                    </span>
                  </label>
                ))}
              </div>
            );

          default:
            return (
              <div className="space-y-2">
                <textarea
                  value={answer || ''}
                  onChange={(e) => onAnswer(question.id, e.target.value)}
                  placeholder="Type your answer here..."
                  className="w-full h-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-vertical"
                />
                <p className="text-sm text-yellow-600 dark:text-yellow-400">
                  Note: This question type ({question.type}) is being treated as short answer.
                </p>
              </div>
            );
        }
      })()}
    </div>
  );
};

export default QuizQuestion;