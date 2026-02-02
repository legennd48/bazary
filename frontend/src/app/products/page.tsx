'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  Filter,
  Grid3X3,
  LayoutList,
  Search,
  SlidersHorizontal,
  Star,
  ShoppingCart,
  Heart,
  ChevronDown,
} from 'lucide-react';
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
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';
import { productsApi, categoriesApi } from '@/lib/api';
import { useCartStore } from '@/lib/store';
import type { Product, Category } from '@/lib/types';
import { cn } from '@/lib/utils';

function ProductsContent() {
  const searchParams = useSearchParams();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [sortBy, setSortBy] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>(
    searchParams.get('category') || ''
  );
  const { addItem, setIsOpen } = useCartStore();

  const { data: productsData, isLoading: productsLoading } = useQuery({
    queryKey: ['products', searchQuery, sortBy, selectedCategory],
    queryFn: () =>
      productsApi.getProducts({
        search: searchQuery || undefined,
        ordering: sortBy || undefined,
        category: selectedCategory ? parseInt(selectedCategory) : undefined,
      }),
  });

  const { data: categoriesData } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getCategories(),
  });

  const products: Product[] = productsData?.data?.results || [];
  const categories: Category[] = categoriesData?.data?.results || [];

  const handleAddToCart = (product: Product) => {
    addItem({
      id: product.id,
      product_id: product.id,
      name: product.name,
      image: product.images?.[0]?.image,
      price: product.sale_price || product.base_price,
      quantity: 1,
    });
    setIsOpen(true);
  };

  const FilterSidebar = () => (
    <div className="space-y-6">
      <div>
        <h3 className="font-semibold mb-3">Categories</h3>
        <div className="space-y-2">
          <button
            onClick={() => setSelectedCategory('')}
            className={cn(
              'block w-full text-left text-sm py-1 transition-colors',
              !selectedCategory
                ? 'text-primary font-medium'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            All Categories
          </button>
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id.toString())}
              className={cn(
                'block w-full text-left text-sm py-1 transition-colors',
                selectedCategory === category.id.toString()
                  ? 'text-primary font-medium'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {category.name}
            </button>
          ))}
        </div>
      </div>

      <Separator />

      <div>
        <h3 className="font-semibold mb-3">Price Range</h3>
        <div className="grid grid-cols-2 gap-2">
          <Input placeholder="Min" type="number" className="h-9" />
          <Input placeholder="Max" type="number" className="h-9" />
        </div>
      </div>

      <Separator />

      <div>
        <h3 className="font-semibold mb-3">Availability</h3>
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" className="rounded" />
            In Stock
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" className="rounded" />
            On Sale
          </label>
        </div>
      </div>
    </div>
  );

  return (
    <div className="container py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Products</h1>
        <p className="text-muted-foreground">
          Browse our collection of {products.length} products
        </p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1 flex gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Mobile filter button */}
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="md:hidden">
                <SlidersHorizontal className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left">
              <SheetHeader>
                <SheetTitle>Filters</SheetTitle>
              </SheetHeader>
              <div className="mt-6">
                <FilterSidebar />
              </div>
            </SheetContent>
          </Sheet>
        </div>

        <div className="flex items-center gap-2">
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="name">Name A-Z</SelectItem>
              <SelectItem value="-name">Name Z-A</SelectItem>
              <SelectItem value="base_price">Price: Low to High</SelectItem>
              <SelectItem value="-base_price">Price: High to Low</SelectItem>
              <SelectItem value="-created_at">Newest First</SelectItem>
            </SelectContent>
          </Select>

          <div className="hidden sm:flex border rounded-lg">
            <Button
              variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
              size="icon"
              className="rounded-r-none"
              onClick={() => setViewMode('grid')}
            >
              <Grid3X3 className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'secondary' : 'ghost'}
              size="icon"
              className="rounded-l-none"
              onClick={() => setViewMode('list')}
            >
              <LayoutList className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      <div className="flex gap-8">
        {/* Desktop Sidebar */}
        <aside className="hidden md:block w-64 flex-shrink-0">
          <FilterSidebar />
        </aside>

        {/* Products Grid */}
        <div className="flex-1">
          {productsLoading ? (
            <div
              className={cn(
                'gap-4',
                viewMode === 'grid'
                  ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
                  : 'space-y-4'
              )}
            >
              {[...Array(6)].map((_, i) => (
                <Card key={i}>
                  <CardContent className="p-0">
                    <Skeleton className="aspect-square" />
                    <div className="p-4 space-y-2">
                      <Skeleton className="h-4 w-2/3" />
                      <Skeleton className="h-4 w-1/3" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No products found</p>
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onAddToCart={() => handleAddToCart(product)}
                />
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {products.map((product) => (
                <ProductListItem
                  key={product.id}
                  product={product}
                  onAddToCart={() => handleAddToCart(product)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ProductCard({
  product,
  onAddToCart,
}: {
  product: Product;
  onAddToCart: () => void;
}) {
  const hasDiscount = product.sale_price && product.sale_price < product.base_price;
  const primaryImage = product.images?.find((img) => img.is_primary) || product.images?.[0];

  return (
    <Card className="group overflow-hidden">
      <CardContent className="p-0">
        <Link href={`/products/${product.id}`}>
          <div className="aspect-square relative bg-muted overflow-hidden">
            {primaryImage ? (
              <Image
                src={primaryImage.image}
                alt={product.name}
                fill
                className="object-cover transition-transform group-hover:scale-105"
              />
            ) : (
              <div className="h-full w-full flex items-center justify-center">
                <ShoppingCart className="h-12 w-12 text-muted-foreground/30" />
              </div>
            )}
            {hasDiscount && (
              <Badge className="absolute top-2 left-2" variant="destructive">
                Sale
              </Badge>
            )}
            {product.is_featured && (
              <Badge className="absolute top-2 right-2" variant="secondary">
                Featured
              </Badge>
            )}
          </div>
        </Link>
        <div className="p-4">
          <Link href={`/products/${product.id}`}>
            <h3 className="font-medium line-clamp-1 group-hover:text-primary transition-colors">
              {product.name}
            </h3>
          </Link>
          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
            {product.short_description || product.description}
          </p>
          <div className="flex items-center gap-1 mt-2">
            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
            <span className="text-sm font-medium">
              {product.average_rating?.toFixed(1) || '0.0'}
            </span>
            <span className="text-sm text-muted-foreground">
              ({product.review_count || 0})
            </span>
          </div>
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-baseline gap-2">
              <span className="font-semibold">
                ${(product.sale_price || product.base_price).toFixed(2)}
              </span>
              {hasDiscount && (
                <span className="text-sm text-muted-foreground line-through">
                  ${product.base_price.toFixed(2)}
                </span>
              )}
            </div>
            <Button size="sm" onClick={onAddToCart}>
              <ShoppingCart className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ProductListItem({
  product,
  onAddToCart,
}: {
  product: Product;
  onAddToCart: () => void;
}) {
  const hasDiscount = product.sale_price && product.sale_price < product.base_price;
  const primaryImage = product.images?.find((img) => img.is_primary) || product.images?.[0];

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex gap-4">
          <Link href={`/products/${product.id}`} className="flex-shrink-0">
            <div className="w-32 h-32 relative bg-muted rounded-lg overflow-hidden">
              {primaryImage ? (
                <Image
                  src={primaryImage.image}
                  alt={product.name}
                  fill
                  className="object-cover"
                />
              ) : (
                <div className="h-full w-full flex items-center justify-center">
                  <ShoppingCart className="h-8 w-8 text-muted-foreground/30" />
                </div>
              )}
            </div>
          </Link>
          <div className="flex-1 min-w-0">
            <Link href={`/products/${product.id}`}>
              <h3 className="font-medium hover:text-primary transition-colors">
                {product.name}
              </h3>
            </Link>
            <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
              {product.short_description || product.description}
            </p>
            <div className="flex items-center gap-1 mt-2">
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              <span className="text-sm font-medium">
                {product.average_rating?.toFixed(1) || '0.0'}
              </span>
              <span className="text-sm text-muted-foreground">
                ({product.review_count || 0} reviews)
              </span>
            </div>
            <div className="flex items-center justify-between mt-3">
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-semibold">
                  ${(product.sale_price || product.base_price).toFixed(2)}
                </span>
                {hasDiscount && (
                  <span className="text-sm text-muted-foreground line-through">
                    ${product.base_price.toFixed(2)}
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="icon">
                  <Heart className="h-4 w-4" />
                </Button>
                <Button onClick={onAddToCart}>
                  <ShoppingCart className="h-4 w-4 mr-2" />
                  Add to Cart
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ProductsPageSkeleton() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex gap-8">
        <div className="hidden md:block w-64 space-y-4">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
        <div className="flex-1 space-y-6">
          <Skeleton className="h-12 w-full" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-80 w-full" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<ProductsPageSkeleton />}>
      <ProductsContent />
    </Suspense>
  );
}
