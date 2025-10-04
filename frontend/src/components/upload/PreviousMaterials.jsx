import React from "react";
import { FileText, History, RefreshCw, AlertCircle } from "lucide-react";
import MaterialsErrorBoundary from "./MaterialsErrorBoundary";

const PreviousMaterials = ({ 
  materials, 
  loading, 
  error, 
  onRefresh 
}) => {
  const renderMaterial = (material) => {
    try {
      return (
        <div
          key={material.id}
          className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-600 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <FileText className="w-5 h-5 text-gray-500" />
            <div>
              <div className="font-medium text-gray-900 dark:text-gray-100">
                {material.filename || 'Unknown file'}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Uploaded: {material.date_uploaded ? new Date(material.date_uploaded).toLocaleDateString() : 'Unknown date'}
                {material.source_type && ` • ${typeof material.source_type === 'object' ? material.source_type.value?.toUpperCase() : material.source_type?.toUpperCase()}`}
                {material.content_type && ` • ${material.content_type.charAt(0).toUpperCase() + material.content_type.slice(1)}`}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              material.ingestion_status === 'completed' 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : material.ingestion_status === 'processing'
                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                : material.ingestion_status === 'failed'
                ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
            }`}>
              {material.ingestion_status || 'unknown'}
            </span>
          </div>
        </div>
      );
    } catch (error) {
      console.error('Error rendering material:', error, material);
      return (
        <div className="p-4 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
          <div className="text-red-700 dark:text-red-300 text-sm">
            Error displaying material: {material.id}
          </div>
        </div>
      );
    }
  };

  return (
    <MaterialsErrorBoundary>
      <div className="bg-white dark:bg-gray-800 p-6 rounded-3xl shadow-lg transition-colors">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <History className="w-5 h-5 text-indigo-600" />
            <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">
              Previously Uploaded Materials
            </h2>
          </div>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
            title="Refresh materials"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <div className="flex items-center space-x-2 text-red-700 dark:text-red-300">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : materials.length > 0 ? (
          <div className="space-y-3">
            {materials.map(renderMaterial)}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No materials uploaded yet.</p>
            <p className="text-sm">Upload your first file to see it here.</p>
          </div>
        )}
      </div>
    </MaterialsErrorBoundary>
  );
};

export default PreviousMaterials;