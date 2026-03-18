"""
Relevance Matcher — Use LLM to extract keywords from intel and match against chats.

Functions
---------
extract_keywords_from_intel(intel_text: str) -> List[str]
    Use LLM to extract relevant keywords (drugs, companies, regulatory terms) from intel text.

is_chat_relevant(keywords: List[str], chat_title: str, prompt_text: str) -> bool
    Check if any keywords match the chat title or prompt text (case-insensitive).
"""

from typing import List, Optional
import re


def extract_keywords_from_intel(intel_text: str, llm_client=None) -> List[str]:
    """
    Use LLM to extract relevant pharmaceutical keywords from intel text.
    
    Returns a list of normalized keywords (drug names, company names, regulatory terms).
    Falls back to simple extraction if LLM is unavailable.
    """
    if not intel_text or not intel_text.strip():
        return []
    
    # If LLM client is provided, use it for intelligent extraction
    if llm_client:
        try:
            system_prompt = """You are a pharmaceutical intelligence keyword extractor. Your job is to identify ALL drug names, company names, and regulatory terms mentioned in text.

IMPORTANT RULES:
1. Extract EVERY drug name (generic and brand), even partial mentions
2. Extract ALL company/manufacturer names
3. Extract regulatory terms (ban, approval, recall, shortage, warning, restriction)
4. Extract disease/condition names
5. Include common misspellings and variations
6. Be generous - include anything that could be pharmaceutical-related
7. Return LOWERCASE keywords only

Examples:
- "semaglutide banned" → semaglutide, banned, ban
- "Pfizer recalls azithromycin" → pfizer, azithromycin, recall, recalled
- "shortage of amoxicillin" → amoxicillin, shortage"""

            user_prompt = f"""Extract ALL pharmaceutical keywords from this text. Return a comma-separated list.

Text: {intel_text}

Keywords (comma-separated, lowercase):"""

            response = llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=300,
            )
            
            result = response.choices[0].message.content.strip()
            
            if result and result.upper() != "NONE":
                # Parse comma-separated keywords
                keywords = [kw.strip().lower() for kw in result.split(",") if kw.strip()]
                return keywords
        except Exception as e:
            print(f"LLM extraction failed, falling back to simple extraction: {e}")
    
    # Fallback: Comprehensive keyword extraction using regex and common patterns
    keywords = []
    text_lower = intel_text.lower()
    
    # Major drug class suffixes (comprehensive list)
    drug_suffixes = [
        # Antibiotics
        'mycin', 'cillin', 'cycline', 'floxacin', 'oxacin', 'azole',
        # Biologics
        'mab', 'zumab', 'umab', 'ximab', 'tumumab',
        # Small molecules
        'nib', 'tinib', 'afenib', 'ciclib',
        # Peptides
        'tide', 'glutide', 'natide',
        # Cardiovascular
        'olol', 'pril', 'sartan', 'dipine',
        # Others
        'statin', 'prazole', 'afil', 'prost', 'vir', 'dipine',
        # Anti-inflammatory  
        'coxib', 'profen',
        # Diabetes
        'formin', 'gliflozin', 'gliptin'
    ]
    
    # Build comprehensive drug pattern (case-insensitive)
    suffix_pattern = '|'.join(drug_suffixes)
    drug_pattern = rf'\b\w*(?:{suffix_pattern})\b'
    drugs = re.findall(drug_pattern, text_lower, re.IGNORECASE)
    keywords.extend([d.lower() for d in drugs if len(d) > 4])
    
    # Extract capitalized words (potential drug/company names) - case-insensitive
    # Match words that are 5+ characters
    word_pattern = r'\b[a-zA-Z]{5,}\b'
    potential_drugs = re.findall(word_pattern, intel_text, re.IGNORECASE)
    keywords.extend([w.lower() for w in potential_drugs])
    
    # Add regulatory keywords if present (with variations)
    regulatory_terms = [
        'ban', 'banned', 'banning', 'approval', 'approved', 'approve',
        'recall', 'recalled', 'recalling', 'fda', 'ema', 'regulatory',
        'warning', 'restriction', 'restricted', 'shortage', 'shortages',
        'withdrawal', 'withdrawn', 'suspend', 'suspended'
    ]
    for term in regulatory_terms:
        if term in text_lower:
            keywords.append(term)
    
    # Deduplicate and return (filter out very common words)
    common_words = {'have', 'been', 'been', 'that', 'this', 'from', 'with', 'will', 'would', 'should'}
    keywords = [k for k in set(keywords) if k not in common_words and len(k) > 2]
    
    return list(set(keywords))


def is_chat_relevant(keywords: List[str], chat_title: str, prompt_text: str, agent_data_str: str = "") -> bool:
    """
    Check if any keywords match the chat content (case-insensitive).
    
    Args:
        keywords: List of extracted keywords from intel
        chat_title: Title of the chat
        prompt_text: The research prompt text
        agent_data_str: Stringified agent data (optional, for deeper matching)
    
    Returns:
        True if at least one keyword matches, False otherwise
    """
    if not keywords:
        return False
    
    # Combine all searchable text
    searchable_text = f"{chat_title} {prompt_text} {agent_data_str}".lower()
    
    # Check for any keyword match
    for keyword in keywords:
        if keyword.lower() in searchable_text:
            return True
    
    return False


def get_matching_keywords(keywords: List[str], chat_title: str, prompt_text: str, agent_data_str: str = "") -> List[str]:
    """
    Return the list of keywords that actually matched the chat content.
    Useful for logging/debugging which keywords triggered the match.
    """
    if not keywords:
        return []
    
    searchable_text = f"{chat_title} {prompt_text} {agent_data_str}".lower()
    matched = []
    
    for keyword in keywords:
        if keyword.lower() in searchable_text:
            matched.append(keyword)
    
    return matched
