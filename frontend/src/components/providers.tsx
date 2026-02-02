'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { Toaster } from '@/components/ui/sonner';
import { useAuthStore } from '@/lib/store';
import { authApi } from '@/lib/api';
import wsService from '@/lib/websocket';
import { useNotificationStore } from '@/lib/store';

function AuthProvider({ children }: { children: React.ReactNode }) {
  const { setUser, setIsLoading, isAuthenticated, logout } = useAuthStore();
  const { addNotification } = useNotificationStore();

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const response = await authApi.getProfile();
          setUser(response.data);
        } catch {
          logout();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, [setUser, setIsLoading, logout]);

  // WebSocket connection
  useEffect(() => {
    if (isAuthenticated) {
      const token = localStorage.getItem('access_token');
      wsService.connect(token || undefined).catch(console.error);

      const unsubscribe = wsService.subscribe('notification', (data) => {
        addNotification({
          id: data.id as string || Date.now().toString(),
          title: data.title as string || 'Notification',
          message: data.message as string || '',
          type: (data.notification_type as 'info' | 'success' | 'warning' | 'error') || 'info',
          read: false,
          created_at: new Date().toISOString(),
          data: data.data as Record<string, unknown>,
        });
      });

      return () => {
        unsubscribe();
        wsService.disconnect();
      };
    }
  }, [isAuthenticated, addNotification]);

  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        {children}
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </QueryClientProvider>
  );
}
