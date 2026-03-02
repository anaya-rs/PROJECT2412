import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Panel } from '@/components/Panel';
import { ControlButton } from '@/components/ControlButton';
import { TextInput } from '@/components/TextInput';
import { apiService } from '@/lib/api';
import {
  ArrowLeft,
  BookOpen,
  Clock,
  Sparkles,
  Upload,
  Loader2,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  HelpCircle,
  Wifi,
  WifiOff,
} from 'lucide-react';

export default function LessonCreator() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [content, setContent] = useState('');
  const [duration, setDuration] = useState(30);
  const [difficulty, setDifficulty] = useState('beginner');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [generationStatus, setGenerationStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'network' | 'auth' | 'server' | 'content' | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const categorizeError = (error: string): 'network' | 'auth' | 'server' | 'content' => {
    if (error.includes('401') || error.includes('Unauthorized')) return 'auth';
    if (error.includes('network') || error.includes('fetch') || error.includes('timeout')) return 'network';
    if (error.includes('500') || error.includes('server')) return 'server';
    return 'content';
  };

  const handleRetry = async () => {
    if (retryCount >= 2) {
      // After 2 retries, suggest alternative actions
      setShowProgressModal(false);
      return;
    }
    
    setRetryCount(prev => prev + 1);
    setGenerationError(null);
    setErrorType(null);
    await handleGenerate();
  };

  const handleReset = () => {
    setShowProgressModal(false);
    setGenerationError(null);
    setErrorType(null);
    setRetryCount(0);
    setIsGenerating(false);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const result = await apiService.uploadFile(file);
      setContent(result.text);
      setUploadedFileName(result.fileName || file.name);
      // Auto-fill title with filename (without extension) if title is empty
      if (!title) {
        const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "");
        setTitle(nameWithoutExt);
      }
    } catch (error) {
      console.error('Failed to upload file:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleGenerate = async () => {
    if (!title || !content || (content?.length || 0) < 100) {
      return;
    }

    setIsGenerating(true);
    setShowProgressModal(true);
    setGenerationProgress(0);
    setGenerationStatus('Starting lesson generation...');
    setGenerationError(null);
    setErrorType(null);
    setRetryCount(0); // Reset retry count for new generation
    
    try {
      // Simulate progress updates
      const progressSteps = [
        { progress: 10, status: 'Validating content...' },
        { progress: 25, status: 'Preparing AI prompts...' },
        { progress: 40, status: 'Generating content sections...' },
        { progress: 60, status: 'Creating questions...' },
        { progress: 80, status: 'Assembling lesson structure...' },
        { progress: 95, status: 'Finalizing lesson...' },
      ];

      // Update progress
      for (const step of progressSteps) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
        setGenerationProgress(step.progress);
        setGenerationStatus(step.status);
      }

      // Start actual generation
      const job = await apiService.startAiLessonJob({
        text: content,
        title,
        description,
        fileName: uploadedFileName || undefined,
        difficulty,
        duration,
      });

      setGenerationProgress(100);
      setGenerationStatus('Lesson generated successfully!');
      
      // Wait a moment to show success
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Close modal and redirect
      setShowProgressModal(false);
      navigate(`/generating?jobId=${job.jobId}`);
      } catch (error) {
      console.error('Failed to generate lesson:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate lesson. Please try again.';
      setGenerationError(errorMessage);
      setErrorType(categorizeError(errorMessage));
      setGenerationStatus('Generation failed');
      // Don't auto-close on error - let user decide what to do
    } finally {
      setIsGenerating(false);
    }
  };

  return (
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <ControlButton
            variant="secondary"
            onClick={() => navigate(-1)}
            className="p-2"
          >
            <ArrowLeft className="w-5 h-5" />
          </ControlButton>
          <div>
            <h1 className="font-heading font-bold text-3xl tracking-tight text-black">
              Create Lesson
            </h1>
            <p className="text-muted mt-1">
              Transform your content into an interactive learning experience
            </p>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Lesson Info */}
          <div className="lg:col-span-1 space-y-6">
            <Panel accent>
              <h2 className="font-heading font-semibold text-lg tracking-tight text-black mb-4">
                Lesson Details
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-black">
                    Title
                  </label>
                  <TextInput
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Enter lesson title"
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium text-black">
                    Description
                  </label>
                  <TextInput
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of the lesson"
                    className="mt-1"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-black">
                    Duration (minutes)
                  </label>
                  <select
                    value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))}
                    className="w-full mt-1 px-3 py-2 border-2 border-black bg-white text-sm rounded-md focus:outline-none focus:border-accent-amber"
                  >
                    <option value={5}>5 minutes</option>
                    <option value={15}>15 minutes</option>
                    <option value={30}>30 minutes</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium text-black">
                    Difficulty Level
                  </label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full mt-1 px-3 py-2 border-2 border-black bg-white text-sm rounded-md focus:outline-none focus:border-accent-amber"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
              </div>
            </Panel>

            <Panel>
              <h3 className="font-heading font-semibold text-lg tracking-tight text-black mb-4">
                Quick Tips
              </h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <BookOpen className="w-4 h-4 text-accent-orange mt-0.5" />
                  <p className="text-sm text-muted">
                    Paste your lesson content or upload a file
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <Sparkles className="w-4 h-4 text-accent-orange mt-0.5" />
                  <p className="text-sm text-muted">
                    AI will create interactive questions and activities
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <Clock className="w-4 h-4 text-accent-orange mt-0.5" />
                  <p className="text-sm text-muted">
                    Generation typically takes 30-60 seconds
                  </p>
                </div>
              </div>
            </Panel>
          </div>

          {/* Right Column - Content Input */}
          <div className="lg:col-span-2 space-y-6">
            <Panel>
              <h2 className="font-heading font-semibold text-lg tracking-tight text-black mb-4">
                Lesson Content
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-black">
                    Content Text
                  </label>
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Paste your lesson content here, or upload a file below..."
                    className="w-full h-96 border-2 border-black px-3 py-2 text-sm rounded-md bg-white transition-all duration-base ease-standard focus:outline-none focus:border-accent-amber placeholder:text-muted resize-none"
                  />
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-xs text-muted">
                      {content?.length || 0} characters
                      {content?.length < 100 && content?.length > 0 && (
                        <span className="text-red-500 font-medium"> (too short - minimum 100 required)</span>
                      )}
                      {content?.length === 0 && (
                        <span className="text-gray-400"> (minimum 100 required)</span>
                      )}
                    </span>
                    {content?.length >= 100 && (
                      <span className="text-xs text-green-600 font-medium">✓ Ready to generate</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <input
                    type="file"
                    accept=".txt,.pdf,.docx"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                  />
                  <ControlButton
                    variant="secondary"
                    className="flex items-center gap-2"
                    onClick={() => document.getElementById('file-upload')?.click()}
                    disabled={isUploading}
                    loading={isUploading}
                  >
                    <Upload className="w-4 h-4" />
                    {isUploading ? 'UPLOADING...' : 'Upload File'}
                  </ControlButton>
                  <span className="text-xs text-muted">
                    PDF, DOCX, or TXT files supported
                  </span>
                  {uploadedFileName && (
                    <span className="text-xs text-accent-orange font-medium">
                      ✓ {uploadedFileName}
                    </span>
                  )}
                </div>
              </div>
            </Panel>

            {/* Content Preview */}
            {content && (
              <Panel>
                <h3 className="font-heading font-semibold text-lg tracking-tight text-black mb-4">
                  Content Preview
                </h3>
                <div className="max-h-64 overflow-y-auto">
                  <div className="text-sm text-muted leading-relaxed whitespace-pre-wrap">
                    {(content?.length || 0) > 500 ? content?.substring(0, 500) + '...' : content}
                  </div>
                  {(content?.length || 0) > 500 && (
                    <div className="text-xs text-accent-orange font-medium mt-2">
                      Showing first 500 characters of {content?.length || 0} total
                    </div>
                  )}
                </div>
              </Panel>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-4">
          <ControlButton
            variant="secondary"
            onClick={() => navigate('/lessons')}
          >
            Cancel
          </ControlButton>
          <ControlButton
            variant="primary"
            onClick={handleGenerate}
            disabled={!title || !content || (content?.length || 0) < 100 || isGenerating}
            loading={isGenerating}
            className="min-w-[140px]"
          >
            {isGenerating ? 'GENERATING...' : 'Generate Lesson'}
          </ControlButton>
        </div>

        {/* Progress Modal */}
        {showProgressModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white border-2 border-black rounded-lg p-8 max-w-lg w-full mx-4 shadow-2xl">
              {!generationError ? (
                // Success/Loading State
                <div className="text-center space-y-6">
                  <div className="flex justify-center">
                    {generationProgress === 100 ? (
                      <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                        <CheckCircle className="w-10 h-10 text-green-600" />
                      </div>
                    ) : (
                      <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
                        <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
                      </div>
                    )}
                  </div>
                  
                  <div>
                    <h3 className="font-heading font-bold text-xl text-black mb-2">
                      {generationProgress === 100 ? 'Lesson Generated Successfully!' : 'Generating Your Lesson...'}
                    </h3>
                    <p className="text-muted-foreground">
                      {generationStatus}
                    </p>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="space-y-2">
                    <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500 ease-out"
                        style={{ width: `${generationProgress}%` }}
                      />
                    </div>
                    <div className="text-xs font-mono text-gray-500">
                      {generationProgress}% Complete
                    </div>
                  </div>
                  
                  {generationProgress === 100 && (
                    <div className="text-sm text-green-600 font-medium bg-green-50 border border-green-200 rounded-lg p-3">
                      🎉 Redirecting to your lesson...
                    </div>
                  )}
                </div>
              ) : (
                // Error State - Much Improved
                <div className="space-y-6">
                  {/* Error Icon and Title */}
                  <div className="text-center">
                    <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
                      {errorType === 'network' ? (
                        <WifiOff className="w-10 h-10 text-red-600" />
                      ) : errorType === 'auth' ? (
                        <AlertCircle className="w-10 h-10 text-red-600" />
                      ) : (
                        <AlertCircle className="w-10 h-10 text-red-600" />
                      )}
                    </div>
                    
                    <h3 className="font-heading font-bold text-xl text-black mb-2">
                      Lesson Generation Failed
                    </h3>
                    
                    <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                      {generationError}
                    </div>
                  </div>
                  
                  {/* Specific Error Help */}
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <HelpCircle className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-gray-700">
                        <p className="font-medium mb-2">What you can try:</p>
                        {errorType === 'auth' && (
                          <ul className="space-y-1 text-xs">
                            <li>• Make sure you're logged in to your account</li>
                            <li>• Refresh the page and try again</li>
                            <li>• Check if your session has expired</li>
                          </ul>
                        )}
                        {errorType === 'network' && (
                          <ul className="space-y-1 text-xs">
                            <li>• Check your internet connection</li>
                            <li>• Try refreshing the page</li>
                            <li>• Wait a moment and retry</li>
                          </ul>
                        )}
                        {errorType === 'server' && (
                          <ul className="space-y-1 text-xs">
                            <li>• The server is temporarily unavailable</li>
                            <li>• Try again in a few minutes</li>
                            <li>• Contact support if the issue persists</li>
                          </ul>
                        )}
                        {!errorType || errorType === 'content' && (
                          <ul className="space-y-1 text-xs">
                            <li>• Check your content meets minimum requirements</li>
                            <li>• Ensure your content is at least 100 characters</li>
                            <li>• Try with different content or title</li>
                          </ul>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    {retryCount < 2 && (
                      <ControlButton
                        variant="primary"
                        onClick={handleRetry}
                        className="flex-1"
                        disabled={isGenerating}
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Try Again {retryCount > 0 && `(${retryCount}/2)`}
                      </ControlButton>
                    )}
                    
                    <ControlButton
                      variant="secondary"
                      onClick={handleReset}
                      className="flex-1"
                    >
                      Close
                    </ControlButton>
                  </div>
                  
                  {retryCount >= 2 && (
                    <div className="text-center">
                      <p className="text-xs text-gray-500 mb-3">
                        Maximum retries reached. Try these alternatives:
                      </p>
                      <div className="flex gap-2">
                        <ControlButton
                          variant="secondary"
                          onClick={() => navigate('/lessons')}
                          className="text-xs"
                        >
                          View Lessons
                        </ControlButton>
                        <ControlButton
                          variant="secondary"
                          onClick={() => window.location.reload()}
                          className="text-xs"
                        >
                          Refresh Page
                        </ControlButton>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
  );
}
