import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

/**
 * Error Boundary Component
 * Catches JavaScript errors in child component tree and displays fallback UI
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error("[ErrorBoundary] Caught error:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      const { fallback, agentName } = this.props;
      
      if (fallback) {
        return fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-red-500/5 border border-red-500/15 backdrop-blur-sm">
          <div className="w-12 h-12 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-4">
            <AlertTriangle className="w-6 h-6 text-red-400" />
          </div>
          <h3 className="text-foreground font-semibold text-lg mb-2 font-[family-name:var(--font-heading)] tracking-tight">
            {agentName ? `${agentName} Error` : "Something went wrong"}
          </h3>
          <p className="text-muted-foreground text-sm text-center max-w-md mb-4">
            {agentName 
              ? `The ${agentName} agent encountered an error while rendering.`
              : "An unexpected error occurred while rendering this component."}
          </p>
          <button
            onClick={this.handleRetry}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition-all duration-200 text-sm font-medium"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
          {process.env.NODE_ENV === "development" && this.state.error && (
            <details className="mt-4 text-xs text-muted-foreground max-w-md">
              <summary className="cursor-pointer hover:text-foreground">Error Details</summary>
              <pre className="mt-2 p-3 bg-background/80 rounded-xl overflow-auto max-h-32 border border-white/[0.04]">
                {this.state.error.toString()}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Agent-specific Error Boundary with styling
 */
export function AgentErrorBoundary({ children, agentName }) {
  return (
    <ErrorBoundary agentName={agentName}>
      {children}
    </ErrorBoundary>
  );
}

export default ErrorBoundary;
