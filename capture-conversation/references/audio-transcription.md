# Audio Transcription

How to turn a recording into a verbatim transcript (SKILL.md step 1c). The
audio file is the canonical original; the transcript is derived. Keep both,
linked.

## Local ASR

On Apple Silicon, mlx-whisper works well: minutes, not tens of minutes, for a
30-minute recording, and the ASR model itself needs no HF token.

```bash
uvx --from mlx-whisper mlx_whisper <audio> --model mlx-community/whisper-large-v3-turbo --output-format json --word-timestamps True
```

Check `~/.cache/huggingface/hub/` first — the model may already be cached from
unrelated work.

## Speaker attribution without a diarization tool

The common case is two people, no diarization tool installed, and no `HF_TOKEN`
(pyannote's gated models need one). Attribute turns **by content**: each
speaker's consistent verbal tics and argument style, cross-checked against any
position already documented for each person elsewhere in the vault (e.g. a
note recording what each side already believes). This is real evidence, not a
coin flip, and confidence is high for substantive turns. But:

- **Say so in the transcript's provenance note.** The turns are attributed by
  content, not diarized ground truth.
- **Group backchannel under one timestamp.** Rapid "yeah" / "right" / "for sure"
  volleys with no distinguishing content can't be attributed from content
  alone. Don't force a label onto each word.

## Never silently clean up ASR mishearings

The pull to "fix" a misheard proper noun, jargon term or course code while
writing out the transcript is **strong**. Resist it as hard as the icon-glyph
case in page text. One meeting capture quietly normalized several garbles (a
course code, a tool name misheard four different ways, a term that was never
actually said) and had to be redone from the raw ASR output. Garbles stay
verbatim in the source and are decoded in the thinking note, every time — no
exceptions for "obviously what they meant."

## Diarization status

Still unsolved, and not the first thing to chase: content-based attribution
worked well enough on substantive turns in a 2-party meeting. True audio
diarization (pyannote needs a gated HF model + token; NeMo is a heavy install)
is untested. Revisit it only if a capture's content is too symmetric in style
for content-based attribution to work (e.g. two people who argue alike, or 3+
speakers where pairwise stylistic contrast breaks down).
