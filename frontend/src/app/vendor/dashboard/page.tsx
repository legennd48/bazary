'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Store,
  Package,
  ShoppingCart,
  DollarSign,
  Star,
  Plus,
  AlertCircle,
  CheckCircle,
  Clock,
  FileText,
  TrendingUp,
  Eye,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';

const statusConfig: Record<string, { color: string; icon: React.ElementType; label: string }> = {
  pending: { color: 'bg-yellow-500', icon: Clock, label: 'Pending Review' },
  documents_required: { color: 'bg-orange-500', icon: FileText, label: 'Documents Required' },
  under_review: { color: 'bg-blue-500', icon: Eye, label: 'Under Review' },
  verified: { color: 'bg-green-500', icon: CheckCircle, label: 'Verified' },
  rejected: { color: 'bg-red-500', icon: AlertCircle, label: 'Rejected' },
  suspended: { color: 'bg-red-500', icon: AlertCircle, label: 'Suspended' },
};

export default function VendorDashboardPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?redirect=/vendor/dashboard');
    }
  }, [authLoading, isAuthenticated, router]);

  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['vendor-dashboard'],
    queryFn: async () => {
      const response = await api.get('/vendors/dashboard/');
      return response.data;
    },
    enabled: isAuthenticated,
  });

  if (authLoading || isLoading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    // User is not a vendor
    return (
      <div className="container py-12 max-w-2xl">
        <Card className="text-center">
          <CardContent className="py-12">
            <Store className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-2xl font-bold mb-2">You&apos;re not a vendor yet</h2>
            <p className="text-muted-foreground mb-6">
              Start selling your products and services on Bazary
            </p>
            <Button asChild size="lg">
              <Link href="/become-vendor">
                <Plus className="h-5 w-5 mr-2" />
                Become a Vendor
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const vendor = dashboardData?.vendor;
  const stats = dashboardData?.stats;
  const verification = dashboardData?.verification;
  const statusInfo = statusConfig[verification?.status] || statusConfig.pending;
  const StatusIcon = statusInfo.icon;

  return (
    <div className="container py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold">{vendor?.store_name}</h1>
          <p className="text-muted-foreground">Vendor Dashboard</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href={`/stores/${vendor?.slug}`}>
              <Eye className="h-4 w-4 mr-2" />
              View Store
            </Link>
          </Button>
          <Button asChild>
            <Link href="/vendor/products/new">
              <Plus className="h-4 w-4 mr-2" />
              Add Product
            </Link>
          </Button>
        </div>
      </div>

      {/* Verification Status Banner */}
      {verification?.status !== 'verified' && (
        <Card className="mb-6 border-l-4" style={{ borderLeftColor: statusInfo.color.replace('bg-', '') }}>
          <CardContent className="py-4">
            <div className="flex items-center gap-4">
              <div className={`p-2 rounded-full ${statusInfo.color}`}>
                <StatusIcon className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1">
                <p className="font-medium">Account Status: {statusInfo.label}</p>
                <p className="text-sm text-muted-foreground">
                  {verification?.status === 'pending' &&
                    'Your application is being reviewed. This usually takes 24-48 hours.'}
                  {verification?.status === 'documents_required' &&
                    'Please upload the required documents to continue verification.'}
                  {verification?.status === 'rejected' &&
                    'Your application was not approved. Please contact support for more information.'}
                </p>
              </div>
              {verification?.status === 'documents_required' && (
                <Button variant="outline" asChild>
                  <Link href="/vendor/documents">Upload Documents</Link>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_products || 0}</div>
            <p className="text-xs text-muted-foreground">
              {verification?.can_sell ? 'Active on store' : 'Pending approval'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Orders</CardTitle>
            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_orders || 0}</div>
            <p className="text-xs text-muted-foreground">All time orders</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${stats?.total_revenue || '0.00'}</div>
            <p className="text-xs text-muted-foreground">Total earnings</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Rating</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-1">
              {stats?.average_rating || '0.0'}
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
            </div>
            <p className="text-xs text-muted-foreground">
              {stats?.total_reviews || 0} reviews
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks for your store</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" className="w-full justify-start" asChild>
              <Link href="/vendor/products">
                <Package className="h-4 w-4 mr-2" />
                Manage Products
              </Link>
            </Button>
            <Button variant="outline" className="w-full justify-start" asChild>
              <Link href="/vendor/orders">
                <ShoppingCart className="h-4 w-4 mr-2" />
                View Orders
              </Link>
            </Button>
            <Button variant="outline" className="w-full justify-start" asChild>
              <Link href="/vendor/settings">
                <Store className="h-4 w-4 mr-2" />
                Store Settings
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Store Completion</CardTitle>
            <CardDescription>Complete your store profile</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Profile completion</span>
                  <span>60%</span>
                </div>
                <Progress value={60} />
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>Basic information</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>Contact details</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <AlertCircle className="h-4 w-4" />
                  <span>Add store logo</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <AlertCircle className="h-4 w-4" />
                  <span>Add shipping policy</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="container py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-32" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-10 w-28" />
          <Skeleton className="h-10 w-32" />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}
