import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Panel } from '@/components/Panel';
import { ControlButton } from '@/components/ControlButton';
import { TextInput } from '@/components/TextInput';
import {
  ArrowLeft,
  Upload,
  Sparkles,
  Clock,
  HelpCircle,
  BookOpen,
} from 'lucide-react';
import { apiService } from '@/lib/api';

export default function LessonCreator() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [content, setContent] = useState('');
  const [duration, setDuration] = useState(30);
  const [difficulty, setDifficulty] = useState('beginner');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

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
    try {
      const job = await apiService.startAiLessonJob({
        text: content,
        title,
        description,
        fileName: uploadedFileName || undefined,
        difficulty,
        duration,
      });

      localStorage.setItem('activeAiLessonJobId', job.jobId);
      localStorage.setItem('activeAiLessonJobTimestamp', Date.now().toString());
      window.dispatchEvent(new Event('ai-job-updated'));
      
      // Redirect to generating page
      navigate(`/generating?jobId=${job.jobId}`);
    } catch (error) {
      console.error('Failed to generate lesson:', error);
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
      </div>
  );
}
