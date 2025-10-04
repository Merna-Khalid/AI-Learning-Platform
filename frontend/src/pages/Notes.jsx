import React, { useEffect, useState } from "react";

const Notes = ({ goToPage }) => {
  const [courses, setCourses] = useState([]);
  const [topics, setTopics] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [notes, setNotes] = useState("");

  // Fetch courses
  useEffect(() => {
    fetch("http://localhost:8000/courses/")
      .then((res) => res.json())
      .then((data) => setCourses(data));
  }, []);

  // Fetch topics when course selected
  useEffect(() => {
    if (selectedCourse) {
      fetch(`http://localhost:8000/topics/course/${selectedCourse}`)
        .then((res) => res.json())
        .then((data) => setTopics(data));
    } else {
      setTopics([]);
    }
  }, [selectedCourse]);

  const handleGenerate = async () => {
    if (!selectedTopic) return;
    setLoading(true);
    setNotes("");
    try {
      const res = await fetch("http://localhost:8000/notes/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          course: selectedCourse,
          topic: selectedTopic,
        }),
      });

      const data = await res.json();
      setNotes(data.notes);
    } catch (err) {
      setNotes("Error generating notes.");
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-center text-gray-800 dark:text-gray-100">
        Notes
      </h1>

      {/* Course selection */}
      <div>
        <label className="block text-gray-700 dark:text-gray-300 mb-1">Select Course</label>
        <select
          value={selectedCourse}
          onChange={(e) => setSelectedCourse(e.target.value)}
          className="w-full border rounded p-2 dark:bg-gray-700 dark:text-white"
        >
          <option value="">-- Select --</option>
          {courses.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Topic selection */}
      {topics.length > 0 && (
        <div>
          <label className="block text-gray-700 dark:text-gray-300 mb-1">Select Topic</label>
          <select
            value={selectedTopic}
            onChange={(e) => setSelectedTopic(e.target.value)}
            className="w-full border rounded p-2 dark:bg-gray-700 dark:text-white"
          >
            <option value="">-- Select --</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Generate button */}
      <button
        onClick={handleGenerate}
        disabled={!selectedTopic || loading}
        className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
      >
        {loading ? "Generating Notes..." : "Generate Notes"}
      </button>

      {/* Notes output */}
      {notes && (
        <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow space-y-2">
          <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-200">
            Generated Notes
          </h2>
          <p className="text-gray-600 whitespace-pre-line dark:text-gray-400">{notes}</p>
        </div>
      )}

      <button
        onClick={() => goToPage("dashboard")}
        className="w-full text-center py-2 text-indigo-600 dark:text-indigo-400 font-medium hover:underline"
      >
        &larr; Back to Dashboard
      </button>
    </div>
  );
};

export default Notes;
