from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse
import os
import re
import base64
from typing import ClassVar, Set

######################################################################################
# DATA SOURCE VALIDATION
######################################################################################

class URLPolicy(BaseModel):
    approved_protocols: set[str] = Field(default_factory=lambda: {"https", "http"})
    approved_domains: set[str] = Field(default_factory=lambda: {"calbears.com", "berkeley.edu"})
    disallowed_extensions: set[str] = Field(
        default_factory=lambda: {".json", ".xml", ".csv", ".zip", ".exe", ".tar", ".gz"}
    )

class ApprovedURL(BaseModel):
    url: str
    policy: URLPolicy = Field(default_factory=URLPolicy)

    @field_validator("url")
    @classmethod
    def validate_url(cls, url: str, info) -> str:
        policy: URLPolicy = info.data["policy"]
        parsed = urlparse(url)

        # 1. Enforce approved protocol
        if parsed.scheme.lower() not in policy.approved_protocols:
            raise ValueError("Unsecure protocol. HTTPS/HTTP only")

        # 2. Check approved domains (exact or subdomain)
        hostname = (parsed.hostname or "").lower()
        if not any(
            hostname == domain or hostname.endswith(f".{domain}")
            for domain in policy.approved_domains
        ):
            raise ValueError("This domain is not approved for data retrieval")

        # 3. Block disallowed file formats
        _, ext = os.path.splitext((parsed.path or "").lower())
        if ext in policy.disallowed_extensions:
            raise ValueError("This data format is not approved for data retrieval")

        return url


######################################################################################
# INPUT/QUERY VALIDATION
######################################################################################
class QueryPolicy(BaseModel):
    dangerous_patterns: list[str] = Field(default_factory=lambda: [
        r"ignore\s*(all\s*)?previous\s*instructions?",
        r"you\s*are\s*now\s*(in\s*)?developer\s*mode",
        r"system\s*override",
        r"reveal\s*prompt",
    ])

    unicode_patterns: list[str] = Field(default_factory=lambda: [
        r"(\u202b|\u202e)",               # Bidi right-to-lefts
        r"(\u2067|\u2068|\u2069)",        # BIDI isolates
    ])

    base64_patterns: list[str] = Field(default_factory=lambda: [
        r"([A-Za-z0-9+/]{4}){3,}([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?"
    ])


class ApprovedQuery(BaseModel):
    query: str = Field(min_length=10)
    policy: QueryPolicy = Field(default_factory=QueryPolicy)

    @field_validator("query")
    @classmethod
    def detect_prompt_injection(cls, v: str, info) -> str:
        policy: QueryPolicy = info.data["policy"]

        # 1. Block common prompt-injection patterns
        for pattern in policy.dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"System Prompt access risk detected: `{pattern}`")

        # 2. Block Unicode bidi control chars (text reordering tricks)
        for pattern in policy.unicode_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Unicode text-reordering detected: `{pattern}`")

        # 3. Detect suspicious Base64 payloads (possible hidden instructions)
        for pattern in policy.base64_patterns:
            for m in re.finditer(pattern, v):
                candidate = m.group(0)

                # quick filters to reduce false positives
                if len(candidate) % 4 != 0 or candidate.isalpha() or candidate.isdigit():
                    continue

                try:
                    base64.b64decode(candidate, validate=True)
                except Exception:
                    continue

                raise ValueError("Suspicious Base64-encoded content detected")

        return v