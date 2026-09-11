import re
import string
from typing import List

# Essential stop words to remove, while keeping critical negation and action terms
DEFAULT_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most",
    "my", "myself", "of", "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

# Negations to KEEP for sentiment and problem detection
PRESERVE_WORDS = {"not", "no", "cannot", "cant", "down", "off", "error", "fail", "failed", "broken", "stop", "stopped"}
ACTIVE_STOPWORDS = DEFAULT_STOPWORDS - PRESERVE_WORDS


def clean_text(text: str) -> str:
    """
    Clean and normalize text:
    1. Lowercase
    2. Remove URLs, file paths, IP addresses (or normalize them)
    3. Remove punctuation except dashes
    4. Normalize whitespace
    5. Filter out common stopwords while keeping negation signals
    """
    if not text:
        return ""

    text = text.lower()

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    # Remove IP addresses
    text = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", " ipaddress ", text)
    # Remove hex codes / error memory addresses like 0xc0000005
    text = re.sub(r"0x[0-9a-fA-F]+", " errorcode ", text)
    # Remove punctuation except letters and numbers
    text = re.sub(r"[^\w\s-]", " ", text)
    # Normalize whitespaces
    tokens = text.split()

    # Remove stopwords
    filtered_tokens = [t for t in tokens if t not in ACTIVE_STOPWORDS and len(t) > 1]

    return " ".join(filtered_tokens)


def combine_ticket_text(title: str, description: str) -> str:
    """
    Format and clean ticket title and description together.
    We give extra weight to title by repeating it or using clear structural indicators.
    """
    clean_t = clean_text(title)
    clean_d = clean_text(description)
    return f"TITLE: {clean_t} TITLE: {clean_t} DESCRIPTION: {clean_d}".strip()
