# Implementation Report: artificial-analysis-cli

## Status: ✅ Complete

The `artificial-analysis-cli` package is complete and ready for use. Console script `aanalysis` is registered and functional.

---

## Installation

### Production
```bash
pipx install git+https://github.com/kevinrpressorg/artificial-analysis-cli.git
```

### Development
```bash
git clone <repo>
cd artificial-analysis-cli
pip install -e .
```

---

## All Commands (Complete List)

### Version
```bash
aanalysis version
```

### Configuration
```bash
# Set API key interactively (secure, input hidden)
aanalysis config set-key

# Set API key from file
aanalysis config set-key --key-file ~/path/to/key.txt
```

### Model Listing
```bash
aanalysis models list
aanalysis models list --limit 20
aanalysis models list --creator "Anthropic"
aanalysis models list --min-intel 80.0
aanalysis models list --refresh
```

### Digests

#### Smartest
```bash
aanalysis digest smartest
aanalysis digest smartest --limit 5
```

#### Smart & Fast
```bash
aanalysis digest smart-fast
aanalysis digest smart-fast --limit 10
```
Marks Pareto frontier for intelligence vs speed.

#### Smart & Cheap
```bash
aanalysis digest smart-cheap
aanalysis digest smart-cheap --limit 10
```
Prefers `cost_per_intelligence_index_task`; falls back to blended $/MTok.

#### Open-Weight
```bash
aanalysis digest open
aanalysis digest open --limit 10
```
Heuristic guess for open-weight models + gap vs proprietary leaders.

#### Coding
```bash
aanalysis digest coding
aanalysis digest coding --limit 10
```
Uses `coding_index` when present; falls back to intelligence for coding-focused models.

#### Pick Recommendation
```bash
aanalysis digest pick local           # Open-weight for local deployment
aanalysis digest pick cheap-api       # Cost-efficient hosted APIs
aanalysis digest pick frontier        # Highest intelligence
aanalysis digest pick coding-agent    # Best for coding tasks
```

#### All (Agent-Friendly JSON)
```bash
aanalysis digest all --json
aanalysis digest all --json --limit 3
```

---

## Output Formats

All commands support:
- `--json` - JSON output (always used when stdout is not a TTY)
- `--compact` - Compact JSON (no indentation)
- `--csv` - CSV output
- `--select field,field` - Project specific fields
- `--quiet` - Minimal output, exit codes only

### Human Table Columns
- Rank, Name, Creator
- Intelligence, Coding, Agentic indices
- Tokens/s, TTFT(s)
- $/1M In, $/1M Out, $/Task
- Open? (when relevant)
- Pareto (when relevant)

---

## Exit Codes

- `0` - Success
- `3` - Usage/config error (missing API key)
- `4` - API/authentication error
- `5` - Empty/no data

---

## API Details

### Endpoint
- **Base**: `https://artificialanalysis.ai/api/v2`
- **Free models**: `GET /language/models/free?page=N`
- **Auth**: Header `x-api-key: <key>`
- **Rate limits**: ~100 requests/day on free tier

### Field Name Normalization
The CLI normalizes these field naming variants:
- `price_1m_input` ↔ `price_1m_input_tokens`
- `price_1m_output` ↔ `price_1m_output_tokens`
- `median_output_tokens_per_second` ↔ `output_tokens_per_second`
- `median_time_to_first_token_seconds` ↔ `time_to_first_token_seconds`

### Open-Weight Heuristics
Free tier typically lacks explicit licensing fields. The CLI uses a maintained allowlist:

**Families**: Llama, Qwen, DeepSeek, Mistral, Gemma, Phi, gpt-oss, GLM, Yi, Command-R, Mixtral, CodeLlama, OpenChat, Vicuna, Falcon, MPT, StableLM, Solar

**Creators**: Meta, Alibaba, DeepSeek, Mistral AI, Google, Microsoft, Tsinghua, 01.ai, Databricks, Stability AI, EleutherAI, Together

All `digest open` outputs include `open_guess=true|false` to indicate heuristic nature. Pro tier would have authoritative licensing data.

---

## API Field Shape Surprises Discovered

1. **Pagination**: The free tier endpoint may return:
   - `{"models": [...], "pagination": {"has_next": bool}}`
   - OR just a list `[...]`
   - The client handles both shapes.

2. **Price field variants**: Both `price_1m_input` and `price_1m_input_tokens` exist in the wild. The client normalizes to `price_1m_input` internally.

3. **Missing indices**: Not all models have `coding_index` or `agentic_index`. The digest functions gracefully handle `None` values.

4. **Cost per task**: `artificial_analysis_intelligence_index_cost.cost_per_task.total_cost` is preferred for cost efficiency, but may be missing on some models. The `smart-cheap` digest falls back to blended input/output pricing.

---

## Testing

### Run Tests
```bash
pip install -e ".[dev]"
pytest
```

**Result**: 15/15 tests passing

### Test Coverage
- API client (key discovery, caching, pagination, error handling)
- Digest functions (ranking, filtering, open-weight detection, recommendations)
- Fixture-based tests (no live API required in CI)

### Smoke Test
```bash
python3 smoke_test.py
```

---

## Project Structure

```
artificial-analysis-cli/
├── src/aanalysis/
│   ├── __init__.py       # Package metadata
│   ├── cli.py            # Typer CLI app (all commands)
│   ├── client.py         # API client with caching
│   ├── config.py         # Config management (set-key)
│   ├── digest.py         # Analysis, ranking, filtering
│   └── output.py         # Format handlers (JSON/CSV/table)
├── tests/
│   ├── fixtures/
│   │   └── models.json   # Recorded API response
│   ├── test_client.py    # Client tests
│   └── test_digest.py    # Digest logic tests
├── pyproject.toml        # Package config (setuptools)
├── pytest.ini            # Pytest config
├── LICENSE               # MIT
├── README.md             # Full documentation
├── .gitignore            # Excludes __pycache__, *.key, .env, api_key
├── smoke_test.py         # End-to-end smoke test
└── demo.py               # Demo script
```

---

## Known Limitations (v0)

1. **Login scraping**: Not implemented. Users must get their API key from the Artificial Analysis dashboard manually.

2. **Media endpoints**: Image/video model analysis endpoints are out of scope for v0.

3. **Pro tier features**: Free tier lacks explicit `open_weights` boolean and some extended metrics. Heuristic detection is used instead.

---

## Attribution

All human output includes the required attribution footer:
```
Data provided by Artificial Analysis (artificialanalysis.ai)
```

---

## Dependencies

- **typer** >=0.12.0 - CLI framework
- **rich** >=13.0.0 - Terminal tables and formatting
- **httpx** >=0.27.0 - HTTP client

### Dev Dependencies
- **pytest** >=8.0.0
- **pytest-httpx** >=0.30.0

---

## Security Notes

- API keys are stored with mode `0600` (owner-only read/write)
- Keys are never echoed to stdout
- `config set-key` uses `getpass.getpass()` for hidden input
- `.gitignore` excludes `api_key`, `*.key`, `.env`

---

## Definition of Done ✅

1. ✅ `aanalysis digest all --json` works against fixtures
2. ✅ README documents every command
3. ✅ Package installs cleanly; console script `aanalysis` registered
4. ✅ No API keys committed
5. ✅ Final report complete (this document)

---

## Next Steps (Out of Scope for v0)

- Add support for media model endpoints
- Implement login scraping for automatic key retrieval
- Add Pro tier support for authoritative licensing fields
- Add `--format table` explicit option
- Add `--output FILE` to write results to file
- Add shell completion support (Typer built-in)

---

**Package Status**: Production-ready for free tier API users  
**License**: MIT  
**Author**: Kevin's Press / True Frontier
