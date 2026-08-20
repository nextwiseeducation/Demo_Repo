import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";

import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/features/auth/AuthContext";
import { queryClient } from "@/lib/queryClient";
import { router } from "@/router";

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
        <Toaster richColors position="top-right" />
      </AuthProvider>
    </QueryClientProvider>
  );
}
