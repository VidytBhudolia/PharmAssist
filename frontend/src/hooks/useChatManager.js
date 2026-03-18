import { useState, useEffect, useCallback } from "react";
import { api } from "../services/api";

const MAX_CHATS = 50;

/**
 * @param {{ enabled?: boolean }} options
 *   Pass `enabled: false` to skip loading sessions (e.g. user not signed in).
 */
export function useChatManager({ enabled = true } = {}) {
  const [chats, setChats] = useState([]);
  const [sharedWithMe, setSharedWithMe] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (enabled) {
      loadChatsFromDB();
      loadSharedSessions();
    } else {
      // Not authenticated – reset to empty
      setChats([]);
      setSharedWithMe([]);
      setActiveChatId(null);
      setIsLoaded(true);
    }
  }, [enabled]);

  const loadChatsFromDB = async () => {
    try {
      console.log("[ChatManager] Loading sessions from API...");
      const response = await api.listSessions(MAX_CHATS, 0);
      console.log("[ChatManager] API response:", response);

      let validSessions = [];
      if (response.status === "success" && response.sessions) {
        validSessions = response.sessions.filter((session) => session && session.sessionId);
      } else if (Array.isArray(response)) {
        validSessions = response.filter((session) => session && session.sessionId);
      }

      // Set initial sessions immediately so sidebar renders
      setChats(validSessions);

      // Fetch full session details in background to get chatHistory/message counts
      if (validSessions.length > 0) {
        const fullSessions = await Promise.all(
          validSessions.map(async (session) => {
            try {
              const res = await api.getSession(session.sessionId);
              if (res.status === "success" && res.session && res.session.sessionId) {
                return res.session;
              }
              return session;
            } catch {
              return session;
            }
          }),
        );
        setChats(fullSessions);
      }
    } catch (e) {
      console.error("[ChatManager] Failed to load sessions:", e);
      setChats([]);
    } finally {
      setIsLoaded(true);
    }
  };

  const loadSharedSessions = async () => {
    try {
      const res = await api.getSharedWithMe();
      const sessions = (res.sessions || []).filter((s) => s && s.sessionId);
      setSharedWithMe(
        sessions.map((s) => ({
          ...s,
          isShared: true,
          id: s.sessionId,
          messages: s.chatHistory || [],
          updatedAt: s.updatedAt || s.createdAt || new Date().toISOString(),
        })),
      );
    } catch (e) {
      console.error("[ChatManager] Failed to load shared sessions:", e);
    }
  };

  const activeChat =
    chats.find((c) => c.sessionId === activeChatId) ||
    sharedWithMe.find((c) => c.sessionId === activeChatId) ||
    null;

  const createChatFromPrompt = useCallback(async (firstPrompt) => {
    setIsLoading(true);
    try {
      console.log("[ChatManager] Creating chat with prompt:", firstPrompt);
      const title = firstPrompt.trim().substring(0, 40);
      const createRes = await api.createSession(title);
      console.log("[ChatManager] Create session response:", createRes);
      const sessionId = createRes.sessionId;

      const optimisticSession = {
        sessionId,
        title,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        chatHistory: [
          {
            id: `temp-user-${Date.now()}`,
            role: "user",
            content: firstPrompt,
            timestamp: new Date().toISOString(),
          },
        ],
      };

      setChats((prev) => [optimisticSession, ...prev.filter((c) => c.sessionId !== sessionId)]);
      setActiveChatId(sessionId);
      localStorage.setItem("activeSessionId", sessionId);

      // Send first prompt immediately
      console.log("[ChatManager] Sending analyze request...");
      const analyzeRes = await api.analyze(sessionId, firstPrompt);
      console.log("[ChatManager] Analyze response:", analyzeRes);

      // Backend returns full session
      const session = analyzeRes.session;
      console.log("[ChatManager] Session from analyze:", session);
      console.log("[ChatManager] AgentsData structure:", session?.agentsData);
      if (session?.agentsData && Array.isArray(session.agentsData)) {
        console.log(
          "[ChatManager] Latest agents entry:",
          session.agentsData[session.agentsData.length - 1],
        );
      }

      if (session && session.sessionId) {
        console.log("[ChatManager] Adding session to chats:", session);
        setChats((prev) => [session, ...prev.filter((c) => c.sessionId !== session.sessionId)]);
        setActiveChatId(session.sessionId);
        localStorage.setItem("activeSessionId", session.sessionId);
      } else {
        console.error("[ChatManager] Invalid session returned:", session);
        throw new Error("Invalid session returned from server");
      }

      // Return session, queryType, and plan so caller can handle planning state
      return {
        session,
        queryType: analyzeRes.queryType,
        plan: analyzeRes.plan,
        response: analyzeRes.response,
      };
    } catch (error) {
      console.error("[ChatManager] Error in createChatFromPrompt:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendPrompt = useCallback(
    async (prompt) => {
      if (!activeChatId) return { queryType: null };

      setIsLoading(true);
      const currentActiveChat = activeChat;
      const fallbackChatSnapshot = currentActiveChat
        ? {
            ...currentActiveChat,
            chatHistory: [...(currentActiveChat.chatHistory || [])],
          }
        : null;

      const optimisticMessage = {
        id: `temp-user-${Date.now()}`,
        role: "user",
        content: prompt,
        timestamp: new Date().toISOString(),
      };

      setChats((prev) =>
        prev.map((c) =>
          c.sessionId === activeChatId
            ? {
                ...c,
                chatHistory: [...(c.chatHistory || []), optimisticMessage],
                updatedAt: new Date().toISOString(),
              }
            : c,
        ),
      );
      setSharedWithMe((prev) =>
        prev.map((c) =>
          c.sessionId === activeChatId
            ? {
                ...c,
                chatHistory: [...(c.chatHistory || []), optimisticMessage],
                messages: [...(c.chatHistory || []), optimisticMessage],
                updatedAt: new Date().toISOString(),
              }
            : c,
        ),
      );

      try {
        const response = await api.analyze(activeChatId, prompt);

        // Always replace entire session
        const updatedSession = response.session;

        if (updatedSession && updatedSession.sessionId) {
          setChats((prev) =>
            prev.map((c) => (c.sessionId === updatedSession.sessionId ? updatedSession : c)),
          );
          setSharedWithMe((prev) =>
            prev.map((c) =>
              c.sessionId === updatedSession.sessionId
                ? {
                    ...c,
                    ...updatedSession,
                    isShared: true,
                    id: updatedSession.sessionId,
                    messages: updatedSession.chatHistory || [],
                    updatedAt:
                      updatedSession.updatedAt ||
                      updatedSession.createdAt ||
                      new Date().toISOString(),
                  }
                : c,
            ),
          );
        }

        // Return queryType and plan so caller can handle planning state
        return {
          queryType: response.queryType,
          plan: response.plan,
          response: response.response,
        };
      } catch (error) {
        if (fallbackChatSnapshot?.sessionId) {
          setChats((prev) =>
            prev.map((c) =>
              c.sessionId === fallbackChatSnapshot.sessionId ? fallbackChatSnapshot : c,
            ),
          );
          setSharedWithMe((prev) =>
            prev.map((c) =>
              c.sessionId === fallbackChatSnapshot.sessionId
                ? {
                    ...c,
                    ...fallbackChatSnapshot,
                    isShared: true,
                    id: fallbackChatSnapshot.sessionId,
                    messages: fallbackChatSnapshot.chatHistory || [],
                    updatedAt:
                      fallbackChatSnapshot.updatedAt ||
                      fallbackChatSnapshot.createdAt ||
                      new Date().toISOString(),
                  }
                : c,
            ),
          );
        }
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [activeChatId, activeChat],
  );

  const selectChat = useCallback(async (sessionId) => {
    if (!sessionId) {
      // Clear active chat to show landing page
      console.log("[ChatManager] Clearing active chat to show landing page");
      setActiveChatId(null);
      localStorage.removeItem("activeSessionId");
      return;
    }

    setActiveChatId(sessionId);
    localStorage.setItem("activeSessionId", sessionId);

    try {
      const response = await api.getSession(sessionId);
      if (response.status === "success" && response.session && response.session.sessionId) {
        const session = response.session;
        setChats((prev) => prev.map((c) => (c.sessionId === sessionId ? session : c)));
        setSharedWithMe((prev) =>
          prev.map((c) =>
            c.sessionId === sessionId
              ? {
                  ...c,
                  ...session,
                  isShared: true,
                  id: session.sessionId,
                  messages: session.chatHistory || [],
                  updatedAt: session.updatedAt || session.createdAt || new Date().toISOString(),
                }
              : c,
          ),
        );
      }
    } catch (error) {
      console.error("[ChatManager] Error selecting chat:", error);
    }
  }, []);

  const updateChatSession = useCallback((session) => {
    if (session && session.sessionId) {
      setChats((prev) => prev.map((c) => (c.sessionId === session.sessionId ? session : c)));
      setSharedWithMe((prev) =>
        prev.map((c) =>
          c.sessionId === session.sessionId
            ? {
                ...c,
                ...session,
                isShared: true,
                id: session.sessionId,
                messages: session.chatHistory || [],
                updatedAt: session.updatedAt || session.createdAt || new Date().toISOString(),
              }
            : c,
        ),
      );
    }
  }, []);

  const deleteChat = useCallback(
    async (sessionId) => {
      try {
        await api.deleteSession(sessionId);
      } catch {
        console.log("Error in deleteChat");
      }

      setChats((prev) => prev.filter((c) => c.sessionId !== sessionId));

      if (sessionId === activeChatId) {
        setActiveChatId(null);
        localStorage.removeItem("activeSessionId");
      }
    },
    [activeChatId],
  );

  const renameChat = useCallback(async (sessionId, newTitle) => {
    try {
      await api.renameSession(sessionId, newTitle);
      
      // Update chat title in local state
      setChats((prev) =>
        prev.map((c) =>
          c.sessionId === sessionId
            ? { ...c, title: newTitle, updatedAt: new Date().toISOString() }
            : c,
        ),
      );
      
      setSharedWithMe((prev) =>
        prev.map((c) =>
          c.sessionId === sessionId
            ? { ...c, title: newTitle, updatedAt: new Date().toISOString() }
            : c,
        ),
      );
    } catch (error) {
      console.error("[ChatManager] Error renaming chat:", error);
      throw error;
    }
  }, []);

  return {
    chats,
    sharedWithMe,
    activeChat,
    activeChatId,
    isLoaded,
    isLoading,

    // Core actions
    createChatFromPrompt,
    sendPrompt,
    selectChat,
    deleteChat,
    renameChat,
    updateChatSession,
    loadSharedSessions,
  };
}
