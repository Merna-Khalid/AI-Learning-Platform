import React, { useState, useEffect } from "react";
import { Brain } from "lucide-react";
import api from "../api/api";
import ExerciseControlPanel from "../components/exercises/ExerciseControlPanel";
import ExerciseCard from "../components/exercises/ExerciseCard";
import GenerationStats from "../components/GenerationStats";
// import DebugInfo from "../components/exercises/DebugInfo";

const Exercises = ({ selectedCourse }) => {
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [allTopics, setAllTopics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingTopics, setLoadingTopics] = useState(false);
  const [exercises, setExercises] = useState([]);
  const [difficulty, setDifficulty] = useState("medium");
  const [numQuestions, setNumQuestions] = useState(5);
  const [error, setError] = useState(null);
  const [generationStats, setGenerationStats] = useState(null);

  // Fetch topics from materials when course changes
  useEffect(() => {
    const fetchTopicsFromMaterials = async () => {
      if (!selectedCourse?.id) {
        setAllTopics([]);
        return;
      }

      try {
        setLoadingTopics(true);
        setError(null);
        
        const materialsResponse = await api.get(`/courses/${selectedCourse.id}/materials`);
        const materials = materialsResponse.data || [];
        
        console.log('📚 Materials loaded:', materials);
        
        // Extract and flatten all topics from all materials
        const allExtractedTopics = new Set();
        
        materials.forEach(material => {
          console.log('🔍 Checking material:', material.filename, 'with topics:', material.extracted_topics);
          
          if (material.extracted_topics) {
            try {
              let topics = material.extracted_topics;
              
              if (typeof topics === 'string') {
                topics = JSON.parse(topics);
              }
              
              if (Array.isArray(topics)) {
                topics.forEach(topic => {
                  if (topic && topic.trim()) {
                    allExtractedTopics.add(topic.trim());
                  }
                });
              }
            } catch (parseError) {
              console.error('Error parsing topics for material:', material.id, parseError);
            }
          }
        });
        
        const uniqueTopics = Array.from(allExtractedTopics).sort();
        console.log('🎯 Final unique topics:', uniqueTopics);
        setAllTopics(uniqueTopics);
        
      } catch (err) {
        console.error("Error fetching materials/topics:", err);
        setError("Failed to load topics. Please try again.");
        setAllTopics([]);
      } finally {
        setLoadingTopics(false);
      }
    };

    fetchTopicsFromMaterials();
  }, [selectedCourse]);

  const handleTopicToggle = (topic) => {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  };

  const generateExercises = async () => {
    setLoading(true);
    setError(null);
    setExercises([]);
    setGenerationStats(null);

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
      const startTime = Date.now();
      const response = await api.post("/exercises/generate", {
        course: selectedCourse.name,
        topics: selectedTopics,
        num_questions: numQuestions,
        difficulty: difficulty,
      });
      
      const endTime = Date.now();
      const generationTime = (endTime - startTime) / 1000;
      
      if (response.data.error) {
        setError(response.data.error);
      } else {
        setExercises(response.data.exercises || []);
        setGenerationStats({
          time: generationTime,
          efficient: response.data.efficient_generation || false,
          count: response.data.exercises?.length || 0
        });
      }
    } catch (err) {
      console.error("Error generating exercises:", err);
      setError("Failed to generate exercises. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const clearSelection = () => {
    setSelectedTopics([]);
    setExercises([]);
    setError(null);
    setGenerationStats(null);
  };

  const selectAllTopics = () => {
    setSelectedTopics([...allTopics]);
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center space-x-3 mb-2">
          <Brain className="w-8 h-8 text-indigo-600" />
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">
            Exercises & Practice
          </h1>
        </div>
        {selectedCourse && (
          <p className="text-gray-600 dark:text-gray-400">
            For course:{" "}
            <span className="font-semibold text-indigo-500">
              {selectedCourse.name}
            </span>
          </p>
        )}
      </div>

      {/* Control Panel */}
      <ExerciseControlPanel
        selectedCourse={selectedCourse}
        allTopics={allTopics}
        selectedTopics={selectedTopics}
        onTopicToggle={handleTopicToggle}
        onSelectAll={selectAllTopics}
        onClearAll={clearSelection}
        difficulty={difficulty}
        onDifficultyChange={(e) => setDifficulty(e.target.value)}
        numQuestions={numQuestions}
        onNumQuestionsChange={(e) => setNumQuestions(parseInt(e.target.value, 10))}
        onGenerate={generateExercises}
        loading={loading}
        loadingTopics={loadingTopics}
        error={error}
      />

      {/* Generation Stats */}
      <GenerationStats stats={generationStats} />

      {/* Debug info */}
      {/* <DebugInfo 
        selectedCourse={selectedCourse}
        allTopics={allTopics}
        selectedTopics={selectedTopics}
      /> */}

      {/* Results */}
      {exercises.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
              Generated Exercises
            </h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {exercises.length} question{exercises.length !== 1 ? 's' : ''}
            </span>
          </div>
          
          {exercises.map((exercise, index) => (
            <ExerciseCard 
              key={index} 
              exercise={exercise} 
              index={index}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Exercises;