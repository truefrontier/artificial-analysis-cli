# Changelog

All notable changes to artificial-analysis-cli will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-29

### Added
- **Text-to-Speech (TTS) support**: Full TTS model commands parallel to LLM commands
  - `aanalysis tts models list` - List TTS models from Speech Arena
  - `aanalysis tts digest smartest` - Top models by Elo rating
  - `aanalysis tts digest smart-fast` - Quality + speed composite (Pro tier)
  - `aanalysis tts digest smart-cheap` - Cost efficiency (Pro tier)
  - `aanalysis tts digest all` - All TTS digests in one JSON payload
- TTS model fields: Elo, CI95, rank, price per 1M chars (Pro), chars/sec (Pro)
- Graceful degradation when Pro-tier fields (price/speed) unavailable
- 9 new tests for TTS functionality (all passing)
- TTS documentation in README
- Exit code 5 for empty/no data when Pro fields required but missing

### Changed
- Version bumped to 0.2.0 (new feature: TTS)
- CLI now has parallel command structure: LLM (`models`, `digest`) and TTS (`tts models`, `tts digest`)

### Technical
- New modules: `tts_digest.py`, `tts_output.py`
- Extended `client.py` with TTS endpoints: `/data/media/text-to-speech`
- TTS fixtures and comprehensive test coverage
- All 27 tests passing (18 LLM + 9 TTS)

## [0.1.1] - 2026-09-23

### Fixed
- **CRITICAL**: Pagination stops after page 1 - Now checks top-level `pagination` object and tolerates both `has_more` and `has_next`
- Digest JSON lacks `slug` and `id` - Now included in all table/JSON/CSV output

### Changed
- Version bumped to 0.1.1 (bug fixes)

### Added
- Test for top-level pagination with 2-page fixture

## [0.1.0] - 2026-09-23

### Added
- Initial release
- LLM model listing and filtering
- 7 digest commands: smartest, smart-fast, smart-cheap, open, coding, pick, all
- Multiple output formats: JSON, CSV, tables
- Caching with 6h TTL
- API key management
- Full test suite (18 tests)
- Documentation (README, implementation report, API verification)
