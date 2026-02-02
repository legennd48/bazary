'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  ChevronLeft,
  ChevronRight,
  Heart,
  Minus,
  Plus,
  Share2,
  ShoppingCart,
  Star,
  Truck,
  Shield,
  RotateCcw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { productsApi } from '@/lib/api';
import { useCartStore } from '@/lib/store';
import type { Product, ProductVariant, VariantOptionValue } from '@/lib/types';
import { cn } from '@/lib/utils';

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params.id as string;

  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(null);

  const { addItem, setIsOpen } = useCartStore();

  const { data: productData, isLoading } = useQuery({
    queryKey: ['product', productId],
    queryFn: () => productsApi.getProduct(productId),
    enabled: !!productId,
  });

  const product: Product | undefined = productData?.data;

  // Get unique variant options
  const variantOptions = product?.variants?.reduce(
    (acc, variant) => {
      variant.options?.forEach((opt) => {
        if (!acc[opt.option_name]) {
          acc[opt.option_name] = [];
        }
        if (!acc[opt.option_name].includes(opt.value)) {
          acc[opt.option_name].push(opt.value);
        }
      });
      return acc;
    },
    {} as Record<string, string[]>
  );

  // Find matching variant based on selected options
  const findMatchingVariant = () => {
    if (!product?.variants || Object.keys(selectedOptions).length === 0) return null;
    return product.variants.find((variant) =>
      variant.options?.every((opt) => selectedOptions[opt.option_name] === opt.value)
    );
  };

  const handleOptionSelect = (optionName: string, value: string) => {
    const newOptions = { ...selectedOptions, [optionName]: value };
    setSelectedOptions(newOptions);
  };

  const currentVariant = findMatchingVariant();
  const currentPrice = currentVariant?.price || product?.sale_price || product?.base_price || 0;
  const comparePrice = currentVariant?.compare_at_price || product?.compare_at_price;
  const hasDiscount = comparePrice && comparePrice > currentPrice;
  const inStock = currentVariant
    ? currentVariant.stock_quantity > 0
    : (product?.stock_quantity || 0) > 0;

  const images = product?.images || [];

  const handleAddToCart = () => {
    if (!product) return;
    addItem({
      id: currentVariant?.id || product.id,
      product_id: product.id,
      variant_id: currentVariant?.id,
      name: currentVariant ? `${product.name} - ${currentVariant.name}` : product.name,
      image: images[0]?.image,
      price: currentPrice,
      quantity,
    });
    setIsOpen(true);
  };

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="grid md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <Skeleton className="aspect-square rounded-lg" />
            <div className="flex gap-2">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="w-20 h-20 rounded-lg" />
              ))}
            </div>
          </div>
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-6 w-1/4" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container py-8 text-center">
        <h1 className="text-2xl font-bold mb-4">Product not found</h1>
        <Button onClick={() => router.push('/products')}>Back to Products</Button>
      </div>
    );
  }

  return (
    <div className="container py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
        <Link href="/" className="hover:text-foreground">
          Home
        </Link>
        <span>/</span>
        <Link href="/products" className="hover:text-foreground">
          Products
        </Link>
        <span>/</span>
        <span className="text-foreground">{product.name}</span>
      </nav>

      <div className="grid md:grid-cols-2 gap-8 lg:gap-12">
        {/* Image Gallery */}
        <div className="space-y-4">
          <div className="aspect-square relative bg-muted rounded-lg overflow-hidden">
            {images.length > 0 ? (
              <Image
                src={images[selectedImageIndex].image}
                alt={product.name}
                fill
                className="object-cover"
                priority
              />
            ) : (
              <div className="h-full w-full flex items-center justify-center">
                <ShoppingCart className="h-24 w-24 text-muted-foreground/30" />
              </div>
            )}
            {images.length > 1 && (
              <>
                <Button
                  variant="outline"
                  size="icon"
                  className="absolute left-2 top-1/2 -translate-y-1/2"
                  onClick={() =>
                    setSelectedImageIndex((i) => (i === 0 ? images.length - 1 : i - 1))
                  }
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  className="absolute right-2 top-1/2 -translate-y-1/2"
                  onClick={() =>
                    setSelectedImageIndex((i) => (i === images.length - 1 ? 0 : i + 1))
                  }
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </>
            )}
            {hasDiscount && (
              <Badge className="absolute top-4 left-4" variant="destructive">
                {Math.round(((comparePrice - currentPrice) / comparePrice) * 100)}% OFF
              </Badge>
            )}
          </div>

          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {images.map((image, index) => (
                <button
                  key={image.id}
                  onClick={() => setSelectedImageIndex(index)}
                  className={cn(
                    'w-20 h-20 flex-shrink-0 rounded-lg overflow-hidden border-2 transition-colors',
                    selectedImageIndex === index
                      ? 'border-primary'
                      : 'border-transparent hover:border-muted-foreground/30'
                  )}
                >
                  <Image
                    src={image.image}
                    alt={`${product.name} ${index + 1}`}
                    width={80}
                    height={80}
                    className="object-cover w-full h-full"
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">{product.name}</h1>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                <span className="font-medium">
                  {product.average_rating?.toFixed(1) || '0.0'}
                </span>
                <span className="text-muted-foreground">
                  ({product.review_count || 0} reviews)
                </span>
              </div>
              {product.is_featured && <Badge variant="secondary">Featured</Badge>}
            </div>
          </div>

          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold">${currentPrice.toFixed(2)}</span>
            {hasDiscount && (
              <span className="text-xl text-muted-foreground line-through">
                ${comparePrice.toFixed(2)}
              </span>
            )}
          </div>

          <p className="text-muted-foreground">{product.description}</p>

          <Separator />

          {/* Variant Options */}
          {variantOptions && Object.keys(variantOptions).length > 0 && (
            <div className="space-y-4">
              {Object.entries(variantOptions).map(([optionName, values]) => (
                <div key={optionName}>
                  <label className="block text-sm font-medium mb-2">
                    {optionName}: {selectedOptions[optionName] || 'Select'}
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {values.map((value) => (
                      <Button
                        key={value}
                        variant={selectedOptions[optionName] === value ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handleOptionSelect(optionName, value)}
                      >
                        {value}
                      </Button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Quantity */}
          <div>
            <label className="block text-sm font-medium mb-2">Quantity</label>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                disabled={quantity <= 1}
              >
                <Minus className="h-4 w-4" />
              </Button>
              <span className="w-12 text-center font-medium">{quantity}</span>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setQuantity((q) => q + 1)}
              >
                <Plus className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground ml-2">
                {inStock ? `${product.stock_quantity} available` : 'Out of stock'}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              size="lg"
              className="flex-1"
              onClick={handleAddToCart}
              disabled={!inStock}
            >
              <ShoppingCart className="h-5 w-5 mr-2" />
              {inStock ? 'Add to Cart' : 'Out of Stock'}
            </Button>
            <Button size="lg" variant="outline">
              <Heart className="h-5 w-5" />
            </Button>
            <Button size="lg" variant="outline">
              <Share2 className="h-5 w-5" />
            </Button>
          </div>

          {/* Trust badges */}
          <div className="grid grid-cols-3 gap-4 pt-4">
            <div className="text-center">
              <Truck className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-xs font-medium">Free Shipping</p>
              <p className="text-xs text-muted-foreground">On orders $50+</p>
            </div>
            <div className="text-center">
              <Shield className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-xs font-medium">Secure Payment</p>
              <p className="text-xs text-muted-foreground">100% protected</p>
            </div>
            <div className="text-center">
              <RotateCcw className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-xs font-medium">Easy Returns</p>
              <p className="text-xs text-muted-foreground">30 day policy</p>
            </div>
          </div>
        </div>
      </div>

      {/* Product Details Tabs */}
      <Tabs defaultValue="description" className="mt-12">
        <TabsList>
          <TabsTrigger value="description">Description</TabsTrigger>
          <TabsTrigger value="specifications">Specifications</TabsTrigger>
          <TabsTrigger value="reviews">Reviews ({product.review_count || 0})</TabsTrigger>
        </TabsList>
        <TabsContent value="description" className="mt-6">
          <div className="prose prose-sm max-w-none">
            <p>{product.description}</p>
          </div>
        </TabsContent>
        <TabsContent value="specifications" className="mt-6">
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="flex justify-between py-2 border-b">
              <span className="text-muted-foreground">SKU</span>
              <span className="font-medium">{currentVariant?.sku || product.id}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-muted-foreground">Category</span>
              <span className="font-medium">{product.category?.name}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-muted-foreground">Stock</span>
              <span className="font-medium">{product.stock_quantity} units</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-muted-foreground">Tags</span>
              <span className="font-medium">
                {product.tags?.map((t) => t.name).join(', ') || 'None'}
              </span>
            </div>
          </div>
        </TabsContent>
        <TabsContent value="reviews" className="mt-6">
          <p className="text-muted-foreground">No reviews yet. Be the first to review!</p>
        </TabsContent>
      </Tabs>
    </div>
  );
}
