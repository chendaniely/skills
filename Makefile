# skills: the front door for this repo's commands, for agents and people alike. `make help` lists
# the targets. Kept to GNU make 3.81 features so it runs on macOS as well as Linux.

PYTEST := uv run --quiet --with pytest --with pyyaml pytest plan-driven-development/tests -q
.DEFAULT_GOAL := help
.PHONY: help test test-utc check-skills install setup setup-check sync-guards

# The private config repo that holds the secrets guard. No default: pass it.
CLAUDE_CONFIG ?=

help: ## List the targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

test: ## Run plan-driven-development's tests: its scripts, hooks and templates
	$(PYTEST)

test-utc: ## The same tests under TZ=UTC, as CI would run them
	TZ=UTC $(PYTEST)

check-skills: ## Check every skill's frontmatter (name = folder, description <= 1024) and line count
	@for f in */SKILL.md; do uv run -q --with pyyaml python -c "import yaml,re,sys; p=sys.argv[1]; t=open(p).read(); fm=yaml.safe_load(re.match(r'^---\n(.*?)\n---\n',t,re.S).group(1)); assert fm['name']==p.split('/')[0], p+': name != folder'; assert len(fm['description'])<=1024, p+': description too long'; print(fm['name'], len(fm['description']), t.count(chr(10)), 'lines')" "$$f" || exit 1; done

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
