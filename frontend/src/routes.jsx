import React from "react";
import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import CourseUpload from "./pages/CourseUpload";
import CourseOverview from "./pages/CourseOverview";
import Notes from "./pages/Notes";
import Exercises from "./pages/Exercises";
import Quizzes from "./pages/Quizzes";
import Exams from "./pages/Exams";
import Progress from "./pages/Progress";

const AppRoutes = ({ darkMode, setDarkMode }) => {
  return (
    <>
      <Sidebar darkMode={darkMode} />
      <main className="flex-1 p-6 overflow-y-auto">
        <div className="flex justify-end mb-4">
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-md"
          >
            {darkMode ? "🌙" : "☀️"}
          </button>
        </div>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/course-upload" element={<CourseUpload />} />
          <Route path="/course-overview" element={<CourseOverview />} />
          <Route path="/notes" element={<Notes />} />
          <Route path="/exercises" element={<Exercises />} />
          <Route path="/quizzes" element={<Quizzes />} />
          <Route path="/exams" element={<Exams />} />
          <Route path="/progress" element={<Progress />} />
        </Routes>
      </main>
    </>
  );
};

export default AppRoutes;
