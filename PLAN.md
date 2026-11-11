# Plan (write this in your own words)
Give a ticket to a bot, completes ticket using claude, runs tests, reviews via chatgpt, resends back to claude if a retry is needed,
if accepted, sends for human review and quiz bot runs, then saves data via MySQL.
## Goal in one sentence
A bot that does my tasks for me and teaches me the task if needed
## The loop (5 steps)
write spec, send ticket to bot, bot completes using claude, run tests for errors, reviews via ChatGPT, sends back if needed to claude to retry, if accepted, sends for human review
and stores data into MySQL, then teaches it back via quiz bot
## What done looks like this week
I atleast want the MVP done by this week so that I can start working with a prototype
## What I am not building yet
Anything that doesn't need to be included other than the MVP