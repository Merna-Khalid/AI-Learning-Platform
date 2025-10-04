import React from "react";

const ExamResult = ({ grade, notes, onRetry }) => {
  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow space-y-4">
      <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
        Exam Result
      </h2>
      <p className="text-gray-700 dark:text-gray-300">
        Final Grade:{" "}
        <span className="font-semibold text-indigo-600 dark:text-indigo-400">
          {grade}%
        </span>
      </p>
      <p className="text-gray-600 dark:text-gray-400">{notes}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition"
        >
          Retry Exam
        </button>
      )}
    </div>
  );
};

export default ExamResult;
