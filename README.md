# artificial-analysis-cli

Read-only CLI for [Artificial Analysis](https://artificialanalysis.ai) LLM data. Part of Kevin's Press / True Frontier agent-native CLI family.

**Purpose**: Quick digests over the Artificial Analysis Free Data API for picking LLMs for fractional AI lead work, coding agents, and local vs hosted API decisions.

## Installation

### Using pipx (recommended)

```bash
pipx install git+https://github.com/kevinrpressorg/artificial-analysis-cli.git
```

### Development install

```bash
git clone https://github.com/kevinrpressorg/artificial-analysis-cli.git
cd artificial-analysis-cli
pip install -e .
```

## Setup

### API Key

Get a free API key from [Artificial Analysis](https://artificialanalysis.ai) (requires login).

Configure your key:

```bash
# Interactive (secure, key hidden)
aanalysis config set-key

# From file
aanalysis config set-key --key-file ~/my-key.txt
```

The key is stored in `~/.config/artificial-analysis/api_key` with mode `0600`.

**Alternative**: Set environment variable `ARTIFICIAL_ANALYSIS_API_KEY`.

## Commands

### Version

```bash
aanalysis version
```

### Configuration

```bash
# Set API key (reads from stdin, input hidden)
aanalysis config set-key

# Set API key from file
aanalysis config set-key --key-file ~/.secrets/aa-key.txt
```

### Model Listing

```bash
# List all models
aanalysis models list

# Limit results
aanalysis models list --limit 20

# Filter by creator
aanalysis models list --creator "Anthropic"

# Minimum intelligence threshold
aanalysis models list --min-intel 80.0

# Refresh cache
aanalysis models list --refresh
```

### Digests

#### Smartest Models

Top models by intelligence index:

```bash
aanalysis digest smartest
aanalysis digest smartest --limit 5
```

#### Smart & Fast Models

Composite intelligence + speed score with Pareto frontier marked:

```bash
aanalysis digest smart-fast
aanalysis digest smart-fast --limit 10
```

#### Smart & Cheap Models

Best cost efficiency (prefer low cost per intelligence task, fallback to blended $/MTok):

```bash
aanalysis digest smart-cheap
aanalysis digest smart-cheap --limit 10
```

#### Open-Weight Models

Top open-weight models (heuristic guess) with gap vs proprietary:

```bash
aanalysis digest open
aanalysis digest open --limit 10
```

**Note**: Free tier typically lacks explicit licensing fields. Open-weight detection uses a maintained heuristic allowlist of families/creators (Llama, Qwen, DeepSeek, Mistral, Gemma, Phi, etc.). Pro tier would have authoritative licensing data.

#### Coding Models

Top models for coding (coding index when present, else intelligence among coding-focused models):

```bash
aanalysis digest coding
aanalysis digest coding --limit 10
```

#### Pick Recommendation

Get one clear recommendation with runners-up for a specific use case:

```bash
# Local deployment (open-weight, good intelligence)
aanalysis digest pick local

# Cheap API hosting
aanalysis digest pick cheap-api

# Frontier intelligence
aanalysis digest pick frontier

# Coding agent use
aanalysis digest pick coding-agent
```

#### All Digests

Run all main digests in one agent-friendly JSON payload:

```bash
aanalysis digest all --json
aanalysis digest all --json --limit 3
```

### Text-to-Speech (TTS) Models

Access Artificial Analysis Speech Arena / TTS leaderboard data.

#### TTS Model Listing

```bash
# List all TTS models
aanalysis tts models list

# Filter by creator
aanalysis tts models list --creator "ElevenLabs"

# Minimum Elo threshold
aanalysis tts models list --min-elo 1250.0

# With all output options
aanalysis tts models list --json --limit 10 --refresh
```

#### TTS Digests

**Smartest TTS Models** (by Elo rating):
```bash
aanalysis tts digest smartest
aanalysis tts digest smartest --limit 5
```

**Smart & Fast TTS** (quality + speed when available):
```bash
aanalysis tts digest smart-fast
```
Note: Speed data requires Pro tier. Free tier falls back to Elo ranking.

**Smart & Cheap TTS** (cost efficiency when available):
```bash
aanalysis tts digest smart-cheap
```
Note: Pricing data requires Pro tier. Free tier returns exit code 5.

**All TTS Digests** (agent-friendly):
```bash
aanalysis tts digest all --json
aanalysis tts digest all --json --limit 3
```

**TTS Model Fields** (free tier):
- Rank, Elo, CI95 (confidence interval)
- Name, Slug, ID, Creator
- Price per 1M chars (Pro tier only)
- Chars per second (Pro tier only)

### Output Formats

All commands support multiple output formats:

```bash
# JSON output (always used when stdout is not a TTY)
aanalysis models list --json

# Compact JSON (no indentation)
aanalysis models list --json --compact

# CSV output
aanalysis models list --csv

# Select specific fields
aanalysis models list --json --select "name,creator,intelligence_index"

# Quiet mode (minimal output, exit codes only)
aanalysis models list --quiet
```

**Human tables** (TTY output) show:
- Rank, Name, Creator
- Intelligence, Coding, Agentic indices
- Speed (tokens/sec, time to first token)
- Pricing ($/1M input, $/1M output, $/task)
- Open-weight guess
- Pareto frontier markers (smart-fast digest)

### Caching

API responses are cached in `~/.cache/aanalysis/` with a default TTL of 6 hours.

```bash
# Bust cache for fresh data
aanalysis models list --refresh
```

### Exit Codes

- `0` - Success
- `3` - Usage/config error (e.g., missing API key)
- `4` - API/authentication error
- `5` - Empty/no data

## API Reference

This CLI uses the [Artificial Analysis Free Data API v2](https://artificialanalysis.ai/api/v2):

- **Base**: `https://artificialanalysis.ai/api/v2`
- **Endpoint**: `GET /language/models/free?page=N`
- **Auth**: Header `x-api-key: <key>`
- **Rate limits**: Free tier ~100 requests/day

### Free Tier Fields (typical)

- `name`, `slug`, `model_creator`
- `evaluations.artificial_analysis_intelligence_index`
- `evaluations.artificial_analysis_coding_index` (when present)
- `evaluations.artificial_analysis_agentic_index` (when present)
- `artificial_analysis_intelligence_index_cost.cost_per_task.total_cost`
- `pricing.price_1m_input` / `pricing.price_1m_output`
- `performance.median_output_tokens_per_second`
- `performance.median_time_to_first_token_seconds`

### Response Structure

```json
{
  "meta": {
    "tier": "free",
    "intelligence_index_version": 4.3,
    "pagination": {
      "page": 1,
      "page_size": 200,
      "total_pages": 4,
      "has_more": true
    }
  },
  "data": [...]
}
```

### Model Fields

Each model in `data` includes:
- `id`, `name`, `slug`, `release_date`
- `model_creator`: `{id, name}` (object, not string)
- `evaluations` with intelligence/coding/agentic indices
- `artificial_analysis_intelligence_index_cost` with `cost_per_task.total_cost`
- `pricing` with `price_1m_input_tokens`, `price_1m_output_tokens`, cache fields
- `performance` with tokens/sec, TTFT, end-to-end time

### Digest Algorithms

**smart-fast**: z(intel) + z(log tok/s), requires intel ≥ median, marks Pareto frontier  
**smart-cheap**: intel / cost_per_task when available, else intel / ((in + 3*out)/4), requires intel ≥ median

**Note**: The CLI normalizes both `price_1m_input_tokens` and `price_1m_input` field naming variants.

## Attribution

All human output includes attribution to Artificial Analysis as required by their terms.

## Development

### Run tests

```bash
pip install -e ".[dev]"
pytest
```

### Project structure

```
src/aanalysis/
  __init__.py       # Package metadata
  cli.py            # Typer CLI app
  client.py         # API client with caching
  config.py         # Config management
  digest.py         # Analysis and ranking logic
  output.py         # Output formatting (JSON/CSV/table)

tests/
  fixtures/         # Recorded API responses
  test_client.py    # Client tests
  test_digest.py    # Digest logic tests
```

## Known Limitations (v0)

- **Login scraping**: Not implemented. Get your API key from the Artificial Analysis dashboard.
- **Media endpoints**: Image/video model analysis is out of scope for v0.
- **Pro tier features**: Free tier lacks explicit open-weights flags and some extended metrics.

## License

MIT

## Links

- [Artificial Analysis](https://artificialanalysis.ai)
- [Kevin's Press](https://kevinrpress.org)
- [True Frontier](https://truefrontier.com)

---

**Data provided by Artificial Analysis** ([artificialanalysis.ai](https://artificialanalysis.ai))
