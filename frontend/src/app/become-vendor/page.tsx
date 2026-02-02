'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useMutation } from '@tanstack/react-query';
import {
  Store,
  Package,
  Briefcase,
  User,
  ArrowRight,
  ArrowLeft,
  Check,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import { toast } from 'sonner';

const vendorTypes = [
  {
    value: 'individual',
    label: 'Individual Seller',
    description: 'Sell products as an individual',
    icon: User,
  },
  {
    value: 'business',
    label: 'Business',
    description: 'Registered business or company',
    icon: Briefcase,
  },
  {
    value: 'service_provider',
    label: 'Service Provider',
    description: 'Offer professional services',
    icon: Package,
  },
];

export default function BecomeVendorPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [step, setStep] = useState(1);

  const [formData, setFormData] = useState({
    store_name: '',
    vendor_type: 'individual',
    business_description: '',
    product_categories: [] as string[],
    contact_email: user?.email || '',
    contact_phone: '',
    business_name: '',
    city: '',
    country: 'Ethiopia',
  });

  const registerMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      return api.post('/vendors/register/', data);
    },
    onSuccess: () => {
      toast.success('Application submitted! We\'ll review it shortly.');
      router.push('/vendor/dashboard');
    },
    onError: (error: any) => {
      const message = error.response?.data?.message || 
                      error.response?.data?.non_field_errors?.[0] ||
                      'Failed to submit application';
      toast.error(message);
    },
  });

  if (!isAuthenticated) {
    return (
      <div className="container py-12 max-w-2xl">
        <Card className="text-center">
          <CardContent className="py-12">
            <Store className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-2xl font-bold mb-2">Become a Vendor</h2>
            <p className="text-muted-foreground mb-6">
              Please sign in to start selling on Bazary
            </p>
            <div className="flex gap-4 justify-center">
              <Button asChild variant="outline">
                <Link href="/login?redirect=/become-vendor">Sign In</Link>
              </Button>
              <Button asChild>
                <Link href="/register?redirect=/become-vendor">Create Account</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleSubmit = () => {
    if (!formData.store_name || !formData.business_description || !formData.contact_phone) {
      toast.error('Please fill in all required fields');
      return;
    }
    registerMutation.mutate(formData);
  };

  return (
    <div className="container py-8 max-w-3xl">
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-center">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-medium ${
                  s < step
                    ? 'bg-primary text-primary-foreground'
                    : s === step
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {s < step ? <Check className="h-5 w-5" /> : s}
              </div>
              {s < 3 && (
                <div
                  className={`w-20 h-1 ${
                    s < step ? 'bg-primary' : 'bg-muted'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-center mt-2">
          <span className="text-sm text-muted-foreground">
            Step {step} of 3:{' '}
            {step === 1 ? 'Vendor Type' : step === 2 ? 'Store Details' : 'Contact Info'}
          </span>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Store className="h-6 w-6" />
            Become a Vendor
          </CardTitle>
          <CardDescription>
            Start selling your products and services on Bazary
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Step 1: Vendor Type */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <Label className="text-base">What type of vendor are you?</Label>
                <p className="text-sm text-muted-foreground mb-4">
                  Select the option that best describes you
                </p>
                <RadioGroup
                  value={formData.vendor_type}
                  onValueChange={(value) =>
                    setFormData({ ...formData, vendor_type: value })
                  }
                  className="grid gap-4"
                >
                  {vendorTypes.map((type) => (
                    <Label
                      key={type.value}
                      htmlFor={type.value}
                      className={`flex items-start gap-4 p-4 border rounded-lg cursor-pointer transition-colors ${
                        formData.vendor_type === type.value
                          ? 'border-primary bg-primary/5'
                          : 'hover:border-primary/50'
                      }`}
                    >
                      <RadioGroupItem value={type.value} id={type.value} />
                      <type.icon className="h-6 w-6 text-primary mt-0.5" />
                      <div>
                        <p className="font-medium">{type.label}</p>
                        <p className="text-sm text-muted-foreground">
                          {type.description}
                        </p>
                      </div>
                    </Label>
                  ))}
                </RadioGroup>
              </div>
            </div>
          )}

          {/* Step 2: Store Details */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="store_name">Store Name *</Label>
                <Input
                  id="store_name"
                  value={formData.store_name}
                  onChange={(e) =>
                    setFormData({ ...formData, store_name: e.target.value })
                  }
                  placeholder="Your unique store name"
                />
                <p className="text-xs text-muted-foreground">
                  This will be your public store name
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="business_description">
                  Business Description *
                </Label>
                <Textarea
                  id="business_description"
                  value={formData.business_description}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      business_description: e.target.value,
                    })
                  }
                  placeholder="Tell us about your business, what you sell, and why customers should buy from you"
                  rows={4}
                />
              </div>

              {formData.vendor_type === 'business' && (
                <div className="space-y-2">
                  <Label htmlFor="business_name">Legal Business Name</Label>
                  <Input
                    id="business_name"
                    value={formData.business_name}
                    onChange={(e) =>
                      setFormData({ ...formData, business_name: e.target.value })
                    }
                    placeholder="Registered business name"
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="city">City</Label>
                  <Input
                    id="city"
                    value={formData.city}
                    onChange={(e) =>
                      setFormData({ ...formData, city: e.target.value })
                    }
                    placeholder="Your city"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="country">Country</Label>
                  <Input
                    id="country"
                    value={formData.country}
                    onChange={(e) =>
                      setFormData({ ...formData, country: e.target.value })
                    }
                    placeholder="Ethiopia"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Contact Info */}
          {step === 3 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="contact_email">Business Email *</Label>
                <Input
                  id="contact_email"
                  type="email"
                  value={formData.contact_email}
                  onChange={(e) =>
                    setFormData({ ...formData, contact_email: e.target.value })
                  }
                  placeholder="business@example.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contact_phone">Phone Number *</Label>
                <Input
                  id="contact_phone"
                  value={formData.contact_phone}
                  onChange={(e) =>
                    setFormData({ ...formData, contact_phone: e.target.value })
                  }
                  placeholder="+251 9XX XXX XXX"
                />
              </div>

              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-medium mb-2">What happens next?</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• We&apos;ll review your application (usually within 24-48 hours)</li>
                  <li>• You may be asked to provide additional documents</li>
                  <li>• Once approved, you can start adding products</li>
                  <li>• You&apos;ll receive a notification when your store is live</li>
                </ul>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8">
            {step > 1 ? (
              <Button variant="outline" onClick={() => setStep(step - 1)}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            ) : (
              <div />
            )}

            {step < 3 ? (
              <Button onClick={() => setStep(step + 1)}>
                Next
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={registerMutation.isPending}
              >
                {registerMutation.isPending && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                Submit Application
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
