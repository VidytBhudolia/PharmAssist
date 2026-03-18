import { SignIn } from "@clerk/clerk-react";
import { Pill } from "lucide-react";

/**
 * Full-page sign-in screen.
 * Uses Clerk's pre-built <SignIn /> component with dark-theme styling.
 */
export default function SignInPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      {/* Brand header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-11 h-11 rounded-2xl border border-primary/40 bg-primary/15 flex items-center justify-center">
          <Pill className="text-primary" size={20} />
        </div>
        <div>
          <div className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            PharmAssist
          </div>
          <div className="text-lg font-semibold text-foreground">Portfolio Studio</div>
        </div>
      </div>

      <SignIn
        routing="virtual"
        signUpUrl="/sign-up"
        afterSignInUrl="/"
        appearance={{
          variables: {
            colorPrimary: "#2dd4bf",
            colorBackground: "#0c1520",
            colorInputBackground: "#12202e",
            colorInputText: "#e2e8f0",
            colorText: "#e2e8f0",
            colorTextSecondary: "#64748b",
            borderRadius: "0.75rem",
          },
          elements: {
            rootBox: "mx-auto",
            card: "bg-[#0c1520] border border-[#1c3044] shadow-2xl shadow-black/50 rounded-2xl",
            headerTitle: "text-white font-semibold",
            headerSubtitle: "text-slate-400",
            socialButtonsBlockButton:
              "bg-[#12202e] border border-[#1c3044] text-slate-200 hover:bg-[#182a3a]",
            socialButtonsBlockButtonText: "text-slate-200",
            formButtonPrimary:
              "bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700 text-white shadow-lg shadow-teal-500/25 border-0",
            formFieldInput:
              "bg-[#12202e] border-[#1c3044] text-slate-100 placeholder:text-slate-500",
            formFieldLabel: "text-slate-300",
            footerActionLink: "text-teal-400 hover:text-teal-300",
            footerActionText: "text-slate-500",
            identityPreviewEditButton: "text-teal-400 hover:text-teal-300",
            identityPreviewText: "text-slate-300",
            formFieldAction: "text-teal-400 hover:text-teal-300",
            dividerLine: "bg-[#1c3044]",
            dividerText: "text-slate-500",
            otpCodeFieldInput: "bg-[#12202e] border-[#1c3044] text-slate-100",
            footer: "[&_span]:text-slate-500 [&_a]:text-teal-400 [&_a:hover]:text-teal-300",
            internal: "text-slate-500",
          },
        }}
      />
    </div>
  );
}
