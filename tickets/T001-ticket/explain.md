# T001 ticket explain

## src/botkit/ticket.py
- Has one main read_ticket function that opens a ticket_folder path and reads in each part of the folder into the necessary variable. The helper functions are called to verify types and raise necessary errors. Then it uses those variables to fill in a record Ticket.

## Compared with the bot's summary
- Missed: how repo_path is found -> dirname called twice
- Missed: where ticket_name comes from -> basename
- Missed: how the TOML is read -> tomllib (opened in "rb") turns it into a dict with Python lists, then the code converts lists to tuples because Ticket is frozen
- Imprecise: it opens the three files, not the folder
- Imprecise: helpers check a key exists AND its type (KeyError vs TypeError)
- Bot's own gap: error cases from the spec were never run (5 tests to add)

## Change by hand
- Removed the inline comments; tests still green: yes