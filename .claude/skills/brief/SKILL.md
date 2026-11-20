---
name: brief
description: Interview me to write a ticket brief from the template, one question at a time.
disable-model-invocation: true
argument-hint: <ticket folder, like T002-sandbox>
---
Role:
1. Complete brief for specific ticket using user input
Steps:
0. Don't overwrite brief if tickets/$ARGUMENTS/brief.md already exists
1. Read first:
  - docs/design.md sections 2, 3 and 9
  - src/botkit/shapes.py
2. Ask the user all questions in tickets/_template/brief.md one by one from top down
3. After all template questions, before showing the brief, ask up to 3 questions about gaps:
  - For each example: would a broken version still pass?
  - What might a helpful bot add that it shouldn't? (out of scope)
  - Anything in the files read that the brief contradicts or leaves out
4. Show the full brief.md in chat
5. When user says OK, create a new folder tickets/$ARGUMENTS/ and create brief.md in that folder
6. Fill in brief.md with given template using users own words
Rules:
1. Brief has to be in the user's words, spec is for claude's words
2. If parts of brief aren't filled out keep questioning the user until they come up with an answer
3. All of brief should be filled out
4. It should only be txt, no creation of code
5. Gap questions are questions only. Never add an answer the user didn't give.
Stop Conditions:
1. When brief is fully filled out
