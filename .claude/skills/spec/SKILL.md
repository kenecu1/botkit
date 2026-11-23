---
name: spec
description: Turn a ticket brief into spec.md, ticket.toml and draft tests, following prompts/spec_writer.md.
disable-model-invocation: true
argument-hint: <ticket folder, like T005-record>
---
1. Read prompts/spec_writer.md and follow it exactly for tickets/$ARGUMENTS.
2. Read tickets/$ARGUMENTS/brief.md and src/botkit/shapes.py before anything else.
3. Ask your questions one at a time and wait for each answer.
4. Show the spec, ticket.toml and tests, and wait for my OK before saving.
5. Never write the implementation. Never commit.