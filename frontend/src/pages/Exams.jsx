import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api/api";

const Exams = ({ selectedCourse }) => {
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exam, setExam] = useState(null);
  const [difficulty, setDifficulty] = useState("medium");
  const [numQuestions, setNumQuestions] = useState(5);
  const [duration, setDuration] = useState(60); // in minutes
  const [error, setError] = useState(null);

  // Example topics for now
  const allTopics = [
    "Neural Nets",
    "Backpropagation",
    "RNNs",
    "CNNs",
    "Linear Regression",
    "Hypothesis Testing",
    "Financial Statements",
  ];

  const handleTopicToggle = (topic) => {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  };

  const createTimedExam = async () => {
    setLoading(true);
    setError(null);
    setExam(null);

    if (!selectedCourse) {
      setError("Please select a course first.");
      setLoading(false);
      return;
    }
    if (selectedTopics.length === 0) {
      setError("Please select at least one topic.");
      setLoading(false);
      return;
    }

    try {
      const res = await api.post("/exams/create_timed", {
        course: selectedCourse.name,
        topics: selectedTopics,
        num_questions: numQuestions,
        difficulty: difficulty,
        duration_minutes: duration,
      });
      setExam(res.data);
    } catch (err) {
      console.error("Error creating exam:", err);
      setError("Failed to create exam. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 space-y-6">
      <h1 className="text-3xl font-bold text-center text-gray-800 dark:text-gray-100">
        Create Timed Exam
      </h1>

      {selectedCourse && (
        <div className="text-center text-gray-600 dark:text-gray-400">
          <p>
            Creating an exam for{" "}
            <span className="font-semibold text-indigo-500">
              {selectedCourse.name}
            </span>
          </p>
        </div>
      )}

      {/* Control Panel */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-lg space-y-4">
        {/* Multi Topic Selector */}
        <div>
          <label className="block text-gray-700 dark:text-gray-300 mb-2 font-medium">
            Select Topics
          </label>
          <div className="flex flex-wrap gap-2">
            {allTopics.map((t) => (
              <label
                key={t}
                className={`flex items-center space-x-2 px-4 py-2 rounded-full cursor-pointer transition-colors
                  ${
                    selectedTopics.includes(t)
                      ? "bg-indigo-500 text-white"
                      : "bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                  }`}
              >
                <input
                  type="checkbox"
                  checked={selectedTopics.includes(t)}
                  onChange={() => handleTopicToggle(t)}
                  className="hidden"
                />
                <span>{t}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Exam Settings */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-gray-700 dark:text-gray-300 mb-2 font-medium">
              Difficulty
            </label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-800 dark:text-gray-100"
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700 dark:text-gray-300 mb-2 font-medium">
              Number of Questions
            </label>
            <input
              type="number"
              value={numQuestions}
              onChange={(e) =>
                setNumQuestions(Math.max(1, parseInt(e.target.value, 10)))
              }
              min="1"
              className="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-800 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="block text-gray-700 dark:text-gray-300 mb-2 font-medium">
              Duration (minutes)
            </label>
            <input
              type="number"
              value={duration}
              onChange={(e) =>
                setDuration(Math.max(1, parseInt(e.target.value, 10)))
              }
              min="1"
              className="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-800 dark:text-gray-100"
            />
          </div>
        </div>

        {/* Generate Button */}
        <button
          onClick={createTimedExam}
          disabled={!selectedCourse || selectedTopics.length === 0 || loading}
          className="w-full bg-indigo-600 text-white font-medium py-3 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Creating Exam..." : "Create Exam"}
        </button>

        {error && (
          <p className="mt-4 text-center text-red-500 dark:text-red-400">
            {error}
          </p>
        )}
      </div>

      {/* Exam View */}
      {exam && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mt-8">
            {exam.course} Exam
          </h2>
          <div className="p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg space-y-3">
            <h3 className="font-semibold text-gray-700 dark:text-gray-200">
              Topics: {exam.topics.join(", ")}
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Duration: {exam.duration_minutes} minutes
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              Total Questions: {exam.questions.length}
            </p>
            <p className="text-sm italic text-gray-500 dark:text-gray-400">
              {exam.instructions}
            </p>
          </div>
          {/* Display exam questions here */}
          <h3 className="text-xl font-bold text-gray-800 dark:text-gray-100">
            Questions
          </h3>
          {exam.questions.map((q, idx) => (
            <div
              key={idx}
              className="p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="bg-indigo-100 text-indigo-800 text-xs font-semibold px-2.5 py-0.5 rounded-full dark:bg-indigo-900 dark:text-indigo-300">
                  {q.type.toUpperCase().replace("_", " ")}
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Question {idx + 1}
                </span>
              </div>
              <p className="text-gray-700 dark:text-gray-200">
                {q.problem_description || q.statement || q.question}
              </p>
              {q.options && (
                <ul className="list-disc pl-5 text-gray-600 dark:text-gray-400 space-y-1">
                  {q.options.map((o, i) => (
                    <li key={i}>{o}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Exams;
