# Decisions

One line per ticket.

| Ticket | Decision | Alternative | Why |
|---|---|---|---|
| Setup | Use GPT-6-luna as the Codex reviewer while building Botkit, then switch to GPT-6.1 Sol through an API key before the 180 experiment runs | Use Sol for everything | Sol is not offered on my Codex plan. Luna is enough for day-to-day reviews, but the experiment needs Sol so the reviewer matches Opus 5.5 in tier |
| Phase 3 | Split approval into a review gate (before commit) and a learning gate (batched, by tier, with a debt cap) | Keep explain back before every commit | Learning on every ticket blocks autonomy; batching keeps both |