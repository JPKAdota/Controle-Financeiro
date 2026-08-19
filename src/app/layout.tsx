import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Controle Financeiro",
  description: "Gerenciado por IA",
};

import AuthGuard from "@/components/AuthGuard";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body
        className={`${inter.className} min-h-screen bg-gray-50 dark:bg-gray-900`}
      >
        <AuthGuard>{children}</AuthGuard>
      </body>
    </html>
  );
}
