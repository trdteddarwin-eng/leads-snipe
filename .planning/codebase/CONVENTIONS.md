# Coding Conventions

**Analysis Date:** 2026-01-17

## Naming Patterns

**Files (Python):**
- snake_case for all modules: `engine_zero.py`, `verify_email.py`
- Descriptive names: `linkedin_finder_unified.py`, `rate_limiter.py`

**Files (TypeScript/React):**
- PascalCase for components: `LeadCard.tsx`, `Header.tsx`, `Sidebar.tsx`
- camelCase for utilities: `api.ts`, `utils.ts`, `types.ts`

**Functions (Python):**
- snake_case: `verify_email()`, `check_syntax()`, `find_single()`
- Private methods with underscore: `_log()`, `_update_progress()`
- Verb-noun format: `expand_location()`, `discover_leads()`

**Functions (TypeScript):**
- camelCase: `fetchJson()`, `formatDate()`, `copyToClipboard()`
- Event handlers: `handleCopy()`, `onSelect()`

**Variables:**
- Python: snake_case (`leads_store`, `hunt_id`, `email_verified`)
- TypeScript: camelCase (`copiedField`, `isExpanded`, `activeTab`)

**Types/Classes:**
- Python: PascalCase for classes/dataclasses (`Lead`, `EngineConfig`, `HuntStage`)
- Python: SCREAMING_SNAKE for constants (`USER_AGENTS`, `EMAIL_REGEX`)
- TypeScript: PascalCase for interfaces (`Lead`, `Hunt`, `HuntDetails`)

## Code Style

**Formatting:**
- No formal formatter configured (no Prettier/Black)
- Python: 4-space indentation
- TypeScript: 2-space indentation
- Line length: ~100-120 characters

**Linting:**
- ESLint via `eslint-config-next` in leadsnipe-app
- TypeScript strict mode enabled

## Import Organization

**Python order:**
```python
# 1. Standard library
import os
import sys
import json

# 2. Third-party packages
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 3. Local imports (with try/except for path flexibility)
try:
    from engine_zero import EngineZero, EngineConfig
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from engine_zero import EngineZero, EngineConfig
```

**TypeScript order:**
```typescript
// 1. React/Next.js
import { useState, useEffect } from 'react';
import Link from 'next/link';

// 2. Third-party
import { Target, ChevronRight } from 'lucide-react';

// 3. Internal with @ alias
import { api } from '@/lib/api';
import type { Hunt } from '@/lib/types';
```

## Error Handling

**Python patterns:**
```python
# Pattern 1: Continue on failure
for item in items:
    try:
        result = process_item(item)
    except Exception as e:
        self._log(f"Error: {e}", "WARN")
        continue

# Pattern 2: Return dict with status
def verify_email(email: str) -> Dict:
    result = {"email": email, "valid": False, "reason": ""}
    # ... logic
    return result
```

**TypeScript patterns:**
```typescript
// Pattern 1: try/catch with console.error
try {
    const data = await api.getHunts();
    setHunts(data);
} catch (error) {
    console.error('Failed to fetch hunts:', error);
} finally {
    setLoading(false);
}

// Pattern 2: Throw from API layer
if (!res.ok) {
    throw new Error(`API Error: ${res.status}`);
}
```

## Logging

**Python:**
```python
def _log(self, message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)

# Levels: INFO, WARN, ERROR, SUCCESS, SCRIPT
```

**TypeScript:**
```typescript
console.error('Failed to fetch hunts:', error);
// No structured logging framework
```

## Comments

**Python docstrings:**
```python
def verify_email(email: str, do_smtp_check: bool = True) -> Dict:
    """
    Full email verification using all 3 layers.

    Args:
        email: Email address to verify
        do_smtp_check: Whether to perform SMTP verification

    Returns:
        {"email": str, "valid": bool, "deliverable": bool, "reason": str}
    """
```

**Section separators:**
```python
# ============================================================================
# Stage 1: Discovery
# ============================================================================
```

## Function Design

**Size:** Python functions typically 20-50 lines; React components 50-150 lines

**Parameters (Python):**
```python
@dataclass
class EngineConfig:
    target_leads: int = 200
    max_cities: int = 15
    hunt_id: Optional[str] = None
    add_log: Optional[Callable] = None
```

**Parameters (TypeScript):**
```typescript
interface LeadCardProps {
  lead: Lead;
  isSelected?: boolean;
  onSelect?: (id: string) => void;
  delay?: number;
}

export function LeadCard({ lead, isSelected, onSelect, delay = 0 }: LeadCardProps) {
```

## React Component Patterns

```typescript
'use client';  // Required for client components

import { useState, useEffect } from 'react';

interface ComponentProps {
  // Props definition
}

export function ComponentName({ prop1, prop2 }: ComponentProps) {
  // State hooks first
  const [state, setState] = useState(initial);

  // Effects
  useEffect(() => { ... }, [deps]);

  // Event handlers
  const handleEvent = () => { ... };

  // Render
  return (
    <div className="...">
      {/* JSX */}
    </div>
  );
}
```

**Styling:** Tailwind CSS classes inline with CSS custom properties for theming

## Data Models

**Python dataclasses:**
```python
@dataclass
class Lead:
    id: str
    name: str
    email: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
```

**TypeScript interfaces:**
```typescript
export interface Lead {
  id: string;
  name: string;
  email: string;
  decision_maker: DecisionMaker | null;
}
```

## Constants

**Environment variables:**
```python
load_dotenv()
API_KEY = os.getenv("SERPAPI_API_KEY")
```

**Module-level constants:**
```python
USER_AGENTS = [...]
EMAIL_REGEX = re.compile(...)
RATE_LIMITS = {"website": {"base_delay": 1.0}}
```

---

*Convention analysis: 2026-01-17*
