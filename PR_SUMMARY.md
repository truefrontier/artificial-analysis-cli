# Pull Request: Add Text-to-Speech (TTS) Support

## Summary

Extends `aanalysis` CLI to cover **Artificial Analysis Speech Arena / TTS leaderboard** in addition to LLM models. Parallel command structure with identical UX patterns.

**Version**: 0.1.1 → **0.2.0**  
**Tests**: 18 → **27** (all passing)  
**Breaking Changes**: None (LLM commands unchanged)

---

## New Commands

### TTS Model Listing
```bash
aanalysis tts models list
aanalysis tts models list --creator "ElevenLabs" --min-elo 1250 --limit 10
aanalysis tts models list --json --refresh
```

### TTS Digests
```bash
aanalysis tts digest smartest              # Top by Elo rating
aanalysis tts digest smart-fast            # Quality + speed (Pro tier)
aanalysis tts digest smart-cheap           # Cost efficiency (Pro tier)
aanalysis tts digest all --json            # Agent-friendly payload
```

All commands support: `--json`, `--compact`, `--csv`, `--select`, `--quiet`

---

## API Endpoints Used

### Primary Endpoint (Free Tier)
**`GET https://artificialanalysis.ai/api/v2/data/media/text-to-speech`**

Response shape:
```json
{
  "status": "success",
  "data": [
    {
      "id": "tts-1",
      "name": "ElevenLabs v4",
      "slug": "elevenlabs-v4",
      "model_creator": {
        "id": "eleven-id",
        "name": "ElevenLabs"
      },
      "elo": 1315.2,
      "rank": 1,
      "ci95": 12.5
    }
  ]
}
```

**Free tier provides**: Elo, rank, CI95 (confidence interval), name, slug, id, creator

**Pro tier adds** (when available):
- `price_per_1m_characters` (for smart-cheap digest)
- `chars_per_second` (for smart-fast digest)

### Behavior
- Free tier: Elo-based ranking works perfectly
- Pro tier digests: Gracefully exit with code 5 and clear message when pricing/speed unavailable
- No crashes, no silent failures

---

## Implementation Details

### New Modules
1. **`src/aanalysis/tts_digest.py`** (236 lines)
   - `normalize_tts_model()` - Handle creator object, ci95/ci_95 variants
   - `rank_by_elo()` - Primary ranking (smartest)
   - `rank_by_smart_fast_tts()` - z-score composite, median filtering, graceful degradation
   - `rank_by_smart_cheap_tts()` - Elo / price efficiency
   - Filters: `filter_tts_models()` by creator, min_elo

2. **`src/aanalysis/tts_output.py`** (149 lines)
   - `build_tts_table_data()` - Normalize to JSON rows (id, slug, name, elo, ci95, price, speed)
   - `output_tts_table()` - Rich tables with optional price/speed columns
   - `output_tts_models()` - Auto-detect format (TTY=table, pipe=JSON)

3. **`src/aanalysis/cli.py`** - Extended
   - New command groups: `tts_app`, `tts_models_app`, `tts_digest_app`
   - Parallel structure to LLM commands
   - Same global options pattern

4. **`src/aanalysis/client.py`** - Extended
   - `list_tts_models()` - Fetch from `/data/media/text-to-speech`
   - `fetch_all_tts_models()` - Handle `{status, data}` response shape

### Test Coverage
**New**: `tests/test_tts.py` (9 tests, all passing)
- API client tests (list, fetch, caching)
- Normalization tests
- Field extraction tests (elo, ci95, rank)
- Ranking tests (elo, smart-fast, smart-cheap)
- Filter tests (creator, min_elo)
- Graceful degradation tests (no speed, no price)

**Fixture**: `tests/fixtures/tts_models.json` (5 TTS models from Speech Arena)

---

## Example Command Output

### TTS Model List (Table)
```
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┳━━━━━━┓
┃ Rank ┃ Name              ┃ Creator    ┃ Elo   ┃ CI95 ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━╇━━━━━━┩
│ 1    │ ElevenLabs v4     │ ElevenLabs │ 1315.2│ 12.5 │
│ 2    │ Sonic 3.6         │ Cartesia   │ 1289.7│ 11.3 │
│ 3    │ Gemini 3.8 Flash  │ Google     │ 1267.4│ 10.8 │
└──────┴───────────────────┴────────────┴───────┴──────┘

Data provided by Artificial Analysis (artificialanalysis.ai)
```

### TTS Digest (JSON)
```json
[
  {
    "rank": 1,
    "id": "tts-1",
    "slug": "elevenlabs-v4",
    "name": "ElevenLabs v4",
    "creator": "ElevenLabs",
    "elo": 1315.2,
    "ci95": 12.5,
    "price_per_1m_chars": null,
    "chars_per_second": null
  }
]
```

### Free Tier Limitation (smart-cheap without Pro)
```
$ aanalysis tts digest smart-cheap
Note: Pricing data not available on free tier. Upgrade to Pro for pricing metrics.
(exit code 5)
```

---

## Verification

### All Tests Passing
```
$ pytest -v
27 passed in 0.19s

- 18 LLM tests (unchanged)
- 9 new TTS tests
```

### LLM Commands Unchanged
```
$ aanalysis digest smartest --json  # Still works
$ aanalysis models list --limit 5   # Still works
```

### TTS Commands Work
```
$ aanalysis tts models list         # Lists TTS models
$ aanalysis tts digest smartest     # Ranks by Elo
$ aanalysis tts --help              # Shows TTS command tree
```

---

## Public Leaderboard Reference

Sanity checks against https://artificialanalysis.ai/text-to-speech/leaderboard:
- ElevenLabs v4: #1, Elo ~1315 ✓
- Sonic 3.6: #2 ✓
- Gemini 3.8 Flash TTS: #3 ✓
- Qwen-Audio-3.0-TTS-Plus: top tier ✓

---

## Documentation

- **README.md**: Full TTS section with all commands and examples
- **CHANGELOG.md**: New file tracking 0.1.0 → 0.1.1 → 0.2.0
- **Commit message**: Comprehensive feature description

---

## Out of Scope (As Requested)

- ❌ Speech synthesis / audio generation (not a synthesizer)
- ❌ Speech-to-Text (STT) / Speech-to-Speech (can add later)
- ❌ OpenRouter/fal integration (TTS listing only)

---

## Breaking Changes

**None.** This is a pure feature addition. All existing LLM commands work identically.

---

## Checklist

- ✅ `aanalysis tts models list` returns real AA TTS models with Elo
- ✅ Digests (smartest/smart-fast/smart-cheap) run without error
- ✅ Smartest ranks by Elo correctly
- ✅ Smart-cheap/smart-fast degrade gracefully when Pro fields missing
- ✅ LLM commands unchanged and working
- ✅ All tests passing (27/27)
- ✅ Version bumped (0.2.0)
- ✅ README and CHANGELOG updated
- ✅ PR opened with summary

---

## Ready for Merge

This PR is ready to merge. TTS support is fully functional, well-tested, and maintains backward compatibility with all LLM commands.
