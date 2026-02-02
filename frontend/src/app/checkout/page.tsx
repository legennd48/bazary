'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  CreditCard,
  MapPin,
  Truck,
  Tag,
  ShoppingCart,
  ArrowLeft,
  Loader2,
  Check,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { authApi, ordersApi, paymentsApi, couponApi, shippingApi } from '@/lib/api';
import { useCartStore, useAuthStore } from '@/lib/store';
import { toast } from 'sonner';

export default function CheckoutPage() {
  const router = useRouter();
  const { items, getTotalPrice, clearCart } = useCartStore();
  const { isAuthenticated, user, isLoading: authLoading } = useAuthStore();

  const [step, setStep] = useState(1);
  const [selectedAddressId, setSelectedAddressId] = useState('');
  const [couponCode, setCouponCode] = useState('');
  const [appliedCoupon, setAppliedCoupon] = useState<{ code: string; discount: number } | null>(null);
  const [paymentMethod, setPaymentMethod] = useState('chapa');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?redirect=/checkout');
    }
  }, [authLoading, isAuthenticated, router]);

  // Redirect to cart if empty
  useEffect(() => {
    if (items.length === 0) {
      router.push('/cart');
    }
  }, [items, router]);

  // Fetch user addresses
  const { data: addressesData, isLoading: addressesLoading } = useQuery({
    queryKey: ['addresses'],
    queryFn: () => authApi.getAddresses(),
    enabled: isAuthenticated,
  });

  const addresses = addressesData?.data || [];

  // Set default address
  useEffect(() => {
    if (addresses.length > 0 && !selectedAddressId) {
      const defaultAddress = addresses.find((a: any) => a.is_default) || addresses[0];
      setSelectedAddressId(defaultAddress.id);
    }
  }, [addresses, selectedAddressId]);

  // Calculate totals
  const subtotal = getTotalPrice();
  const discount = appliedCoupon?.discount || 0;
  const shipping = subtotal >= 50 ? 0 : 5.99;
  const tax = (subtotal - discount) * 0.1;
  const total = subtotal - discount + shipping + tax;

  // Apply coupon mutation
  const applyCouponMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await couponApi.validate(code, subtotal);
      return response.data;
    },
    onSuccess: (data) => {
      setAppliedCoupon({ code: couponCode, discount: data.discount_amount });
      toast.success(`Coupon applied! You saved $${data.discount_amount.toFixed(2)}`);
    },
    onError: () => {
      toast.error('Invalid or expired coupon code');
    },
  });

  // Create order mutation
  const createOrderMutation = useMutation({
    mutationFn: async () => {
      const orderData = {
        shipping_address_id: selectedAddressId,
        payment_method: paymentMethod,
        coupon_code: appliedCoupon?.code,
        items: items.map((item) => ({
          product_id: item.product_id,
          variant_id: item.variant_id,
          quantity: item.quantity,
        })),
      };
      return ordersApi.createOrder(orderData);
    },
    onSuccess: async (response) => {
      const orderId = response.data.id;
      
      // Initialize payment
      try {
        const paymentResponse = await paymentsApi.initiate(orderId);
        
        if (paymentResponse.data.checkout_url) {
          clearCart();
          window.location.href = paymentResponse.data.checkout_url;
        } else {
          clearCart();
          router.push(`/orders/${orderId}?success=true`);
        }
      } catch {
        toast.error('Payment initialization failed. Please try again.');
      }
    },
    onError: () => {
      toast.error('Failed to create order. Please try again.');
    },
  });

  const handleApplyCoupon = () => {
    if (!couponCode.trim()) {
      toast.error('Please enter a coupon code');
      return;
    }
    applyCouponMutation.mutate(couponCode);
  };

  const handlePlaceOrder = () => {
    if (!selectedAddressId) {
      toast.error('Please select a shipping address');
      return;
    }
    createOrderMutation.mutate();
  };

  if (authLoading || items.length === 0) {
    return <CheckoutSkeleton />;
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="container py-8 max-w-6xl">
      <div className="mb-6">
        <Link
          href="/cart"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Cart
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-8">Checkout</h1>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Left Column - Checkout Steps */}
        <div className="lg:col-span-2 space-y-6">
          {/* Shipping Address */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Shipping Address
              </CardTitle>
            </CardHeader>
            <CardContent>
              {addressesLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                </div>
              ) : addresses.length === 0 ? (
                <div className="text-center py-6">
                  <p className="text-muted-foreground mb-4">
                    No shipping addresses found
                  </p>
                  <Button variant="outline" asChild>
                    <Link href="/account?tab=addresses">Add Address</Link>
                  </Button>
                </div>
              ) : (
                <RadioGroup
                  value={selectedAddressId}
                  onValueChange={setSelectedAddressId}
                  className="space-y-3"
                >
                  {addresses.map((address: any) => (
                    <Label
                      key={address.id}
                      htmlFor={address.id}
                      className={`flex items-start gap-3 p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedAddressId === address.id
                          ? 'border-primary bg-primary/5'
                          : 'hover:border-primary/50'
                      }`}
                    >
                      <RadioGroupItem value={address.id} id={address.id} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{address.label || 'Address'}</span>
                          {address.is_default && (
                            <Badge variant="secondary" className="text-xs">
                              Default
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {address.address_line1}
                          {address.address_line2 && `, ${address.address_line2}`}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {address.city}, {address.state} {address.postal_code}
                        </p>
                        <p className="text-sm text-muted-foreground">{address.country}</p>
                      </div>
                    </Label>
                  ))}
                </RadioGroup>
              )}
            </CardContent>
          </Card>

          {/* Payment Method */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Payment Method
              </CardTitle>
            </CardHeader>
            <CardContent>
              <RadioGroup
                value={paymentMethod}
                onValueChange={setPaymentMethod}
                className="space-y-3"
              >
                <Label
                  htmlFor="chapa"
                  className={`flex items-center gap-3 p-4 border rounded-lg cursor-pointer transition-colors ${
                    paymentMethod === 'chapa'
                      ? 'border-primary bg-primary/5'
                      : 'hover:border-primary/50'
                  }`}
                >
                  <RadioGroupItem value="chapa" id="chapa" />
                  <div className="flex-1">
                    <span className="font-medium">Chapa</span>
                    <p className="text-sm text-muted-foreground">
                      Pay with mobile money, bank transfer, or card
                    </p>
                  </div>
                </Label>

                <Label
                  htmlFor="stripe"
                  className={`flex items-center gap-3 p-4 border rounded-lg cursor-pointer transition-colors ${
                    paymentMethod === 'stripe'
                      ? 'border-primary bg-primary/5'
                      : 'hover:border-primary/50'
                  }`}
                >
                  <RadioGroupItem value="stripe" id="stripe" />
                  <div className="flex-1">
                    <span className="font-medium">Credit/Debit Card</span>
                    <p className="text-sm text-muted-foreground">
                      Pay securely with Stripe
                    </p>
                  </div>
                </Label>
              </RadioGroup>
            </CardContent>
          </Card>

          {/* Coupon Code */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Tag className="h-5 w-5" />
                Coupon Code
              </CardTitle>
            </CardHeader>
            <CardContent>
              {appliedCoupon ? (
                <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
                  <div className="flex items-center gap-2">
                    <Check className="h-5 w-5 text-green-600" />
                    <span className="font-medium text-green-700 dark:text-green-400">
                      {appliedCoupon.code}
                    </span>
                    <span className="text-sm text-green-600">
                      (-${appliedCoupon.discount.toFixed(2)})
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setAppliedCoupon(null)}
                    className="text-destructive"
                  >
                    Remove
                  </Button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter coupon code"
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                  />
                  <Button
                    variant="outline"
                    onClick={handleApplyCoupon}
                    disabled={applyCouponMutation.isPending}
                  >
                    {applyCouponMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      'Apply'
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Order Summary */}
        <div>
          <Card className="sticky top-24">
            <CardHeader>
              <CardTitle>Order Summary</CardTitle>
              <CardDescription>{items.length} items</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Item List */}
              <div className="space-y-3 max-h-60 overflow-y-auto">
                {items.map((item) => (
                  <div key={item.id} className="flex gap-3">
                    <div className="relative h-14 w-14 rounded bg-muted overflow-hidden flex-shrink-0">
                      {item.image ? (
                        <Image
                          src={item.image}
                          alt={item.name}
                          fill
                          className="object-cover"
                        />
                      ) : (
                        <div className="h-full w-full flex items-center justify-center">
                          <ShoppingCart className="h-5 w-5 text-muted-foreground/50" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{item.name}</p>
                      <p className="text-xs text-muted-foreground">
                        Qty: {item.quantity}
                      </p>
                    </div>
                    <p className="text-sm font-medium">
                      ${(item.price * item.quantity).toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>

              <Separator />

              {/* Totals */}
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                {appliedCoupon && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount</span>
                    <span>-${discount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Shipping</span>
                  <span>
                    {shipping === 0 ? (
                      <span className="text-green-600">Free</span>
                    ) : (
                      `$${shipping.toFixed(2)}`
                    )}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tax</span>
                  <span>${tax.toFixed(2)}</span>
                </div>
              </div>

              <Separator />

              <div className="flex justify-between text-lg font-semibold">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>

              <Button
                className="w-full"
                size="lg"
                onClick={handlePlaceOrder}
                disabled={createOrderMutation.isPending || !selectedAddressId}
              >
                {createOrderMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  `Pay $${total.toFixed(2)}`
                )}
              </Button>

              <p className="text-xs text-muted-foreground text-center">
                By placing this order, you agree to our{' '}
                <Link href="/terms" className="underline">
                  Terms of Service
                </Link>
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function CheckoutSkeleton() {
  return (
    <div className="container py-8 max-w-6xl">
      <Skeleton className="h-6 w-24 mb-6" />
      <Skeleton className="h-10 w-48 mb-8" />
      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-48" />
          <Skeleton className="h-24" />
        </div>
        <div>
          <Skeleton className="h-96" />
        </div>
      </div>
    </div>
  );
}
