"use client";

// Root route: bounce to dashboard or login based on auth state.

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    router.replace(user ? "/dashboard" : "/login");
  }, [user, loading, router]);

  return (
    <div className="flex flex-1 items-center justify-center text-gray-500">
      Loading…
    </div>
  );
}
