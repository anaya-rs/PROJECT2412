import { ReactNode, useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { apiService, AiJob } from '@/lib/api';
import { ControlButton } from '@/components/ControlButton';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<AiJob | null>(null);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  useEffect(() => {
    const storedJobId = localStorage.getItem('activeAiLessonJobId');
    if (storedJobId) {
      // Check if the job is stale (older than 1 hour) and clear it
      const jobTimestamp = localStorage.getItem('activeAiLessonJobTimestamp');
      if (jobTimestamp) {
        const age = Date.now() - parseInt(jobTimestamp);
        if (age > 3600000) { // 1 hour
          localStorage.removeItem('activeAiLessonJobId');
          localStorage.removeItem('activeAiLessonJobTimestamp');
          return;
        }
      }
      setActiveJobId(storedJobId);
    }
  }, []);

  useEffect(() => {
    const syncFromStorage = () => {
      const storedJobId = localStorage.getItem('activeAiLessonJobId');
      setActiveJobId(storedJobId);
    };

    const onStorage = (e: StorageEvent) => {
      if (e.key === 'activeAiLessonJobId') {
        syncFromStorage();
      }
    };

    window.addEventListener('storage', onStorage);
    window.addEventListener('ai-job-updated', syncFromStorage as EventListener);

    return () => {
      window.removeEventListener('storage', onStorage);
      window.removeEventListener('ai-job-updated', syncFromStorage as EventListener);
    };
  }, []);

  useEffect(() => {
    if (!activeJobId) {
      setActiveJob(null);
      return;
    }

    let intervalId: number | undefined;
    let cancelled = false;

    const poll = async () => {
      try {
        const job = await apiService.getAiLessonJob(activeJobId);
        if (cancelled) return;
        setActiveJob(job);
        if (job.status === 'completed' || job.status === 'failed') {
          if (intervalId) {
            window.clearInterval(intervalId);
          }
          // Auto-dismiss completed/failed jobs after 5 seconds
          setTimeout(() => {
            localStorage.removeItem('activeAiLessonJobId');
            localStorage.removeItem('activeAiLessonJobTimestamp');
            setActiveJobId(null);
            setActiveJob(null);
          }, 5000);
        }
      } catch (error) {
        if (cancelled) return;
        // If job not found (404), dismiss it
        if (error.message?.includes('404') || error.message?.includes('Job not found')) {
          if (intervalId) {
            window.clearInterval(intervalId);
          }
          localStorage.removeItem('activeAiLessonJobId');
          localStorage.removeItem('activeAiLessonJobTimestamp');
          setActiveJobId(null);
          setActiveJob(null);
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
  }, [activeJobId]);

  const dismissJob = () => {
    localStorage.removeItem('activeAiLessonJobId');
    setActiveJobId(null);
    setActiveJob(null);
  };

  return (
    <div className="min-h-screen bg-paper">
      {sidebarOpen && (
        <Sidebar 
          isOpen={sidebarOpen} 
          onToggle={toggleSidebar}
        />
      )}
      <div className={`${sidebarOpen ? 'ml-64' : 'ml-0'} transition-all duration-300 ease-in-out`}>
        <TopBar onToggleSidebar={toggleSidebar} sidebarOpen={sidebarOpen} />
        <main className="min-h-screen">
          {children}
        </main>
      </div>

      {/* Show progress banner only when NOT on generating page */}
      {activeJob && location.pathname !== '/generating' && (
        <div className="fixed bottom-4 left-4 right-4 z-50">
          <div className="border-2 border-black bg-white rounded-md p-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-black truncate">
                  {activeJob.inputTitle || 'Creating lesson'}
                </div>
                <div className="text-xs text-muted truncate">
                  {activeJob.message || (activeJob.status === 'completed' ? 'Completed' : 'Processing')}
                </div>
                <div className="mt-2 w-full bg-black/10 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent-orange transition-all duration-base ease-standard"
                    style={{ width: `${Math.max(0, Math.min(100, activeJob.progress || 0))}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 flex-wrap justify-end">
                {(activeJob.status === 'queued' || activeJob.status === 'running') && (
                  <ControlButton
                    variant="secondary"
                    onClick={() => navigate(`/generating?jobId=${activeJob.id}`)}
                    className="px-3 py-1.5"
                  >
                    View Progress
                  </ControlButton>
                )}

                {activeJob.status === 'completed' && activeJob.lessonId && (
                  <ControlButton
                    variant="primary"
                    onClick={() => navigate(`/lesson/${activeJob.lessonId}`)}
                    className="px-3 py-1.5"
                  >
                    View Lesson
                  </ControlButton>
                )}

                <ControlButton
                  variant="secondary"
                  onClick={dismissJob}
                  className="px-3 py-1.5"
                >
                  Dismiss
                </ControlButton>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
