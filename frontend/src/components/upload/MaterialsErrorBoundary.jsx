import React from "react";
import { AlertCircle } from "lucide-react";

class MaterialsErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error in materials section:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-3xl shadow-lg transition-colors">
          <div className="text-center py-8 text-red-500">
            <AlertCircle className="w-12 h-12 mx-auto mb-3" />
            <h3 className="text-lg font-semibold mb-2">Error Loading Materials</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              There was an error loading the previously uploaded materials.
            </p>
            <div className="space-x-2">
              <button
                onClick={() => this.setState({ hasError: false, error: null })}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default MaterialsErrorBoundary;