# 🎯 Simplicity First: The 3 Rules

These rules **SUPERSEDE** everything else in the instructions. When in doubt, choose simpler.

---

## Rule 1: Keep It Simple ✅

**No defensive code. No over-engineering. No premature optimization.**

### What This Means

| ❌ Don't | ✅ Do |
|----------|--------|
| Error handling for cases that won't happen | Error handling for real risks only |
| Try/except blocks "just in case" | Let exceptions bubble up (you'll catch real ones) |
| Multiple validation layers | Trust the source (your 3 groups) |
| Fancy logging/monitoring | Print to console for MVP |
| Abstract classes for "future extensibility" | Hardcode for current need |

### Examples

**❌ WRONG - Over-defensive**:
```python
def extract_signal(message: str) -> Optional[Dict[str, Any]]:
    if not message:
        raise ValueError("Message empty")
    if not isinstance(message, str):
        raise TypeError("Not a string")
    if len(message) > 10000:
        raise ValueError("Message too long")
    try:
        match = pattern.search(message)
        if not match:
            return None
        data = match.groupdict()
        # Validate each field separately
        if not data.get('stock'):
            return None
        if float(data['entry']) < 0:
            return None
        if float(data['stop_loss']) < 0:
            return None
        # ... 10 more validations
        return data
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None
```

**✅ RIGHT - Simple**:
```python
def extract_signal(message: str) -> Optional[Dict[str, Any]]:
    match = pattern.search(message)
    return match.groupdict() if match else None
```

**Why?**
- Your messages come from 3 known WhatsApp groups
- They're formatted consistently (MSK signals follow one pattern)
- You're not building an API for strangers
- If something breaks, you'll see it immediately
- Keep code simple until you see a real problem

---

## Rule 2: Don't Add Code Unless Needed 📝

**No one-time usage code. No "might be useful later" utilities. No functions with 1 caller.**

### The Simplicity Hierarchy (Use This Order)

1. **SQL Query** (best: no code, just data)
2. **Shell one-liner** (use once, then delete)
3. **Python REPL** (interactive, no file)
4. **Simple function** (<20 lines, one job)
5. **n8n node** (if workflow needs it)
6. **Module/class** (only if 3+ callers)
7. **Async/concurrent** (only if queue backs up)
8. **External service** (only if nothing else works)

**Pick the simplest option that works.**

### Examples

**❌ WRONG - Creating a script for one-time use**:
```python
# scripts/seed_symbols.py (used ONCE)
def format_symbol(s):
    return s.upper().strip()

def parse_csv(filepath):
    with open(filepath) as f:
        return [format_symbol(line) for line in f]

if __name__ == "__main__":
    symbols = parse_csv("symbols.txt")
    # Insert to DB...
```

**✅ RIGHT - Do it directly in SQL**:
```sql
-- One command, no script needed
INSERT INTO symbols (stock_name_raw, nse_symbol, occurrences)
SELECT TRIM(raw_symbol), UPPER(TRIM(raw_symbol)), 1
FROM (VALUES 
    ('reliance'),
    ('tcs'),
    ('infy')
) AS t(raw_symbol);
```

**❌ WRONG - Helper function for one caller**:
```python
def validate_entry_price(price: float) -> bool:
    """Validate that entry price is positive."""
    return price > 0

# Called once
if validate_entry_price(signal['entry']):
    insert_signal(signal)
```

**✅ RIGHT - Inline it**:
```python
if signal['entry'] > 0:
    insert_signal(signal)
```

**❌ WRONG - Creating a util module**:
```python
# utils/text_processing.py
def trim_whitespace(s):
    return s.strip()

def upper_case(s):
    return s.upper()

def format_symbol(s):
    return upper_case(trim_whitespace(s))

# Used in 1 place
symbol = format_symbol(raw_symbol)
```

**✅ RIGHT - Inline it**:
```python
symbol = raw_symbol.strip().upper()
```

### What About "One-Time" Code?

**One-time usage code should be**:
- ✅ SQL queries (run once, commit the result)
- ✅ Shell one-liners (type it, don't save it)
- ✅ Python REPL (interactive, don't save)
- ❌ NOT committed Python scripts (unless reusable)
- ❌ NOT utility functions (unless >1 caller)

**Example - Right Way**:
```bash
# One-liner to check message count (don't save this)
docker exec -i stack-postgres psql -U stackadmin -d n8n -c "SELECT COUNT(*) FROM raw_messages;"

# Or in REPL (don't save this)
python
>>> import json
>>> data = json.load(open('export.json'))
>>> print(len(data))
>>> exit()
```

---

## Rule 3: Simple Workflow, Not Complex Algorithm 🔄

**No ML. No async. No state machines. No optimization algorithms.**

### What Your Bot Actually Does

```
1. WhatsApp sends message
2. We extract signal using regex
3. We insert to database
4. Done
```

**That's it.** Everything else is overthinking.

### Examples of UNNECESSARY Complexity

**❌ WRONG - Async processing (unnecessary)**:
```python
# Why? You have 3 groups, max 20 messages/day
async def process_messages():
    tasks = [process_signal(msg) for msg in messages]
    results = await asyncio.gather(*tasks)
    return results
```

**✅ RIGHT - Simple loop**:
```python
for msg in messages:
    signal = extract_signal(msg)
    if signal:
        insert_signal(signal)
```

**❌ WRONG - State machine (unnecessary)**:
```python
class SignalProcessor:
    def __init__(self):
        self.state = "idle"
        self.processed = []
        
    def on_message(self, msg):
        if self.state == "idle":
            self.state = "processing"
            self._process(msg)
        elif self.state == "processing":
            self.processed.append(msg)
        elif self.state == "waiting":
            self._retry()
            
    def _process(self, msg):
        # 20 lines...
        self.state = "idle"
```

**✅ RIGHT - Simple if/else**:
```python
signal = extract_signal(msg)
if signal:
    insert_signal(signal)
```

**❌ WRONG - Over-generalized extraction (unnecessary)**:
```python
class SignalExtractor:
    def __init__(self):
        self.patterns = {}
        self.validators = {}
        
    def register_pattern(self, name, pattern, validator):
        self.patterns[name] = pattern
        self.validators[name] = validator
        
    def extract(self, message, pattern_type):
        pattern = self.patterns[pattern_type]
        validator = self.validators[pattern_type]
        # 30 lines of generic extraction logic
```

**✅ RIGHT - Simple one function**:
```python
def extract_signal(message: str) -> Optional[Dict]:
    match = pattern.search(message)
    return match.groupdict() if match else None
```

### The Decision Tree

```
Do you need async?
├─ Is queue backing up? NO → Don't use async
└─ YES → Use async (but this won't happen for 3 groups)

Do you need a state machine?
├─ Does the workflow have >3 steps? NO → Use if/else
└─ YES → Use a state machine (but linear workflow doesn't)

Do you need ML?
├─ Does regex miss >10% of signals? NO → Regex is enough
└─ YES → Add LLM fallback (we already did this)

Do you need an abstract class?
├─ Will there be >1 implementation? NO → Use concrete class
└─ YES → Use abstract class (but we have 1 extraction method)
```

---

## How to Apply These 3 Rules

### Before Writing ANY Code:

1. **Is this really needed?**
   - "Yes, the feature requires it" ✅
   - "It might be useful later" ❌
   - "Other projects do it" ❌
   - "Best practices say so" ❌

2. **Can I do it simpler?**
   - Can SQL replace this? (Use SQL)
   - Can a loop replace async? (Use loop)
   - Can I inline this function? (Inline it)
   - Can I hardcode this? (Hardcode it)

3. **Will this be reused?**
   - Used >1 time? Keep it as function ✅
   - Used once? Delete it after ❌
   - Used in future? Write it then ❌

### If Answer is NO to Any Question: Delete/Simplify

---

## Simplicity Checklist

Before committing code, verify:

- [ ] No try/except for hypothetical errors
- [ ] No functions with 1 caller
- [ ] No utility modules for 1 use case
- [ ] No async/concurrent unless needed
- [ ] No class hierarchies for 1 implementation
- [ ] No config constants for 1 value (hardcode it)
- [ ] No "future-proofing" abstractions
- [ ] No defensive input validation (unless real risk)
- [ ] Function <30 lines? If >30, simplify
- [ ] No comments needed? If yes, simplify

---

## Real Examples From Your Project

### ✅ Good Simplicity

**Your Phase 1 workflow** (17 nodes, well-structured)
- Simple: filter → extract → insert
- Not over-engineered
- Does exactly what's needed
- Room to add features (LLM fallback, cost tracking)

**Your symbol mapping** (190 symbols in table)
- Could've built abstract symbol manager class ❌
- Instead: simple SQL table ✅

**Your cost controls** (LLM_ENABLED=false kills it)
- Could've built complex cost limit calculator ❌
- Instead: one environment variable ✅

### ❌ Complexity to Avoid

**Don't build**:
- Generic signal extraction library (use regex function)
- Plugin system for different advisory groups (hardcode 3)
- Async message processing (no queue buildup yet)
- Trade confirmation state machine (use if/else)
- Symbol caching layer (DB is fast enough)
- Rate limiting with backoff (3 groups won't trigger it)

**If you ever need any of these**: Write it then, not now.

---

## The Bottom Line

**Your bot is a simple pipeline:**

```
INPUT: WhatsApp message
PROCESS: Regex extraction
OUTPUT: Insert to Postgres
```

**Keep code matching this simplicity.**

**When you're tempted to add complexity:**
- Ask: "Is this needed for Phase X?"
- If no: Delete it
- If yes: Use the simplest tool that works

**Complexity is a debt you pay later.**
**Simplicity is the best investment.**

---

## In Case of Doubt

**Ask yourself**:
1. Will this code be used >1 time? (No → delete)
2. Is there a simpler way? (Yes → use it)
3. Will this break without it? (No → don't add)

If all answers are "no", **delete the code**.

**Remember**: The best code is code that doesn't exist.

---

## Questions?

- **"Should I add error handling?"** → Only for real risks (API timeouts, DB connection drops). Not for "what if message is None".
- **"Should I make this a class?"** → Only if 3+ places need it. Otherwise inline the function.
- **"Should I use async?"** → Only if queue backs up. It won't (3 groups).
- **"Should I support multiple formats?"** → Only when you see need for it. Not preemptively.
- **"Should I abstract this?"** → Only if 2+ implementations needed. Not for future-proofing.

**Default answer**: Simpler is better. Ship it simple, add complexity when needed.

---

**Status**: Locked in these 3 rules. Apply them to every decision going forward. ✅
