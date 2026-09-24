# Class notes: generate notes from session transcripts with the course prompt
# (prompt-notes.md). The generator is class-notes/scripts/class_notes.py in the public
# chendaniely/skills repository; README-prompt.md explains the whole setup.
#
#   make               same as `make notes`
#   make notes         generate notes for sessions that don't have them yet
#   make notes-force   rebuild every session from the current prompt (after editing it)
#   make payload ONLY=<session folder>   print the exact message sent for one session
#   make fetch URL=<plaud share link>    add a session from a recording (instructor only)
#
# Extra flags pass through ARGS, e.g. `make notes ARGS="--dry-run"` or
# `make notes-force ARGS="--only <session folder> --model sonnet"`.
# If you cloned the skills repo somewhere else, add CLASS_NOTES=<path to class_notes.py>.

CLASS_NOTES ?= $(HOME)/.claude/skills/class-notes/scripts/class_notes.py
PYTHON ?= python3
ARGS ?=

.PHONY: notes notes-force payload fetch

notes:  ## Generate notes for sessions with no notes yet
	$(PYTHON) $(CLASS_NOTES) generate $(ARGS)

notes-force:  ## Rebuild every session from the current prompt
	$(PYTHON) $(CLASS_NOTES) generate --force $(ARGS)

payload:  ## Print the message sent for one session (ONLY=<folder>)
	$(PYTHON) $(CLASS_NOTES) payload --only $(ONLY) $(ARGS)

fetch:  ## Add a session from a Plaud share link (URL=<link>)
	$(PYTHON) $(CLASS_NOTES) fetch $(URL) $(ARGS)
