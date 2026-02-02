'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { useQuery, useMutation } from '@tanstack/react-query';
import { format, addDays, parseISO } from 'date-fns';
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  MapPin,
  Star,
  User,
  Check,
  Plus,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { servicesApi, bookingsApi } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import type { Service, ServiceProvider, AvailabilitySlot, ServiceAddon } from '@/lib/types';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

export default function ServiceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const serviceId = params.id as string;
  const { isAuthenticated } = useAuthStore();

  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedAddons, setSelectedAddons] = useState<string[]>([]);
  const [notes, setNotes] = useState('');
  const [bookingStep, setBookingStep] = useState<'details' | 'booking' | 'confirm'>('details');

  const { data: serviceData, isLoading } = useQuery({
    queryKey: ['service', serviceId],
    queryFn: () => servicesApi.getService(serviceId),
    enabled: !!serviceId,
  });

  const { data: availabilityData, isLoading: slotsLoading } = useQuery({
    queryKey: ['availability', serviceId, format(selectedDate, 'yyyy-MM-dd'), selectedProvider],
    queryFn: () =>
      bookingsApi.getAvailability(
        serviceId,
        format(selectedDate, 'yyyy-MM-dd'),
        selectedProvider || undefined
      ),
    enabled: !!serviceId && bookingStep !== 'details',
  });

  const createBookingMutation = useMutation({
    mutationFn: (data: {
      service: string;
      provider?: string;
      start_time: string;
      notes?: string;
      addons?: string[];
    }) => bookingsApi.createBooking(data),
    onSuccess: (data) => {
      toast.success('Booking created successfully!');
      router.push(`/bookings/${data.data.id}`);
    },
    onError: () => {
      toast.error('Failed to create booking. Please try again.');
    },
  });

  const service: Service | undefined = serviceData?.data;
  const slots: AvailabilitySlot[] = availabilityData?.data?.slots || [];
  const availableSlots = slots.filter((slot) => slot.available);

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0 && mins > 0) return `${hours}h ${mins}m`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''}`;
    return `${mins} minutes`;
  };

  const calculateTotal = () => {
    let total = service?.base_price || 0;
    selectedAddons.forEach((addonId) => {
      const addon = service?.addons?.find((a) => a.id === addonId);
      if (addon) total += addon.price;
    });
    return total;
  };

  const handleBook = () => {
    if (!isAuthenticated) {
      router.push(`/login?redirect=/services/${serviceId}`);
      return;
    }

    if (!selectedSlot) {
      toast.error('Please select a time slot');
      return;
    }

    createBookingMutation.mutate({
      service: serviceId,
      provider: selectedProvider || undefined,
      start_time: selectedSlot.start_time,
      notes: notes || undefined,
      addons: selectedAddons.length > 0 ? selectedAddons : undefined,
    });
  };

  const toggleAddon = (addonId: string) => {
    setSelectedAddons((prev) =>
      prev.includes(addonId) ? prev.filter((id) => id !== addonId) : [...prev, addonId]
    );
  };

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="aspect-video rounded-lg" />
            <Skeleton className="h-8 w-2/3" />
            <Skeleton className="h-24 w-full" />
          </div>
          <div>
            <Skeleton className="h-64 w-full rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (!service) {
    return (
      <div className="container py-8 text-center">
        <h1 className="text-2xl font-bold mb-4">Service not found</h1>
        <Button onClick={() => router.push('/services')}>Back to Services</Button>
      </div>
    );
  }

  const primaryImage = service.images?.find((img) => img.is_primary) || service.images?.[0];

  return (
    <div className="container py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
        <Link href="/" className="hover:text-foreground">
          Home
        </Link>
        <span>/</span>
        <Link href="/services" className="hover:text-foreground">
          Services
        </Link>
        <span>/</span>
        <span className="text-foreground">{service.name}</span>
      </nav>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* Hero Image */}
          <div className="aspect-video relative bg-muted rounded-lg overflow-hidden">
            {primaryImage ? (
              <Image
                src={primaryImage.image}
                alt={service.name}
                fill
                className="object-cover"
                priority
              />
            ) : (
              <div className="h-full w-full flex items-center justify-center bg-gradient-to-br from-primary/10 to-primary/5">
                <Calendar className="h-24 w-24 text-primary/30" />
              </div>
            )}
          </div>

          {/* Service Info */}
          <div>
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h1 className="text-3xl font-bold mb-2">{service.name}</h1>
                <div className="flex items-center gap-4 text-muted-foreground">
                  <Badge variant="outline">{service.category?.name}</Badge>
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    <span>{service.average_rating?.toFixed(1) || '0.0'}</span>
                    <span>({service.review_count || 0} reviews)</span>
                  </div>
                </div>
              </div>
              {service.is_featured && <Badge>Featured</Badge>}
            </div>

            <p className="text-muted-foreground mb-6">{service.description}</p>

            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-muted-foreground" />
                <span>{formatDuration(service.duration_minutes)}</span>
              </div>
              {service.min_notice_hours && (
                <div className="flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-muted-foreground" />
                  <span>{service.min_notice_hours}h advance booking required</span>
                </div>
              )}
            </div>
          </div>

          <Separator />

          {/* Providers */}
          {service.providers && service.providers.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Our Providers</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                {service.providers.map((provider) => (
                  <Card
                    key={provider.id}
                    className={cn(
                      'cursor-pointer transition-all',
                      selectedProvider === provider.id && 'ring-2 ring-primary'
                    )}
                    onClick={() =>
                      setSelectedProvider((prev) =>
                        prev === provider.id ? null : provider.id
                      )
                    }
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-12 w-12">
                          <AvatarImage src={provider.user.avatar} />
                          <AvatarFallback>
                            {provider.user.first_name[0]}
                            {provider.user.last_name[0]}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <h3 className="font-medium">
                            {provider.user.first_name} {provider.user.last_name}
                          </h3>
                          <p className="text-sm text-muted-foreground line-clamp-1">
                            {provider.bio || 'Professional service provider'}
                          </p>
                        </div>
                        {selectedProvider === provider.id && (
                          <Check className="h-5 w-5 text-primary" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Addons */}
          {service.addons && service.addons.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Add-ons</h2>
              <div className="space-y-3">
                {service.addons.map((addon) => (
                  <Card
                    key={addon.id}
                    className={cn(
                      'cursor-pointer transition-all',
                      selectedAddons.includes(addon.id) && 'ring-2 ring-primary bg-primary/5'
                    )}
                    onClick={() => toggleAddon(addon.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div
                            className={cn(
                              'h-5 w-5 rounded border flex items-center justify-center',
                              selectedAddons.includes(addon.id)
                                ? 'bg-primary border-primary'
                                : 'border-muted-foreground/30'
                            )}
                          >
                            {selectedAddons.includes(addon.id) && (
                              <Check className="h-3 w-3 text-primary-foreground" />
                            )}
                          </div>
                          <div>
                            <h4 className="font-medium">{addon.name}</h4>
                            {addon.description && (
                              <p className="text-sm text-muted-foreground">
                                {addon.description}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">+${addon.price.toFixed(2)}</p>
                          {addon.duration_minutes && (
                            <p className="text-xs text-muted-foreground">
                              +{addon.duration_minutes}m
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Booking Sidebar */}
        <div>
          <Card className="sticky top-24">
            <CardHeader>
              <CardTitle>Book This Service</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {bookingStep === 'details' ? (
                <>
                  <div className="text-center py-4">
                    <p className="text-3xl font-bold">${service.base_price.toFixed(2)}</p>
                    <p className="text-sm text-muted-foreground">
                      {service.pricing_type === 'hourly' && 'per hour'}
                      {service.pricing_type === 'daily' && 'per day'}
                    </p>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Duration</span>
                      <span>{formatDuration(service.duration_minutes)}</span>
                    </div>
                    {selectedAddons.length > 0 && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Add-ons</span>
                        <span>{selectedAddons.length} selected</span>
                      </div>
                    )}
                    <Separator />
                    <div className="flex justify-between font-medium">
                      <span>Total</span>
                      <span>${calculateTotal().toFixed(2)}</span>
                    </div>
                  </div>

                  <Button
                    className="w-full"
                    size="lg"
                    onClick={() => setBookingStep('booking')}
                  >
                    <Calendar className="h-4 w-4 mr-2" />
                    Select Date & Time
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="mb-2"
                    onClick={() => {
                      setBookingStep('details');
                      setSelectedSlot(null);
                    }}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Back
                  </Button>

                  {/* Date Picker */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Select Date</label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button variant="outline" className="w-full justify-start">
                          <Calendar className="h-4 w-4 mr-2" />
                          {format(selectedDate, 'EEEE, MMMM d, yyyy')}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <CalendarComponent
                          mode="single"
                          selected={selectedDate}
                          onSelect={(date) => date && setSelectedDate(date)}
                          disabled={(date) => date < new Date()}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>

                  {/* Time Slots */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Available Times</label>
                    {slotsLoading ? (
                      <div className="grid grid-cols-3 gap-2">
                        {[...Array(6)].map((_, i) => (
                          <Skeleton key={i} className="h-10" />
                        ))}
                      </div>
                    ) : availableSlots.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        No available slots for this date
                      </p>
                    ) : (
                      <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto">
                        {availableSlots.map((slot, i) => (
                          <Button
                            key={i}
                            variant={selectedSlot === slot ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setSelectedSlot(slot)}
                          >
                            {format(parseISO(slot.start_time), 'h:mm a')}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Notes */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Notes (optional)
                    </label>
                    <Textarea
                      placeholder="Any special requests or information..."
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      rows={3}
                    />
                  </div>

                  {/* Summary */}
                  <div className="bg-muted/50 rounded-lg p-4 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Service</span>
                      <span>{service.name}</span>
                    </div>
                    {selectedSlot && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Date & Time</span>
                        <span>
                          {format(parseISO(selectedSlot.start_time), 'MMM d, h:mm a')}
                        </span>
                      </div>
                    )}
                    <Separator />
                    <div className="flex justify-between font-medium">
                      <span>Total</span>
                      <span>${calculateTotal().toFixed(2)}</span>
                    </div>
                  </div>

                  <Button
                    className="w-full"
                    size="lg"
                    onClick={handleBook}
                    disabled={!selectedSlot || createBookingMutation.isPending}
                  >
                    {createBookingMutation.isPending ? 'Booking...' : 'Confirm Booking'}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
