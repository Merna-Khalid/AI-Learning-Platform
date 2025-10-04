import React from "react";
import { XCircle, Upload, Database, CheckCircle, AlertCircle, FileText } from "lucide-react";
import RealTimeStatus from "./RealTimeStatus";

const FileList = ({ 
  files, 
  fileStatuses, 
  uploadedMaterials, 
  onRemoveFile 
}) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case "uploading":
        return <Upload className="w-5 h-5 text-blue-500 animate-pulse" />;
      case "processing":
        return <Database className="w-5 h-5 text-yellow-500 animate-pulse" />;
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "error":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <FileText className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case "uploading":
        return "Uploading...";
      case "processing":
        return "Processing...";
      case "completed":
        return "Completed";
      case "error":
        return "Failed";
      default:
        return "Pending";
    }
  };

  return (
    <div className="mb-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300">
          Upload Progress ({files.length} file{files.length !== 1 ? 's' : ''})
        </h3>
        <button
          type="button"
          onClick={() => files.forEach(file => onRemoveFile(file.name))}
          className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
        >
          Clear all
        </button>
      </div>
      {files.map((file) => (
        <div
          key={file.name}
          className="p-4 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              {getStatusIcon(fileStatuses[file.name])}
              <div>
                <span className="font-medium text-gray-800 dark:text-gray-100">{file.name}</span>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {getStatusText(fileStatuses[file.name])}
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => onRemoveFile(file.name)}
              className="p-1 rounded-full text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              disabled={fileStatuses[file.name] === "uploading" || fileStatuses[file.name] === "processing"}
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>

          {/* Real-time status tracking */}
          {uploadedMaterials[file.name] && (
            <RealTimeStatus 
              fileName={file.name} 
              materialId={uploadedMaterials[file.name]} 
            />
          )}
        </div>
      ))}
    </div>
  );
};

export default FileList;