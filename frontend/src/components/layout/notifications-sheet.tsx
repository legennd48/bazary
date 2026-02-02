'use client';

import { formatDistanceToNow } from 'date-fns';
import { Bell, Check, CheckCheck, Package, Calendar, CreditCard, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { useNotificationStore } from '@/lib/store';
import { notificationsApi } from '@/lib/api';
import { cn } from '@/lib/utils';

const iconMap: Record<string, React.ElementType> = {
  order_update: Package,
  booking_reminder: Calendar,
  payment: CreditCard,
  info: Info,
  success: Check,
  warning: Info,
  error: Info,
  system: Bell,
};

export function NotificationsSheet() {
  const { notifications, isOpen, setIsOpen, markAsRead, markAllAsRead } = useNotificationStore();

  const handleMarkAsRead = async (id: string) => {
    try {
      await notificationsApi.markAsRead(id);
      markAsRead(id);
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      markAllAsRead();
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetContent className="flex flex-col w-full sm:max-w-md">
        <SheetHeader>
          <div className="flex items-center justify-between">
            <SheetTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notifications
              {unreadCount > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {unreadCount} new
                </Badge>
              )}
            </SheetTitle>
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMarkAllAsRead}
                className="text-xs"
              >
                <CheckCheck className="h-4 w-4 mr-1" />
                Mark all read
              </Button>
            )}
          </div>
        </SheetHeader>

        {notifications.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center py-12">
            <Bell className="h-16 w-16 text-muted-foreground/50 mb-4" />
            <h3 className="font-semibold text-lg mb-2">No notifications</h3>
            <p className="text-muted-foreground text-sm">
              You&apos;re all caught up! Check back later.
            </p>
          </div>
        ) : (
          <ScrollArea className="flex-1 -mx-6 px-6">
            <div className="space-y-2 py-4">
              {notifications.map((notification) => {
                const Icon = iconMap[notification.type] || Bell;
                return (
                  <div
                    key={notification.id}
                    className={cn(
                      'p-4 rounded-lg border transition-colors cursor-pointer',
                      notification.read
                        ? 'bg-background hover:bg-muted/50'
                        : 'bg-primary/5 border-primary/20 hover:bg-primary/10'
                    )}
                    onClick={() => !notification.read && handleMarkAsRead(notification.id)}
                  >
                    <div className="flex gap-3">
                      <div
                        className={cn(
                          'h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0',
                          notification.read
                            ? 'bg-muted'
                            : 'bg-primary/10 text-primary'
                        )}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <h4
                            className={cn(
                              'text-sm font-medium',
                              !notification.read && 'text-primary'
                            )}
                          >
                            {notification.title}
                          </h4>
                          {!notification.read && (
                            <div className="h-2 w-2 rounded-full bg-primary flex-shrink-0 mt-1.5" />
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-xs text-muted-foreground mt-2">
                          {formatDistanceToNow(new Date(notification.created_at), {
                            addSuffix: true,
                          })}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        )}
      </SheetContent>
    </Sheet>
  );
}
