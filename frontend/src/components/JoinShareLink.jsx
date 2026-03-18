import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { api } from "@/services/api";

export function JoinShareLink() {
  const { token } = useParams();
  const navigate = useNavigate();
  const { isSignedIn, isLoaded } = useAuth();
  const [status, setStatus] = useState("loading"); // loading | success | error

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }
    if (!isLoaded) return;

    if (!isSignedIn) {
      const redirectUrl = encodeURIComponent(`/join/${token}`);
      navigate(`/sign-in?redirect_url=${redirectUrl}`);
      return;
    }

    (async () => {
      try {
        const res = await api.redeemShareLink(token);
        const sessionId = res.session?.sessionId || res.sessionId;
        if (!sessionId) throw new Error("Missing sessionId");
        setStatus("success");
        navigate(`/?session=${sessionId}`);
      } catch (e) {
        console.error("[JoinShareLink] Failed to redeem:", e);
        setStatus("error");
      }
    })();
  }, [token, isLoaded, isSignedIn, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="bg-card border border-border/70 rounded-3xl shadow-xl px-8 py-10 w-[420px] text-center">
        {status === "loading" && (
          <>
            <Loader2 size={28} className="mx-auto mb-4 animate-spin text-primary" />
            <h1 className="text-lg font-semibold text-foreground">Joining chat...</h1>
            <p className="text-sm text-muted-foreground mt-2">
              Please wait while we verify the invite.
            </p>
          </>
        )}
        {status === "success" && (
          <>
            <CheckCircle size={28} className="mx-auto mb-4 text-emerald-500" />
            <h1 className="text-lg font-semibold text-foreground">Invite accepted</h1>
            <p className="text-sm text-muted-foreground mt-2">Redirecting to the shared chat.</p>
          </>
        )}
        {status === "error" && (
          <>
            <XCircle size={28} className="mx-auto mb-4 text-destructive" />
            <h1 className="text-lg font-semibold text-foreground">Invite invalid</h1>
            <p className="text-sm text-muted-foreground mt-2">
              The link may be expired or revoked. Ask the owner for a new invite.
            </p>
          </>
        )}
      </div>
    </div>
  );
}

export default JoinShareLink;
