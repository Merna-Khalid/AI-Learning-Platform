import React from "react";

const Progress = ({ goToPage }) => {
  const progress = { mastered: 3, total: 10, quizzesTaken: 5 };

  const percent = Math.round((progress.mastered / progress.total) * 100);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-center text-gray-800 dark:text-gray-100">
        Progress
      </h1>
      <div className="w-full bg-gray-300 dark:bg-gray-700 rounded-lg overflow-hidden">
        <div
          className="bg-indigo-600 h-6 text-xs flex items-center justify-center text-white font-medium"
          style={{ width: `${percent}%` }}
        >
          {percent}%
        </div>
      </div>
      <p className="text-center text-gray-600 dark:text-gray-400">
        {progress.mastered} of {progress.total} topics mastered
      </p>
      <p className="text-center text-gray-600 dark:text-gray-400">
        {progress.quizzesTaken} quizzes taken so far
      </p>
      <button
        onClick={() => goToPage("dashboard")}
        className="w-full text-center py-2 text-indigo-600 dark:text-indigo-400 font-medium hover:underline"
      >
        &larr; Back to Dashboard
      </button>
    </div>
  );
};

export default Progress;
