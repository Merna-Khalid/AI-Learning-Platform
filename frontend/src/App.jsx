import React, { useState } from "react";
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
import CourseSelection from "./pages/CourseSelection";

const App = () => {
  const [selectedCourse, setSelectedCourse] = useState(null);

  // Conditional rendering to show the course selection page first
  if (!selectedCourse) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
        
        <CourseSelection
          setSelectedCourse={setSelectedCourse}
        />
      </div>
    );
  }

  // Main application layout
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Sidebar with fixed positioning */}
      <Sidebar 
        selectedCourse={selectedCourse}
        setSelectedCourse={setSelectedCourse}
      />
      
      {/* Main content with margin to account for sidebar */}
      <div className="ml-20 sm:ml-64 p-4 sm:p-6 min-h-screen">
        <div className="rounded-3xl p-6 sm:p-8 md:p-10 shadow-lg min-h-[calc(100vh-3rem)] bg-white dark:bg-gray-800">
          <Routes>
            <Route path="/" element={<Dashboard selectedCourse={selectedCourse} />} />
            <Route path="/course-upload" element={<CourseUpload selectedCourse={selectedCourse} />} />
            <Route path="/course-overview" element={<CourseOverview selectedCourse={selectedCourse} />} />
            <Route path="/notes" element={<Notes selectedCourse={selectedCourse} />} />
            <Route path="/exercises" element={<Exercises selectedCourse={selectedCourse} />} />
            <Route path="/quizzes" element={<Quizzes selectedCourse={selectedCourse} />} />
            <Route path="/progress" element={<Progress selectedCourse={selectedCourse} />} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

export default App;