'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Heart,
  Trash2,
  ShoppingCart,
  Share2,
  Plus,
  MoreHorizontal,
  ExternalLink,
  Bell,
  BellOff,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { wishlistApi, cartApi } from '@/lib/api';
import { useCartStore, useAuthStore } from '@/lib/store';
import type { Wishlist, WishlistItem } from '@/lib/types';

export default function WishlistPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuthStore();
  const { addItem } = useCartStore();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newWishlistName, setNewWishlistName] = useState('');
  const [newWishlistPublic, setNewWishlistPublic] = useState(false);

  // Redirect if not authenticated
  if (!isAuthenticated) {
    router.push('/login?redirect=/wishlist');
    return null;
  }

  const { data: wishlistsData, isLoading } = useQuery({
    queryKey: ['wishlists'],
    queryFn: () => wishlistApi.getWishlists(),
  });

  const wishlists: Wishlist[] = wishlistsData?.data || [];

  const createWishlistMutation = useMutation({
    mutationFn: (data: { name: string; is_public: boolean }) =>
      wishlistApi.createWishlist(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlists'] });
      setCreateDialogOpen(false);
      setNewWishlistName('');
      setNewWishlistPublic(false);
      toast.success('Wishlist created!');
    },
    onError: () => {
      toast.error('Failed to create wishlist');
    },
  });

  const removeItemMutation = useMutation({
    mutationFn: (itemId: string) => wishlistApi.removeItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlists'] });
      toast.success('Item removed from wishlist');
    },
    onError: () => {
      toast.error('Failed to remove item');
    },
  });

  const addToCartMutation = useMutation({
    mutationFn: (item: WishlistItem) =>
      cartApi.addToCart(item.product_id, item.variant_id || undefined),
    onSuccess: (_, item) => {
      toast.success(`${item.product_name} added to cart!`);
    },
    onError: () => {
      toast.error('Failed to add to cart');
    },
  });

  const handleCreateWishlist = () => {
    if (!newWishlistName.trim()) {
      toast.error('Please enter a name');
      return;
    }
    createWishlistMutation.mutate({
      name: newWishlistName,
      is_public: newWishlistPublic,
    });
  };

  const handleShareWishlist = async (wishlist: Wishlist) => {
    if (wishlist.share_url) {
      await navigator.clipboard.writeText(wishlist.share_url);
      toast.success('Share link copied to clipboard!');
    } else {
      toast.error('Make wishlist public to share');
    }
  };

  if (isLoading) {
    return <WishlistSkeleton />;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">My Wishlists</h1>
          <p className="text-muted-foreground mt-1">
            Save items for later and organize your favorites
          </p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Wishlist
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Wishlist</DialogTitle>
              <DialogDescription>
                Create a new wishlist to organize your favorite items.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Wishlist Name</Label>
                <Input
                  id="name"
                  value={newWishlistName}
                  onChange={(e) => setNewWishlistName(e.target.value)}
                  placeholder="e.g., Birthday Ideas"
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="public">Make Public</Label>
                  <p className="text-sm text-muted-foreground">
                    Others can view with a shared link
                  </p>
                </div>
                <Switch
                  id="public"
                  checked={newWishlistPublic}
                  onCheckedChange={setNewWishlistPublic}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setCreateDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateWishlist}
                disabled={createWishlistMutation.isPending}
              >
                {createWishlistMutation.isPending ? 'Creating...' : 'Create'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {wishlists.length === 0 ? (
        <Card className="text-center py-16">
          <CardContent>
            <Heart className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">No wishlists yet</h2>
            <p className="text-muted-foreground mb-4">
              Create a wishlist to save items you love
            </p>
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Wishlist
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Tabs defaultValue={wishlists[0]?.id} className="space-y-6">
          <TabsList className="flex flex-wrap h-auto gap-2">
            {wishlists.map((wishlist) => (
              <TabsTrigger
                key={wishlist.id}
                value={wishlist.id}
                className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              >
                {wishlist.name}
                {wishlist.is_default && (
                  <Badge variant="secondary" className="ml-2 text-xs">
                    Default
                  </Badge>
                )}
                <Badge variant="outline" className="ml-2">
                  {wishlist.item_count}
                </Badge>
              </TabsTrigger>
            ))}
          </TabsList>

          {wishlists.map((wishlist) => (
            <TabsContent key={wishlist.id} value={wishlist.id}>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {wishlist.name}
                      {wishlist.is_public && (
                        <Badge variant="secondary">
                          <Share2 className="h-3 w-3 mr-1" />
                          Public
                        </Badge>
                      )}
                    </CardTitle>
                    {wishlist.description && (
                      <p className="text-sm text-muted-foreground mt-1">
                        {wishlist.description}
                      </p>
                    )}
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => handleShareWishlist(wishlist)}
                      >
                        <Share2 className="h-4 w-4 mr-2" />
                        Share
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-destructive">
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete Wishlist
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </CardHeader>
                <CardContent>
                  {wishlist.items.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-muted-foreground">
                        This wishlist is empty
                      </p>
                      <Button variant="link" asChild className="mt-2">
                        <Link href="/products">Browse Products</Link>
                      </Button>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {wishlist.items.map((item) => (
                        <WishlistItemCard
                          key={item.id}
                          item={item}
                          onRemove={() => removeItemMutation.mutate(item.id)}
                          onAddToCart={() => addToCartMutation.mutate(item)}
                        />
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
      )}
    </div>
  );
}

function WishlistItemCard({
  item,
  onRemove,
  onAddToCart,
}: {
  item: WishlistItem;
  onRemove: () => void;
  onAddToCart: () => void;
}) {
  const hasDiscount =
    item.product_compare_price && item.product_compare_price > item.product_price;

  return (
    <Card className="overflow-hidden group">
      <div className="relative aspect-square bg-muted">
        {item.product_image ? (
          <Image
            src={item.product_image}
            alt={item.product_name}
            fill
            className="object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Heart className="h-12 w-12 text-muted-foreground" />
          </div>
        )}
        {item.is_on_sale && (
          <Badge className="absolute top-2 left-2 bg-red-500">Sale</Badge>
        )}
        {!item.is_available && (
          <div className="absolute inset-0 bg-background/80 flex items-center justify-center">
            <Badge variant="secondary">Out of Stock</Badge>
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 bg-background/80 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={onRemove}
        >
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </div>
      <CardContent className="p-4">
        <Link href={`/products/${item.product_slug}`}>
          <h3 className="font-medium line-clamp-2 hover:underline">
            {item.product_name}
          </h3>
        </Link>
        <div className="flex items-baseline gap-2 mt-2">
          <span className="font-bold">${item.product_price.toFixed(2)}</span>
          {hasDiscount && (
            <span className="text-sm text-muted-foreground line-through">
              ${item.product_compare_price?.toFixed(2)}
            </span>
          )}
        </div>
        <Button
          className="w-full mt-3"
          size="sm"
          disabled={!item.is_available}
          onClick={onAddToCart}
        >
          <ShoppingCart className="h-4 w-4 mr-2" />
          Add to Cart
        </Button>
      </CardContent>
    </Card>
  );
}

function WishlistSkeleton() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <Skeleton className="h-10 w-32" />
      </div>
      <Skeleton className="h-12 w-full mb-6" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-80 w-full" />
        ))}
      </div>
    </div>
  );
}
