const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Auth token injection – set by the React <AuthTokenBridge /> in App.jsx
// ---------------------------------------------------------------------------
let _tokenGetter = null;

/**
 * Register a function that returns a Promise<string|null> with the Clerk
 * session token.  Called once from App.jsx via `useAuth().getToken`.
 */
export function setTokenGetter(fn) {
  _tokenGetter = fn;
}

/**
 * Wrapper around `fetch` that automatically attaches a Bearer token
 * (if authenticated) and retries on 401 if the token wasn't ready yet.
 */
async function authFetch(url, options = {}) {
  const headers = { ...(options.headers || {}) };

  // Attach auth token when available
  if (_tokenGetter) {
    try {
      const token = await _tokenGetter();
      console.log("[authFetch] Token obtained:", token ? `${token.substring(0, 20)}...` : "NULL");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      // If token is null, the Clerk session might still be loading.
      // Send the request anyway – if auth is required, the backend will
      // return 401 and we'll retry once after a short delay.
    } catch (e) {
      // Token retrieval failed – proceed without auth header
      console.warn("[authFetch] Failed to get token:", e);
    }
  }

  let response = await fetch(url, { ...options, headers });

  // If we got 401 and have a token getter, retry once after waiting for token
  if (response.status === 401 && _tokenGetter && !options._isRetry) {
    console.log("[authFetch] Got 401, retrying after waiting for token...");
    await new Promise((resolve) => setTimeout(resolve, 500));

    try {
      const token = await _tokenGetter();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
        response = await fetch(url, {
          ...options,
          headers,
          _isRetry: true,
        });
      }
    } catch (e) {
      console.warn("[authFetch] Retry failed:", e);
    }
  }

  // Surface 401s as errors after retry
  if (response.status === 401) {
    throw new Error("Authentication required");
  }

  return response;
}

export const api = {
  async analyze(sessionId, prompt) {
    if (!sessionId) throw new Error("Session ID is required");

    const response = await authFetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId,
        prompt,
      }),
    });

    if (!response.ok) throw new Error("Analysis failed");
    return response.json();
  },

  async createSession(title) {
    const response = await authFetch(`${API_BASE_URL}/sessions/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });

    if (!response.ok) throw new Error("Failed to create session");
    return response.json();
  },

  async listSessions(limit = 50, skip = 0) {
    const params = new URLSearchParams({ limit, skip });
    const response = await authFetch(`${API_BASE_URL}/sessions?${params}`);
    if (!response.ok) throw new Error("Failed to list sessions");
    return response.json();
  },

  async getSession(sessionId) {
    const response = await authFetch(`${API_BASE_URL}/sessions/${sessionId}`);
    if (!response.ok) throw new Error("Failed to get session");
    return response.json();
  },

  async deleteSession(sessionId) {
    const response = await authFetch(`${API_BASE_URL}/sessions/${sessionId}/delete`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("Failed to delete session");
    return response.json();
  },

  async renameSession(sessionId, title) {
    const response = await authFetch(`${API_BASE_URL}/sessions/${sessionId}/rename`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    if (!response.ok) throw new Error("Failed to rename session");
    return response.json();
  },

  async generateReport(promptId) {
    console.log(`[API] generateReport: requesting PDF for promptId=${promptId}`);
    const response = await authFetch(`${API_BASE_URL}/generate-report/${promptId}`, {
      method: "GET",
    });
    if (!response.ok) {
      let errorDetail = `HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || errJson.message || errorDetail;
      } catch {
        // response wasn't JSON
      }
      console.error(`[API] generateReport failed: ${errorDetail}`);
      throw new Error(`Report generation failed: ${errorDetail}`);
    }
    const blob = await response.blob();
    console.log(`[API] generateReport: received blob, size=${blob.size}, type=${blob.type}`);
    if (blob.size === 0) {
      throw new Error("Received empty PDF from server");
    }
    return blob;
  },

  /**
   * Get the URL for viewing a report inline (in iframe/modal)
   * Returns a blob URL that can be used in an iframe
   */
  async getReportViewUrl(promptId) {
    console.log(`[API] getReportViewUrl: requesting inline PDF for promptId=${promptId}`);
    const response = await authFetch(`${API_BASE_URL}/view-report/${promptId}`, {
      method: "GET",
    });
    if (!response.ok) {
      let errorDetail = `HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || errJson.message || errorDetail;
      } catch {
        // response wasn't JSON
      }
      console.error(`[API] getReportViewUrl failed: ${errorDetail}`);
      throw new Error(`Report view failed: ${errorDetail}`);
    }
    const blob = await response.blob();
    console.log(`[API] getReportViewUrl: received blob, size=${blob.size}, type=${blob.type}`);
    if (blob.size === 0) {
      throw new Error("Received empty PDF from server");
    }
    
    // Ensure blob has correct MIME type
    const pdfBlob = blob.type === 'application/pdf' ? blob : new Blob([blob], { type: 'application/pdf' });
    
    // Create a blob URL for viewing in iframe/object
    const blobUrl = URL.createObjectURL(pdfBlob);
    console.log(`[API] getReportViewUrl: created blob URL: ${blobUrl}`);
    return blobUrl;
  },

  async uploadDocument(sessionId, file) {
    if (!sessionId) throw new Error("Session ID is required");
    if (!file) throw new Error("File is required");

    const formData = new FormData();
    formData.append("file", file);

    const response = await authFetch(`${API_BASE_URL}/sessions/${sessionId}/upload-document`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(error.detail || "Failed to upload document");
    }
    return response.json();
  },

  async getDocumentInfo(sessionId) {
    const response = await authFetch(`${API_BASE_URL}/sessions/${sessionId}/document`);
    if (!response.ok) throw new Error("Failed to get document info");
    return response.json();
  },

  async deleteDocument(sessionId) {
    const response = await authFetch(`${API_BASE_URL}/sessions/${sessionId}/document`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("Failed to delete document");
    return response.json();
  },

  // ===== VOICE ASSISTANT API =====

  /**
   * Process transcribed voice text through the voice assistant
   */
  async voiceProcessText(sessionId, text, isFinal = true) {
    if (!sessionId) throw new Error("Session ID is required");

    const response = await authFetch(`${API_BASE_URL}/voice/process-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId,
        text,
        is_final: isFinal,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Voice processing failed" }));
      throw new Error(error.detail || "Failed to process voice input");
    }
    return response.json();
  },

  /**
   * Process raw audio through the voice assistant
   */
  async voiceProcessAudio(sessionId, audioBase64, audioFormat = "webm", language = "en") {
    if (!sessionId) throw new Error("Session ID is required");

    const response = await authFetch(`${API_BASE_URL}/voice/process-audio`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId,
        audio_base64: audioBase64,
        audio_format: audioFormat,
        language,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Audio processing failed" }));
      throw new Error(error.detail || "Failed to process audio");
    }
    return response.json();
  },

  /**
   * Handle voice interruption during agent speech
   */
  async voiceInterrupt(sessionId, text) {
    if (!sessionId) throw new Error("Session ID is required");

    const response = await authFetch(`${API_BASE_URL}/voice/interrupt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId,
        text,
      }),
    });

    if (!response.ok) throw new Error("Failed to process interruption");
    return response.json();
  },

  /**
   * Confirm or reject refined prompt
   */
  async voiceConfirm(sessionId, confirmed, additionalText = null) {
    if (!sessionId) throw new Error("Session ID is required");

    const response = await authFetch(`${API_BASE_URL}/voice/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId,
        confirmed,
        additional_text: additionalText,
      }),
    });

    if (!response.ok) throw new Error("Failed to process confirmation");
    return response.json();
  },

  /**
   * Get current voice state for a session
   */
  async voiceGetState(sessionId) {
    const response = await authFetch(`${API_BASE_URL}/voice/state/${sessionId}`);
    if (!response.ok) throw new Error("Failed to get voice state");
    return response.json();
  },

  /**
   * Reset voice state for a session
   */
  async voiceReset(sessionId) {
    if (!sessionId) throw new Error("Session ID is required");

    const response = await authFetch(`${API_BASE_URL}/voice/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId }),
    });

    if (!response.ok) throw new Error("Failed to reset voice state");
    return response.json();
  },

  /**
   * Mark that agent has started speaking (for TTS)
   */
  async voiceSpeakingStarted(sessionId, responseText) {
    const response = await authFetch(
      `${API_BASE_URL}/voice/speaking-started?sessionId=${sessionId}&response_text=${encodeURIComponent(responseText)}`,
      { method: "POST" },
    );
    if (!response.ok) throw new Error("Failed to mark speaking started");
    return response.json();
  },

  /**
   * Mark that agent has finished speaking
   */
  async voiceSpeakingEnded(sessionId) {
    const response = await authFetch(
      `${API_BASE_URL}/voice/speaking-ended?sessionId=${sessionId}`,
      { method: "POST" },
    );
    if (!response.ok) throw new Error("Failed to mark speaking ended");
    return response.json();
  },

  /**
   * Get intent and backchannel word lexicons
   */
  async voiceGetLexicons() {
    const response = await authFetch(`${API_BASE_URL}/voice/lexicons`);
    if (!response.ok) throw new Error("Failed to get lexicons");
    return response.json();
  },

  async executePlan(sessionId) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout for long-running agent operations

    try {
      const res = await authFetch(`${API_BASE_URL}/execute?sessionId=${sessionId}`, {
        method: "POST",
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: "Execution failed" }));
        throw new Error(errorData.detail || "Execution failed");
      }
      return res.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === "AbortError") {
        throw new Error("Request timed out. The analysis is taking longer than expected.");
      }
      throw error;
    }
  },

  async cancelPlan(sessionId) {
    const res = await authFetch(`${API_BASE_URL}/planning/cancel?sessionId=${sessionId}`, {
      method: "POST",
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: "Failed to cancel plan" }));
      throw new Error(errorData.detail || "Failed to cancel plan");
    }
    return res.json();
  },

  // ===== NEWS MONITOR API =====

  async enableNotification(sessionId, promptId, tagName = "", enabled = true) {
    const response = await authFetch(`${API_BASE_URL}/news/enable`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, promptId, tagName, enabled }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Failed" }));
      throw new Error(err.detail || "Failed to toggle notification");
    }
    return response.json();
  },

  async recheckNotification(sessionId, promptId, rerunAnalysis = false) {
    const response = await authFetch(`${API_BASE_URL}/news/recheck`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, promptId, rerunAnalysis }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Recheck failed" }));
      throw new Error(err.detail || "Recheck failed");
    }
    return response.json();
  },

  async getMonitored(sessionId) {
    const response = await authFetch(
      `${API_BASE_URL}/news/monitored?sessionId=${encodeURIComponent(sessionId)}`,
    );
    if (!response.ok) throw new Error("Failed to get monitored list");
    return response.json();
  },

  async getAllMonitored() {
    const response = await authFetch(`${API_BASE_URL}/news/monitored-all`);
    if (!response.ok) throw new Error("Failed to get all monitored");
    return response.json();
  },

  async broadcastIntel(text) {
    const response = await authFetch(`${API_BASE_URL}/news/broadcast-intel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Failed" }));
      throw new Error(err.detail || "Intel broadcast failed");
    }
    return response.json();
  },

  async acknowledgeAllNotifications(sessionIds = null) {
    const response = await authFetch(`${API_BASE_URL}/news/acknowledge-all`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionIds }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Failed" }));
      throw new Error(err.detail || "Acknowledge failed");
    }
    return response.json();
  },

  async getNotificationDetails(notificationId) {
    const response = await authFetch(
      `${API_BASE_URL}/news/details/${encodeURIComponent(notificationId)}`,
    );
    if (!response.ok) throw new Error("Failed to get notification details");
    return response.json();
  },

  // ===== COLLABORATIVE SHARING API =====

  async inviteCollaborator(sessionId, email, role = "editor") {
    const response = await authFetch(`${API_BASE_URL}/sharing/invite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, email, role }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Invite failed" }));
      throw new Error(err.detail || "Failed to invite collaborator");
    }
    return response.json();
  },

  async createShareLink(sessionId, role = "editor", expiresHours = 72) {
    const response = await authFetch(`${API_BASE_URL}/sharing/create-link`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, role, expiresHours }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Failed" }));
      throw new Error(err.detail || "Failed to create share link");
    }
    return response.json();
  },

  async redeemShareLink(token) {
    const response = await authFetch(`${API_BASE_URL}/sharing/redeem-link`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Invalid link" }));
      throw new Error(err.detail || "Failed to redeem share link");
    }
    return response.json();
  },

  async revokeShareLink(token, sessionId) {
    const response = await authFetch(`${API_BASE_URL}/sharing/revoke-link`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, sessionId }),
    });
    if (!response.ok) throw new Error("Failed to revoke link");
    return response.json();
  },

  async getShareLinks(sessionId) {
    const response = await authFetch(`${API_BASE_URL}/sharing/links/${sessionId}`);
    if (!response.ok) throw new Error("Failed to get share links");
    return response.json();
  },

  async getCollaborators(sessionId) {
    const response = await authFetch(`${API_BASE_URL}/sharing/collaborators/${sessionId}`);
    if (!response.ok) throw new Error("Failed to get collaborators");
    return response.json();
  },

  async removeCollaborator(sessionId, userId) {
    const response = await authFetch(`${API_BASE_URL}/sharing/remove-collaborator`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, userId }),
    });
    if (!response.ok) throw new Error("Failed to remove collaborator");
    return response.json();
  },

  async leaveSession(sessionId) {
    const response = await authFetch(`${API_BASE_URL}/sharing/leave`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId }),
    });
    if (!response.ok) throw new Error("Failed to leave session");
    return response.json();
  },

  async getSharedWithMe(limit = 50, skip = 0) {
    const params = new URLSearchParams({ limit, skip });
    const response = await authFetch(`${API_BASE_URL}/sharing/shared-with-me?${params}`);
    if (!response.ok) throw new Error("Failed to get shared sessions");
    return response.json();
  },

  async searchUsers(query) {
    const response = await authFetch(
      `${API_BASE_URL}/sharing/search-users?q=${encodeURIComponent(query)}`,
    );
    if (!response.ok) throw new Error("Failed to search users");
    return response.json();
  },
};

export default api;
