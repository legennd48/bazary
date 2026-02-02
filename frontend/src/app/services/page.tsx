'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Search, Clock, Star, Calendar, MapPin, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { servicesApi } from '@/lib/api';
import type { Service, ServiceCategory } from '@/lib/types';

function ServicesContent() {
  const searchParams = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [selectedCategory, setSelectedCategory] = useState(
    searchParams.get('category') || 'all'
  );
  const [sortBy, setSortBy] = useState('default');

  const { data: servicesData, isLoading } = useQuery({
    queryKey: ['services', searchQuery, selectedCategory, sortBy],
    queryFn: () =>
      servicesApi.getServices({
        search: searchQuery || undefined,
        category: selectedCategory === 'all' ? undefined : selectedCategory,
      }),
  });

  const { data: categoriesData } = useQuery({
    queryKey: ['service-categories'],
    queryFn: () => servicesApi.getCategories(),
  });

  const services: Service[] = servicesData?.data?.results || [];
  const categories: ServiceCategory[] = categoriesData?.data?.results || [];

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0 && mins > 0) return `${hours}h ${mins}m`;
    if (hours > 0) return `${hours}h`;
    return `${mins}m`;
  };

  const formatPrice = (price: number, pricingType: string) => {
    const priceStr = `$${price.toFixed(2)}`;
    switch (pricingType) {
      case 'hourly':
        return `${priceStr}/hr`;
      case 'daily':
        return `${priceStr}/day`;
      default:
        return priceStr;
    }
  };

  return (
    <div className="container py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Services</h1>
        <p className="text-muted-foreground">
          Book professional services with trusted providers
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search services..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-full md:w-[200px]">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category.id} value={category.id}>
                {category.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-full md:w-[180px]">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="default">Sort by</SelectItem>
            <SelectItem value="name">Name A-Z</SelectItem>
            <SelectItem value="-name">Name Z-A</SelectItem>
            <SelectItem value="base_price">Price: Low to High</SelectItem>
            <SelectItem value="-base_price">Price: High to Low</SelectItem>
            <SelectItem value="-average_rating">Top Rated</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Services Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-0">
                <Skeleton className="aspect-video" />
                <div className="p-4 space-y-2">
                  <Skeleton className="h-5 w-2/3" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : services.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium mb-2">No services found</h3>
          <p className="text-muted-foreground">
            Try adjusting your filters or search query
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service) => (
            <ServiceCard key={service.id} service={service} formatDuration={formatDuration} formatPrice={formatPrice} />
          ))}
        </div>
      )}
    </div>
  );
}

function ServiceCard({
  service,
  formatDuration,
  formatPrice,
}: {
  service: Service;
  formatDuration: (minutes: number) => string;
  formatPrice: (price: number, pricingType: string) => string;
}) {
  const primaryImage = service.images?.find((img) => img.is_primary) || service.images?.[0];

  return (
    <Link href={`/services/${service.id}`}>
      <Card className="group overflow-hidden h-full transition-shadow hover:shadow-lg">
        <CardContent className="p-0">
          <div className="aspect-video relative bg-muted overflow-hidden">
            {primaryImage ? (
              <Image
                src={primaryImage.image}
                alt={service.name}
                fill
                className="object-cover transition-transform group-hover:scale-105"
              />
            ) : (
              <div className="h-full w-full flex items-center justify-center bg-gradient-to-br from-primary/10 to-primary/5">
                <Calendar className="h-12 w-12 text-primary/30" />
              </div>
            )}
            {service.is_featured && (
              <Badge className="absolute top-3 left-3" variant="secondary">
                Featured
              </Badge>
            )}
          </div>

          <div className="p-4">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h3 className="font-semibold group-hover:text-primary transition-colors line-clamp-1">
                {service.name}
              </h3>
              <Badge variant="outline" className="flex-shrink-0">
                {service.category?.name}
              </Badge>
            </div>

            <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
              {service.short_description || service.description}
            </p>

            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {formatDuration(service.duration_minutes)}
              </div>
              <div className="flex items-center gap-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                {service.average_rating?.toFixed(1) || '0.0'}
                <span className="text-xs">({service.review_count || 0})</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-lg font-bold">
                {formatPrice(service.base_price, service.pricing_type)}
              </span>
              <Button size="sm">Book Now</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function ServicesPageSkeleton() {
  return (
    <div className="container mx-auto px-4 py-8 space-y-6">
      <Skeleton className="h-10 w-64" />
      <Skeleton className="h-12 w-full" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-80 w-full" />
        ))}
      </div>
    </div>
  );
}

export default function ServicesPage() {
  return (
    <Suspense fallback={<ServicesPageSkeleton />}>
      <ServicesContent />
    </Suspense>
  );
}
