import { Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Navbar from '../components/Navbar';
import LandingPage from '../pages/LandingPage';
import CreateAccount from '../pages/CreateAccount';
import RedditAuth from '../pages/RedditAuth';
import ProtectedRoute from '../components/ProtectedRoute';
import { AuthProvider } from '../context/auth/exports';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <div className="min-h-screen bg-gray-100">
          <Navbar />
          <Routes>
            <Route index element={<LandingPage />} />
            <Route path="create-account" element={<CreateAccount />} />
            <Route 
              path="reddit-auth" 
              element={
                <ProtectedRoute>
                  <RedditAuth />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </div>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;