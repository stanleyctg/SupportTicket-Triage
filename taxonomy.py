"""
All rule definitions live here. To add a new category, subcategory,
or urgency signal, this is the only file that needs to change.
"""

TAXONOMY: dict = {
    "Model Output": {
        "Hallucination": {
            "base_priority": "High",
            "keywords": [
                "hallucin", "fabricat", "made up", "doesn't exist", "do not exist",
                "citing sources", "fictional", "wrong answers", "making up",
                "confidently citing", "invented", "fabricated case",
            ],
        },
        "Inconsistency": {
            "base_priority": "High",
            "keywords": [
                "inconsisten", "different answer", "same question", "deterministic",
                "non deterministic", "output varies", "different output",
                "different behaviour same prompt",
            ],
        },
        "Bias": {
            "base_priority": "High",
            "keywords": [
                "bias", "different behaviour", "male or female", "gender",
                "discriminat", "unfair", "prejudic",
            ],
        },
        "Context Window": {
            "base_priority": "Medium",
            "keywords": [
                "context window", "forget", "lost context", "long conversation",
                "earlier parts", "message 15", "message 20",
            ],
        },
        "Quality": {
            "base_priority": "Medium",
            "keywords": [
                "verbose", "too long", "quality", "tone", "non english",
                "german", "multilingual", "hard to read", "different tones",
                "output quality", "technically correct",
            ],
        },
    },
    "Integration": {
        "API Timeout": {
            "base_priority": "High",
            "keywords": [
                "timeout", "timed out", "timing out", "30 seconds",
                "large batch", "large payload",
            ],
        },
        "API Error": {
            "base_priority": "High",
            "keywords": [
                "429", "500 error", "rate limit", "malformed json",
                "constantly getting", "intermittent error", "error code",
            ],
        },
        "Authentication": {
            "base_priority": "High",
            "keywords": [
                "api key", "stopped working", "key rotation", "authenticat",
                "rotate", "credentials", "securely",
            ],
        },
        "Webhook": {
            "base_priority": "Low",
            "keywords": [
                "webhook", "webhooks", "not firing", "real time notification",
                "batch processing completes", "job completes",
            ],
        },
        "Data Format": {
            "base_priority": "Low",
            "keywords": [
                "markdown", "plain text", "output format", "inconsistent format",
                "sometimes markdown", "format explicitly",
            ],
        },
        "SDK": {
            "base_priority": "Low",
            "keywords": [
                "sdk", "deprecation", "deprecation warning",
                "python sdk", "latest sdk",
            ],
        },
    },
    "Performance": {
        "Latency": {
            "base_priority": "Medium",
            "keywords": [
                "latency", "slow response", "response time", "response times",
                "doubled", "averaging", "unusable", "getting worse",
            ],
        },
        "Throughput": {
            "base_priority": "Medium",
            "keywords": [
                "throughput", "per hour", "documents per hour", "document length",
                "concurren", "paralleliz", "degrade", "performance degrade",
            ],
        },
    },
    "Billing": {
        "Overage Charges": {
            "base_priority": "Low",
            "keywords": [
                "overage", "unexpected charge", "token count",
                "token counting", "usage looked normal",
            ],
        },
        "Disputed Charge": {
            "base_priority": "Medium",
            "keywords": [
                "disputed", "didn't use", "paused subscription",
                "charged for a month", "didn't use the service",
            ],
        },
        "Pricing": {
            "base_priority": "Low",
            "keywords": [
                "pro vs", "enterprise plan", "plan comparison",
                "difference between", "plan features",
            ],
        },
        "Invoice": {
            "base_priority": "Low",
            "keywords": [
                "invoice", "download invoice", "how do i download",
            ],
        },
    },
    "Safety": {
        "Content Filter": {
            "base_priority": "High",
            "keywords": [
                "content filter", "filter", "blocked", "compliance quer",
                "sensitive but legal", "constant blocks",
                "filters flagging", "not configured",
            ],
        },
    },
    "Onboarding": {
        "Setup": {
            "base_priority": "Low",
            "keywords": [
                "getting started", "setup", "fine tun", "fine-tun",
                "prompt engineer", "how to structure", "best results",
                "structure prompts", "documentation confusing",
            ],
        },
        "Training": {
            "base_priority": "Low",
            "keywords": [
                "training session", "new team", "team members",
            ],
        },
    },
    "Account": {
        "Cancellation": {
            "base_priority": "High",
            "keywords": [
                "cancel", "cancell", "data export", "process cancellation",
                "switching provider", "switch provider",
            ],
        },
    },
}

# Priority levels in ascending order, used for comparison and bumping
PRIORITY_ORDER: list = ["Low", "Medium", "High", "Critical"]

# Recurrence: bump priority up one level when prior ticket count hits this
RECURRENCE_BUMP_THRESHOLD: int = 2

# Urgency signals that override the inferred priority upward.
# Checked after base priority and recurrence bump are applied.
CRITICAL_SIGNALS: list = [
    r"legal\b",
    r"formal.?complaint",
    r"sla.?compensation",
    r"issuing.?complaint",
    r"lawsuit",
]

HIGH_SIGNALS: list = [
    r"threaten.?cancel",
    r"threatening\s+to\s+cancel",
    r"going.?live",
    r"live.?with.?bug",
    r"now.?live",
    r"completely.?unusable",
    r"no.?response.?to.?previous",
    r"real.?harm",
    r"causing.?harm",
]

# Known data quality issues in the source CSV: normalised on ingest
SUBCATEGORY_CORRECTIONS: dict = {
    "setup":    "Setup",           # TKT-027: lowercase inconsistency
    "overage":  "Overage Charges", # TKT-043: truncated subcategory name
    "webhooks": "Webhook",         # TKT-036: plural vs singular
}
