'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { format, parseISO } from 'date-fns';
import {
  Calendar,
  Clock,
  MapPin,
  User,
  MoreVertical,
  XCircle,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { bookingsApi } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import type { Booking, BookingStatus } from '@/lib/types';

const statusConfig: Record<
  BookingStatus,
  { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ElementType }
> = {
  pending: { label: 'Pending', variant: 'secondary', icon: AlertCircle },
  confirmed: { label: 'Confirmed', variant: 'default', icon: CheckCircle },
  cancelled: { label: 'Cancelled', variant: 'destructive', icon: XCircle },
  completed: { label: 'Completed', variant: 'outline', icon: CheckCircle },
  no_show: { label: 'No Show', variant: 'destructive', icon: XCircle },
};

export default function BookingsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: isAuthLoading } = useAuthStore();

  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      router.push('/login?redirect=/bookings');
    }
  }, [isAuthLoading, isAuthenticated, router]);

  const { data: bookingsData, isLoading } = useQuery({
    queryKey: ['bookings'],
    queryFn: () => bookingsApi.getBookings(),
    enabled: isAuthenticated,
  });

  const bookings: Booking[] = bookingsData?.data?.results || [];

  const upcomingBookings = bookings.filter(
    (b) => ['pending', 'confirmed'].includes(b.status) && new Date(b.start_time) >= new Date()
  );
  const pastBookings = bookings.filter(
    (b) => !['pending', 'confirmed'].includes(b.status) || new Date(b.start_time) < new Date()
  );

  if (isAuthLoading || isLoading) {
    return (
      <div className="container py-8">
        <div className="mb-8">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">My Bookings</h1>
        <p className="text-muted-foreground">
          View and manage your service appointments
        </p>
      </div>

      <Tabs defaultValue="upcoming">
        <TabsList className="mb-6">
          <TabsTrigger value="upcoming">
            Upcoming ({upcomingBookings.length})
          </TabsTrigger>
          <TabsTrigger value="past">
            Past ({pastBookings.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upcoming">
          {upcomingBookings.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Calendar className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                <h3 className="font-semibold text-lg mb-2">No upcoming bookings</h3>
                <p className="text-muted-foreground mb-4">
                  You don&apos;t have any scheduled appointments
                </p>
                <Button asChild>
                  <Link href="/services">Book a Service</Link>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {upcomingBookings.map((booking) => (
                <BookingCard key={booking.id} booking={booking} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="past">
          {pastBookings.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Calendar className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                <h3 className="font-semibold text-lg mb-2">No past bookings</h3>
                <p className="text-muted-foreground">
                  Your booking history will appear here
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {pastBookings.map((booking) => (
                <BookingCard key={booking.id} booking={booking} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function BookingCard({ booking }: { booking: Booking }) {
  const status = statusConfig[booking.status];
  const StatusIcon = status.icon;
  const isPast = new Date(booking.start_time) < new Date();
  const canCancel = ['pending', 'confirmed'].includes(booking.status) && !isPast;
  const canReschedule = ['pending', 'confirmed'].includes(booking.status) && !isPast;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="font-semibold text-lg">{booking.service.name}</h3>
              <Badge variant={status.variant}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {status.label}
              </Badge>
            </div>

            <div className="grid sm:grid-cols-2 gap-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                {format(parseISO(booking.start_time), 'EEEE, MMMM d, yyyy')}
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                {format(parseISO(booking.start_time), 'h:mm a')} -{' '}
                {format(parseISO(booking.end_time), 'h:mm a')}
              </div>
              {booking.provider && (
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  {booking.provider.user.first_name} {booking.provider.user.last_name}
                </div>
              )}
            </div>

            {booking.notes && (
              <p className="text-sm text-muted-foreground mt-2 line-clamp-1">
                Note: {booking.notes}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="text-right mr-2">
              <p className="text-lg font-semibold">${booking.total_price.toFixed(2)}</p>
              {booking.addons && booking.addons.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  +{booking.addons.length} add-on{booking.addons.length > 1 ? 's' : ''}
                </p>
              )}
            </div>

            <Button variant="outline" size="sm" asChild>
              <Link href={`/bookings/${booking.id}`}>View</Link>
            </Button>

            {(canCancel || canReschedule) && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {canReschedule && (
                    <DropdownMenuItem>Reschedule</DropdownMenuItem>
                  )}
                  {canCancel && (
                    <DropdownMenuItem className="text-destructive">
                      Cancel Booking
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
