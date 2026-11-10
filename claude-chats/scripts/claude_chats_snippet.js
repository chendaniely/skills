await (async () => {
  // `claude_chats.py snippet <link>` prints this with the values filled in. Run it in a fresh
  // Chrome tab on https://claude.ai/robots.txt (never one of Dan's). Given a share link, or a
  // chat's own URL from the address bar, it fetches that chat from Dan's own account and saves
  // it, with its photos, as one file: claude-chat-<id>.json. It returns IDs and counts only; the
  // chat goes straight to the file. A chat whose title matches a hold rule is never saved, and
  // its title is never returned.
  // <helpers>
  const SHARE = __SHARE__;  // a share link's ID, or null
  const CHAT = __CHAT__;  // a chat's own ID, or null
  const HOLD_PREFIXES = __HOLD_PREFIXES__;
  const HOLD_PATTERNS = __HOLD_PATTERNS__;
  const PHOTO_DELAY_MS = 100;
  // Same rule as normalize_title() and is_held() in claude_chats_archive.py; a test runs both.
  const norm = s => String(s || "").normalize("NFKC").toLowerCase().replace(/[^a-z0-9:]/g, "");
  const isHeld = t => {
    const n = norm(t);
    return HOLD_PREFIXES.some(p => n.startsWith(p)) || HOLD_PATTERNS.some(p => n.includes(p));
  };
  // </helpers>
  if (location.origin !== "https://claude.ai") return {error: "run this on https://claude.ai/robots.txt"};
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const get = p => fetch("/api" + p, {credentials: "include", headers: {accept: "application/json"}});

  // A share link names its chat: the org-scoped snapshot carries conversation_uuid. A chat URL
  // already is the chat's ID. Either way, the org is whichever one of Dan's can open it.
  const chatPath = (o, c) => `/organizations/${o}/chat_conversations/${c}?tree=True&rendering_mode=messages&render_all_tools=true`;
  const orgsRes = await get("/organizations");
  if (!orgsRes.ok) return {error: "not signed in to claude.ai", status: orgsRes.status};
  let org = null, id = CHAT, cr = null;
  for (const o of await orgsRes.json()) {
    if (SHARE) {
      const r = await get(`/organizations/${o.uuid}/chat_snapshots/${SHARE}?rendering_mode=messages&render_all_tools=true`);
      if (!r.ok) continue;
      const snap = await r.json();
      if (isHeld(snap.snapshot_name)) return {held: true};
      org = o.uuid;
      id = snap.conversation_uuid;
      break;
    }
    const r = await get(chatPath(o.uuid, CHAT));
    if (r.ok) { org = o.uuid; cr = r; break; }
  }
  if (!org) return SHARE ? {error: "this account can't open that share link"} : {notYours: true};
  if (!id) return {error: "the share link names no chat"};

  // The chat itself, current and with every branch, exactly as the API sends it.
  if (!cr) cr = await get(chatPath(org, id));
  if (!cr.ok) return {notYours: true, status: cr.status};
  const raw = await cr.text();
  const conv = JSON.parse(raw);
  if (isHeld(conv.name)) return {held: true};

  // A chat in a project brings its project's name, for its folder and project note, and
  // nothing else of the project: instructions and files wait for project sync.
  let project = null;
  if (conv.project_uuid) {
    const pr = await get(`/organizations/${org}/projects/${conv.project_uuid}`);
    // Without the project's name its hold rules can't be checked, so nothing is saved.
    if (!pr.ok) return {error: "couldn't read the chat's project, so nothing was saved; run it again", status: pr.status};
    const p = await pr.json();
    if (isHeld(p.name)) return {held: true};
    project = {uuid: conv.project_uuid, name: p.name || null, created_at: p.created_at || null};
  }

  // Its photos: claude.ai's preview copies. One that fails is left out and reported;
  // a later run of the same link adds it.
  const toB64 = async blob => {
    const buf = new Uint8Array(await blob.arrayBuffer());
    let s = "";
    for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    return btoa(s);
  };
  const files = {}, missing = [];
  for (const f of (conv.chat_messages || []).flatMap(m => (m.files || []).concat(m.files_v2 || []))) {
    if (!f || f.file_kind !== "image" || files[f.file_uuid] || missing.includes(f.file_uuid)) continue;
    const asset = f.preview_asset || {};
    try {
      const r = await fetch(asset.url || f.preview_url, {credentials: "include"});
      if (!r.ok) throw new Error(String(r.status));
      const blob = await r.blob();
      files[f.file_uuid] = {file_name: f.file_name, file_kind: f.file_kind, variant: "preview", mime: blob.type,
                            width: asset.image_width || null, height: asset.image_height || null,
                            bytes: blob.size, base64: await toB64(blob)};
    } catch (e) {
      missing.push(f.file_uuid);
    }
    await sleep(PHOTO_DELAY_MS);
  }

  // One file, so Chrome never has to allow a second automatic download from this page.
  const name = `claude-chat-${id.slice(0, 8)}.json`;
  const blob = new Blob([JSON.stringify({schema: 1, kind: "claude-chat", fetched_at: new Date().toISOString(),
                                         share: SHARE, project, conversation: raw, files})], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement("a"), {href: url, download: name});
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 600000);
  return {saved: name, id, project: conv.project_uuid || null, messages: (conv.chat_messages || []).length,
          photos: Object.keys(files).length, photosMissing: missing.length, bytes: blob.size};
})()
