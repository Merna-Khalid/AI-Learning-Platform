import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Upload,
  BookOpen,
  FileText,
  Layers,
  HelpCircle,
  // ClipboardCheck,
  TrendingUp,
  Sun,
  Moon,
  Home,
  LogOut,
} from "lucide-react";

const Sidebar = ({ selectedCourse, setSelectedCourse }) => {
  const location = useLocation();

  const navItems = [
    { name: "Dashboard", icon: <Home />, path: "/" },
    { name: "Upload", icon: <Upload />, path: "/course-upload" },
    { name: "Overview", icon: <BookOpen />, path: "/course-overview" },
    { name: "Notes", icon: <FileText />, path: "/notes" },
    { name: "Exercises", icon: <Layers />, path: "/exercises" },
    { name: "Quizzes", icon: <HelpCircle />, path: "/quizzes" },
    // { name: "Exams", icon: <ClipboardCheck />, path: "/exams" },
    { name: "Progress", icon: <TrendingUp />, path: "/progress" },
  ];

  const handleLogout = () => {
    setSelectedCourse(null);
  };

  return (
    <div className="flex flex-col h-screen p-4 sm:p-6 bg-white dark:bg-gray-800 shadow-xl transition-colors w-20 sm:w-64 fixed top-0 left-0 z-50">
      {/* Course Name */}
      <div className="flex-shrink-0 mb-6 text-center">
        <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100 truncate">
          {selectedCourse.name}
        </h2>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 overflow-y-auto">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.name}>
              <Link
                to={item.path}
                className={`flex items-center space-x-2 p-3 rounded-lg transition-colors group
                  ${location.pathname === item.path
                    ? "bg-indigo-500 text-white shadow-md"
                    : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  }`}
              >
                <div className="w-5 h-5 flex-shrink-0">{item.icon}</div>
                <span className="text-sm font-medium hidden sm:inline-block">{item.name}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {/* Bottom controls */}
      <div className="flex-shrink-0 mt-6 space-y-2">
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center sm:justify-start space-x-2 p-3 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-red-500 hover:text-white transition-colors group"
        >
          <LogOut className="w-5 h-5" />
          <span className="text-sm font-medium hidden sm:inline-block">Change Course</span>
        </button>
       
      </div>
    </div>
  );
};

export default Sidebar;
