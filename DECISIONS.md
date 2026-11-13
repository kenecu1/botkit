# Decisions

One line per ticket.

| Ticket | Decision | Alternative | Why |
|---|---|---|---|
| Setup | Use GPT-6-luna as the Codex reviewer while building Botkit, then switch to GPT-6.1 Sol through an API key before the 180 experiment runs | Use Sol for everything | Sol is not offered on my Codex plan. Luna is enough for day-to-day reviews, but the experiment needs Sol so the reviewer matches Opus 5.5 in tier |
| Day 1 commit probe | The guard is the real control against bot commits. Deny rules are kept only as a courtesy | Rely on the `git commit` deny rule alone | In a throwaway repo, the deny rule blocked a plain `git commit`, but `git -C . commit` matched no rule and created a real commit. The guard compares HEAD, every ref and the reflog before and after a run, so it catches a commit however it is spelled |