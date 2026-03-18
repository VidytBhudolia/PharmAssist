import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ClerkProvider } from "@clerk/clerk-react";
import { ThemeProvider } from "@/components/ui/theme-provider";
import "./index.css";
import App from "./App.jsx";

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!CLERK_PUBLISHABLE_KEY) {
  throw new Error(
    "Missing VITE_CLERK_PUBLISHABLE_KEY in .env.local. " +
      "Get it from https://dashboard.clerk.com → API Keys.",
  );
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} afterSignOutUrl="/">
      <ThemeProvider defaultTheme="dark" storageKey="pharma-ai-theme">
        <App />
      </ThemeProvider>
    </ClerkProvider>
  </StrictMode>,
);
