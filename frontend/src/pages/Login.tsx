import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Panel } from '@/components/Panel';
import { ControlButton } from '@/components/ControlButton';
import { TextInput } from '@/components/TextInput';
import { AlertCircle } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [mounted, setMounted] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  useEffect(() => {
    setMounted(true);
  }, []);
  
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    
    const success = await login(username, password);
    
    if (success) {
      navigate(from, { replace: true });
    } else {
      setError('Invalid username or password');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:flex-1 bg-black items-center justify-center p-12">
        <div className={`max-w-md text-white ${mounted ? 'page-enter' : ''}`}>
          <div className="flex items-center gap-3 mb-8">
            <img 
              src="/logo.svg" 
              alt="Project2412" 
              className="w-12 h-12 logo-stamp"
            />
            <span className="font-heading font-bold text-2xl tracking-tight">Project2412</span>
          </div>
          <h1 className="font-heading font-bold text-4xl tracking-tight mb-6 leading-tight">
            Gamify Your Learning
          </h1>
          <p className="text-lg text-white/80 leading-relaxed">
            Master complex topics with ease. Track progress, earn achievements, and become a learning champion.
          </p>
        </div>
      </div>

      {/* Right side - Login Form */}
      <div className="flex-1 lg:max-w-md flex items-center justify-center p-8">
        <div className={`w-full max-w-sm ${mounted ? 'section-enter' : ''}`}>
          <Panel>
            <div className="relative">
              <div className="absolute top-0 left-0 w-full h-1 bg-accent-yellow accent-bar-reveal"></div>
              <h2 className="font-heading font-semibold text-2xl tracking-tight text-black mb-6 pt-2">
                Sign In
              </h2>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-accent-yellow border-2 border-black p-4 error-flash">
                  <div className="flex items-center gap-2 text-sm font-medium text-black">
                    <AlertCircle className="w-4 h-4" />
                    {error}
                  </div>
                </div>
              )}
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-black">
                  Username
                </label>
                <TextInput
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  required
                  error={!!error}
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-black">
                  Password
                </label>
                <TextInput
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  error={!!error}
                />
              </div>
              
              <ControlButton 
                type="submit" 
                variant="primary" 
                className="w-full btn-active"
                disabled={isSubmitting}
                loading={isSubmitting}
              >
                {isSubmitting ? (
                  'AUTHENTICATING...'
                ) : (
                  'Sign In'
                )}
              </ControlButton>
            </form>
            
            <div className="mt-6 pt-6 border-t-2 border-black">
              <p className="text-xs font-mono text-muted text-center">
                Demo credentials: admin / password
              </p>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
