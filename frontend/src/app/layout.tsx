import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { CartSheet } from "@/components/layout/cart-sheet";
import { NotificationsSheet } from "@/components/layout/notifications-sheet";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: {
    default: "Bazary - Products, Services & Bookings",
    template: "%s | Bazary",
  },
  description:
    "Your one-stop destination for products and services. Shop, book, and experience with confidence.",
  keywords: ["ecommerce", "marketplace", "booking", "services", "shopping"],
  authors: [{ name: "Bazary Team" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://bazary.com",
    siteName: "Bazary",
    title: "Bazary - Products, Services & Bookings",
    description:
      "Your one-stop destination for products and services. Shop, book, and experience with confidence.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          <div className="relative flex min-h-screen flex-col">
            <Header />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
          <CartSheet />
          <NotificationsSheet />
        </Providers>
      </body>
    </html>
  );
}
