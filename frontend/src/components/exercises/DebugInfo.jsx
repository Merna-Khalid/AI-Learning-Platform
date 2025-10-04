import React from "react";

const DebugInfo = ({ selectedCourse, allTopics, selectedTopics }) => {
  if (process.env.NODE_ENV !== 'development') return null;

  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
      <h3 className="font-semibold text-yellow-800 dark:text-yellow-300">Debug Info:</h3>
      <p className="text-sm text-yellow-700 dark:text-yellow-400">
        Selected Course: {selectedCourse?.name}<br/>
        Available Topics: {allTopics.length}<br/>
        Selected Topics: {selectedTopics.join(', ')}<br/>
        Materials Loaded: {allTopics.length > 0 ? 'Yes' : 'No'}
      </p>
    </div>
  );
};

export default DebugInfo;