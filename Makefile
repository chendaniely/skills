# skills: the front door for this repo's commands, for agents and people alike. `make help` lists
# the targets. Kept to GNU make 3.81 features so it runs on macOS as well as Linux.

PYTEST := uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests -q
.DEFAULT_GOAL := help
.PHONY: help test test-utc test-claude-chats check-skills install setup setup-check sync-guards

# The private config repo that holds the secrets guard. No default: pass it.
CLAUDE_CONFIG ?=

help: ## List the targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

test: ## Run plan-driven-development's tests: its scripts, hooks and templates
	$(PYTEST)

test-utc: ## The same tests under TZ=UTC, as CI would run them
	TZ=UTC $(PYTEST)

test-claude-chats: ## Run claude-chats' tests: its archive, renderer and command line
	@for t in archive render cli; do uv run claude-chats/tests/test_claude_chats_$$t.py || exit 1; done

check-skills: ## Check every skill's frontmatter (name = folder, description <= 1024) and line count
	@for f in */SKILL.md; do uv run -q --with pyyaml python -c "import yaml,re,sys; p=sys.argv[1]; t=open(p).read(); fm=yaml.safe_load(re.match(r'^---\n(.*?)\n---\n',t,re.S).group(1)); assert fm['name']==p.split('/')[0], p+': name != folder'; assert len(fm['description'])<=1024, p+': description too long'; print(fm['name'], len(fm['description']), t.count(chr(10)), 'lines')" "$$f" || exit 1; done

install: ## Link each skill into ~/.claude/skills
	./install.sh

setup: ## Wire preferences.md and the leak-check guard into this machine's harness config
	bash setup.sh

setup-check: ## Report what setup would do, changing nothing
	bash setup.sh --check

# This repo is public, so it describes the guard and never names its files: the names live only in
# the git-ignored guards/, and this target refreshes what is already there.
sync-guards: ## Refresh the copies already in guards/ (git-ignored) from CLAUDE_CONFIG=<private config repo>
	@test -n "$(CLAUDE_CONFIG)" || { echo "CLAUDE_CONFIG is not set: pass CLAUDE_CONFIG=<path to the private config repo>" >&2; exit 1; }
	@test -d "$(CLAUDE_CONFIG)" || { echo "CLAUDE_CONFIG is not a folder: $(CLAUDE_CONFIG)" >&2; exit 1; }
	@count=0; refreshed=0; \
	for copy in guards/*; do \
	  [ -f "$$copy" ] || continue; \
	  count=$$((count + 1)); name=$${copy##*/}; \
	  if [ -f "$(CLAUDE_CONFIG)/$$name" ]; then source="$(CLAUDE_CONFIG)/$$name"; \
	  elif [ -f "$(CLAUDE_CONFIG)/hooks/$$name" ]; then source="$(CLAUDE_CONFIG)/hooks/$$name"; \
	  else echo "left as is, not in CLAUDE_CONFIG: $$name"; continue; fi; \
	  cp "$$source" "$$copy" || exit 1; \
	  refreshed=$$((refreshed + 1)); \
	done; \
	test "$$count" -gt 0 || { echo "guards/ is empty: copy the guard's files there by hand once, then this refreshes them" >&2; exit 1; }; \
	test "$$refreshed" -gt 0 || { echo "none of the files in guards/ is in CLAUDE_CONFIG: is the path right?" >&2; exit 1; }; \
	echo "refreshed $$refreshed of $$count files in guards/"
