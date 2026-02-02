'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { format, parseISO } from 'date-fns';
import {
  Package,
  ChevronRight,
  Truck,
  CreditCard,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { ordersApi } from '@/lib/api';
import type { Order, OrderStatus, PaymentStatus } from '@/lib/types';

const orderStatusConfig: Record<
  OrderStatus,
  { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ElementType }
> = {
  pending: { label: 'Pending', variant: 'secondary', icon: Clock },
  processing: { label: 'Processing', variant: 'default', icon: Package },
  shipped: { label: 'Shipped', variant: 'default', icon: Truck },
  delivered: { label: 'Delivered', variant: 'outline', icon: CheckCircle },
  cancelled: { label: 'Cancelled', variant: 'destructive', icon: XCircle },
  refunded: { label: 'Refunded', variant: 'destructive', icon: AlertCircle },
};

const paymentStatusConfig: Record<
  PaymentStatus,
  { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }
> = {
  pending: { label: 'Pending', variant: 'secondary' },
  paid: { label: 'Paid', variant: 'default' },
  failed: { label: 'Failed', variant: 'destructive' },
  refunded: { label: 'Refunded', variant: 'outline' },
  partially_refunded: { label: 'Partially Refunded', variant: 'outline' },
};

export default function OrdersPage() {
  const { data: ordersData, isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: () => ordersApi.getOrders(),
  });

  const orders: Order[] = ordersData?.data?.results || [];

  const activeOrders = orders.filter((o) =>
    ['pending', 'processing', 'shipped'].includes(o.status)
  );
  const completedOrders = orders.filter((o) =>
    ['delivered', 'cancelled', 'refunded'].includes(o.status)
  );

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="mb-8">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">My Orders</h1>
        <p className="text-muted-foreground">Track and manage your orders</p>
      </div>

      <Tabs defaultValue="active">
        <TabsList className="mb-6">
          <TabsTrigger value="active">Active ({activeOrders.length})</TabsTrigger>
          <TabsTrigger value="completed">
            Completed ({completedOrders.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active">
          {activeOrders.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Package className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                <h3 className="font-semibold text-lg mb-2">No active orders</h3>
                <p className="text-muted-foreground mb-4">
                  You don&apos;t have any orders in progress
                </p>
                <Button asChild>
                  <Link href="/products">Start Shopping</Link>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {activeOrders.map((order) => (
                <OrderCard key={order.id} order={order} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="completed">
          {completedOrders.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Package className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                <h3 className="font-semibold text-lg mb-2">No completed orders</h3>
                <p className="text-muted-foreground">
                  Your order history will appear here
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {completedOrders.map((order) => (
                <OrderCard key={order.id} order={order} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function OrderCard({ order }: { order: Order }) {
  const status = orderStatusConfig[order.status];
  const paymentStatus = paymentStatusConfig[order.payment_status];
  const StatusIcon = status.icon;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h3 className="font-semibold">Order #{order.order_number}</h3>
              <Badge variant={status.variant}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {status.label}
              </Badge>
              <Badge variant={paymentStatus.variant}>
                <CreditCard className="h-3 w-3 mr-1" />
                {paymentStatus.label}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Placed on {format(parseISO(order.created_at), 'MMMM d, yyyy')}
            </p>
          </div>
          <div className="text-right">
            <p className="text-lg font-semibold">${order.total.toFixed(2)}</p>
            <p className="text-sm text-muted-foreground">
              {order.items.length} item{order.items.length > 1 ? 's' : ''}
            </p>
          </div>
        </div>

        <Separator className="my-4" />

        {/* Order Items Preview */}
        <div className="flex items-center gap-4 overflow-x-auto pb-2">
          {order.items.slice(0, 4).map((item) => (
            <div
              key={item.id}
              className="flex-shrink-0 w-16 h-16 rounded-lg bg-muted flex items-center justify-center"
            >
              {item.product.image ? (
                <img
                  src={item.product.image}
                  alt={item.product.name}
                  className="w-full h-full object-cover rounded-lg"
                />
              ) : (
                <Package className="h-6 w-6 text-muted-foreground/50" />
              )}
            </div>
          ))}
          {order.items.length > 4 && (
            <div className="flex-shrink-0 w-16 h-16 rounded-lg bg-muted flex items-center justify-center text-sm font-medium text-muted-foreground">
              +{order.items.length - 4}
            </div>
          )}
          <div className="ml-auto">
            <Button variant="outline" size="sm" asChild>
              <Link href={`/orders/${order.id}`}>
                View Details
                <ChevronRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </div>
        </div>

        {/* Shipping Info */}
        {order.shipping_address && (
          <div className="mt-4 p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-2 text-sm">
              <Truck className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">Shipping to:</span>
              <span className="text-muted-foreground">
                {order.shipping_address.street_address}, {order.shipping_address.city}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
