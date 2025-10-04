// src/pages/CourseOverview.jsx
import React, { useState, useEffect } from "react";
import { Brain, Loader, AlertCircle, BookOpen, Zap, Download, Share2 } from "lucide-react";
import api from "../api/api";
import html2canvas from 'html2canvas';

const CourseOverview = ({ selectedCourse, goToPage }) => {
  const [mindMap, setMindMap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBranch, setSelectedBranch] = useState(null);

  useEffect(() => {
    if (selectedCourse) {
      generateMindMap();
    }
  }, [selectedCourse]);

  const generateMindMap = async () => {
    if (!selectedCourse?.id) return;
    
    setLoading(true);
    setError(null);
    setMindMap(null);
    
    try {
      const response = await api.post("/mindmap/generate", {
        course_id: selectedCourse.id
      });
      
      setMindMap(response.data);
    } catch (err) {
      console.error("Error generating mind map:", err);
      setError("Failed to generate mind map. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const exportAsImage = () => {
    // Simple export functionality
    const element = document.querySelector('.mindmap-container');
    html2canvas(element).then(canvas => {
      const link = document.createElement('a');
      link.download = `mindmap-${selectedCourse.name}-${new Date().getTime()}.png`;
      link.href = canvas.toDataURL();
      link.click();
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-12 h-12 text-indigo-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Generating your course mind map...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <Brain className="w-10 h-10 text-indigo-600" />
            <h1 className="text-4xl font-bold text-gray-800 dark:text-gray-100">
              Course Overview
            </h1>
          </div>
          {selectedCourse && (
            <p className="text-xl text-gray-600 dark:text-gray-400">
              {selectedCourse.name} • Knowledge Map
            </p>
          )}
        </div>

        {/* Controls */}
        <div className="flex justify-center space-x-4 mb-8">
          <button
            onClick={generateMindMap}
            className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors flex items-center space-x-2"
          >
            <Zap className="w-5 h-5" />
            <span>Regenerate Map</span>
          </button>
          <button
            onClick={exportAsImage}
            className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
          >
            <Download className="w-5 h-5" />
            <span>Export</span>
          </button>
          <button
            onClick={() => goToPage("dashboard")}
            className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
          >
            ← Back to Dashboard
          </button>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center mb-8">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
            <p className="text-red-700 dark:text-red-300 text-lg">{error}</p>
            <button
              onClick={generateMindMap}
              className="mt-4 bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {mindMap && (
          <div className="space-y-8">
            {/* Mind Map Visualization */}
            <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl p-8 mindmap-container">
              <MindMapVisualization 
                mindMap={mindMap.mind_map}
                selectedBranch={selectedBranch}
                onBranchSelect={setSelectedBranch}
              />
            </div>

            {/* Branch Details Panel */}
            {selectedBranch && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                <BranchDetails 
                  branch={selectedBranch}
                  onClose={() => setSelectedBranch(null)}
                />
              </div>
            )}

            {/* Generation Info */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
              <div className="flex items-center justify-between text-sm text-blue-700 dark:text-blue-300">
                <span>✨ AI-generated knowledge structure</span>
                <span>Context used: {mindMap.context_used} sections</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Mind Map Visualization Component
const MindMapVisualization = ({ mindMap, selectedBranch, onBranchSelect }) => {
  const centralTopic = mindMap.central_topic;
  const mainBranches = mindMap.main_branches || [];

  return (
    <div className="relative">
      {/* Central Topic */}
      <div className="flex justify-center mb-12">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-2xl font-bold py-6 px-8 rounded-2xl shadow-lg transform hover:scale-105 transition-transform duration-200">
          {centralTopic}
        </div>
      </div>

      {/* Main Branches */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mainBranches.map((branch, index) => (
          <BranchNode
            key={branch.name}
            branch={branch}
            index={index}
            isSelected={selectedBranch?.name === branch.name}
            onSelect={onBranchSelect}
          />
        ))}
      </div>
    </div>
  );
};

// Individual Branch Component
const BranchNode = ({ branch, index, isSelected, onSelect }) => {
  const getImportanceColor = (importance) => {
    const colors = {
      high: 'bg-red-500 border-red-600',
      medium: 'bg-blue-500 border-blue-600', 
      low: 'bg-green-500 border-green-600'
    };
    return colors[importance] || 'bg-gray-500 border-gray-600';
  };

  return (
    <div 
      className={`relative p-6 rounded-xl border-2 cursor-pointer transform transition-all duration-200 ${
        isSelected 
          ? 'scale-105 shadow-2xl ring-4 ring-opacity-50 ring-yellow-400' 
          : 'hover:scale-102 hover:shadow-lg'
      } ${getImportanceColor(branch.importance)} text-white`}
      onClick={() => onSelect(branch)}
    >
      {/* Importance Badge */}
      <div className="absolute -top-2 -right-2 bg-white dark:bg-gray-800 text-xs font-bold px-2 py-1 rounded-full text-gray-800 dark:text-gray-200 capitalize">
        {branch.importance}
      </div>

      {/* Branch Content */}
      <h3 className="text-xl font-bold mb-3">{branch.name}</h3>
      <p className="text-white text-opacity-90 text-sm mb-4 line-clamp-2">
        {branch.description}
      </p>

      {/* Sub-branches Preview */}
      <div className="space-y-2">
        {branch.sub_branches.slice(0, 3).map((sub, subIndex) => (
          <div 
            key={subIndex}
            className="bg-white bg-opacity-20 rounded-lg px-3 py-2 text-sm backdrop-blur-sm"
          >
            {sub}
          </div>
        ))}
        {branch.sub_branches.length > 3 && (
          <div className="text-white text-opacity-70 text-sm">
            +{branch.sub_branches.length - 3} more
          </div>
        )}
      </div>

      {/* Key Points Count */}
      {branch.key_points.length > 0 && (
        <div className="absolute -bottom-2 -left-2 bg-yellow-500 text-yellow-900 text-xs font-bold px-2 py-1 rounded-full">
          {branch.key_points.length} key points
        </div>
      )}
    </div>
  );
};

// Branch Details Component
const BranchDetails = ({ branch, onClose }) => {
  return (
    <div className="relative">
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
      >
        ✕
      </button>

      <div className="pr-12">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-4">
          {branch.name}
        </h2>
        
        <p className="text-gray-600 dark:text-gray-400 mb-6 text-lg">
          {branch.description}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sub-branches */}
          <div>
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center">
              <BookOpen className="w-5 h-5 mr-2" />
              Sub-topics
            </h3>
            <ul className="space-y-2">
              {branch.sub_branches.map((sub, index) => (
                <li 
                  key={index}
                  className="bg-gray-50 dark:bg-gray-700 rounded-lg px-4 py-3 text-gray-700 dark:text-gray-300"
                >
                  {sub}
                </li>
              ))}
            </ul>
          </div>

          {/* Key Points */}
          <div>
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center">
              <Zap className="w-5 h-5 mr-2" />
              Key Points
            </h3>
            <ul className="space-y-2">
              {branch.key_points.map((point, index) => (
                <li 
                  key={index}
                  className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg px-4 py-3 text-yellow-800 dark:text-yellow-200"
                >
                  {point}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Connections */}
        {branch.connections.length > 0 && (
          <div className="mt-6">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">
              Related Concepts
            </h3>
            <div className="flex flex-wrap gap-2">
              {branch.connections.map((connection, index) => (
                <span 
                  key={index}
                  className="bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 px-3 py-1 rounded-full text-sm"
                >
                  {connection}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CourseOverview;