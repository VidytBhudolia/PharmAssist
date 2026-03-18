import { useState, useCallback } from "react";

/**
 * useCompareStudies — manages comparison mode state.
 *
 * Tracks:
 *  - whether comparison mode is active
 *  - the two selected chat sessions
 *  - the currently‑selected agent for each split
 */
export function useCompareStudies() {
  const [isComparing, setIsComparing] = useState(false);
  const [showSelectionModal, setShowSelectionModal] = useState(false);

  // Each slot holds { chat, agentKey }
  const [leftChat, setLeftChat] = useState(null);
  const [rightChat, setRightChat] = useState(null);
  const [leftAgent, setLeftAgent] = useState(null);
  const [rightAgent, setRightAgent] = useState(null);

  /** Open the selection modal */
  const startCompare = useCallback(() => {
    setShowSelectionModal(true);
  }, []);

  /** Called when user confirms two chats in the modal */
  const confirmSelection = useCallback((chatA, chatB) => {
    setLeftChat(chatA);
    setRightChat(chatB);
    setLeftAgent(null);
    setRightAgent(null);
    setShowSelectionModal(false);
    setIsComparing(true);
  }, []);

  /** Exit comparison mode and restore normal view */
  const exitCompare = useCallback(() => {
    setIsComparing(false);
    setLeftChat(null);
    setRightChat(null);
    setLeftAgent(null);
    setRightAgent(null);
  }, []);

  const cancelSelection = useCallback(() => {
    setShowSelectionModal(false);
  }, []);

  return {
    isComparing,
    showSelectionModal,
    leftChat,
    rightChat,
    leftAgent,
    rightAgent,

    setLeftAgent,
    setRightAgent,

    startCompare,
    confirmSelection,
    exitCompare,
    cancelSelection,
  };
}
