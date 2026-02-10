import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Panel } from '@/components/Panel';
import { ControlButton } from '@/components/ControlButton';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  Home,
  Trophy,
  BookOpen,
} from 'lucide-react';
import { apiService, Lesson, SessionState, AuthoredState } from '@/lib/api';

export default function LessonPlayer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);

  useEffect(() => {
    if (id) {
      initializeLesson(parseInt(id));
    }
  }, [id]);

  const initializeLesson = async (lessonId: number) => {
    try {
      setLoading(true);
      
      // Load lesson data
      const lessonData = await apiService.getLesson(lessonId);
      setLesson(lessonData);
      
      // Create new session
      const sessionResponse = await apiService.createSession(lessonId);
      setSessionId(sessionResponse.session_id);
      setSessionState(sessionResponse.session_state);
      
    } catch (error) {
      console.error('Failed to initialize lesson:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async () => {
    if (!sessionId || selectedAnswer === null || !sessionState?.state) return;

    try {
      setSubmitting(true);
      const result = await apiService.submitAnswer(sessionId, { answer: selectedAnswer });
      setSessionState(result.result);
      setSelectedAnswer(null);
    } catch (error) {
      console.error('Failed to submit answer:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = async () => {
    if (!sessionId) return;

    try {
      setSubmitting(true);
      const result = await apiService.submitNext(sessionId);
      setSessionState(result.result);
    } catch (error) {
      console.error('Failed to advance:', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-black border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-muted">Loading lesson...</p>
          </div>
        </div>
    );
  }

  if (sessionState?.completed) {
    return (
        <div className="max-w-2xl mx-auto">
          <Panel className="text-center">
            <div className="space-y-6">
              <Trophy className="w-16 h-16 text-accent-orange mx-auto" />
              <h1 className="font-heading font-bold text-3xl tracking-tight text-black">
                Lesson Complete!
              </h1>
              <p className="text-muted">
                Congratulations! You've successfully completed this lesson.
              </p>
              <div className="flex justify-center gap-4">
                <ControlButton
                  variant="secondary"
                  onClick={() => navigate('/lessons')}
                  className="flex items-center gap-2"
                >
                  <BookOpen className="w-4 h-4" />
                  More Lessons
                </ControlButton>
                <ControlButton
                  variant="primary"
                  onClick={() => navigate('/dashboard')}
                  className="flex items-center gap-2"
                >
                  <Home className="w-4 h-4" />
                  Dashboard
                </ControlButton>
              </div>
            </div>
          </Panel>
        </div>
    );
  }

  const currentState = sessionState?.state;
  const isQuestion = currentState?.type === 'question';
  const isContent = currentState?.type === 'content';

  return (
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <ControlButton
              variant="secondary"
              onClick={() => navigate('/lessons')}
              className="p-2"
            >
              <ArrowLeft className="w-5 h-5" />
            </ControlButton>
            <div>
              <h1 className="font-heading font-bold text-2xl tracking-tight text-black">
                {lesson?.title || 'Untitled Lesson'}
              </h1>
              <p className="text-muted mt-1">
                Progress: {Math.round((sessionState?.progress || 0) * 100)}%
              </p>
            </div>
          </div>
          
          <ControlButton
            variant="secondary"
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2"
          >
            <Home className="w-4 h-4" />
            Dashboard
          </ControlButton>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-black/10 h-2 rounded-full overflow-hidden">
          <div 
            className="h-full bg-accent-orange transition-all duration-base ease-standard"
            style={{ width: `${Math.round((sessionState?.progress || 0) * 100)}%` }}
          />
        </div>

        {/* Content */}
        <Panel>
          <div className="space-y-6">
            {isContent && (
              <div className="prose prose-black max-w-none">
                <h2 className="font-heading font-semibold text-xl tracking-tight text-black">
                  Content
                </h2>
                <div className="text-black leading-relaxed">
                  {currentState?.text || 'No content available.'}
                </div>
              </div>
            )}

            {isQuestion && (
              <div className="border-2 border-black rounded-md p-4 bg-accent-yellow/10">
                <p className="font-medium text-black mb-4">
                  {currentState?.prompt}
                </p>
                
                {currentState?.question_format === 'mcq' && currentState?.options && (
                  <div className="space-y-2">
                    {currentState.options.map((option: string, index: number) => (
                      <button
                        key={index}
                        onClick={() => setSelectedAnswer(index)}
                        disabled={submitting}
                        className={
                          "w-full text-left border-2 rounded-md px-4 py-2 transition-all duration-base ease-standard btn-active " +
                          (selectedAnswer === index
                            ? 'border-black bg-accent-yellow'
                            : 'border-black hover:bg-accent-yellow')
                        }
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                )}

                {currentState?.explanation && (
                  <div className="mt-4 text-muted text-sm">
                    {currentState.explanation}
                  </div>
                )}
              </div>
            )}
          </div>
        </Panel>

        {/* Navigation */}
        <div className="flex justify-between">
          <div className="w-24" /> {/* Spacer for centering */}
          
          {isContent && (
            <ControlButton
              variant="primary"
              onClick={handleNext}
              disabled={submitting}
              loading={submitting}
              className="flex items-center gap-2"
            >
              Next
              <ArrowRight className="w-4 h-4" />
            </ControlButton>
          )}
          
          {isQuestion && (
            <ControlButton
              variant="primary"
              onClick={handleAnswer}
              disabled={selectedAnswer === null || submitting}
              loading={submitting}
              className="flex items-center gap-2"
            >
              Submit Answer
              <ArrowRight className="w-4 h-4" />
            </ControlButton>
          )}
        </div>
      </div>
  );
}
