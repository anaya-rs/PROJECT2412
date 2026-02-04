import { useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { Panel } from '@/components/Panel';
import { ControlButton } from '@/components/ControlButton';

const NotFound = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
      <div className="min-h-screen bg-paper flex items-center justify-center p-4">
        <Panel className="max-w-md w-full">
          <div className="text-center space-y-6">
            <h1 className="font-heading font-bold text-6xl tracking-tight text-black">
              404
            </h1>
            <h2 className="font-heading font-semibold text-xl tracking-tight text-black">
              Page Not Found
            </h2>
            <p className="text-muted">
              The page you're looking for doesn't exist or has been moved.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <ControlButton 
                variant="primary" 
                onClick={() => navigate(-1)}
              >
                Go Back
              </ControlButton>
              <ControlButton 
                variant="secondary" 
                onClick={() => navigate('/dashboard')}
              >
                Dashboard
              </ControlButton>
            </div>
          </div>
        </Panel>
      </div>
  );
};

export default NotFound;
