import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Panel } from '@/components/Panel';
import { ControlButton } from '@/components/ControlButton';
import { apiService, AiJob } from '@/lib/api';
import {
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  BookOpen,
  ArrowLeft,
} from 'lucide-react';

export default function LessonGenerating() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('jobId');
  const [job, setJob] = useState<AiJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      navigate('/create');
      return;
    }

    let intervalId: number | undefined;
    let cancelled = false;

    const poll = async () => {
      try {
        const jobData = await apiService.getAiLessonJob(jobId);
        if (cancelled) return;
        setJob(jobData);
        setError(null);
        
        if (jobData.status === 'completed') {
          if (intervalId) {
            window.clearInterval(intervalId);
          }
          // Redirect to lessons page after 2 seconds
          setTimeout(() => {
            navigate('/lessons');
          }, 2000);
        } else if (jobData.status === 'failed') {
          if (intervalId) {
            window.clearInterval(intervalId);
          }
        }
      } catch (err) {
        if (cancelled) return;
        setError('Failed to fetch job status');
        if (intervalId) {
          window.clearInterval(intervalId);
        }
      }
    };

    poll();
    intervalId = window.setInterval(poll, 2000);

    return () => {
      cancelled = true;
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [jobId, navigate]);

  const getStatusIcon = () => {
    if (!job) return <Loader2 className="w-8 h-8 animate-spin" />;
    
    switch (job.status) {
      case 'completed':
        return <CheckCircle className="w-8 h-8 text-green-600" />;
      case 'failed':
        return <XCircle className="w-8 h-8 text-red-600" />;
      case 'running':
        return <Loader2 className="w-8 h-8 animate-spin text-blue-600" />;
      default:
        return <Clock className="w-8 h-8 text-gray-600" />;
    }
  };

  const getStatusText = () => {
    if (!job) return 'Initializing...';
    
    switch (job.status) {
      case 'completed':
        return 'Lesson generation completed!';
      case 'failed':
        return 'Generation failed';
      case 'running':
        return 'Generating your lesson...';
      case 'queued':
        return 'Queued for processing...';
      default:
        return 'Processing...';
    }
  };

  const getProgressColor = () => {
    if (!job) return 'bg-gray-300';
    
    switch (job.status) {
      case 'completed':
        return 'bg-green-600';
      case 'failed':
        return 'bg-red-600';
      case 'running':
        return 'bg-blue-600';
      default:
        return 'bg-gray-300';
    }
  };

  const getBorderColor = () => {
    if (!job) return 'border-black';
    
    switch (job.status) {
      case 'completed':
        return 'border-accent-green';
      case 'failed':
        return 'border-accent-orange';
      case 'running':
        return 'border-accent-blue';
      default:
        return 'border-black';
    }
  };

  return (
    <div className="min-h-screen bg-paper p-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <ControlButton
            variant="secondary"
            onClick={() => navigate('/create')}
            className="px-3 py-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Creator
          </ControlButton>
          <h1 className="font-heading font-bold text-3xl tracking-tight text-black">
            Generating Lesson
          </h1>
        </div>

        {/* Main Status Panel */}
        <Panel className={`mb-6 ${getBorderColor()}`}>
          <div className="text-center py-12">
            <div className="flex justify-center mb-6">
              {getStatusIcon()}
            </div>
            
            <h2 className="font-heading font-semibold text-2xl text-black mb-2">
              {getStatusText()}
            </h2>
            
            {job?.inputTitle && (
              <p className="text-lg text-muted mb-4">
                "{job.inputTitle}"
              </p>
            )}
            
            {job?.message && (
              <p className="text-sm text-muted mb-6">
                {job.message}
              </p>
            )}

            {/* Progress Bar */}
            <div className="w-full max-w-md mx-auto">
              <div className="w-full bg-black/10 h-3 rounded-full overflow-hidden mb-2">
                <div
                  className={`h-full ${getProgressColor()} transition-all duration-500 ease-out`}
                  style={{ width: `${Math.max(0, Math.min(100, job?.progress || 0))}%` }}
                />
              </div>
              <div className="text-sm font-mono text-muted">
                {job?.progress || 0}% Complete
              </div>
            </div>
          </div>
        </Panel>

        {/* Additional Info */}
        {job && (
          <Panel>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium text-black mb-1">Job ID</div>
                <div className="font-mono text-muted truncate">{job.id}</div>
              </div>
              <div>
                <div className="font-medium text-black mb-1">Status</div>
                <div className="font-mono text-muted capitalize">{job.status}</div>
              </div>
              {job.duration && (
                <div>
                  <div className="font-medium text-black mb-1">Duration</div>
                  <div className="font-mono text-muted">{job.duration} minutes</div>
                </div>
              )}
              {job.difficulty && (
                <div>
                  <div className="font-medium text-black mb-1">Difficulty</div>
                  <div className="font-mono text-muted capitalize">{job.difficulty}</div>
                </div>
              )}
            </div>
          </Panel>
        )}

        {/* Error State */}
        {error && (
          <Panel className="border-accent-orange">
            <div className="text-center py-6">
              <XCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
              <h3 className="font-heading font-semibold text-lg text-black mb-2">
                Something went wrong
              </h3>
              <p className="text-sm text-muted mb-4">
                {error}
              </p>
              <div className="flex gap-2 justify-center">
                <ControlButton
                  variant="secondary"
                  onClick={() => window.location.reload()}
                >
                  Try Again
                </ControlButton>
                <ControlButton
                  variant="primary"
                  onClick={() => navigate('/create')}
                >
                  Create New Lesson
                </ControlButton>
              </div>
            </div>
          </Panel>
        )}

        {/* Completed State */}
        {job?.status === 'completed' && (
          <Panel className="border-accent-green">
            <div className="text-center py-6">
              <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
              <h3 className="font-heading font-semibold text-lg text-black mb-2">
                Ready to Learn!
              </h3>
              <p className="text-sm text-muted mb-4">
                Your lesson has been generated and is now available.
              </p>
              <div className="flex gap-2 justify-center">
                <ControlButton
                  variant="primary"
                  onClick={() => navigate('/lessons')}
                >
                  <BookOpen className="w-4 h-4 mr-2" />
                  View All Lessons
                </ControlButton>
                {job.lessonId && (
                  <ControlButton
                    variant="secondary"
                    onClick={() => navigate(`/lesson/${job.lessonId}`)}
                  >
                    Start Lesson
                  </ControlButton>
                )}
              </div>
            </div>
          </Panel>
        )}

        {/* Failed State */}
        {job?.status === 'failed' && (
          <Panel className="border-accent-orange">
            <div className="text-center py-6">
              <XCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
              <h3 className="font-heading font-semibold text-lg text-black mb-2">
                Generation Failed
              </h3>
              <p className="text-sm text-muted mb-4">
                {job.message || 'An error occurred while generating your lesson.'}
              </p>
              <div className="flex gap-2 justify-center">
                <ControlButton
                  variant="secondary"
                  onClick={() => navigate('/create')}
                >
                  Try Again
                </ControlButton>
                <ControlButton
                  variant="primary"
                  onClick={() => navigate('/lessons')}
                >
                  <BookOpen className="w-4 h-4 mr-2" />
                  Browse Lessons
                </ControlButton>
              </div>
            </div>
          </Panel>
        )}
      </div>
    </div>
  );
}
