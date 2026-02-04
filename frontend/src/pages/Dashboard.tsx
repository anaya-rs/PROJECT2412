import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { apiService, Lesson } from '@/lib/api';
import { Panel } from '@/components/Panel';
import { ControlButton } from '@/components/ControlButton';
import {
  Plus,
  RefreshCw,
  Clock,
  BookOpen,
  Trophy,
  Target,
  TrendingUp,
  PlayCircle,
  Calendar,
  Award,
  BarChart3,
} from 'lucide-react';

function StatCard({ 
  title, 
  value, 
  icon: Icon, 
  trend, 
  color = "accent-yellow" 
}: {
  title: string;
  value: string | number;
  icon: any;
  trend?: string;
  color?: string;
}) {
  return (
    <Panel className="hover:border-accent-amber transition-all duration-base ease-standard">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm text-muted font-medium">{title}</p>
          <p className="font-heading font-bold text-2xl tracking-tight text-black">{value}</p>
          {trend && (
            <div className="flex items-center gap-1 text-xs text-muted">
              <TrendingUp className="w-3 h-3" />
              {trend}
            </div>
          )}
        </div>
        <div className={`p-3 bg-${color} rounded-lg`}>
          <Icon className="w-6 h-6 text-black" />
        </div>
      </div>
    </Panel>
  );
}

function RecentActivityCard({ lesson, onResume }: { 
  lesson: Lesson; 
  onResume: () => void;
}) {
  const metadata = lesson.metadata || {};
  const difficulty = metadata.difficulty || 'beginner';
  const duration = metadata.duration || 30;

  const getDifficultyColor = (diff: string) => {
    switch (diff) {
      case 'beginner': return 'bg-accent-yellow';
      case 'intermediate': return 'bg-accent-amber';
      case 'advanced': return 'bg-accent-orange';
      default: return 'bg-accent-yellow';
    }
  };

  return (
    <Panel className="hover:border-accent-amber transition-all duration-base ease-standard">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h4 className="font-heading font-semibold text-black tracking-tight">{lesson.title}</h4>
          <div className="flex items-center gap-4 mt-2 text-xs text-muted">
            <span className={`${getDifficultyColor(difficulty)} px-2 py-1 rounded text-black font-medium`}>
              {difficulty}
            </span>
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {duration}min
            </div>
          </div>
        </div>
        <ControlButton 
          variant="primary"
          onClick={onResume}
          className="px-3 py-1.5"
        >
          <PlayCircle className="w-4 h-4 mr-1" />
          Resume
        </ControlButton>
      </div>
    </Panel>
  );
}

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    setMounted(true);
    loadLessons();
  }, []);

  const loadLessons = async () => {
    try {
      setLoading(true);
      const fetchedLessons = await apiService.getLessons();
      setLessons(fetchedLessons);
    } catch (err) {
      console.error('Error fetching lessons:', err);
    } finally {
      setLoading(false);
    }
  };

  // Calculate stats
  const totalLessons = lessons.length;
  const completedLessons = 0; // TODO: Implement progress tracking
  const totalMinutes = lessons.reduce((acc, lesson) => {
    const metadata = lesson.metadata || {};
    return acc + (metadata.duration || 30);
  }, 0);
  const averageDifficulty = lessons.length > 0 
    ? lessons.reduce((acc, lesson) => {
        const metadata = lesson.metadata || {};
        const difficulty = metadata.difficulty || 'beginner';
        const difficultyScore = difficulty === 'beginner' ? 1 : difficulty === 'intermediate' ? 2 : 3;
        return acc + difficultyScore;
      }, 0) / lessons.length
    : 0;

  const recentLessons = lessons.slice(0, 3);

  return (
    <div className="p-6 space-y-6">
      <div className={`${mounted ? 'page-enter' : ''}`}>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="font-heading font-bold text-4xl tracking-tight text-black mb-2">
              Welcome back, {user?.username}!
            </h1>
            <p className="text-lg text-muted">
              Track your learning progress and achievements
            </p>
          </div>
          <div className="flex gap-3">
            <ControlButton
              variant="secondary"
              onClick={loadLessons}
              className="flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </ControlButton>
            <ControlButton
              variant="primary"
              onClick={() => navigate('/create')}
              className="flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Lesson
            </ControlButton>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className={`${mounted ? 'section-enter' : ''} grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6`}>
        <StatCard
          title="Total Lessons"
          value={totalLessons}
          icon={BookOpen}
          trend={totalLessons > 0 ? "+0 this week" : undefined}
          color="accent-yellow"
        />
        <StatCard
          title="Completed"
          value={completedLessons}
          icon={Trophy}
          trend="Keep going!"
          color="accent-green"
        />
        <StatCard
          title="Learning Time"
          value={`${totalMinutes}min`}
          icon={Clock}
          trend={totalMinutes > 60 ? "Great progress!" : undefined}
          color="accent-blue"
        />
        <StatCard
          title="Avg Difficulty"
          value={averageDifficulty > 0 ? averageDifficulty.toFixed(1) : "N/A"}
          icon={Target}
          trend={averageDifficulty > 1.5 ? "Challenging yourself" : undefined}
          color="accent-orange"
        />
      </div>

      {/* Learning Progress */}
      <div className={`${mounted ? 'section-enter' : ''}`}>
        <Panel>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="font-heading font-semibold text-xl tracking-tight text-black">
                Learning Progress
              </h2>
              <ControlButton
                variant="secondary"
                onClick={() => navigate('/lessons')}
                className="flex items-center gap-2"
              >
                <BookOpen className="w-4 h-4" />
                View All
              </ControlButton>
            </div>
            
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted">Overall Progress</span>
                <span className="font-medium text-black">{completedLessons}/{totalLessons} lessons</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-accent-yellow h-3 rounded-full transition-all duration-base ease-standard"
                  style={{ width: `${totalLessons > 0 ? (completedLessons / totalLessons) * 100 : 0}%` }}
                ></div>
              </div>
            </div>

            {/* Achievement Badges */}
            <div className="flex gap-4">
              <div className="flex items-center gap-2 px-3 py-2 bg-accent-yellow rounded-lg">
                <Award className="w-4 h-4 text-black" />
                <span className="text-xs font-medium text-black">First Steps</span>
              </div>
              {totalLessons >= 5 && (
                <div className="flex items-center gap-2 px-3 py-2 bg-accent-amber rounded-lg">
                  <Trophy className="w-4 h-4 text-black" />
                  <span className="text-xs font-medium text-black">Lesson Creator</span>
                </div>
              )}
              {totalMinutes >= 60 && (
                <div className="flex items-center gap-2 px-3 py-2 bg-accent-orange rounded-lg">
                  <Clock className="w-4 h-4 text-black" />
                  <span className="text-xs font-medium text-black">Time Master</span>
                </div>
              )}
            </div>
          </div>
        </Panel>
      </div>

      {/* Recent Activity */}
      <div className={`${mounted ? 'section-enter' : ''}`}>
        <Panel>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="font-heading font-semibold text-xl tracking-tight text-black">
                Recent Lessons
              </h2>
              <ControlButton
                variant="secondary"
                onClick={() => navigate('/lessons')}
                className="flex items-center gap-2"
              >
                <BarChart3 className="w-4 h-4" />
                Browse All
              </ControlButton>
            </div>

            {loading ? (
              <div className="flex items-center justify-center min-h-[120px]">
                <div className="text-center">
                  <div className="w-8 h-8 border-4 border-black border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                  <p className="text-sm text-muted">Loading...</p>
                </div>
              </div>
            ) : recentLessons.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="w-12 h-12 text-muted mx-auto mb-3" />
                <h3 className="font-heading font-semibold text-lg tracking-tight text-black mb-2">
                  No lessons yet
                </h3>
                <p className="text-sm text-muted mb-4">
                  Create your first lesson to get started
                </p>
                <ControlButton
                  variant="primary"
                  onClick={() => navigate('/create')}
                  className="flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Create Lesson
                </ControlButton>
              </div>
            ) : (
              <div className="space-y-3">
                {recentLessons.map((lesson) => (
                  <RecentActivityCard
                    key={lesson.id}
                    lesson={lesson}
                    onResume={() => navigate(`/lesson/${lesson.id}`)}
                  />
                ))}
              </div>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}
