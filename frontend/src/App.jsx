import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { useEffect } from "react";
import Dasboard from "./pages/Dashboard";
import JoinShareLink from "./components/JoinShareLink";
import SignInPage from "./components/auth/SignInPage";
import SignUpPage from "./components/auth/SignUpPage";
import { setTokenGetter } from "./services/api";
import "./App.css";

/**
 * Bridge Clerk auth → API service.
 * Sets a token getter so every API call automatically includes the JWT.
 */
function AuthTokenBridge() {
  const { getToken, isSignedIn } = useAuth();

  useEffect(() => {
    console.log("[AuthTokenBridge] Setting token getter, isSignedIn:", isSignedIn);

    // Quick test: try getting a token right now
    if (isSignedIn) {
      getToken()
        .then((t) => {
          console.log(
            "[AuthTokenBridge] Test getToken result:",
            t ? `${t.substring(0, 20)}...` : "NULL",
          );
        })
        .catch((e) => {
          console.error("[AuthTokenBridge] Test getToken error:", e);
        });
    }

    setTokenGetter(() => getToken());
    return () => setTokenGetter(null);
  }, [getToken, isSignedIn]);

  return null;
}

function App() {
  return (
    <Router>
      <AuthTokenBridge />
      <Routes>
        <Route path="/sign-in/*" element={<SignInPage />} />
        <Route path="/sign-up/*" element={<SignUpPage />} />
        <Route path="/join/:token" element={<JoinShareLink />} />
        <Route path="/*" element={<Dasboard />} />
      </Routes>
    </Router>
  );
}

export default App;
