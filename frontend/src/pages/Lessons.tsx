import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Panel } from '@/components/Panel';
import { ControlButton } from '@/components/ControlButton';
import { TextInput } from '@/components/TextInput';
import {
  Plus,
  Search,
  PlayCircle,
  Trash2,
  RefreshCw,
  Clock,
  HelpCircle,
  BookOpen,
  Filter,
} from 'lucide-react';
import { apiService, Lesson } from '@/lib/api';

function LessonCard({ lesson, onPlay, onDelete }: { 
  lesson: Lesson; 
  onPlay: () => void;
  onDelete: () => void;
}) {
  const metadata = lesson.metadata || {};
  const difficulty = metadata.difficulty || 'beginner';
  const duration = metadata.duration || 30;
  const computedQuestionCount = (() => {
    const nodes = lesson.nodes || {};
    if (Array.isArray(nodes)) {
      return nodes.filter((n: any) => n?.type === 'question').length;
    }
    if (typeof nodes === 'object') {
      return Object.values(nodes).filter((n: any) => (n as any)?.type === 'question').length;
    }
    return 0;
  })();

  const questionCount = metadata.questionCount ?? computedQuestionCount;
  const fileName = metadata.fileName;

  return (
    <Panel className="hover:border-accent-amber transition-all duration-base ease-standard btn-active">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex justify-between items-start">
          <h3 className="font-heading font-semibold text-lg tracking-tight text-black">
            {lesson.title}
          </h3>
          <div className="flex gap-2">
            <ControlButton 
              variant="primary"
              onClick={onPlay}
              className="px-3 py-1.5"
            >
              <PlayCircle className="w-4 h-4 mr-1" />
              Play
            </ControlButton>
            <ControlButton 
              variant="secondary"
              onClick={onDelete}
              className="px-3 py-1.5"
            >
              <Trash2 className="w-4 h-4" />
            </ControlButton>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-muted line-clamp-2">
          {lesson.description}
        </p>

        {fileName && (
          <div className="text-xs text-muted font-mono truncate">
            {fileName}
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center gap-6 text-xs font-mono text-muted">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {duration}min
          </div>
          <div className="flex items-center gap-1">
            <HelpCircle className="w-3 h-3" />
            {questionCount} questions
          </div>
          <div className="px-2 py-1 bg-accent-yellow text-black font-medium rounded">
            {difficulty}
          </div>
        </div>
      </div>
    </Panel>
  );
}

export default function Lessons() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');

  const fetchLessons = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedLessons = await apiService.getLessons();
      setLessons(fetchedLessons);
    } catch (err) {
      setError('Failed to load lessons');
      console.error('Error fetching lessons:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLessons();
  }, []);

  const filteredLessons = lessons.filter((lesson) => {
    const metadata = lesson.metadata || {};
    const matchesSearch = 
      lesson.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      lesson.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDifficulty = selectedDifficulty === 'all' || metadata.difficulty === selectedDifficulty;
    return matchesSearch && matchesDifficulty;
  });

  const handleDelete = async (id: number) => {
    try {
      await apiService.deleteLesson(id);
      setLessons(lessons.filter((l) => l.id !== id));
    } catch (err) {
      console.error('Error deleting lesson:', err);
      setError('Failed to delete lesson');
    }
  };

  const difficulties = ['all', 'beginner', 'intermediate', 'advanced'];

  return (
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="font-heading font-bold text-4xl tracking-tight text-black mb-2">
              All Lessons
            </h1>
            <p className="text-lg text-muted">
              Browse and manage your learning content
            </p>
          </div>
          <ControlButton 
            variant="primary"
            onClick={() => navigate('/create')}
            className="transform active:scale-95 transition-transform"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Lesson
          </ControlButton>
        </div>

        {/* Accent underline */}
        <div className="h-1 w-24 bg-accent-yellow rounded-full mb-8"></div>

        {/* Filters */}
        <Panel className="mb-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <TextInput
                placeholder="Search lessons..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="px-4 py-2 border-2 border-black bg-white text-sm rounded-md focus:outline-none focus:border-accent-orange"
              >
                {difficulties.map(diff => (
                  <option key={diff} value={diff}>
                    {diff.charAt(0).toUpperCase() + diff.slice(1)}
                  </option>
                ))}
              </select>
              <ControlButton 
                variant="secondary"
                onClick={fetchLessons}
                className="transform active:scale-95 transition-transform"
              >
                <RefreshCw className="w-4 h-4" />
              </ControlButton>
            </div>
          </div>
        </Panel>

        {/* Error Message */}
        {error && (
          <Panel className="mb-6 border-accent-orange">
            <div className="text-sm text-black font-medium">
              Error: {error}
            </div>
          </Panel>
        )}

        {/* Lessons Grid */}
        {loading ? (
          <Panel>
            <div className="text-center py-12">
              <div className="text-sm text-muted">Loading lessons...</div>
            </div>
          </Panel>
        ) : filteredLessons.length === 0 ? (
          <Panel>
            <div className="text-center py-12">
              <BookOpen className="w-12 h-12 text-muted mx-auto mb-4" />
              <div className="text-lg font-heading font-medium text-black mb-2">
                {searchQuery || selectedDifficulty !== 'all' ? 'No lessons found' : 'No lessons yet'}
              </div>
              <div className="text-sm text-muted mb-4">
                {searchQuery || selectedDifficulty !== 'all' 
                  ? 'Try adjusting your filters'
                  : 'Create your first lesson to get started'
                }
              </div>
              <ControlButton 
                variant="primary"
                onClick={() => navigate('/create')}
                className="transform active:scale-95 transition-transform"
              >
                Create Your First Lesson
              </ControlButton>
            </div>
          </Panel>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredLessons.map((lesson) => (
              <LessonCard
                key={lesson.id}
                lesson={lesson}
                onPlay={() => navigate(`/lesson/${lesson.id}`)}
                onDelete={() => handleDelete(lesson.id)}
              />
            ))}
          </div>
        )}
      </div>
  );
}
