# Decisions

One line per ticket.

| Ticket | Decision | Alternative | Why |
|---|---|---|---|
| Setup | Use GPT-6-luna as the Codex reviewer while building Botkit, then switch to GPT-6.1 Sol through an API key before the 180 experiment runs | Use Sol for everything | Sol is not offered on my Codex plan. Luna is enough for day-to-day reviews, but the experiment needs Sol so the reviewer matches Opus 5.5 in tier |
| Day 1 commit probe | The guard is the real control against bot commits. Deny rules are kept only as a courtesy | Rely on the `git commit` deny rule alone | In a throwaway repo, the deny rule blocked a plain `git commit`, but `git -C . commit` matched no rule and created a real commit. The guard compares HEAD, every ref and the reflog before and after a run, so it catches a commit however it is spelled |
| Nov 18 | The ticket does not choose its model. The builder and reviewer models come from `botkit.toml` | A model field in `ticket.toml` | One place to see and change the models at any time, and writing a ticket cannot set the wrong one |
| Nov 19 | Make the clone inside the run folder | Build in the real repo | A separate copy keeps the bot away from the real repo, lets us remove the remote when the copy is made, and is easy to delete if something goes wrong |
| Nov 23 | One branch per ticket | Work directly on `main` | Each ticket is built on its own branch, so if something goes wrong it does not affect `main` |
| Nov 23 | Builders write one line docstrings and no inline comments | Let the builder comment freely | On T001 the builder added many inline comments. They explained the code for me and weakened the explain gate |
| Nov 23 | Spec writer rule 8: every error case named in the spec gets its own test | One test per brief example only | T001's spec named 5 error cases with no tests, and the builder tried an outside script to check them |
| Nov 23 | Pause time guesses until the MVP runs | Track every bootstrap ticket | Manual tickets mix in setup and learning, and the guesses were written late, so the numbers would not represent Botkit |
| Nov 24 | Bootstrap tickets get interface level explanations | A full line by line explanation | I already planned these tickets in the brief, spec and tests, so a line by line explanation would cost a couple of hours |