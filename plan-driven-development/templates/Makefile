# __PROJECT__: the front door for every command, for agents and people alike. `make help` lists
# the targets. Made from plan-driven-development's template, kept to GNU make 3.81 features so it
# runs on macOS as well as Linux. Kickoff fills __TEST_COMMAND__ and __LINT_COMMAND__, and deletes
# the docs target (and its .PHONY entry) when the docs are read on GitHub instead (AGENTS.md, Docs and security).
# A command anyone will run more than once becomes a target here.

SHELL := /bin/bash
LEAKCHECK := uv run --quiet --script scripts/leakcheck.py
.DEFAULT_GOAL := help
.PHONY: help hooks check test test-utc lint leaks docs

help: ## List the targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

hooks: ## Turn this clone's leak and commit-message hooks on, after checking their tools and the denylist
	@command -v gitleaks >/dev/null || { echo "install gitleaks 8.19 or later first"; exit 1; }
	@gitleaks git --help >/dev/null 2>&1 || { echo "this gitleaks has no 'git' command: the hooks need 8.19 or later"; exit 1; }
	@command -v uv >/dev/null || { echo "install uv first"; exit 1; }
	@$(LEAKCHECK) --message /dev/null || { echo "the denylist is missing or invalid: stop and tell Dan"; exit 1; }
	@for hook in pre-commit commit-msg pre-push pre-merge-commit; do \
	  [ -x ".githooks/$$hook" ] || { echo ".githooks/$$hook is missing or not executable: copy the hooks in first"; exit 1; }; \
	done
	git config core.hooksPath .githooks
	@echo "hooks on for this clone"

check: test test-utc lint leaks ## Everything a task runs before review: the suite, again under TZ=UTC, lint, the leak scan

test: ## Run the test suite
	__TEST_COMMAND__

test-utc: ## Run the test suite again under TZ=UTC, as CI does
	export TZ=UTC; __TEST_COMMAND__

lint: ## Run the linters
	__LINT_COMMAND__

leaks: ## Scan every tracked file with the leak check and this machine's denylist
	$(LEAKCHECK) --tracked

docs: ## Render the site; every doc has its wrapper, no unresolved link, every internal link resolves
	@missing=0; while IFS= read -r -d '' doc; do wrapper="website/$${doc#docs/}"; \
	  if [ ! -f "$$wrapper" ]; then echo "no wrapper for $$doc (expected $$wrapper)"; missing=1; fi; \
	done < <(git ls-files -z 'docs/superpowers/*.md'); exit $$missing
	@set -o pipefail; quarto render website 2>&1 | tee website/.render.log
	@! grep -q "Unable to resolve link target" website/.render.log || { echo "a link Quarto couldn't resolve: see above"; exit 1; }
	@if command -v lychee >/dev/null; then lychee --offline --no-progress website/_site; \
	else echo "lychee isn't installed here: CI checks every internal link"; fi
