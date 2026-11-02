#!/usr/bin/env python3
"""The Board's page: each role's corner (its state, what it works on, what just finished, what is next) and, below,
every role's open questions and decisions, answered with one click; mock-ups in a window of their own.

The reviewer, 2026-10-09: "we need a special screen where each agent can supply answers to my questions and present
decisions to me" (board.py says how the roles post and wait). Served on 127.0.0.1 only; it takes an answer only as JSON
from its own page (Origin and Host checked), as the review server takes rulings. Started by the operator, detached:

    python3 board_server.py --detach [--port PORT] [--log <board_dir>/server.log]
Needs only Python's standard library."""
import argparse
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board  # noqa: E402
import config  # noqa: E402
import role_usage  # noqa: E402

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Girsa Board</title>
<style>
/* THE LOOK: "A - Quiet" (the reviewer's Board #28, 2026-10-13, after "this tmux panels look fine, nice clear font and muted
   colors. the girsa panel looks amateurish and non-prof."; girsa-ui-steward's sheet). One face at few sizes, neutral greys
   and 1px hairlines; colour only in small marks - a role's thin top edge and its name, a state's dot, a plan step's dot.
   No filled pills, no thick stripes, no sentence in colour. */
:root{--bg:#f5f5f4;--card:#fff;--ink:#24272b;--muted:#6b7075;--line:#e0e0dd;--accent:#3a6596;--ok:#4f8048;
 --operator:#9a7f2e;--builder:#3d8590;--verifier:#4f8048;--ui-steward:#a75a80;--architect:#4a6fa0;
 --st-done:#4f8048;--st-next:#8a8f94;--st-working:#4f8048;--st-idle:#8a8f94;--st-waiting-agent:#b07a2a;--st-waiting-reviewer:#b5493f;--st-not-running:#a0a4a8;--st-landed:#4a6f9a}
@media (prefers-color-scheme:dark){:root{--bg:#161719;--card:#1d1e21;--ink:#d6d8db;--muted:#868b92;--line:#2b2d31;
 --accent:#86a8d2;--ok:#8fb487;--operator:#bfa66e;--builder:#73aab2;--verifier:#8fb487;--ui-steward:#c793ab;--architect:#86a2c9;
 --st-done:#8fb487;--st-next:#868b92;--st-working:#8fb487;--st-idle:#7b8087;--st-waiting-agent:#cda265;
 --st-waiting-reviewer:#d9857b;--st-not-running:#575c62;--st-landed:#8fb0d6}}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--ink);font:13px/1.5 -apple-system,"Segoe UI",system-ui,sans-serif;display:flex;
 flex-direction:column;overflow:hidden;-webkit-font-smoothing:antialiased;font-feature-settings:"tnum"}
header{display:flex;align-items:baseline;gap:14px;padding:10px 14px 8px;margin:0 0 10px;border-bottom:1px solid var(--line);flex:none}
h1{font-size:14px;font-weight:600;margin:0;white-space:nowrap}
#held{margin-left:auto;font-size:12px;font-weight:500;color:var(--st-waiting-agent);border:1px solid var(--st-waiting-agent);
 border-radius:4px;padding:1px 8px}#held:empty{display:none}
#quiet{font-size:12px;font-weight:600;color:var(--st-waiting-agent);border:1px solid var(--st-waiting-agent);border-radius:4px;
 padding:1px 8px}#quiet:empty{display:none}
#usage{font-size:12px;color:var(--muted)}#usage:empty{display:none}#usage.warn{color:var(--st-waiting-agent);font-weight:600}.key{display:flex;gap:10px;flex-wrap:wrap;color:var(--muted);font-size:11.5px}
.key span::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px;background:var(--c)}
/* THE CORNERS, laid out as the role panes in agents.sh's tmux window: steward and architect on top, operator and
   verifier in the middle, the builder along the bottom */
#roles{flex:none;height:54vh;display:grid;gap:10px;padding:0 14px;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr 1fr;
 grid-template-areas:"ui-steward architect" "operator verifier" "builder builder"}
.corner{grid-area:var(--area);min-height:0;overflow:hidden;background:var(--card);border:1px solid var(--line);
 box-shadow:inset 0 2px 0 var(--role);border-radius:4px;padding:9px 12px;display:flex;flex-direction:column;gap:6px}
.corner.not-running{opacity:.6}
.stall{flex:none;max-width:45%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11.5px;font-weight:600;
 color:var(--st-waiting-agent);border:1px solid var(--st-waiting-agent);border-radius:4px;padding:0 6px}
.landed-sum{white-space:pre-wrap;overflow:auto;min-height:0;font-size:12.5px}
.landing .sum{white-space:pre-wrap;margin:4px 0 0}
.tele{display:flex;gap:10px;flex:1 1 0;min-width:0;font-size:11.5px;color:var(--muted)}.tele span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tele .inpane{color:var(--st-waiting-reviewer);font-weight:600;flex:none;max-width:60%}
.tokens{border-collapse:collapse;font-size:12.5px}.tokens th,.tokens td{padding:3px 10px;text-align:right;border-bottom:1px solid var(--line)}
.tokens th:first-child,.tokens td:first-child,.tokens td:last-child{text-align:left}
.tokens.visits td:last-child{text-align:right}
.chead{display:flex;align-items:center;gap:10px;min-width:0}
.rname{font-weight:600;color:var(--role)}.age{margin-left:auto;color:var(--muted);font-size:11.5px;white-space:nowrap}
.badge{color:var(--sc);font-size:12px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:60%}
.badge::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--sc);margin-right:6px;
 vertical-align:1px}
.rows{display:grid;grid-template-columns:auto 1fr;grid-auto-rows:max-content;column-gap:10px;row-gap:5px;min-height:0;margin:0}
.corner.wide .rows{grid-template-columns:auto 1fr auto 1fr auto 1fr}.corner.wide .rows dd{padding-right:28px}
.rows dt{color:var(--muted);font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;padding-top:2px;white-space:nowrap}
.rows dd{margin:0;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:var(--clamp,2);overflow:hidden;min-width:0}
.rows dd.none{color:var(--muted);font-style:italic}
@media (max-height:800px){.corner:not(.wide) .rows dd{--clamp:1}}   /* a smaller window: one line each, the rest on hover */
/* A line box is never squeezed (max-content rows): a corner whose two-line entries do not fit is set to one line each by
   fitCorners() instead - the reviewer, 2026-10-12: "on the architect corner of the board, second lines are cut off"
   (girsa-ui-steward's measure: 1229x940, each dd 36px where its two lines need 39) */
/* THE QUESTIONS, below */
#q{flex:1;min-height:0;display:flex;flex-direction:column;padding:10px 14px 8px}
.qhead{display:flex;gap:12px;align-items:baseline;flex:none}
.qhead h2{font-size:13px;font-weight:600;margin:0}.qhead button{font:inherit;font-size:12px;background:none;border:none;
 color:var(--accent);cursor:pointer;padding:0}
#qlist{flex:1;min-height:0;overflow:auto;margin-top:6px}
.card,.plan,.qa{background:var(--card);border:1px solid var(--line);box-shadow:inset 0 2px 0 var(--role,var(--line));
 border-radius:4px;padding:10px 12px;margin:0 0 8px}
.head{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;font-size:11.5px;color:var(--muted)}
.role{font-weight:600;color:var(--role)}.title{font-size:14px;font-weight:600;margin:3px 0}
.body{white-space:pre-wrap;margin:0 0 6px}
.links a{display:inline-block;margin:0 12px 4px 0;color:var(--accent);word-break:break-all}
.change{font:inherit;font-size:12px;margin:4px 0 0 8px;padding:2px 10px;border-radius:4px;border:1px solid var(--line);
 background:var(--card);color:var(--accent);cursor:pointer;font-weight:400}
.mock{font:inherit;font-size:12px;margin:0 0 6px;padding:3px 10px;border-radius:4px;border:1px solid var(--line);
 background:transparent;color:var(--accent);cursor:pointer}
.change:hover,.mock:hover{border-color:var(--accent)}
.opts{display:flex;flex-direction:column;gap:5px;margin:6px 0}
.opt{display:flex;gap:10px;align-items:flex-start;text-align:left;font:inherit;color:inherit;background:transparent;
 border:1px solid var(--line);border-radius:4px;padding:6px 10px;cursor:pointer}
.opt:hover{border-color:var(--accent)}.opt b{min-width:1.6em}.opt .rec{color:var(--ok);font-weight:500;margin-left:6px}
.opt .detail{display:block;color:var(--muted);font-size:12px}
.free{display:flex;gap:8px;margin-top:6px}.free textarea{flex:1;min-height:34px;font:inherit;padding:5px 8px;
 border:1px solid var(--line);border-radius:4px;background:var(--bg);color:var(--ink)}
.free button{font:inherit;font-weight:600;padding:5px 14px;border-radius:4px;border:1px solid var(--accent);
 background:var(--accent);color:var(--card);cursor:pointer}
.done{opacity:.8}.answered{margin-top:4px;color:var(--ok);font-weight:500}.empty{color:var(--muted)}
/* A DEFERRED QUESTION (the reviewer: "i need a way to defer questions on the board"): "Later" is a secondary action beside
   Send - the quiet .change look, as tall as Send, no filled second button (Board #28, "A - Quiet"); the deferred line is a
   fact, not an answer - muted, not the answered green; "Bring back" sits on its line. (girsa-ui-steward's rules) */
.free button.change{margin:0;padding:5px 12px;background:var(--card);color:var(--accent);border-color:var(--line);font-weight:400}
.free button.change:hover{border-color:var(--accent)}
.answered:has(> button[data-undefer]){color:var(--muted);font-weight:400}
.answered .change{margin:0 0 0 6px}
/* THE PLAN: a multi-day effort's steps, in the questions' place while none waits - done greyed with a green dot, now in
   bold with an amber dot, coming in ink with an empty ring (no sentence in colour: Board #28) */
.plan .ptitle{font-size:14px;font-weight:600}.plan .pnote{color:var(--muted);font-size:11.5px;margin:0 0 4px}
.plan ol{margin:4px 0 0;padding:0;list-style:none;columns:300px;column-gap:28px}
.plan li{break-inside:avoid;padding:2px 0 2px 15px;text-indent:-15px;color:var(--ink)}
.plan li.d1{padding-left:31px}
.plan li::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:8px;vertical-align:1px}
.plan li.s-done{color:var(--muted)}.plan li.s-done::before{background:var(--st-done)}
.plan li.s-now{font-weight:600}.plan li.s-now::before{background:var(--st-waiting-agent)}
.plan li.s-next::before{box-shadow:inset 0 0 0 1.2px var(--muted)}
.plan .pkey{display:flex;gap:12px;font-size:11.5px;margin:0 0 2px;color:var(--muted)}
/* YOUR QUESTIONS: the reviewer's own questions asked in a role's pane, and the answers, kept (2026-10-13) */
.qa:target{outline:1px solid var(--accent)}
.qa .lbl{font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:8px 0 2px}
.qa .ask{white-space:pre-wrap;font-weight:600;margin:0}.qa .ans{white-space:pre-wrap;margin:0}
.qa .more{border-top:1px dashed var(--line);margin-top:8px;padding-top:2px}
</style></head><body>
<header><h1>Girsa Board</h1><div class="key" id="key"></div><div id="usage"></div><div id="quiet"></div><div id="held"></div></header>
<section id="roles"></section>
<section id="q"><div class="qhead"><h2 id="qtitle">Questions for you</h2><button id="toggle"></button><button id="deftoggle"></button><button id="qatoggle"></button><button id="tokentoggle">Tokens by role</button><button id="visittoggle">Visitors</button><button id="landtoggle"></button></div>
<div id="qlist"></div></section>
<script>
"use strict";
const ROLES = ["ui-steward", "architect", "operator", "verifier", "builder"];
const STATES = [["working", "Working"], ["idle", "Idle"], ["waiting-agent", "Waiting for another role"],
                ["waiting-reviewer", "Waiting for you"], ["landed", "Landed"], ["not-running", "Not running"]];
const ROLE_VAR = r => "var(--" + r.replace(/^girsa-/, "") + ")";
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const linkify = s => esc(s).replace(/https?:\/\/[^\s<]+/g, u => `<a href="${u}" target="_blank" rel="noopener">${u}</a>`);
const when = ts => { try { return new Date(ts).toLocaleString(); } catch (e) { return ts; } };
const ago = ts => { if (!ts) return "no report yet"; const m = Math.round((Date.now() - new Date(ts)) / 60000);
  return m < 1 ? "reported just now" : m < 60 ? `reported ${m} min ago` : m < 1440 ? `reported ${Math.floor(m / 60)} h ${m % 60} min ago` : "reported " + when(ts); };
let last = "", showDone = false, showQA = false, showDeferred = false, showTokens = false, showLandings = false, showVisitors = false, visitors = null, tokens = null, tokenDay = "", data = {items: [], roles: {}, qa: []};
const changing = new Set();   // answered items the reviewer is changing (their options open again)
document.getElementById("key").innerHTML = STATES.map(([k, w]) => `<span style="--c:var(--st-${k})">${w}</span>`).join("");
// WHAT THE SESSION ITSELF REPORTS (Q&A #56 ideas 1, 2 and 5): a prompt waiting for you in its pane, its context and
// prompt cache as its status line last saw them (compacted, no context until its next turn: what it was at its last
// turn), and the file it edited in the last 15 minutes - in the corner's head, so a corner keeps its height (the rows
// below are clamped to fit it)
function tele(s) {
  const hm = t => new Date(t * 1000).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
  const c = s.cache || {}, parts = [];
  if (s.context) parts.push(`context ${Math.round(s.context / 1000)}k`);
  else if (s.last_turn) parts.push(`compacted: context not known until its next turn (it was ${Math.round(s.last_turn.context / 1000)}k at ${hm(s.last_turn.at)})`);
  if (c.hit_ratio != null) parts.push(`cache ${c.warm && c.expires_at * 1000 > Date.now() ? "warm until " + hm(c.expires_at) : "cold"}, ${Math.round(c.hit_ratio * 100)}% read from it, ${c.misses || 0} miss${c.misses === 1 ? "" : "es"}${c.last_miss_cause && c.last_miss_cause.causes ? " (last: " + c.last_miss_cause.causes.join(", ") + ")" : ""}`);
  const e = s.editing;
  if (e && Date.now() - e.ts * 1000 < 15 * 60000) parts.push(`editing ${e.path.split("/").slice(-2).join("/")} at ${hm(e.ts)}`);
  const ask = s.prompt ? `<span class="inpane" title="${esc(s.prompt.message)}">Waiting for you in its pane since ${hm(s.prompt.ts)}: ${esc(s.prompt.message)}</span>` : "";
  return ask || parts.length ? `<div class="tele">${ask}<span title="${esc(parts.join(" · "))}">${esc(parts.join(" · "))}</span></div>` : "";
}
function corner(short) {
  const r = data.roles["girsa-" + short] || {}, wide = short === "builder";
  const row = (label, text) => `<dt>${label}</dt><dd dir="auto" class="${text ? "" : "none"}" title="${esc(text)}">${text ? esc(text) : "not reported"}</dd>`;
  return `<div class="corner ${esc(r.shown || "")}${wide ? " wide" : ""}" style="--area:${short};--role:${ROLE_VAR(short)};--sc:var(--st-${esc(r.shown || "idle")})">
    <div class="chead"><span class="rname">girsa-${short}</span><span class="badge" title="${esc(r.shown_words)}">${esc(r.shown_words || "")}</span>${r.also_words ? `<span class="badge" style="--sc:var(--st-waiting-agent)" title="${esc(r.also_words)}">${esc(r.also_words)}</span>` : ""}
      ${r.stall ? `<span class="stall" title="${esc(r.stall)}">${esc(r.stall)}</span>` : ""}${tele(r.session || {})}<span class="age">${esc(ago(r.ts))}${r.behind ? " - before its current work" : ""}</span></div>
    ${r.landing ? `<div class="landed-sum" dir="auto" title="${esc(r.landing.summary)}">${esc(r.landing.summary)}</div>`
      : `<dl class="rows">${row("Working on", r.now)}${row("Just finished", r.done)}${row("Next", r.next)}</dl>`}</div>`;
}
function card(it, open) {
  const opts = (it.options || []).map(o => `<button class="opt" data-id="${it.id}" data-key="${esc(o.key)}"${open ? "" : " disabled"}>
     <b>${esc(o.key)}</b><span><span dir="auto">${esc(o.label)}</span>${it.recommend === o.key ? '<span class="rec">(recommended)</span>' : ""}
     ${o.detail ? `<span class="detail" dir="auto">${linkify(o.detail)}</span>` : ""}</span></button>`).join("");
  const a = it.answer, w = it.withdrawn;
  const picked = a && (it.options || []).find(o => o.key === a.answer);
  const result = w ? `<div class="answered">Withdrawn by the role: ${esc(w.why)}</div>`
    : a ? `<div class="answered">Your answer: ${esc(a.answer)}${picked ? " - " + esc(picked.label) : ""}${a.note ? " (" + esc(a.note) + ")" : ""}
       <span class="head">${esc(when(a.ts))}</span>${(it.earlier || []).length ? `<div class="detail">Changed from ${
         it.earlier.map(x => esc(x.answer)).join(", then ")}. The role read your earlier answer when it came: say the change in its pane too.</div>` : ""}
       <button class="change" data-change="${it.id}">Change answer</button></div>` : "";
  const links = (it.links || []).filter(l => /^https?:\/\//i.test(l));
  const pages = it.mockup_pages || 0;
  return `<div class="card${open ? "" : " done"}" id="item-${it.id}" style="--role:${ROLE_VAR(it.role)}">
    <div class="head"><span class="role">${esc(it.role)}</span><span>#${it.id}</span><span>${esc(it.kind)}</span><span>${esc(when(it.ts))}</span></div>
    <div class="title" dir="auto">${esc(it.title)}</div>
    ${it.body ? `<div class="body" dir="auto">${linkify(it.body)}</div>` : ""}
    ${links.length ? `<div class="links">${links.map(l => `<a href="${esc(l)}" target="_blank" rel="noopener">${esc(l)}</a>`).join("")}</div>` : ""}
    ${pages ? `<button class="mock" data-mock="${it.id}">Mock-ups: ${pages} page${pages > 1 ? "s" : ""}, in their own window</button>` : ""}
    ${opts ? `<div class="opts">${opts}</div>` : ""}
    ${open && a ? `<div class="answered">Changing your answer - it is now ${esc(a.answer)}. <button class="change" data-unchange="${it.id}">Keep it</button></div>` : ""}
    ${open && it.deferred ? `<div class="answered">Deferred ${esc(when(it.deferred.ts))} - answer it here, or <button class="change" data-undefer="${it.id}">Bring back</button></div>` : ""}
    ${open ? `<div class="free"><textarea data-note="${it.id}" dir="auto" placeholder="${(it.options || []).length ? "A note with your choice, or your own answer" : "Your answer"}"></textarea>
      <button data-send="${it.id}">Send</button>${a || it.deferred ? "" : `<button class="change" data-defer="${it.id}" title="Put this question off: it moves to Deferred, and its role is told to go on with other work">Later</button>`}</div>` : result}</div>`;
}
function planCard(p) {
  const rows = p.steps.map(s => `<li class="s-${esc(s.state)} d${s.depth ? 1 : 0}" dir="auto">${esc(s.label)}</li>`).join("");
  return `<div class="plan" style="--role:${ROLE_VAR(p.role)}"><div class="ptitle" dir="auto">${esc(p.effort)}</div>
    <div class="pnote">${esc(p.role)}, ${esc(when(p.ts))}${p.note ? " - " + linkify(p.note) : ""}</div>
    <div class="pkey"><span style="color:var(--st-done)">done</span><b>in progress</b><span style="color:var(--st-next)">coming</span></div>
    <ol>${rows}</ol></div>`;
}
function qaCard(q) {
  const linksOf = ls => (ls || []).filter(l => /^https?:\/\//i.test(l));
  const part = (x, first) => `${x.question ? `<div class="lbl">${first ? "You asked" : "You asked next"}${first ? "" : ", " + esc(when(x.ts))}</div><div class="ask" dir="auto">${esc(x.question)}</div>` : ""}
    <div class="lbl">${esc(x.role)} answered${first || x.question ? "" : " further, " + esc(when(x.ts))}</div><div class="ans" dir="auto">${linkify(x.answer)}</div>
    ${linksOf(x.links).length ? `<div class="links">${linksOf(x.links).map(l => `<a href="${esc(l)}" target="_blank" rel="noopener">${esc(l)}</a>`).join("")}</div>` : ""}`;
  return `<div class="qa" id="qa-${q.qa}" style="--role:${ROLE_VAR(q.role)}">
    <div class="head"><span class="role">${esc(q.role)}</span><span>Q&amp;A #${q.qa}</span><span>${esc(when(q.ts))}</span></div>
    ${part(q, true)}${(q.more || []).map(m => `<div class="more" style="--role:${ROLE_VAR(m.role)}">${part(m, false)}</div>`).join("")}</div>`;
}
function fitCorners() {   // two lines each where they fit, else one line each (the rest on hover), corner by corner
  document.querySelectorAll("#roles .corner:not(.wide)").forEach(c => {
    c.style.removeProperty("--clamp");
    if (c.scrollHeight > c.clientHeight + 1) c.style.setProperty("--clamp", 1);
  });
}
addEventListener("resize", fitCorners);
// THE PLAN'S BUDGET (Q&A #56 A): each window's use as the roles' status lines last read it, in the waiting colour at
// BUDGET_WARN, when every role is told to land
function drawUsage() {
  const u = data.usage, el = document.getElementById("usage");
  const t = (s, o) => new Date(s * 1000).toLocaleString([], o);
  const ws = u ? [["five_hour", "5-hour", {hour: "2-digit", minute: "2-digit"}], ["seven_day", "7-day", {weekday: "short", hour: "2-digit", minute: "2-digit"}]]
    .filter(([k]) => u[k]).map(([k, label, o]) => `${label} ${Math.round(u[k].used_percentage)}% (resets ${t(u[k].resets_at, o)})`) : [];
  el.textContent = ws.length ? `Plan used: ${ws.join(" · ")} - as of ${t(u.seen_at, {hour: "2-digit", minute: "2-digit"})}` : "";
  el.className = u && ["five_hour", "seven_day"].some(k => u[k] && u[k].used_percentage >= data.budget_warn) ? "warn" : "";
}
function drawHeld() {
  const h = data.held;
  document.getElementById("held").textContent = h ? `Main held by ${h.role} since ${new Date(h.ts).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})} - ${h.why}` : "";
}
// NOTHING IS MOVING (the reviewer, 2026-10-28: "why are we stuck? not waiting for me" - every role idle 10:56-14:34
// while the builder's next piece waited on conditions met hours before): no role working and nothing on the reviewer
// for QUIET_MIN minutes, with each role's Next - one of them may be waiting on what has already happened
function drawQuiet() {
  const q = data.quiet, el = document.getElementById("quiet");
  const next = q ? Object.entries(q.next).filter(([, n]) => n).map(([r, n]) => `${r.replace(/^girsa-/, "")}: ${n}`) : [];
  const stuck = q ? Object.entries(q.stuck || {}).map(([r, w]) => `${r.replace(/^girsa-/, "")} waits for ${(w || "?").replace(/^girsa-/, "")}`) : [];
  el.textContent = q ? `Nothing is moving since ${new Date(q.since * 1000).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})} (${q.minutes} min): no role working, ` +
    (stuck.length ? stuck.join(", ") : "nothing waiting for you") : "";
  el.title = next.join("\n");
}
function draw() {
  drawHeld(); drawUsage(); drawQuiet();
  document.getElementById("roles").innerHTML = ROLES.map(corner).join(""); fitCorners();
  const items = data.items;
  // DEFERRED (the reviewer, 2026-10-13: "i need a way to defer questions on the board"): put off, in a list of its own
  const open = items.filter(it => !it.answer && !it.withdrawn && !it.deferred).sort((a, b) => a.id - b.id);
  const deferred = items.filter(it => !it.answer && !it.withdrawn && it.deferred).sort((a, b) => a.id - b.id);
  const done = items.filter(it => it.answer || it.withdrawn).sort((a, b) => b.id - a.id);
  // THE PLAN TAKES THE QUESTIONS' PLACE WHILE NONE WAITS, and gives it back when one comes
  const plan = !showDone && !showDeferred && !open.length && (data.plans || []).length;
  // YOUR QUESTIONS, newest first, in the questions' place while chosen
  const qa = (data.qa || []).slice().sort((a, b) => b.qa - a.qa);
  document.getElementById("tokentoggle").hidden = showTokens;
  document.getElementById("visittoggle").hidden = showVisitors;
  const lands = (data.landings || []).slice().reverse(), lt = document.getElementById("landtoggle");
  lt.hidden = showLandings || !lands.length; lt.textContent = `Landings (${lands.length})`;
  // LANDINGS, newest first: every session's landing summary, kept after its corner moves on (the reviewer, 2026-10-25)
  if (showLandings) {
    document.getElementById("qtitle").textContent = `Landings (${lands.length})`;
    document.getElementById("toggle").textContent = "Back";
    document.getElementById("deftoggle").hidden = true; document.getElementById("qatoggle").hidden = false;
    document.getElementById("qlist").innerHTML = lands.map(l => `<div class="qa landing" style="--role:${ROLE_VAR(l.role)}">
      <div class="head"><span class="role">${esc(l.role)}</span><span>landed ${esc(when(l.ts))}</span>${l.length ? `<span>ran ${esc(l.length)}</span>` : ""}${l.nth_words ? `<span>${esc(l.nth_words)}</span>` : ""}${l.session ? `<span>session ${esc(l.session.slice(0, 8))}</span>` : ""}</div>
      <div class="sum" dir="auto">${linkify(l.summary)}</div></div>`).join("");
    return;
  }
  if (showVisitors) {
    document.getElementById("qtitle").textContent = "Visitors";
    document.getElementById("toggle").textContent = "Back";
    document.getElementById("deftoggle").hidden = true; document.getElementById("qatoggle").hidden = false;
    document.getElementById("qlist").innerHTML = visitorsTable();
    return;
  }
  if (showTokens) {
    document.getElementById("qtitle").textContent = "Tokens by role";
    document.getElementById("toggle").textContent = "Back";
    document.getElementById("deftoggle").hidden = true; document.getElementById("qatoggle").hidden = false;
    document.getElementById("qlist").innerHTML = tokenTable();
    return;
  }
  document.getElementById("qtitle").textContent = showQA ? `Your questions and the answers (${qa.length})`
    : showDone ? `Answered and withdrawn (${done.length})`
    : showDeferred ? `Deferred (${deferred.length})`
    : plan ? "No question waits for you - the plan" : "Questions for you" + (open.length ? ` (${open.length})` : "");
  document.getElementById("toggle").textContent = showDone || showQA || showDeferred ? "Back" : `Show answered and withdrawn (${done.length})`;
  const dt = document.getElementById("deftoggle");
  dt.hidden = showDone || showQA || showDeferred || !deferred.length; dt.textContent = `Deferred (${deferred.length})`;
  const qt = document.getElementById("qatoggle");
  qt.hidden = showQA; qt.textContent = `Your questions (${qa.length})`;
  document.getElementById("qlist").innerHTML = showQA
    ? (qa.length ? qa.map(qaCard).join("") : '<p class="empty">None yet: a question you ask in a role\'s pane is copied here with its answer.</p>')
    : showDone ? done.map(it => card(it, changing.has(it.id))).join("")
    : showDeferred ? (deferred.length ? deferred.map(it => card(it, true)).join("") : '<p class="empty">Nothing is deferred.</p>')
    : open.length ? open.map(it => card(it, true)).join("")
    : plan ? data.plans.map(planCard).join("") : '<p class="empty">Nothing is waiting for you.</p>';
  document.title = (open.length ? "(" + open.length + ") " : "") + "Girsa Board";
}
// TOKENS BY ROLE (Q&A #56 ideas 3-4): one day's calls, tokens and compactions per role from the transcripts, weighted
// at relative list prices (input 1, cache write 2, cache read 0.1, output 5), subagents by model
async function loadTokens() {
  const r = await fetch("/api/usage" + (tokenDay ? "?day=" + tokenDay : "")); tokens = r.ok ? await r.json() : {};
  const w = await fetch("/api/usage-week"); week = w.ok ? await w.json() : null; draw();
}
let week = null;
const errWords = e => !e ? "" : Object.entries(e).filter(([, n]) => n).map(([k, n]) => n + " " + k).join(", ") || "none";
// THE WEEK (Q&A #56 idea 3): each role's weighted tokens on each of the last seven days, subagents included
function weekTable() {
  if (!week) return "";
  const roles = [...new Set(week.flatMap(([, d]) => Object.keys(d)))].sort();
  const m = x => x ? (x / 1e6).toFixed(1) + "M" : "-";
  return `<h3>The last seven days, weighted</h3><table class="tokens"><tr><th>Role</th>${week.map(([d]) => `<th>${esc(d.slice(5))}</th>`).join("")}</tr>` +
    roles.map(r => `<tr><td>${esc(r)}</td>${week.map(([, d]) => `<td>${m(d[r])}</td>`).join("")}</tr>`).join("") + "</table>";
}
function tokenTable() {
  const n = x => Number(x || 0).toLocaleString();
  const rows = Object.entries(tokens || {}).sort((a, b) => b[1].main.weighted - a[1].main.weighted).map(([role, r]) =>
    `<tr><td>${esc(role)}</td><td>${r.sessions}</td><td>${n(r.main.calls)}</td><td><b>${n(r.main.weighted)}</b></td><td>${n(r.main.inp)}</td><td>${n(r.main.cw)}</td><td>${n(r.main.cr)}</td><td>${n(r.main.out)}</td><td>${r.compactions}</td><td>${errWords(r.errors)}</td><td>${
      Object.entries(r.sub).map(([m, t]) => esc(m.replace(/^claude-/, "")) + ": " + n(t.weighted)).join(", ")}</td></tr>`).join("");
  return `<p><label>Day <input type="date" id="tokenday" value="${esc(tokenDay)}"></label> - weighted: input 1, cache write 2, cache read 0.1, output 5 (relative list prices on one model)</p>
    <table class="tokens"><tr><th>Role</th><th>Sessions</th><th>Calls</th><th>Weighted</th><th>Input</th><th>Cache write</th><th>Cache read</th><th>Output</th><th>Compactions</th><th>Errors</th><th>Subagents, weighted by model</th></tr>${rows || '<tr><td colspan="11">No calls that day.</td></tr>'}</table>
    <p>Errors: api - the API answered with an error; hook - a hook failed; refused - the role guard refused a call; tool - any other failed tool call.</p>
    ${weekTable()}`;
}
// VISITORS (the reviewer, 2026-10-28: "show the visitor stats on the board. updated twice a day for now"; Board #96):
// the host's traffic report per site and day, newest first, as traffic.json last brought it; a report more than 13 hours
// old says so, since one is due every 12
async function loadVisitors() {
  const r = await fetch("/api/visitors"); visitors = r.ok ? await r.json() : {error: "The Board could not read the report."}; draw();
}
function visitorsTable() {
  const v = visitors || {};
  if (v.missing) return '<p class="empty">No report yet: traffic.json in the Board\'s folder is written twice a day from the host\'s access logs.</p>';
  if (v.error) return `<p class="empty">${esc(v.error)}</p>`;
  const hours = v.made ? (Date.now() - new Date(v.made)) / 3600000 : null;
  // A NUMBER THE REPORT DOES NOT HAVE IS "?", NEVER 0 (Lesson 59; girsa-demo-operator on bea05539: its cron run has no
  // --own, since the home address changes, so every day's "ours" is null and our visits are among the visits)
  const n = x => x == null ? "?" : Number(x).toLocaleString(), m = x => x == null ? "?" : Number(x).toFixed(1);
  const apart = (v.sites || []).every(s => (s.days || []).every(d => d.ours != null));
  const head = `<p>Made on the host ${esc(when(v.made))}, from its logs through ${esc(when(v.logs_through))}${hours != null && hours > 13 ? ` - <b>${Math.floor(hours)} hours old: the last update did not come</b>` : ""}.
    Visits by people - bots, scanners and our checks left out; a visit ends after 30 minutes without a request; ${apart ? `"ours" are our own machines' visits, counted apart` : `our own visits are not told apart in this report ("?" under Ours): they are among the visits`}; days in UTC.</p>`;
  return head + (v.sites || []).map(s => {
    const demo = s.kind === "demo", days = (s.days || []).slice().sort((a, b) => b.day < a.day ? -1 : 1);
    const rows = days.map(d => `<tr><td>${esc(d.day)}</td><td><b>${n(d.visits)}</b></td><td>${n(d.ours)}</td><td>${n(d.phones)}</td><td>${n(d.minutes_total == null ? null : Math.round(d.minutes_total))}</td><td>${m(d.minutes_median)}</td><td>${m(d.minutes_longest)}</td>${
      demo ? `<td>${n(d.saved)} (${n(d.saves)})</td><td>${n(d.checked)}</td>` : `<td>${n(d.films)}</td>`}</tr>`).join("");
    return `<h3>${esc(s.site)}</h3><table class="tokens visits"><tr><th>Day</th><th>Visits</th><th>Ours</th><th>On a phone</th><th>Minutes</th><th>Median</th><th>Longest</th>${
      demo ? "<th>Saved a ruling (saves)</th><th>Checked their answers</th>" : "<th>Played a film</th>"}</tr>${rows || `<tr><td colspan="${demo ? 9 : 8}">No visits.</td></tr>`}</table>`;
  }).join("");
}
document.addEventListener("change", e => { if (e.target.id === "tokenday") { tokenDay = e.target.value; loadTokens(); } });
async function refresh(force) {
  const typing = document.activeElement && document.activeElement.tagName === "TEXTAREA" && document.activeElement.value;
  const r = await fetch("/api/board"); const got = await r.json(); const key = JSON.stringify(got);
  if (!force && key === last) return;
  last = key; data = got;
  if (typing) { document.getElementById("roles").innerHTML = ROLES.map(corner).join(""); fitCorners(); drawHeld(); drawUsage(); return; }   // keep a draft answer
  draw();
}
async function setDeferred(id, on) {
  const r = await fetch("/api/defer", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({id, defer: on})});
  if (!r.ok) { document.getElementById("qtitle").textContent = "Not changed: " + await r.text(); return; }
  refresh(true);
}
async function send(id, answer) {
  const note = (document.querySelector(`textarea[data-note="${id}"]`) || {}).value || "";
  const body = answer === null ? {id, answer: note} : {id, answer, note};
  if (changing.has(id)) body.change = true;
  if (!String(body.answer).trim()) return;
  const r = await fetch("/api/answer", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
  if (!r.ok) { document.getElementById("qtitle").textContent = "Not sent: " + await r.text(); return; }
  if (document.activeElement) document.activeElement.blur();
  changing.delete(id);
  refresh(true);
}
document.addEventListener("click", e => {
  const m = e.target.closest("button[data-mock]");
  if (m) { window.open("/mockups/" + m.dataset.mock, "girsa-mockups", "popup,width=1400,height=850"); return; }
  if (e.target.id === "toggle") { if (showQA || showDeferred || showTokens || showLandings || showVisitors) showQA = showDeferred = showTokens = showLandings = showVisitors = false; else showDone = !showDone; draw(); return; }
  if (e.target.id === "landtoggle") { showLandings = true; showDone = showQA = showDeferred = showTokens = showVisitors = false; draw(); return; }
  if (e.target.id === "tokentoggle") { showTokens = true; showDone = showQA = showDeferred = showLandings = showVisitors = false; return loadTokens(); }
  if (e.target.id === "visittoggle") { showVisitors = true; showDone = showQA = showDeferred = showTokens = showLandings = false; return loadVisitors(); }
  if (e.target.id === "qatoggle") { showQA = true; showDone = showDeferred = showTokens = showLandings = showVisitors = false; draw(); return; }
  if (e.target.id === "deftoggle") { showDeferred = true; showDone = showQA = false; draw(); return; }
  const df = e.target.closest("button[data-defer], button[data-undefer]");
  if (df) return setDeferred(+(df.dataset.defer || df.dataset.undefer), !!df.dataset.defer);
  const ch = e.target.closest("button[data-change]"); if (ch) { changing.add(+ch.dataset.change); draw(); return; }
  const un = e.target.closest("button[data-unchange]"); if (un) { changing.delete(+un.dataset.unchange); draw(); return; }
  const opt = e.target.closest(".opt[data-id]"); if (opt && !opt.disabled) return send(+opt.dataset.id, opt.dataset.key);
  const s = e.target.closest("button[data-send]"); if (s) return send(+s.dataset.send, null);
});
// A LINK TO ONE Q&A (http://127.0.0.1:8450/#qa-N, the link a role gives in its pane) opens Your questions at it
function goToQA() {
  if (!/^#qa-\d+$/.test(location.hash)) return;
  showQA = true; showDone = showDeferred = false; draw();
  const el = document.getElementById(location.hash.slice(1)); if (el) el.scrollIntoView({block: "start"});
}
addEventListener("hashchange", goToQA);
refresh(true).then(goToQA); setInterval(() => refresh(false), 5000);
</script></body></html>"""

MOCKUPS = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Girsa Board - mock-ups</title>
<style>
/* The mock-ups' window in the Board's look (Board #28, "A - Quiet") */
:root{--bg:#f5f5f4;--card:#fff;--ink:#24272b;--muted:#6b7075;--line:#e0e0dd;--accent:#3a6596}
@media (prefers-color-scheme:dark){:root{--bg:#161719;--card:#1d1e21;--ink:#d6d8db;--muted:#868b92;--line:#2b2d31;--accent:#86a8d2}}
*{box-sizing:border-box}html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--ink);font:13px/1.5 -apple-system,"Segoe UI",system-ui,sans-serif;display:flex;
 flex-direction:column;overflow:hidden;-webkit-font-smoothing:antialiased}
header{flex:none;display:flex;gap:14px;align-items:baseline;padding:8px 12px}
header b{font-size:14px;font-weight:600}.muted{color:var(--muted)}
header button{font:inherit;padding:2px 10px;border-radius:4px;border:1px solid var(--line);background:var(--card);color:var(--ink);
 cursor:pointer}
main{flex:1;min-height:0;display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 8px 8px}
figure{margin:0;min-height:0;display:flex;flex-direction:column;background:var(--card);border:1px solid var(--line);border-radius:4px;
 padding:6px}
figcaption{flex:none;font-weight:600;margin:0 0 4px}
figure div{flex:1;min-height:0;display:flex;align-items:center;justify-content:center}
figure img{max-width:100%;max-height:100%;object-fit:contain}
</style></head><body>
<header><b id="title"></b><span id="where" class="muted"></span>
 <button id="prev">Previous page</button><button id="next">Next page</button>
 <span class="muted">Keys: left and right arrows</span></header>
<main id="pane"></main>
<script>
"use strict";
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const id = +location.pathname.split("/").pop();
let pages = [], at = 0;
function show() {
  at = Math.max(0, Math.min(at, pages.length - 1));
  document.getElementById("where").textContent = pages.length ? `page ${at + 1} of ${pages.length}` : "no mock-ups";
  document.getElementById("pane").innerHTML = (pages[at] || []).map(p => `<figure><figcaption dir="auto">${p.key ? esc(p.key) + ": " : ""}${esc(p.label)}</figcaption>
    <div><img src="/img/${id}/${p.n}" alt="${esc(p.label)}"></div></figure>`).join("");
  history.replaceState(null, "", "#page-" + (at + 1));
}
async function load() {
  const r = await fetch("/api/mockups/" + id); if (!r.ok) { document.getElementById("title").textContent = "No such item"; return; }
  const d = await r.json(); pages = d.pages;
  document.getElementById("title").textContent = `#${id} ${d.title}`;
  document.title = `#${id} mock-ups - Girsa Board`;
  at = Math.max(0, (parseInt((location.hash.match(/page-(\d+)/) || [])[1], 10) || 1) - 1); show();
}
document.addEventListener("keydown", e => {
  if (e.key === "ArrowRight") { at++; show(); e.preventDefault(); }
  if (e.key === "ArrowLeft") { at--; show(); e.preventDefault(); }
});
document.getElementById("prev").onclick = () => { at--; show(); };
document.getElementById("next").onclick = () => { at++; show(); };
load();
</script></body></html>"""


def _rendered(cfg):
    """THE PAGES WITH THE PROJECT'S NAMES (mishmeret/config.py): its name, its roles' prefix, page colours and order -
    each put where the template names the project it was written for, every spot counted, so a template edit that
    moves one fails here at start rather than drawing a page half one project's. The corners are laid out two to a
    row in `page_order`, a last odd one across the row."""
    corners = [r for r in cfg["roles"] if r["corner"]]
    prefixes = {r["name"][:-len(r["short"])] for r in cfg["roles"] if r["name"].endswith(r["short"])}
    if len(prefixes) != 1 or any(not r["name"].endswith(r["short"]) for r in cfg["roles"]):
        raise config.ConfigError("every role's name must be one prefix and its short name, for the page")
    prefix, order = prefixes.pop(), cfg["page_order"]
    rows = [order[i:i + 2] if i + 1 < len(order) else [order[i]] * 2 for i in range(0, len(order), 2)]
    wide = order[-1] if len(order) % 2 else ""
    page, mock = PAGE, MOCKUPS
    for old, new, n, which in (
            ("Girsa Board", cfg["project"] + " Board", 3, "page"), ("Girsa Board", cfg["project"] + " Board", 2, "mock"),
            ("--operator:#9a7f2e;--builder:#3d8590;--verifier:#4f8048;--ui-steward:#a75a80;--architect:#4a6fa0;",
             "".join(f"--{r['short']}:{r['page_light']};" for r in corners), 1, "page"),
            ("--operator:#bfa66e;--builder:#73aab2;--verifier:#8fb487;--ui-steward:#c793ab;--architect:#86a2c9;",
             "".join(f"--{r['short']}:{r['page_dark']};" for r in corners), 1, "page"),
            ('grid-template-areas:"ui-steward architect" "operator verifier" "builder builder"',
             "grid-template-areas:" + " ".join('"' + " ".join(r) + '"' for r in rows), 1, "page"),
            ('const ROLES = ["ui-steward", "architect", "operator", "verifier", "builder"];',
             "const ROLES = [" + ", ".join(json.dumps(s) for s in order) + "];", 1, "page"),
            ('short === "builder"', f'short === "{wide}"', 1, "page"),
            ("/^girsa-/", "/^" + prefix + "/", 4, "page"), ('"girsa-" + short', f'"{prefix}" + short', 1, "page"),
            ("girsa-${short}", prefix + "${short}", 1, "page"), ('"girsa-mockups"', f'"{prefix}mockups"', 1, "page"),
            ("http://127.0.0.1:8450/#qa-N", f"http://127.0.0.1:{cfg['board_port']}/#qa-N", 1, "page")):
        text = page if which == "page" else mock
        if text.count(old) != n:
            raise RuntimeError(f"the Board's {which} template has {text.count(old)} of {old!r}, not {n}")
        if which == "page":
            page = page.replace(old, new)
        else:
            mock = mock.replace(old, new)
    return page, mock


PAGE, MOCKUPS = _rendered(config.load())


class Live:
    """Each role's running state, from `claude agents --json`, and the time of the last prompt put to it (from the tail of
    its transcript) - read at most every few seconds, whatever the number of pages open."""
    EVERY = 5

    def __init__(self):
        self.lock, self.at, self.value = threading.Lock(), 0.0, {}

    def get(self):
        with self.lock:
            if time.time() - self.at >= self.EVERY:
                self.value, self.at = self._read(), time.time()
            return self.value

    @staticmethod
    def _read():
        out = {}
        for row in board.live_agents():
            if row.get("name") in board.ROLES:
                status = row.get("status")
                if status == "busy" and role_usage.turn_ended(row.get("sessionId")):
                    status = "idle"     # busy only for a background task of its own: its turn has ended
                out[row["name"]] = {"status": status, "last_prompt": last_prompt(row.get("sessionId")),
                                    "session_id": row.get("sessionId")}
        return out


def last_prompt(session_id, tail=512 * 1024):
    """The time of the last message put to a session (a prompt or a notification - not a tool's result), or None."""
    path = role_usage.transcript(session_id)
    if path:
        with open(path, "rb") as fh:
            fh.seek(max(0, os.path.getsize(path) - tail))
            lines = fh.read().decode("utf-8", "replace").splitlines()
        for line in reversed(lines):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") != "user":
                continue
            c = (e.get("message") or {}).get("content")
            if isinstance(c, str) or (isinstance(c, list) and not any(b.get("type") == "tool_result" for b in c
                                                                      if isinstance(b, dict))):
                return e.get("timestamp")
    return None


LIVE = Live()
USAGE_LOCK = threading.Lock()


STALL_WORKING_MIN, STALL_WAITING_MIN, QUIET_MIN = 20, 60, 30


def _ends_at_the_reviewer(role, roles):
    """True when following waiting_for from a waiting-agent role reaches a role waiting for the reviewer; False at a
    role doing nothing, an unknown one, or a cycle."""
    seen = set()
    while roles.get(role, {}).get("shown") == "waiting-agent" and role not in seen:
        seen.add(role)
        role = roles[role].get("waiting_for")
    return role not in seen and roles.get(role, {}).get("shown") == "waiting-reviewer"


def quiet(roles, live, its, held, now=None):
    """NOTHING IS MOVING (the reviewer, 2026-10-28: "why are we stuck? not waiting for me"; "go"), or None: at least one
    role running, none working or waiting for the reviewer (in its window, on the Board, or by its report), no item
    waiting, main not held - and no running role's transcript written for QUIET_MIN minutes. As {"since", "minutes",
    "next"}: the last write, and each running role's Next, where a wait on what has already happened shows.
    A WAIT ON A ROLE THAT IS NOT WORKING (the reviewer, 2026-10-30: "the ver [verifier] says it is waiting on the build
    [builder] who is doing nothing"; 09:13-11:00 no quiet, because #108 waited for the reviewer): with no role working,
    a role waiting for another is stuck whatever waits for the reviewer elsewhere - "stuck", each such role and whom it
    waits for. A wait whose chain ends at a role waiting for the reviewer is not (girsa-verifier's LOW on ff051e8e:
    21 such chains on the Board since 10-11, e.g. 10-27 11:31, four roles on girsa-architect while it waited for the
    reviewer); a cycle is."""
    if held or not live or any(r["shown"] == "working" for r in roles.values()):
        return None
    stuck = {role: r.get("waiting_for") for role, r in roles.items()
             if r["shown"] == "waiting-agent" and not _ends_at_the_reviewer(role, roles)}
    if not stuck and (any(board.is_waiting(it) for it in its.values())
                      or any(r["shown"] == "waiting-reviewer" for r in roles.values())):
        return None
    paths = [role_usage.transcript(lv.get("session_id")) for lv in live.values()]
    moved = [os.path.getmtime(p) for p in paths if p]
    if not moved:
        return None
    since, now = max(moved), now or time.time()
    if now - since < QUIET_MIN * 60:
        return None
    return {"since": int(since), "minutes": int((now - since) // 60),
            "next": {role: roles.get(role, {}).get("next") for role in sorted(live)}, "stuck": stuck}


def stalled(st, lv, shown, also_words):
    """A role that may be stuck (Q&A #56 idea 1; the reviewer, 2026-10-25: "build 1 - 4"), as words, or None: working
    with nothing written to its transcript for STALL_WORKING_MIN minutes (a hung command, or the API stalled - or a long
    command it is waiting on), or reported waiting for another role for STALL_WAITING_MIN minutes.
    THE WAIT ONLY WHERE THE CORNER SHOWS IT (girsa-verifier, 2026-10-26, MEDIUM 1): `shown` and `also_words` are
    shown_state's and also_waiting's, so one freshness rule decides both - a waiting report the role has since moved on
    from, or a role not running or landed, is not flagged as waiting."""
    now = time.time()
    if lv and lv.get("status") == "busy" and lv.get("session_id"):
        path = role_usage.transcript(lv["session_id"])
        quiet = (now - os.path.getmtime(path)) / 60 if path else 0
        if quiet >= STALL_WORKING_MIN:
            return f"working, but nothing new for {int(quiet)} min - a long command, or stuck"
    if (shown == "waiting-agent" or also_words) and st.get("waiting_for"):
        since = board._when(st.get("state_ts"))
        waited = (now - since.timestamp()) / 60 if since else 0
        if waited >= STALL_WAITING_MIN:
            return f"waiting for {st['waiting_for']} for {int(waited // 60)} h {int(waited % 60)} min"
    return None


FACTS = {}   # session id: its start and its number that day - fixed once the session has landed


def with_facts(landing):
    """A landing with how long its session ran and which of its role's sessions that day it was (the reviewer,
    2026-10-25: "include session length alongside completion time - and number of sessions today")."""
    sid = landing.get("session")
    if sid and sid not in FACTS:
        FACTS[sid] = role_usage.session_facts(sid)
    f = FACTS.get(sid) or {}
    out = dict(landing, **f)
    if f.get("started"):
        mins = max(0, int((board._when(landing["ts"]) - board._when(f["started"])).total_seconds() // 60))
        out["length"] = (f"{mins // 60} h {mins % 60} min" if mins >= 60 else f"{mins} min")
        n = f["nth_today"]
        out["nth_words"] = f"session {n} of the day"
    return out


def visitors():
    """The demo's and the home page's visits by people, as handover/web/traffic_report.py --json wrote them on the host
    and the fetch, twice a day, brought them to traffic.json in the Board's folder (the reviewer, 2026-10-28: "show the
    visitor stats on the board. updated twice a day for now"; Board #96); {"missing": True} before the first."""
    path = os.path.join(board.board_dir(), "traffic.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {"missing": True}
    except (OSError, ValueError) as e:
        return {"error": f"{path} could not be read: {e}"}


def board_view():
    events = board.read_events()
    its = board.items(events)
    live = LIVE.get()
    roles = {}
    for role, st in board.statuses().items():
        open_ids = sorted(i for i, it in its.items() if it["role"] == role and board.is_waiting(it))
        lv = live.get(role)
        shown, words = board.shown_state(st, lv and lv["status"], open_ids, lv and lv["last_prompt"])
        # LANDED (the reviewer, 2026-10-25): the role's last landing is shown until another session runs as it - over
        # "Not running" once the night run has closed it, and over Idle while the landed session is still open
        landing = board.last_landing(role, events)
        if landing and shown in ("not-running", "idle") and (
                lv.get("session_id") == landing.get("session") if lv else not board.started_since(role, landing)):
            landing = with_facts(landing)
            shown, words = "landed", "Landed " + landing["ts"][11:16] + "".join(
                " \u00b7 " + x for x in (landing.get("length"), landing.get("nth_words")) if x)
        else:
            landing = None
        also_words = board.also_waiting(st, lv and lv["status"], lv and lv["last_prompt"])
        roles[role] = dict(st, shown=shown, shown_words=words, landing=landing, stall=stalled(st, lv, shown, also_words),
                           also_words=also_words,
                           behind=board.behind_its_work(st, lv and lv["status"], lv and lv["last_prompt"]),
                           session=board.session_record(lv["session_id"]) if lv and lv.get("session_id") else {})
    items = [dict(it, mockup_pages=len(board.mockup_pages(it))) for it in its.values()]
    held = board.held(events)
    return {"roles": roles, "items": items, "plans": board.plans(), "held": held, "quiet": quiet(roles, live, its, held),
            "qa": list(board.qas(events).values()),
            "landings": [with_facts(l) for l in board.landings(events)],
            "usage": board.usage(), "budget_warn": board.BUDGET_WARN}


class Handler(BaseHTTPRequestHandler):
    ALLOWED_HOSTS = ("127.0.0.1", "localhost")

    def _host_ok(self):
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        return host in self.ALLOWED_HOSTS

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, "host not allowed", "text/plain; charset=utf-8")
        if self.path in ("/", "/index.html") or self.path.startswith("/#"):
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if self.path.startswith("/img/"):           # only an image an item names, and only an image
            try:
                _, _, item_id, n = self.path.split("/")
                path = board.items()[int(item_id)]["images"][int(n)]
            except (ValueError, KeyError, IndexError, TypeError):
                return self._send(404, "not found", "text/plain; charset=utf-8")
            ext = os.path.splitext(path)[1].lower()
            if ext not in board.IMAGE_TYPES or not os.path.isfile(path):
                return self._send(404, "not found", "text/plain; charset=utf-8")
            with open(path, "rb") as fh:
                return self._send(200, fh.read(), {".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}.get(ext, "image/jpeg"))
        if self.path == "/api/items":
            return self._send(200, json.dumps(list(board.items().values()), ensure_ascii=False))
        if self.path == "/api/visitors":             # the host's traffic report, fetched twice a day (Board #96)
            return self._send(200, json.dumps(visitors(), ensure_ascii=False))
        if self.path == "/api/usage-week":           # the last seven days, weighted, per role (Q&A #56 idea 3)
            with USAGE_LOCK:
                return self._send(200, json.dumps(role_usage.role_week(), ensure_ascii=False))
        if self.path.split("?")[0] == "/api/usage":     # tokens per role for a day (Q&A #56 ideas 3-4)
            day = self.path.partition("day=")[2][:10] or None
            if day and not (len(day) == 10 and day[4] == day[7] == "-" and (day[:4] + day[5:7] + day[8:]).isdigit()):
                return self._send(400, "day is YYYY-MM-DD", "text/plain; charset=utf-8")
            with USAGE_LOCK:
                return self._send(200, json.dumps(role_usage.role_usage(day), ensure_ascii=False))
        if self.path == "/api/board":
            return self._send(200, json.dumps(board_view(), ensure_ascii=False))
        if self.path.startswith(("/mockups/", "/api/mockups/")):
            try:
                it = board.items()[int(self.path.rstrip("/").split("/")[-1].split("#")[0])]
            except (ValueError, KeyError):
                return self._send(404, "not found", "text/plain; charset=utf-8")
            if self.path.startswith("/mockups/"):
                return self._send(200, MOCKUPS, "text/html; charset=utf-8")
            return self._send(200, json.dumps({"title": it["title"], "pages": board.mockup_pages(it)}, ensure_ascii=False))
        return self._send(404, "not found", "text/plain; charset=utf-8")

    def _body(self):
        """The request's JSON object; anything else a ValueError, which each route answers with its own code (a list
        dropped the connection, the audit's item 18)."""
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        if not isinstance(data, dict):
            raise ValueError("a JSON object is needed")
        return data

    def do_POST(self):
        origin = self.headers.get("Origin") or ""
        own = {f"http://{h}:{self.server.server_address[1]}" for h in self.ALLOWED_HOSTS}
        if not self._host_ok() or origin not in own \
                or not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self._send(403, "answers are taken only from the Board's own page", "text/plain; charset=utf-8")
        if self.path == "/api/defer":
            try:
                data = self._body()
                board.defer(int(data.get("id")), data.get("defer") is True)
            except (ValueError, TypeError) as e:
                return self._send(409, str(e), "text/plain; charset=utf-8")
            return self._send(200, json.dumps({"ok": True}))
        if self.path != "/api/answer":
            return self._send(404, "not found", "text/plain; charset=utf-8")
        try:
            data = self._body()
            item = board.items().get(int(data.get("id")))
            # A CHANGED ANSWER (the reviewer, 2026-10-11: "change #13 answer to B. no option to do that on the board"):
            # an answered item takes a new answer only when the page asks for a change; a withdrawn one never
            changing = data.get("change") is True and item is not None and item["answer"] and not item["withdrawn"]
            if item is None or item["withdrawn"] or (item["answer"] and not changing):
                return self._send(409, "that item is not open", "text/plain; charset=utf-8")
            board.answer(item["id"], data.get("answer", ""), data.get("note", ""))
        except (ValueError, TypeError) as e:
            return self._send(400, str(e), "text/plain; charset=utf-8")
        return self._send(200, json.dumps({"ok": True}))

    def log_message(self, fmt, *args):
        sys.stderr.write("board: " + (fmt % args) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--port", type=int, default=config.load()["board_port"])
    ap.add_argument("--detach", action="store_true", help="run in its own session, output to --log, and return")
    ap.add_argument("--log", default=os.path.join(board.board_dir(), "server.log"))
    args = ap.parse_args(argv)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)      # bound before detaching: a busy port fails here
    if args.detach:                          # as scratch/serve_detached.py starts the review servers
        if os.fork() > 0:
            print(f"the Board on http://127.0.0.1:{args.port}/ (log {args.log})")
            os._exit(0)
        os.setsid()
        if os.fork() > 0:
            os._exit(0)
        os.makedirs(os.path.dirname(args.log), exist_ok=True)
        fd_in, fd_out = os.open(os.devnull, os.O_RDONLY), os.open(args.log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        for fd, target in ((fd_in, 0), (fd_out, 1), (fd_out, 2)):
            os.dup2(fd, target)
    server.serve_forever()


if __name__ == "__main__":
    main()
