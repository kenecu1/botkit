# Plan (write this in your own words)
Give a ticket to a bot, completes ticket using claude, runs tests, reviews via chatgpt, resends back to claude if a retry is needed,
if accepted, sends for human review, then saves data via SQLite. Run experiment on both ai bots, comparing errors and hallucinations and if different
AI actually matter.
## Goal in one sentence
A bot that automates tasks for me without losing the control/learning aspect, I control commit, bots never do.
## The loop (5 steps)
1.write spec, send ticket to bot
2.bot completes using claude,
3.run tests for errors and send back to retry
4.reviews via ChatGPT send back to retry
5.if accepted, sends for human review and stores data into SQLite
## What done looks like this week
I atleast want the MVP done 11/14 so that I can start working with a prototype, additions after, experiment by 11/17, I plan to take a couple long days to complete more than mecessary per day
## What I am not building yet
Anything that doesn't need to be included other than the MVP: quiz, sandboxing, phone, status page, parallel builders