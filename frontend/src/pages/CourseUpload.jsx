import React, { useState, useEffect } from "react";
import { Upload } from "lucide-react";
import { uploadCourseMaterial, getCourseMaterials } from "../api/courseApi";
import FileUploadArea from "../components/upload/FileUploadArea";
import FileList from "../components/upload/FileList";
import PreviousMaterials from "../components/upload/PreviousMaterials";

const CourseUpload = ({ selectedCourse }) => {
  const [files, setFiles] = useState([]);
  const [contentType, setContentType] = useState("lecture");
  const [isDragOver, setIsDragOver] = useState(false);
  const [fileStatuses, setFileStatuses] = useState({});
  const [message, setMessage] = useState("");
  const [uploadedMaterials, setUploadedMaterials] = useState({});
  const [previousMaterials, setPreviousMaterials] = useState([]);
  const [loadingMaterials, setLoadingMaterials] = useState(true);
  const [materialsError, setMaterialsError] = useState(null);

  // File validation
  const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

  const validateFileType = (filename) => {
    const allowedExtensions = ['.pdf', '.txt', '.md', '.doc', '.docx', '.ppt', '.pptx', '.mp4', '.mov', '.avi'];
    const extension = filename.toLowerCase().slice((filename.lastIndexOf(".") - 1 >>> 0) + 2);
    return allowedExtensions.includes('.' + extension);
  };

  const validateFile = (file) => {
    const isTypeValid = validateFileType(file.name);
    const isSizeValid = file.size <= MAX_FILE_SIZE;
    
    if (!isTypeValid) return { valid: false, reason: "Unsupported file type" };
    if (!isSizeValid) return { valid: false, reason: "File too large (max 50MB)" };
    
    return { valid: true };
  };

  // Load previous materials when course changes
  const loadMaterials = async () => {
    if (selectedCourse?.id) {
      try {
        setLoadingMaterials(true);
        setMaterialsError(null);
        console.log('Loading materials for course:', selectedCourse.id);
        const materials = await getCourseMaterials(selectedCourse.id);
        console.log('Loaded materials:', materials);
        setPreviousMaterials(materials);
      } catch (error) {
        console.error("Error loading materials:", error);
        setMaterialsError(error.message || "Failed to load materials");
        setPreviousMaterials([]);
      } finally {
        setLoadingMaterials(false);
      }
    }
  };

  useEffect(() => {
    loadMaterials();
  }, [selectedCourse]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    
    const validFiles = [];
    const invalidFiles = [];
    
    droppedFiles.forEach(file => {
      const validation = validateFile(file);
      if (validation.valid) {
        validFiles.push(file);
      } else {
        invalidFiles.push({ file, reason: validation.reason });
      }
    });
    
    if (invalidFiles.length > 0) {
      setMessage(`Some files were skipped: ${invalidFiles.map(f => `${f.file.name} (${f.reason})`).join(', ')}`);
    }
    
    setFiles((prevFiles) => [...prevFiles, ...validFiles]);
    validFiles.forEach((file) => {
      setFileStatuses((prev) => ({ ...prev, [file.name]: "pending" }));
    });
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    const validFiles = [];
    const invalidFiles = [];
    
    selectedFiles.forEach(file => {
      const validation = validateFile(file);
      if (validation.valid) {
        validFiles.push(file);
      } else {
        invalidFiles.push({ file, reason: validation.reason });
      }
    });
    
    if (invalidFiles.length > 0) {
      setMessage(`Some files were skipped: ${invalidFiles.map(f => `${f.file.name} (${f.reason})`).join(', ')}`);
    }
    
    setFiles((prevFiles) => [...prevFiles, ...validFiles]);
    validFiles.forEach((file) => {
      setFileStatuses((prev) => ({ ...prev, [file.name]: "pending" }));
    });
    
    // Reset file input
    e.target.value = '';
  };

  const handleRemoveFile = (fileName) => {
    setFiles((prevFiles) => prevFiles.filter((file) => file.name !== fileName));
    setFileStatuses((prev) => {
      const newStatuses = { ...prev };
      delete newStatuses[fileName];
      return newStatuses;
    });
    setUploadedMaterials((prev) => {
      const newMaterials = { ...prev };
      delete newMaterials[fileName];
      return newMaterials;
    });
    if (message && message.includes(fileName)) {
      setMessage("");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (files.length === 0) {
      setMessage("Please select at least one file.");
      return;
    }

    setMessage("Starting upload and ingestion process...");
    
    for (const file of files) {
      setFileStatuses((prev) => ({ ...prev, [file.name]: "uploading" }));
      
      try {
        console.log('Uploading file:', file.name);
        const response = await uploadCourseMaterial(selectedCourse.id, file, contentType);
        console.log('Upload response:', response);
        setFileStatuses((prev) => ({ ...prev, [file.name]: "processing" }));
        
        setUploadedMaterials((prev) => ({
          ...prev,
          [file.name]: response.id
        }));
        
      } catch (err) {
        console.error(`Failed to upload ${file.name}:`, err);
        setFileStatuses((prev) => ({ ...prev, [file.name]: "error" }));
        setMessage(`Failed to upload ${file.name}: ${err.message}`);
      }
    }
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 space-y-6">
      {/* Upload Section */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-3xl shadow-lg transition-colors">
        <h1 className="text-3xl font-bold mb-2 text-gray-800 dark:text-gray-100">
          Upload Material
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Selected Course:{" "}
          <span className="font-semibold text-indigo-500">{selectedCourse?.name || 'Unknown'}</span>
        </p>
        
        <form onSubmit={handleSubmit}>
          {/* Content type (lecture, tutorial, reference) */}
          <label className="block mb-2 text-gray-700 dark:text-gray-300 font-medium">Content Type</label>
          <select
            value={contentType}
            onChange={(e) => setContentType(e.target.value)}
            className="w-full mb-4 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="lecture">Lecture</option>
            <option value="tutorial">Tutorial</option>
            <option value="reference">Reference</option>
          </select>

          {/* Drag and drop area */}
          <FileUploadArea
            isDragOver={isDragOver}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onFileSelect={handleFileSelect}
          />

          {/* File list with real-time status */}
          {files.length > 0 && (
            <FileList
              files={files}
              fileStatuses={fileStatuses}
              uploadedMaterials={uploadedMaterials}
              onRemoveFile={handleRemoveFile}
            />
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={
              files.length === 0 ||
              Object.values(fileStatuses).some(status => 
                status === "uploading" || status === "processing"
              ) ||
              loadingMaterials
            }
            className="w-full bg-indigo-600 text-white font-medium py-3 rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            <Upload className="w-5 h-5" />
            <span>Start Upload & Ingestion</span>
          </button>
        </form>

        {message && (
          <div className={`mt-4 p-3 rounded-lg border text-center ${
            message.includes('Failed') || message.includes('skipped') 
              ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
              : 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300'
          }`}>
            <p className="text-sm">{message}</p>
          </div>
        )}
      </div>

      {/* Previously Uploaded Files Section */}
      <PreviousMaterials
        materials={previousMaterials}
        loading={loadingMaterials}
        error={materialsError}
        onRefresh={loadMaterials}
      />
    </div>
  );
};

export default CourseUpload;