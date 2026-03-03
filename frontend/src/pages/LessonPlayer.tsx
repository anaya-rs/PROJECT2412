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
  const [selectedAnswer, setSelectedAnswer] = useState<number | number[] | null>(null);
  const [showWrongAnswer, setShowWrongAnswer] = useState(false);

  useEffect(() => {
    if (id) {
      // Set auth token for testing
      const testToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzcyNjI2MDY4fQ.Glpo7NyyDrtJCVeiInYqtgdcr9C2HClES7Z4oK6EgKs';
      if (!localStorage.getItem('authToken')) {
        localStorage.setItem('authToken', testToken);
      }
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
      
      // Submit answer with proper payload format
      const result = await apiService.submitAnswer(sessionId, { 
        type: 'answer', 
        payload: { selected_option: selectedAnswer } 
      });
      
      console.log('Answer submitted, result:', result);
      
      // Handle different response statuses
      if (result.result.status === 'retry') {
        // Wrong answer, show feedback
        setShowWrongAnswer(true);
        setSessionState(result.result);
      } else if (result.result.status === 'reveal_answer') {
        // No attempts left, reveal answer
        setShowWrongAnswer(true);
        setSessionState(result.result);
      } else if (result.result.status === 'correct') {
        // Correct answer, stay in question state with correct status
        setSessionState(result.result);
        setShowWrongAnswer(false);
      } else {
        // Content state or other, advance
        setSessionState(result.result);
        setSelectedAnswer(null);
        setShowWrongAnswer(false);
      }
      
    } catch (error) {
      console.error('Failed to submit answer:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleOptionSelect = (index: number) => {
    const currentState = sessionState?.state;
    
    if (currentState?.question_type === 'multiple_choice') {
      // For multiple choice, toggle selection
      const currentAnswers = Array.isArray(selectedAnswer) ? selectedAnswer : [];
      const newAnswers = currentAnswers.includes(index)
        ? currentAnswers.filter(i => i !== index)
        : [...currentAnswers, index];
      setSelectedAnswer(newAnswers);
    } else {
      // For single choice, replace selection
      setSelectedAnswer(index);
    }
    
    setShowWrongAnswer(false);
  };

  const handleNext = async () => {
    if (!sessionId) return;

    try {
      setSubmitting(true);
      console.log('🔍 [DEBUG] Submitting next action for session:', sessionId);
      const result = await apiService.submitNext(sessionId);
      console.log('🔍 [DEBUG] API response:', result);
      console.log('🔍 [DEBUG] Result data:', result.result);
      setSessionState(result.result);
    } catch (error) {
      console.error('❌ [DEBUG] Failed to advance:', error);
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
  console.log('🔍 [DEBUG] Current state:', currentState);
  console.log('🔍 [DEBUG] Session state:', sessionState);
  
  const isQuestion = currentState?.type === 'question';
  const isContent = currentState?.type === 'content';
  const isEndNotes = currentState?.type === 'end_notes';
  
  // Defensive check for undefined state
  if (sessionState && !currentState && !sessionState.completed) {
    console.error('❌ [DEBUG] Session state exists but current state is undefined!');
    return (
      <div className="p-6">
        <Panel className="border-accent-orange">
          <div className="text-center py-8">
            <h2 className="font-heading font-semibold text-lg text-black mb-2">
              Debug: State Error
            </h2>
            <p className="text-sm text-muted mb-4">
              Session state exists but current state is undefined
            </p>
            <pre className="text-xs bg-gray-100 p-2 rounded">
              {JSON.stringify(sessionState, null, 2)}
            </pre>
          </div>
        </Panel>
      </div>
    );
  }

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
                
                {currentState?.question_type && currentState?.options && (
                  <div className="space-y-2">
                    {currentState.question_type === 'multiple_choice' && (
                      <p className="text-sm text-muted mb-2">
                        Select all that apply:
                      </p>
                    )}
                    {currentState.options.map((option: string, index: number) => {
                      const isSelected = Array.isArray(selectedAnswer) ? selectedAnswer.includes(index) : selectedAnswer === index;
                      
                      // Determine option styling based on status ONLY (no derived validation)
                      let optionClass = "w-full text-left border-2 rounded-md px-4 py-2 transition-all duration-base ease-standard btn-active ";
                      
                      if (sessionState?.status === 'correct') {
                        // Correct answer state - highlight selected option green
                        optionClass += isSelected ? 'border-green-500 bg-green-50' : 'border-black hover:bg-accent-yellow';
                      } else if (sessionState?.status === 'retry') {
                        // Retry state - highlight selected wrong option red with shake
                        optionClass += isSelected ? 'border-red-500 bg-red-50 animate-shake' : 'border-black hover:bg-accent-yellow';
                      } else if (sessionState?.status === 'reveal_answer') {
                        // Reveal answer state - highlight correct green, selected wrong red
                        // Use backend response for correct answer identification
                        const isCorrectAnswer = sessionState?.correct_answer === index || 
                                               (Array.isArray(sessionState?.correct_answer) && sessionState.correct_answer.includes(index));
                        if (isCorrectAnswer) {
                          optionClass += 'border-green-500 bg-green-50';
                        } else if (isSelected) {
                          optionClass += 'border-red-500 bg-red-50';
                        } else {
                          optionClass += 'border-black hover:bg-accent-yellow';
                        }
                      } else {
                        // Default state - no validation feedback
                        optionClass += isSelected ? 'border-black bg-accent-yellow' : 'border-black hover:bg-accent-yellow';
                      }
                      
                      return (
                        <button
                          key={index}
                          onClick={() => handleOptionSelect(index)}
                          disabled={submitting}
                          className={optionClass}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-4 h-4 border-2 rounded flex items-center justify-center ${
                              sessionState?.status === 'correct' && isSelected ? 'border-green-500' :
                              sessionState?.status === 'retry' && isSelected ? 'border-red-500' :
                              sessionState?.status === 'reveal_answer' && sessionState?.correct_answer === index ? 'border-green-500' :
                              sessionState?.status === 'reveal_answer' && isSelected ? 'border-red-500' :
                              'border-black'
                            }`}>
                              {isSelected && (
                                <div className={`w-2 h-2 rounded-full ${
                                  sessionState?.status === 'correct' && isSelected ? 'bg-green-500' :
                                  sessionState?.status === 'retry' ? 'bg-red-500' :
                                  sessionState?.status === 'reveal_answer' && sessionState?.correct_answer === index ? 'bg-green-500' :
                                  sessionState?.status === 'reveal_answer' && isSelected ? 'bg-red-500' :
                                  'bg-black'
                                }`} />
                              )}
                              {sessionState?.status === 'reveal_answer' && sessionState?.correct_answer === index && !isSelected && (
                                <div className="w-2 h-2 bg-green-500 rounded-full" />
                              )}
                            </div>
                            {option}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}

                {showWrongAnswer && sessionState?.status === 'retry' && (
                  <div className="mt-4 p-3 border-2 border-red-500 bg-red-50 rounded-md">
                    <p className="text-red-700 font-medium text-sm">
                      Oops! Wrong answer. Try again!
                    </p>
                  </div>
                )}

                {sessionState?.status === 'correct' && (
                  <div className="mt-4 p-3 border-2 border-green-500 bg-green-50 rounded-md">
                    <p className="text-green-700 font-medium text-sm">
                      Correct! Well done!
                    </p>
                  </div>
                )}

                {sessionState?.status === 'reveal_answer' && (
                  <div className="mt-4 p-3 border-2 border-green-500 bg-green-50 rounded-md">
                    <p className="text-green-700 font-medium text-sm">
                      The correct answer is: {currentState.options?.[sessionState.correct_answer as number] || sessionState.correct_answer}
                    </p>
                  </div>
                )}

                {currentState?.explanation && sessionState?.explanation_visible && (
                  <div className="mt-4 text-muted text-sm">
                    {currentState.explanation}
                  </div>
                )}
              </div>
            )}

            {isEndNotes && (
              <div className="text-center space-y-6">
                <div className="prose prose-black max-w-none">
                  <h2 className="font-heading font-semibold text-xl tracking-tight text-black">
                    Lesson Summary
                  </h2>
                  <div className="text-black leading-relaxed">
                    {currentState?.summary || 'Great job completing this lesson!'}
                  </div>
                  
                  {currentState?.key_takeaways && currentState.key_takeaways.length > 0 && (
                    <div className="mt-6">
                      <h3 className="font-heading font-semibold text-lg text-black mb-3">
                        Key Takeaways
                      </h3>
                      <ul className="space-y-2 text-left max-w-md mx-auto">
                        {currentState.key_takeaways.map((takeaway: string, index: number) => (
                          <li key={index} className="flex items-start gap-2">
                            <span className="text-accent-orange font-bold">•</span>
                            <span className="text-black">{takeaway}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                
                <div className="flex justify-center gap-4 pt-6">
                  <ControlButton
                    variant="primary"
                    onClick={() => navigate('/lessons')}
                    className="flex items-center gap-2"
                  >
                    <BookOpen className="w-4 h-4" />
                    All Done - Back to Lessons
                  </ControlButton>
                </div>
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
            <>
              {sessionState?.status === 'correct' || sessionState?.status === 'reveal_answer' ? (
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
              ) : (
                <ControlButton
                  variant="primary"
                  onClick={handleAnswer}
                  disabled={selectedAnswer === null || (Array.isArray(selectedAnswer) && selectedAnswer.length === 0) || submitting}
                  loading={submitting}
                  className="flex items-center gap-2"
                >
                  Submit Answer
                  <ArrowRight className="w-4 h-4" />
                </ControlButton>
              )}
            </>
          )}
          
          {isEndNotes && (
            <div className="w-24" />
          )}
        </div>
      </div>
  );
}
