# Redfox API Key Guide

Every plugin in this repository calls the [Redfox](https://redfox.hk) API for
data fetching, video parsing and AI generation. You need one free API key for
all of them.

## Get Your Key

1. Visit **https://redfox.hk/settings/api-keys?source=github**
2. Sign up / sign in
3. Create an API key and copy it (`rf-...`)

## Configure Your Key

### Option 1: Environment variable (recommended, works everywhere)

```bash
# ~/.zshrc or ~/.bashrc
export REDFOX_API_KEY="rf-your-key-here"
```

Then restart your terminal and the AI client.

### Option 2: Platform plugin settings

| Platform | Where to fill |
|---|---|
| Cursor | Prompted on install (declared via `variables` in `.cursor-plugin/plugin.json`), or Settings → Plugins → Redfox plugin |
| Gemini CLI | Prompted on first run (declared via `settings` in `gemini-extension.json`) |
| Claude Code | Environment variable (Option 1) |
| Codex | Environment variable (Option 1) |

## Security Notes

- **Never commit your API key** to this or any repository
- The key is sent only to `https://redfox.hk` over HTTPS
- Revoke or rotate keys anytime at https://redfox.hk/settings/api-keys

## Pricing

Skills are free to install. API usage is metered — see
https://redfox.hk/pricing for current rates and free-tier quotas.

## Support

- Docs: https://redfox.hk/skills
- Email: redfoxdata@proton.me
