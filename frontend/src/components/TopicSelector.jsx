import React from "react";
import { CheckCircle, AlertCircle, Loader } from "lucide-react";

const TopicSelector = ({ 
  topics, 
  selectedTopics, 
  onTopicToggle, 
  onSelectAll, 
  onClearAll, 
  loading = false 
}) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader className="w-5 h-5 text-indigo-600 animate-spin mr-2" />
        <span className="text-gray-600 dark:text-gray-400">Loading topics from course materials...</span>
      </div>
    );
  }

  if (topics.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500 dark:text-gray-400">
        <AlertCircle className="w-6 h-6 mx-auto mb-2" />
        <p>No topics available for this course.</p>
        <p className="text-sm">Upload course materials first to generate topics.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <label className="block text-gray-700 dark:text-gray-300 font-medium">
          Select Topics ({topics.length} available)
        </label>
        <div className="flex space-x-2">
          {topics.length > 0 && selectedTopics.length < topics.length && (
            <button
              onClick={onSelectAll}
              className="text-sm text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
            >
              Select all
            </button>
          )}
          {selectedTopics.length > 0 && (
            <button
              onClick={onClearAll}
              className="text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              Clear all
            </button>
          )}
        </div>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {topics.map((topic, index) => (
          <label
            key={index}
            className={`flex items-center space-x-2 px-4 py-2 rounded-full cursor-pointer transition-all duration-200 border ${
              selectedTopics.includes(topic)
                ? "bg-indigo-500 text-white border-indigo-500 shadow-md"
                : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-400"
            }`}
          >
            <input
              type="checkbox"
              checked={selectedTopics.includes(topic)}
              onChange={() => onTopicToggle(topic)}
              className="hidden"
            />
            <span className="text-sm font-medium">{topic}</span>
            {selectedTopics.includes(topic) && (
              <CheckCircle className="w-4 h-4" />
            )}
          </label>
        ))}
      </div>
    </div>
  );
};

export default TopicSelector;