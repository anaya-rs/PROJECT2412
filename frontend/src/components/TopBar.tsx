import { useAuth } from '@/contexts/AuthContext';
import { ControlButton } from './ControlButton';
import { LogOut, User, Menu } from 'lucide-react';

export function TopBar({ onToggleSidebar, sidebarOpen }: { onToggleSidebar: () => void; sidebarOpen: boolean }) {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-accent-yellow border-b-2 border-black z-30">
      <div className="px-6 h-full flex items-center justify-between">
        {/* Logo and Menu */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="p-2 hover:bg-accent-amber rounded-md transition-all duration-300 ease-in-out btn-active"
          >
            <Menu className="w-5 h-5 text-black" />
          </button>
          <div className="flex items-center gap-2">
            <img 
              src="/logo.svg" 
              alt="Project2412" 
              className="w-14 h-14"
            />
            <span className="font-heading font-bold text-2xl text-black">Project2412</span>
          </div>
        </div>

        {/* User Actions */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2">
            <User className="w-4 h-4 text-black" />
            <span className="text-sm font-medium text-black">{user?.username}</span>
          </div>
          <ControlButton
            variant="secondary"
            onClick={logout}
            className="p-2"
          >
            <LogOut className="w-4 h-4" />
          </ControlButton>
        </div>
      </div>
    </header>
  );
}
