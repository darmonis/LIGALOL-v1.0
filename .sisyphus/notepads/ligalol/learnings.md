# LIGALOL Learnings

## Config Module (2026-05-11)

### Pattern Established
- Config files: `config/players.json`, `config/.env.example`
- Loader: `src/config_loader.py` with `load_players()` and `load_config()`
- Uses `python-dotenv` for env variables

### Player JSON Structure
```json
[
  {"game_name": "Player1", "tag_line": "EUW"}
]
```

### Validation
- `load_players()` validates required fields: `game_name`, `tag_line`
- Raises `ValueError` with index info if missing
- Raises `FileNotFoundError` if players.json missing

### Dependencies
- Only `python-dotenv` for env loading