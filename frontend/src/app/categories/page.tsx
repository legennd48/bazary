'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { ChevronRight, Folder } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { categoriesApi } from '@/lib/api';
import type { CategoryTree } from '@/lib/types';

export default function CategoriesPage() {
  const { data: categoriesData, isLoading } = useQuery({
    queryKey: ['categories-tree'],
    queryFn: () => categoriesApi.getCategoryTree(),
  });

  const categories: CategoryTree[] = categoriesData?.data || [];

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="mb-8">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Categories</h1>
        <p className="text-muted-foreground">
          Browse products by category
        </p>
      </div>

      {categories.length === 0 ? (
        <div className="text-center py-12">
          <Folder className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium mb-2">No categories found</h3>
          <p className="text-muted-foreground">Categories will appear here once added</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {categories.map((category) => (
            <CategoryCard key={category.id} category={category} />
          ))}
        </div>
      )}
    </div>
  );
}

function CategoryCard({ category }: { category: CategoryTree }) {
  return (
    <Link href={`/products?category=${category.id}`}>
      <Card className="group h-full transition-all hover:shadow-md hover:-translate-y-1">
        <CardContent className="p-6">
          <div className="aspect-square bg-gradient-to-br from-primary/10 to-primary/5 rounded-lg flex items-center justify-center mb-4">
            {category.image ? (
              <img
                src={category.image}
                alt={category.name}
                className="w-full h-full object-cover rounded-lg"
              />
            ) : (
              <Folder className="h-12 w-12 text-primary/30" />
            )}
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold group-hover:text-primary transition-colors">
                {category.name}
              </h3>
              {category.product_count !== undefined && (
                <p className="text-sm text-muted-foreground">
                  {category.product_count} products
                </p>
              )}
            </div>
            <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
          {category.children && category.children.length > 0 && (
            <div className="mt-3 pt-3 border-t">
              <p className="text-xs text-muted-foreground">
                {category.children.length} subcategories
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
