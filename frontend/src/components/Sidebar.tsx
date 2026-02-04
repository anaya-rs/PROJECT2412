import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { SidebarItem } from '@/components/SidebarItem';
import { ControlButton } from '@/components/ControlButton';
import { 
  LayoutDashboard, 
  BookOpen, 
  GraduationCap, 
  BarChart3, 
  Settings, 
  LogOut 
} from 'lucide-react';

export function Sidebar({ isOpen, onToggle }: { 
  isOpen: boolean; 
  onToggle: () => void; 
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const menuItems = [
    {
      icon: LayoutDashboard,
      label: 'Dashboard',
      path: '/dashboard',
      active: location.pathname === '/dashboard'
    },
    {
      icon: BookOpen,
      label: 'Lessons',
      path: '/lessons',
      active: location.pathname === '/lessons'
    },
    {
      icon: GraduationCap,
      label: 'Create',
      path: '/create',
      active: location.pathname === '/create'
    },
    {
      icon: BarChart3,
      label: 'Progress',
      path: '/progress',
      active: location.pathname === '/progress'
    },
    {
      icon: Settings,
      label: 'Settings',
      path: '/settings',
      active: location.pathname === '/settings'
    }
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <>
      {/* Sidebar Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 h-screen bg-white border-r-2 border-black z-40 flex flex-col
        w-64 overflow-hidden
      `}>
        <nav className="flex-1 p-4 pt-3 overflow-y-auto">
          <div className="space-y-1">
            {menuItems.map((item) => (
              <SidebarItem
                key={item.path}
                active={item.active}
                onClick={() => handleNavigation(item.path)}
              >
                <div className="flex items-center gap-2">
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  <span className="text-base font-medium truncate">{item.label}</span>
                </div>
              </SidebarItem>
            ))}
          </div>
        </nav>

        {/* User Section */}
        <div className="mt-auto p-4 border-t-2 border-black bg-paper">
          <div className="mb-4">
            <div className="text-sm font-medium text-black">{user?.username}</div>
            <div className="text-xs text-muted">Level 5 Learner</div>
          </div>
          <ControlButton
            variant="secondary"
            onClick={logout}
            className="w-full bg-white hover:bg-accent-yellow"
          >
            <span className="flex items-center justify-center gap-2">
              <LogOut className="w-4 h-4" />
              <span>Sign out</span>
            </span>
          </ControlButton>
        </div>
      </div>
    </>
  );
}
