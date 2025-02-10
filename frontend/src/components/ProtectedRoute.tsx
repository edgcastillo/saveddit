import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/auth/exports';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/" />;
  }

  return <>{children}</>;
} 