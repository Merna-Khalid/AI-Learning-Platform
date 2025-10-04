import React from "react";

const ProgressBar = ({ current, total }) => {
  const percent = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <div className="w-full space-y-2">
      <div className="w-full bg-gray-300 dark:bg-gray-700 rounded-lg overflow-hidden">
        <div
          className="bg-indigo-600 h-6 text-xs flex items-center justify-center text-white font-medium"
          style={{ width: `${percent}%` }}
        >
          {percent}%
        </div>
      </div>
      <p className="text-center text-gray-600 dark:text-gray-400">
        {current} of {total} topics mastered
      </p>
    </div>
  );
};

export default ProgressBar;
