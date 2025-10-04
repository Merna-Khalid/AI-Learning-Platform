import React from "react";

const TopicList = ({ topics }) => {
  return (
    <ul className="space-y-3">
      {topics.map((topic) => (
        <li
          key={topic.id}
          className={`p-4 rounded-lg shadow ${
            topic.mastered
              ? "bg-green-100 dark:bg-green-800"
              : "bg-gray-100 dark:bg-gray-700"
          }`}
        >
          {topic.name}{" "}
          {topic.mastered && (
            <span className="text-green-700 dark:text-green-300 font-medium">
              ✔ Mastered
            </span>
          )}
        </li>
      ))}
    </ul>
  );
};

export default TopicList;
