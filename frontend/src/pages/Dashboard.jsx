import React from "react";
import { BookOpen, Upload, HelpCircle, FileText, ClipboardCheck, Layers, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";

const Dashboard = ({ selectedCourse }) => {
  const features = [
    {
      title: "Notes",
      description: "Access AI-generated notes and additional explanations.",
      icon: <FileText className="w-8 h-8 text-yellow-500" />,
      to: "/notes",
    },
    {
      title: "Exercises",
      description: "Practice with exercises created for mastery.",
      icon: <Layers className="w-8 h-8 text-purple-500" />,
      to: "/exercises",
    },
    {
      title: "Quizzes",
      description: "Test your knowledge with quizzes of different types.",
      icon: <HelpCircle className="w-8 h-8 text-pink-500" />,
      to: "/quizzes",
    },
    // {
    //   title: "Exams",
    //   description: "Challenge yourself with exams to measure progress.",
    //   icon: <ClipboardCheck className="w-8 h-8 text-red-500" />,
    //   to: "/exams",
    // },
    {
      title: "Progress",
      description: "Track mastery levels and learning progress.",
      icon: <TrendingUp className="w-8 h-8 text-blue-500" />,
      to: "/progress",
    },
  ];

  return (
    <div className="py-6 px-4 sm:px-6 lg:px-8 space-y-6">
      <h1 className="text-3xl font-bold text-center text-gray-800 dark:text-gray-100">
        <span className="text-indigo-500">{selectedCourse.name}</span> Dashboard
      </h1>
      <p className="text-center text-gray-600 dark:text-gray-400 mb-6">
        {selectedCourse.description || "No description provided."}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {features.map((feature) => (
          <Link
            key={feature.title}
            to={feature.to}
            className="flex flex-col items-center justify-center p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-md hover:shadow-lg transition-shadow text-center"
          >
            {feature.icon}
            <h2 className="mt-4 text-xl font-semibold text-gray-800 dark:text-gray-100">
              {feature.title}
            </h2>
            <p className="mt-2 text-gray-600 dark:text-gray-400 text-sm">
              {feature.description}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
