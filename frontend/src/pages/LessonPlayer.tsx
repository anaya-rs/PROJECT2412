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
import { apiService } from '@/lib/api';

export default function LessonPlayer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [lesson, setLesson] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [currentNodeId, setCurrentNodeId] = useState<string>('start');
  const [history, setHistory] = useState<string[]>([]);
  const [completed, setCompleted] = useState(false);
  const [selectedOptionIndex, setSelectedOptionIndex] = useState<number | null>(null);
  const [selectedOptionByNodeId, setSelectedOptionByNodeId] = useState<Record<string, number>>({});
  const [answeredNodeIds, setAnsweredNodeIds] = useState<Record<string, boolean>>({});
  const [mistakes, setMistakes] = useState<
    Array<{ nodeId: string; question: string; selected: string; correct: string }>
  >([]);

  useEffect(() => {
    if (id) {
      loadLesson(id);
    }
  }, [id]);

  useEffect(() => {
    const existing = selectedOptionByNodeId[currentNodeId];
    setSelectedOptionIndex(typeof existing === 'number' ? existing : null);
  }, [currentNodeId]);

  const loadLesson = async (lessonId: string) => {
    try {
      const lessonData = await apiService.getLesson(parseInt(lessonId));
      setLesson(lessonData);
      const startId = lessonData?.startNodeId || 'start';
      setCurrentNodeId(startId);
      setHistory([startId]);
    } catch (error) {
      console.error('Failed to load lesson:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (!lesson) return;

    const nodes = lesson.nodes || {};
    const current = nodes[currentNodeId];
    if (!current) {
      setCompleted(true);
      return;
    }

    const nextId = current?.transitions?.next;
    if (!nextId || nextId === 'end') {
      setCompleted(true);
      return;
    }

    setCurrentNodeId(nextId);
    setHistory((prev) => [...prev, nextId]);
  };

  const handleSelectOption = (index: number) => {
    if (!lesson) return;
    const current = lesson?.nodes?.[currentNodeId];
    if (!current || current.type !== 'question') return;
    if (answeredNodeIds[currentNodeId]) return;

    const options: string[] = Array.isArray(current.options) ? current.options : [];
    const correctIndex: number | null =
      typeof current.correctIndex === 'number' ? current.correctIndex : null;
    const correct =
      correctIndex !== null && options[correctIndex] !== undefined ? options[correctIndex] : '';
    const selected = options[index] ?? '';

    setSelectedOptionIndex(index);
    setSelectedOptionByNodeId((prev) => ({ ...prev, [currentNodeId]: index }));
    setAnsweredNodeIds((prev) => ({ ...prev, [currentNodeId]: true }));

    if (correctIndex !== null && index !== correctIndex) {
      setMistakes((prev) => {
        if (prev.some((m) => m.nodeId === currentNodeId)) return prev;
        return [
          ...prev,
          {
            nodeId: currentNodeId,
            question: current.question ?? 'Question',
            selected,
            correct,
          },
        ];
      });
    }
  };

  const handlePrevious = () => {
    if (history.length <= 1) return;
    const newHistory = history.slice(0, -1);
    const prevId = newHistory[newHistory.length - 1];
    setHistory(newHistory);
    setCurrentNodeId(prevId);
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

  if (completed) {
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

  const currentNode = lesson?.nodes?.[currentNodeId];
  const isQuestion = currentNode?.type === 'question';
  const isReview = currentNode?.type === 'review';
  const isAnswered = !!answeredNodeIds[currentNodeId];
  const correctIndex: number | null =
    isQuestion && typeof currentNode?.correctIndex === 'number' ? currentNode.correctIndex : null;

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
                Step {history.length}
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
            style={{ width: `${Math.min(100, Math.max(5, history.length * 20))}%` }}
          />
        </div>

        {/* Content */}
        <Panel>
          <div className="space-y-6">
            <div className="prose prose-black max-w-none">
              <h2 className="font-heading font-semibold text-xl tracking-tight text-black">
                {lesson?.nodes?.[currentNodeId]?.title || 'Content'}
              </h2>
              <div className="text-black leading-relaxed">
                {lesson?.nodes?.[currentNodeId]?.content || 'No content available.'}
              </div>
            </div>

            {/* Interactive Elements */}
            {isQuestion && (
              <div className="border-2 border-black rounded-md p-4 bg-accent-yellow/10">
                <p className="font-medium text-black mb-4">
                  {lesson.nodes[currentNodeId].question}
                </p>
                <div className="space-y-2">
                  {lesson.nodes[currentNodeId].options?.map((option: string, index: number) => (
                    <button
                      key={index}
                      onClick={() => handleSelectOption(index)}
                      disabled={isAnswered}
                      className={
                        "w-full text-left border-2 rounded-md px-4 py-2 transition-all duration-base ease-standard btn-active " +
                        (isAnswered
                          ? index === correctIndex
                            ? 'border-black bg-accent-yellow'
                            : index === selectedOptionIndex
                              ? 'border-black bg-black/5'
                              : 'border-black/40 bg-white'
                          : 'border-black hover:bg-accent-yellow')
                      }
                    >
                      {option}
                    </button>
                  ))}
                </div>

                {isAnswered && (
                  <div className="mt-4 text-black">
                    {correctIndex !== null && selectedOptionIndex === correctIndex ? (
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        <span className="font-medium">Correct</span>
                      </div>
                    ) : (
                      <div className="font-medium">Incorrect</div>
                    )}
                    {lesson.nodes[currentNodeId].explanation && (
                      <div className="text-muted mt-2">{lesson.nodes[currentNodeId].explanation}</div>
                    )}
                  </div>
                )}
              </div>
            )}

            {isReview && (
              <div className="border-2 border-black rounded-md p-4 bg-white">
                <div className="space-y-6">
                  {mistakes.length > 0 && (
                    <div>
                      <h3 className="font-heading font-semibold text-lg tracking-tight text-black">
                        Where you made mistakes
                      </h3>
                      <div className="mt-3 space-y-3">
                        {mistakes.map((m) => (
                          <div key={m.nodeId} className="border-2 border-black/20 rounded-md p-3">
                            <div className="font-medium text-black">{m.question}</div>
                            <div className="text-muted mt-1">
                              Your answer: <span className="text-black">{m.selected || '—'}</span>
                            </div>
                            <div className="text-muted">
                              Correct answer: <span className="text-black">{m.correct || '—'}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {Array.isArray(currentNode?.quickNotes) && currentNode.quickNotes.length > 0 && (
                    <div>
                      <h3 className="font-heading font-semibold text-lg tracking-tight text-black">Quick notes</h3>
                      <ul className="mt-2 list-disc pl-6 text-black">
                        {currentNode.quickNotes.map((n: string, i: number) => (
                          <li key={i}>{n}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {Array.isArray(currentNode?.dontForget) && currentNode.dontForget.length > 0 && (
                    <div>
                      <h3 className="font-heading font-semibold text-lg tracking-tight text-black">DON'T FORGET</h3>
                      <ul className="mt-2 list-disc pl-6 text-black">
                        {currentNode.dontForget.map((n: string, i: number) => (
                          <li key={i}>{n}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {Array.isArray(currentNode?.commonMistakes) && currentNode.commonMistakes.length > 0 && (
                    <div>
                      <h3 className="font-heading font-semibold text-lg tracking-tight text-black">
                        Common mistakes
                      </h3>
                      <ul className="mt-2 list-disc pl-6 text-black">
                        {currentNode.commonMistakes.map((n: string, i: number) => (
                          <li key={i}>{n}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </Panel>

        {/* Navigation */}
        <div className="flex justify-between">
          <ControlButton
            variant="secondary"
            onClick={handlePrevious}
            disabled={history.length <= 1}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Previous
          </ControlButton>
          
          <ControlButton
            variant="primary"
            onClick={handleNext}
            disabled={isQuestion && !isAnswered}
            className="flex items-center gap-2"
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </ControlButton>
        </div>
      </div>
  );
}
