(() => {
  // `claude_chats.py snippet --project <name>` prints this with the values filled in. Run it in
  // a fresh Chrome tab on https://claude.ai/robots.txt (never one of Dan's). It starts a job in
  // the page and returns at once; poll it with `await window.__claudeProject.wait()`. The job
  // fetches the project's new or changed chats, as the API sends them, with their photos, and
  // saves everything as one file: claude-project-<id>.json. Status holds counts and IDs only.
  // A chat or project whose title matches a hold rule is never saved.
  // <helpers>
  const PROJECT = __PROJECT__;
  const HOLD_PREFIXES = __HOLD_PREFIXES__;
  const HOLD_PATTERNS = __HOLD_PATTERNS__;
  const KNOWN = __KNOWN__;
  const KNOWN_FILE_IDS = __KNOWN_FILES__;
  const KNOWN_PROJECT = __KNOWN_PROJECT__;
  const DELAY_MS = __DELAY_MS__;
  const MAX_BYTES = __MAX_BYTES__;
  const PHOTO_DELAY_MS = 100;
  const PHOTO_TYPES = __PHOTO_TYPES__;
  // Same rule as normalize_title() and is_held() in claude_chats_archive.py; a test runs both.
  const norm = s => String(s || "").normalize("NFKC").toLowerCase().replace(/[^a-z0-9:]/g, "");
  const isHeld = t => {
    const n = norm(t);
    return HOLD_PREFIXES.some(p => n.startsWith(p)) || HOLD_PATTERNS.some(p => n.includes(p));
  };
  // </helpers>
  if (location.origin !== "https://claude.ai") return "run this on https://claude.ai/robots.txt";
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const job = window.__claudeProject = {state: "running", listed: 0, toFetch: 0, fetched: 0, held: 0, photos: 0,
                                        bytes: 0, errors: [], more: false, saved: null, error: null};
  Object.defineProperty(job, "wait", {enumerable: false, value: async () => {
    const t0 = Date.now();
    while (job.state === "running" && Date.now() - t0 < 20000) await sleep(250);
    return {...job};
  }});

  // One API call at a time, paced, waiting out rate limits.
  const call = async path => {
    for (let tries = 0; ; tries++) {
      const r = await fetch("/api" + path, {credentials: "include", headers: {accept: "application/json"}});
      await sleep(DELAY_MS);
      if (r.status !== 429 || tries >= 3) return r;
      await sleep(1000 * (Number(r.headers.get("retry-after")) || 30));
    }
  };
  const toB64 = async blob => {
    const buf = new Uint8Array(await blob.arrayBuffer());
    let s = "";
    for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    return btoa(s);
  };

  (async () => {
    try {
      const orgsRes = await call("/organizations");
      if (orgsRes.status === 401 || orgsRes.status === 403) { job.state = "auth"; return; }
      if (!orgsRes.ok) throw new Error(`organizations answered ${orgsRes.status}`);
      let org = null, projectRaw = null;
      for (const o of await orgsRes.json()) {
        const r = await call(`/organizations/${o.uuid}/projects/${PROJECT}`);
        if (r.ok) { org = o.uuid; projectRaw = await r.text(); break; }
      }
      if (!org) { job.state = "failed"; job.error = "this account can't open that project"; return; }
      const project = JSON.parse(projectRaw);
      if (isHeld(project.name)) { job.state = "held"; return; }

      const docsRes = await call(`/organizations/${org}/projects/${PROJECT}/docs`);
      if (!docsRes.ok) throw new Error(`docs answered ${docsRes.status}`);
      const docsRaw = await docsRes.text();

      // Titles are checked on the list, before any chat is opened.
      const items = [];
      let listComplete = true;
      for (let offset = 0; ;) {
        const r = await call(`/organizations/${org}/projects/${PROJECT}/conversations_v2?limit=30&offset=${offset}`);
        if (!r.ok) throw new Error(`the chat list answered ${r.status}`);
        const page = await r.json();
        items.push(...(page.data || []));
        // Only the API saying "no more" makes the list whole: ingest marks what's missing from it as gone.
        const more = page.pagination ? page.pagination.has_more : undefined;
        if (typeof more !== "boolean" || (more && !(page.data || []).length)) { listComplete = false; break; }
        if (!more) break;
        offset += page.data.length;
      }
      job.listed = items.length;
      const held = items.filter(c => isHeld(c.name)).map(c => c.uuid);
      job.held = held.length;
      const visible = items.filter(c => !isHeld(c.name));
      const list = visible.map(c => ({uuid: c.uuid, updated_at: c.updated_at}));
      const toFetch = visible.filter(c => KNOWN[c.uuid] !== c.updated_at);
      job.toFetch = toFetch.length;
      if (!toFetch.length && visible.length === Object.keys(KNOWN).length && project.updated_at === KNOWN_PROJECT) {
        job.state = "unchanged";
        return;
      }

      const knownFiles = new Set(KNOWN_FILE_IDS);
      const conversations = {}, files = {}, photosMissing = {};
      let bytes = projectRaw.length + docsRaw.length;
      for (const c of toFetch) {
        if (job.fetched && bytes > MAX_BYTES) { job.more = true; break; }
        // One chat failing is never fatal, and the status never says why in words: an error can quote the chat.
        let raw, conv;
        try {
          const r = await call(`/organizations/${org}/chat_conversations/${c.uuid}?tree=True&rendering_mode=messages&render_all_tools=true`);
          if (!r.ok) { job.errors.push({id: c.uuid, status: r.status}); continue; }
          raw = await r.text();
          conv = JSON.parse(raw);
        } catch (e) {
          job.errors.push({id: c.uuid, status: "unreadable"});
          continue;
        }
        if (isHeld(conv.name)) { held.push(c.uuid); job.held++; continue; }
        const got = {}, missing = [];
        for (const f of (conv.chat_messages || []).flatMap(m => (m.files || []).concat(m.files_v2 || []))) {
          if (!f || f.file_kind !== "image" || knownFiles.has(f.file_uuid) || got[f.file_uuid] || missing.includes(f.file_uuid)) continue;
          const asset = f.preview_asset || {};
          try {
            const pr = await fetch(asset.url || f.preview_url, {credentials: "include"});
            if (!pr.ok) throw new Error(String(pr.status));
            const blob = await pr.blob();
            if (!PHOTO_TYPES.includes(blob.type)) throw new Error("unsupported type");  // ingest would refuse the whole file
            got[f.file_uuid] = {file_name: f.file_name, file_kind: f.file_kind, variant: "preview", mime: blob.type,
                                width: asset.image_width || null, height: asset.image_height || null,
                                bytes: blob.size, base64: await toB64(blob)};
            bytes += got[f.file_uuid].base64.length;
          } catch (e) {
            missing.push(f.file_uuid);
          }
          await sleep(PHOTO_DELAY_MS);
        }
        conversations[c.uuid] = raw;
        if (Object.keys(got).length) files[c.uuid] = got;
        if (missing.length) photosMissing[c.uuid] = missing;
        bytes += raw.length;
        job.fetched++;
        job.photos += Object.keys(got).length;
        job.bytes = bytes;
      }

      // One file, so Chrome never has to allow a second automatic download from this page.
      const name = `claude-project-${PROJECT.slice(0, 8)}.json`;
      const blob = new Blob([JSON.stringify({schema: 1, kind: "claude-project", fetched_at: new Date().toISOString(),
                                             project_id: PROJECT, project: projectRaw, docs: docsRaw, list,
                                             list_complete: listComplete, held,
                                             conversations, files, photos_missing: photosMissing,
                                             errors: job.errors, more: job.more})], {type: "application/json"});
      const url = URL.createObjectURL(blob);
      const a = Object.assign(document.createElement("a"), {href: url, download: name});
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 600000);
      job.bytes = blob.size;
      job.saved = name;
      job.state = "saved";
    } catch (e) {
      job.state = "failed";
      job.error = `${e.name}: ${String(e.message).slice(0, 80)}`;
    }
  })();
  return "started";
})()
