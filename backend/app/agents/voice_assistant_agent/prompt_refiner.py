"""
Prompt Refiner for Voice Assistant Agent

Uses LLM to generate natural conversational responses for voice interaction.
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json
import re

from crewai import LLM

# Initialize LLM - same pattern as working agents (iqvia_agent)
llm = LLM(model="groq/llama-3.3-70b-versatile", max_tokens=500)


VOICE_ASSISTANT_SYSTEM = """You are a friendly voice assistant for PharmAssist, a pharmaceutical intelligence platform.

You help users research drugs, diseases, market trends, clinical trials, and patents.

TASK: Respond naturally to the user's voice input. Be conversational and helpful.

Given the user's spoken input, analyze it and respond appropriately:

1. If they mention a DRUG (like metformin, ozempic, etc.) - acknowledge it and ask what they want to know
2. If they mention a DISEASE/CONDITION - acknowledge and ask which drug or general analysis
3. If they have BOTH drug and indication - confirm and offer to start analysis
4. If unclear - ask a simple clarifying question

CRITICAL: Your "voice_response" will be SPOKEN ALOUD to the user. Make it:
- Natural and conversational (like talking to a friend)
- Brief (1-2 sentences max)
- Helpful and warm

Return STRICT JSON only:
{
  "understood": true,
  "drug_mentioned": "<drug name or null>",
  "indication_mentioned": "<disease/condition or null>",
  "needs_clarification": true/false,
  "ready_for_planning": true/false,
  "refined_prompt": "<clear analysis request>",
  "voice_response": "<what to SAY to the user - be natural!>"
}

EXAMPLE RESPONSES (voice_response should sound like this):
- "Metformin! Great choice. Are you looking at diabetes specifically, or another condition?"
- "Sure, I can help with that diabetes market analysis. Which drug are you interested in?"
- "Perfect! Ozempic for diabetes - I'll pull up the full analysis for you. Sound good?"
- "Interesting! Tell me more - what aspect of cancer treatment would you like to explore?"

Remember: voice_response is SPOKEN, so no bullet points, no long text, just natural speech."""


@dataclass
class RefinementResult:
    """Result of prompt refinement."""
    success: bool
    understood: bool
    drug: Optional[str]
    indication: Optional[str]
    analysis_type: Optional[str]
    needs_clarification: bool
    clarifying_questions: List[str]
    refined_prompt: str
    voice_response: str
    ready_for_planning: bool = False
    error: Optional[str] = None


class PromptRefiner:
    """
    Refines transcribed voice prompts using LLM.
    """
    
    def __init__(self):
        """Initialize the prompt refiner."""
        self.llm = llm
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        # Find JSON in response
        start = response_text.find("{")
        end = response_text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON found in response")
        
        json_str = response_text[start:end + 1]
        # Clean up any control characters
        json_str = re.sub(r'[\x00-\x1f\x7f]', '', json_str)
        return json.loads(json_str)
    
    async def refine(
        self,
        text: str,
        context: Optional[str] = None
    ) -> RefinementResult:
        """
        Refine a transcribed prompt using LLM.
        """
        try:
            # Build the full prompt with system context
            full_prompt = VOICE_ASSISTANT_SYSTEM + "\n\n"
            
            # Add context if available
            if context:
                full_prompt += f"Previous conversation context:\n{context}\n\n"
            
            full_prompt += f"User said: {text}"
            
            # Call LLM using the working pattern from iqvia_agent
            print(f"[PromptRefiner] Calling LLM with: {text}")
            try:
                # Try messages format first (preferred)
                response = self.llm.call(messages=[{"role": "user", "content": full_prompt}])
            except Exception:
                # Fallback to simple string call
                response = self.llm.call(full_prompt)
            
            # Ensure response is a string
            if not isinstance(response, str):
                response = str(response)
            
            print(f"[PromptRefiner] LLM response: {response}")
            
            # Parse response
            data = self._parse_llm_response(response)
            
            # Determine if ready for planning
            has_drug = bool(data.get("drug_mentioned"))
            has_indication = bool(data.get("indication_mentioned"))
            ready = data.get("ready_for_planning", has_drug and has_indication)
            
            return RefinementResult(
                success=True,
                understood=data.get("understood", True),
                drug=data.get("drug_mentioned"),
                indication=data.get("indication_mentioned"),
                analysis_type=data.get("analysis_type"),
                needs_clarification=data.get("needs_clarification", False),
                clarifying_questions=data.get("clarifying_questions", []),
                refined_prompt=data.get("refined_prompt", text),
                voice_response=data.get("voice_response", "I'm processing your request."),
                ready_for_planning=ready
            )
            
        except Exception as e:
            print(f"[PromptRefiner] Error: {e}")
            import traceback
            traceback.print_exc()
            # Return a helpful response even on error
            return RefinementResult(
                success=True,  # Still "success" so we continue
                understood=True,
                drug=None,
                indication=None,
                analysis_type=None,
                needs_clarification=False,
                clarifying_questions=[],
                refined_prompt=text,
                voice_response=f"I heard: {text}. Let me process that for you.",
                ready_for_planning=True,  # Forward to planning anyway
                error=str(e)
            )
    
    def generate_confirmation_prompt(
        self,
        drug: str,
        indication: str,
        analysis_type: Optional[str] = None
    ) -> str:
        """Generate a spoken confirmation prompt."""
        if analysis_type:
            return f"So you want {analysis_type} analysis for {drug} in {indication}. Should I proceed?"
        return f"I'll analyze {drug} for {indication}. Ready to start?"


# Global singleton
_prompt_refiner: Optional[PromptRefiner] = None


def get_prompt_refiner() -> PromptRefiner:
    """Get or create global prompt refiner instance."""
    global _prompt_refiner
    if _prompt_refiner is None:
        _prompt_refiner = PromptRefiner()
    return _prompt_refiner
