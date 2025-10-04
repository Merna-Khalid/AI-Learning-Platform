import React from "react";
import { Upload } from "lucide-react";

const FileUploadArea = ({ 
  isDragOver, 
  onDragOver, 
  onDragLeave, 
  onDrop, 
  onFileSelect 
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center w-full mb-4 p-8 rounded-lg border-2 border-dashed transition-colors cursor-pointer ${
        isDragOver
          ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950"
          : "border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 hover:border-indigo-300 dark:hover:border-indigo-600"
      }`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onClick={() => document.getElementById('file-input').click()}
    >
      <Upload className="w-10 h-10 text-gray-400 dark:text-gray-500" />
      <p className="mt-2 text-center text-gray-600 dark:text-gray-400">
        <span className="font-semibold">Click to upload</span> or drag and drop files here.
      </p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
        Supported: PDF, TXT, MD, DOC, DOCX, PPT, PPTX, MP4, MOV, AVI (max 50MB)
      </p>
      <input
        type="file"
        className="hidden"
        multiple
        onChange={onFileSelect}
        id="file-input"
      />
    </div>
  );
};

export default FileUploadArea;