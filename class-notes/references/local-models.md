# Local models: notes from a model on your own hardware

Dan's local models write notes for every session alongside the Claude run, whenever
they're loaded. `generate` sends any `--model` name that isn't Claude to
`run_local()`, which is still a placeholder: it fails with `local backend not set up
yet`. Until it's built, run each local model by hand. Send the same message, with the
same system prompt, and write the result with the filename and footer `generate` uses,
so `generate` treats the file as its own.

## Dan's local models

Dan's DGX Spark serves them through the SSH tunnel's forwards to the Mac. These two are
the default set:

| Model id | Base URL on the Mac | Engine | Key, by env var name | Requests at once |
|---|---|---|---|---|
| `qwen3.6-35b-a3b` | `http://localhost:9100/v1` | llama-swap, the stack's front: loads models on demand | `SPARK_API_KEY` | 1 (one slot: its MTP drafting allows no more) |
| `qwen3.8-27b-sglang` | `http://localhost:8990/v1` | SGLang, the fast coder, started by hand | `SPARK_SGLANG_KEY` | 1 (`--max-running-requests 1`) |

- **Take the model id from `/v1/models`,** not from the name you were given. Model
  versions move, and a spoken name can mix two models: the version of one and the size or
  engine of another. Use the server's id. When the name fits more than one model, say
  which you ran.
- **When a default id is missing from `/v1/models`,** a newer version has probably
  replaced it. Skip that model and tell Dan: the replacement is his call.
- **Other models run the same way when Dan names them:** another model on llama-swap, or
  any OpenAI-compatible endpoint (vLLM, llama.cpp's server, Ollama's `/v1`).

## Check which are loaded

Run a model when every check passes. The checks take seconds, so make them all before
starting any run, the Claude one included.

- **Its key is exported** to child processes.
- **Its endpoint answers, and lists its id in `/v1/models`.** `Unauthorized` means the
  key is missing or wrong. No answer means the tunnel is down or the server is off.
- **On llama-swap, it's loaded.** `spark-tunnel menu` lists the loaded models under
  `Loaded`. A request for any other model makes llama-swap load it, and a load can unload
  models other people are using. If `spark-tunnel` isn't on `PATH`, this can't be
  checked, so skip the model and tell Dan.
- **On SGLang, the answer is enough:** the server holds its one model, already loaded.

Skip each model that fails a check, and report the check it failed. Load and unload
models only when Dan asks.

These print a boolean and the model ids, never the key: the variable goes straight to
`curl`, which expands it.

```bash
python3 -c "import os; print(bool(os.environ.get('SPARK_API_KEY')))"
curl -s -m 10 -H "Authorization: Bearer $SPARK_API_KEY" http://localhost:9100/v1/models | python3 -c "import json,sys; print([m['id'] for m in json.load(sys.stdin)['data']])"
```

## Run them in parallel

- **Run every loaded model at once, alongside the Claude run,** without waiting for any
  of them to finish: one background command per model, each under `caffeinate -i`. If
  the Mac sleeps during a run, spark-tunnel reconnects on wake, and that drops every
  stream in flight.
- **Within a model, run as many sessions at once as it takes requests at once** (the
  table's last column). A request past that waits silently behind the others, and a long
  wait can outlast the runner's socket timeout, so queue the rest inside that model's
  background command. A model the table doesn't list takes one at a time unless Dan says
  otherwise.
- **Runs that share the Spark are slower:** `qwen3.6-35b-a3b` took about 9 minutes
  beside the SGLang run, against 5–6 alone.
- **One runner, launched for each run.** Write it once in the session's scratchpad,
  taking the base URL, model id, key's env var name, engine and session folder as
  arguments, doing what the next two sections say.

## Send one request (recommended) or use opencode

Dan has made local notes through opencode, which can reach both endpoints. Its files
carry `backend: opencode`. That works, but an agent builds its own message from the files
(its system prompt and tool calls included), and it writes the footer by hand, so check
the footer: one such run put the prompt hash where the commit belongs. An agent can also
go exploring the repository instead of writing notes, which is why `run_claude` runs with
no tools.

A single request gives the model the same message and system prompt that Claude got, so
the two sets of notes compare fairly, and the script writes the footer. Send one chat
completion:

- **system:** `AGENT_SYSTEM_PROMPT` from `class_notes.py`.
- **user:** what `payload --only <folder>` prints (`build_message(prompt, session)`).
- **`max_tokens`:** large, around 60000. A thinking model spends tokens on reasoning
  before it writes anything. A two-hour lecture is about 25K prompt tokens, or 42–50K
  with a week's `materials.md`. On those, `qwen3.6-35b-a3b` took 5–6 minutes and about
  6K completion tokens, and `qwen3.8-27b-sglang` took 11–16 minutes and 18–24K
  completion tokens, two-thirds of them reasoning.
- **`stream: true`,** with `stream_options: {"include_usage": true}`. A run takes
  minutes, and streaming keeps the connection busy the whole time.
- **Sampling:** leave it at the server's defaults, as the Claude run does.

Check the reply before saving anything. These are the checks `run_local()` must make once
it's built:

- **`finish_reason: "length"`** means the reply was cut off. Fail; don't save it.
- **No `finish_reason` and no `usage`** means the stream ended early: the connection
  dropped. A chunk with an `error` key is the server refusing. Report either one; don't
  call it an empty answer.
- **`usage.prompt_tokens`:** compare it with the size of the message, at about 4
  characters a token. Far fewer tokens (under one per 6 characters, say) means the
  transcript was cut to fit a small context window. A cut transcript comes back looking
  complete, so fail.
- **`content` holds the notes.** With a reasoning parser on (SGLang's
  `--reasoning-parser`), the thinking arrives separately, in `reasoning_content`. Keep it
  out of the notes.
- **The response's `model` field** names the model that answered. Use it in the filename.

## Write it the way `generate` does

- **File:** `notes-class-<variant>--<model slug>.md` (`output_name`).
- **Contents:** the reply, then `\n\n---\n\n`, then the footer, all passed through
  `tidy_markdown`, then saved with `write_atomic`:

  ```text
  - prompt: prompt-notes.md @ <prompt.version>
  - prompt-hash: <prompt.hash>
  - model: <the model that answered> (requested: <the name you'd pass to --model>)
  - backend: local (<engine: SGLang, llama-swap, …>)
  - inputs: <session.inputs>
  - generated: <YYYY-MM-DD>
  ```

- **`requested:`** is the field `generate` matches on. Set it to the `--model` name.
  Then `generate --model <that name>` sees the notes as current and skips them. After a
  prompt edit, it lists them as stale. It never reaches the placeholder.

Every piece is in the script. Put `scripts/` on `sys.path`, `import class_notes`, and use
`repo_root`, `select_prompts(root, ["main"], None, None)`, `discover_sessions(root,
[folder])`, `Session`, `build_message`, `AGENT_SYSTEM_PROMPT`, `output_name`,
`tidy_markdown` and `write_atomic`. Run `tidy --check` afterwards. Report the notes file,
its line count and the model, as for a Claude run, along with the time it took and the
prompt and completion tokens.
