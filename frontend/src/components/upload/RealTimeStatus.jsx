import React from "react";
import { Wifi, WifiOff, Clock, AlertCircle, CheckCircle } from "lucide-react";
import useIngestionStatus from "../../hooks/useIngestionStatus";

const RealTimeStatus = ({ fileName, materialId }) => {
  const { status, isConnected, isStale, lastUpdate } = useIngestionStatus(materialId);
  
  if (!materialId) return null;

  const currentStatus = status || { 
    status: "processing", 
    progress: 0, 
    message: "Waiting for status updates..." 
  };

  const getStatusColor = () => {
    if (currentStatus.status === "error" || currentStatus.status === "failed") 
      return "red";
    if (currentStatus.status === "completed") 
      return "green";
    if (!isConnected || isStale) 
      return "yellow";
    return "blue";
  };

  const statusColor = getStatusColor();
  const colorClasses = {
    red: "bg-red-500",
    green: "bg-green-500", 
    yellow: "bg-yellow-500",
    blue: "bg-blue-500"
  };

  return (
    <div className="space-y-3">
      {/* Status header */}
      <div className="flex justify-between items-center text-sm">
        <span className="flex items-center space-x-2">
          {!isConnected ? (
            <WifiOff className="w-4 h-4 text-yellow-500" />
          ) : (
            <Wifi className="w-4 h-4 text-green-500" />
          )}
          <span className={
            statusColor === "red" ? "text-red-600 dark:text-red-400" :
            statusColor === "green" ? "text-green-600 dark:text-green-400" :
            statusColor === "yellow" ? "text-yellow-600 dark:text-yellow-400" :
            "text-blue-600 dark:text-blue-400"
          }>
            {currentStatus.message}
          </span>
        </span>
        <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
          <span>{currentStatus.progress}%</span>
          {isStale && <Clock className="w-3 h-3" />}
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${colorClasses[statusColor]}`}
          style={{ width: `${currentStatus.progress}%` }}
        ></div>
      </div>

      {/* Connection status */}
      <div className="flex justify-between items-center text-xs">
        <div className="flex items-center space-x-2">
          {!isConnected ? (
            <>
              <WifiOff className="w-3 h-3 text-yellow-500" />
              <span className="text-yellow-600 dark:text-yellow-400">
                Using polling updates
              </span>
            </>
          ) : (
            <>
              <Wifi className="w-3 h-3 text-green-500" />
              <span className="text-green-600 dark:text-green-400">
                Live updates connected
              </span>
            </>
          )}
        </div>
        
        {isStale && (
          <span className="text-yellow-600 dark:text-yellow-400 flex items-center space-x-1">
            <AlertCircle className="w-3 h-3" />
            <span>Updates delayed</span>
          </span>
        )}
        
        <span className="text-gray-500 dark:text-gray-400 text-xs">
          Last: {lastUpdate}
        </span>
      </div>

      {/* Final status messages */}
      {currentStatus.status === "completed" && (
        <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <div className="flex items-center space-x-2 text-green-700 dark:text-green-300">
            <CheckCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Ingestion completed successfully!</span>
          </div>
        </div>
      )}
      
      {currentStatus.status === "failed" && (
        <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
          <div className="flex items-center space-x-2 text-red-700 dark:text-red-300">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Ingestion failed. Please try again.</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default RealTimeStatus;