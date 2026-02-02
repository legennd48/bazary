import Link from 'next/link';
import { ArrowRight, Package, Calendar, ShieldCheck, Truck, Clock, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const features = [
  {
    icon: Package,
    title: 'Quality Products',
    description: 'Curated selection of premium products with detailed variants and options.',
  },
  {
    icon: Calendar,
    title: 'Easy Booking',
    description: 'Book services and appointments with real-time availability.',
  },
  {
    icon: Truck,
    title: 'Fast Delivery',
    description: 'Quick and reliable shipping to your doorstep.',
  },
  {
    icon: ShieldCheck,
    title: 'Secure Payments',
    description: 'Safe and encrypted payment processing for peace of mind.',
  },
];

const categories = [
  { name: 'Electronics', image: '/images/categories/electronics.jpg', count: 150 },
  { name: 'Fashion', image: '/images/categories/fashion.jpg', count: 320 },
  { name: 'Home & Garden', image: '/images/categories/home.jpg', count: 180 },
  { name: 'Beauty', image: '/images/categories/beauty.jpg', count: 95 },
];

const services = [
  { name: 'Spa & Wellness', icon: '🧖', count: 45 },
  { name: 'Fitness', icon: '💪', count: 32 },
  { name: 'Consulting', icon: '💼', count: 28 },
  { name: 'Education', icon: '📚', count: 56 },
];

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary/5 via-background to-primary/10">
        <div className="container py-20 md:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <Badge variant="secondary" className="mb-4">
              🚀 Hybrid Commerce Platform
            </Badge>
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
              Products, Services &{' '}
              <span className="text-primary">Bookings</span>
              <br />
              All in One Place
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
              Discover premium products, book professional services, and manage your
              appointments—all from a single, seamless platform.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" asChild>
                <Link href="/products">
                  Browse Products
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="/services">Explore Services</Link>
              </Button>
            </div>
          </div>
        </div>
        <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]" />
      </section>

      {/* Features Section */}
      <section className="py-16 md:py-24 bg-muted/30">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Why Choose Bazary?</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              We bring together the best of e-commerce and service booking into one powerful platform.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => (
              <Card key={feature.title} className="border-0 shadow-sm">
                <CardContent className="pt-6">
                  <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Products Section */}
      <section className="py-16 md:py-24">
        <div className="container">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold mb-2">Shop by Category</h2>
              <p className="text-muted-foreground">
                Explore our wide range of product categories
              </p>
            </div>
            <Button variant="ghost" asChild>
              <Link href="/categories">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {categories.map((category) => (
              <Link
                key={category.name}
                href={`/products?category=${category.name.toLowerCase()}`}
                className="group"
              >
                <Card className="overflow-hidden border-0 shadow-sm transition-shadow hover:shadow-md">
                  <CardContent className="p-0">
                    <div className="aspect-square bg-gradient-to-br from-muted to-muted/50 relative">
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Package className="h-12 w-12 text-muted-foreground/30" />
                      </div>
                    </div>
                    <div className="p-4">
                      <h3 className="font-semibold group-hover:text-primary transition-colors">
                        {category.name}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {category.count} products
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-16 md:py-24 bg-muted/30">
        <div className="container">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold mb-2">Book a Service</h2>
              <p className="text-muted-foreground">
                Professional services with easy online booking
              </p>
            </div>
            <Button variant="ghost" asChild>
              <Link href="/services">
                View All Services
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {services.map((service) => (
              <Link
                key={service.name}
                href={`/services?category=${service.name.toLowerCase()}`}
              >
                <Card className="border-0 shadow-sm transition-all hover:shadow-md hover:-translate-y-1">
                  <CardContent className="p-6 text-center">
                    <span className="text-4xl mb-4 block">{service.icon}</span>
                    <h3 className="font-semibold mb-1">{service.name}</h3>
                    <p className="text-sm text-muted-foreground">
                      {service.count} providers
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 md:py-24">
        <div className="container">
          <Card className="bg-primary text-primary-foreground border-0">
            <CardContent className="py-12 md:py-16 text-center">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to Get Started?
              </h2>
              <p className="text-primary-foreground/80 max-w-2xl mx-auto mb-8">
                Join thousands of satisfied customers. Create your account today
                and start shopping or booking services instantly.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" variant="secondary" asChild>
                  <Link href="/register">Create Account</Link>
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="bg-transparent border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground/10"
                  asChild
                >
                  <Link href="/products">Browse as Guest</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Trust Indicators */}
      <section className="py-12 border-t">
        <div className="container">
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16 text-muted-foreground">
            <div className="flex items-center gap-2">
              <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
              <span className="font-medium">4.9/5 Rating</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              <span className="font-medium">24/7 Support</span>
            </div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5" />
              <span className="font-medium">Secure Checkout</span>
            </div>
            <div className="flex items-center gap-2">
              <Truck className="h-5 w-5" />
              <span className="font-medium">Free Shipping $50+</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
