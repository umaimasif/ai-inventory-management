import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";

// Layout for all authenticated pages. The route group "(app)" does not
// affect URLs — /dashboard, /products, etc. stay at the top level.
export default function AppLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
