import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useAuth } from '../context/auth/exports';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();

  const loginMutation = useMutation({
    mutationFn: async (credentials: { username: string; password: string }) => {
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      return response.json();
    },
    onSuccess: (data) => {
      login(data.access_token);
      onClose();
    },
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg w-96">
        <h2 className="text-2xl font-bold mb-4">Login</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            loginMutation.mutate({ username, password });
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
              required
            />
          </div>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-900"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? 'Logging in...' : 'Login'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 