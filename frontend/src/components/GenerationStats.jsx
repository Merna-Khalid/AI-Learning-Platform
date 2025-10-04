import React from "react";
import { CheckCircle, Zap, Clock } from "lucide-react";

const GenerationStats = ({ stats }) => {
  if (!stats) return null;

  return (
    <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg border border-green-200 dark:border-green-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-green-700 dark:text-green-300">
          <CheckCircle className="w-4 h-4" />
          <span className="font-medium">Generation Complete!</span>
        </div>
        <div className="flex items-center space-x-4 text-sm">
          {stats.efficient && (
            <div className="flex items-center space-x-1">
              <Zap className="w-4 h-4" />
              <span className="text-green-600 dark:text-green-400">Fast Mode</span>
            </div>
          )}
          <div className="flex items-center space-x-1">
            <Clock className="w-4 h-4" />
            <span className="text-green-600 dark:text-green-400">
              {stats.time.toFixed(1)}s
            </span>
          </div>
          <span className="text-green-600 dark:text-green-400">
            {stats.count} questions
          </span>
        </div>
      </div>
    </div>
  );
};

export default GenerationStats;