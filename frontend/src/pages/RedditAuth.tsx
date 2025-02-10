import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/auth/exports';

export default function RedditAuth() {
  const [redditUsername, setRedditUsername] = useState('');
  const [redditPassword, setRedditPassword] = useState('');
  const { token } = useAuth();
  const navigate = useNavigate();

  const redditAuthMutation = useMutation({
    mutationFn: async (credentials: { username: string; password: string }) => {
      const response = await fetch('http://localhost:8000/reddit/auth', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        throw new Error('Reddit authentication failed');
      }

      return response.json();
    },
    onSuccess: () => {
      navigate('/');
    },
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow">
        <h1 className="text-2xl font-bold mb-6">Connect Reddit Account</h1>
        <form onSubmit={(e) => {
          e.preventDefault();
          redditAuthMutation.mutate({ 
            username: redditUsername, 
            password: redditPassword 
          });
        }}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Reddit Username
              </label>
              <input
                type="text"
                value={redditUsername}
                onChange={(e) => setRedditUsername(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Reddit Password
              </label>
              <input
                type="password"
                value={redditPassword}
                onChange={(e) => setRedditPassword(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600"
              disabled={redditAuthMutation.isPending}
            >
              {redditAuthMutation.isPending ? 'Connecting...' : 'Connect Reddit Account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 