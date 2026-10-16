.DEFAULT_GOAL := help
.PHONY: help install setup setup-check sync-guards

# The private config repo that holds the secrets guard. No default: pass it.
CLAUDE_CONFIG ?=

help: ## List the targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Link each skill into ~/.claude/skills
	./install.sh

setup: ## Wire preferences.md and the leak-check guard into this machine's harness config
	bash setup.sh

setup-check: ## Report what setup would do, changing nothing
	bash setup.sh --check

sync-guards: ## Copy the guard files from CLAUDE_CONFIG=<private config repo> into guards/ (git-ignored)
	@test -n "$(CLAUDE_CONFIG)" || { echo "CLAUDE_CONFIG is not set: pass CLAUDE_CONFIG=<path to the private config repo>" >&2; exit 1; }
	@test -d "$(CLAUDE_CONFIG)" || { echo "CLAUDE_CONFIG is not a folder: $(CLAUDE_CONFIG)" >&2; exit 1; }
	mkdir -p guards
	cp "$(CLAUDE_CONFIG)/hooks/block-secret-access.sh" "$(CLAUDE_CONFIG)/hooks/test_block_secret_access.py" \
	  "$(CLAUDE_CONFIG)/settings.reference.json" "$(CLAUDE_CONFIG)/README.md" "$(CLAUDE_CONFIG)/Makefile" guards/
