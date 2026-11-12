"""THE ONE READER OF A PROJECT'S MISHMERET CONFIG (design-study/STEP-MISHMERET-MOVE-PLAN.md in Girsa, section 1).

The mechanism names no project. What is the project's - its roles and their colours, the operator's name, the Board's
folder and port, the tmux session, where Claude Code keeps its transcripts, the night run's knobs - is in the
project's `.claude/mishmeret.json`, read here and nowhere else:

    MISHMERET_CONFIG    the config file's path (the project's shim sets it); unset, `<root>/.claude/mishmeret.json`,
                        the root from $CLAUDE_PROJECT_DIR, else `git rev-parse --show-toplevel` in the current folder
    MISHMERET_<FIELD>   overrides a text or number field (a number field's value read as an int), and
    MISHMERET_NIGHT_<KEY> one key of `night` - no other table's key has a variable

A field missing from the file, but one OPTIONAL names (its reader takes it as off), or one the file has that FIELDS
does not list, is an error (ConfigError) - never a default (Lesson 21 in Girsa: a loader that raises over one that
returns nothing). The project's shim runs the one
pinned commit its config names, so the code and the config it reads change together, in one commit of the project.

    python3 config.py --shell    prints the fields the shell scripts read, as `NAME=value` lines for `eval`
"""
import json
import os
import re
import shlex
import subprocess
import sys

# EVERY FIELD, AND WHO READS IT (a test fails on a field no module reads: Lesson 47). `repository` and
# `mishmeret_commit` are the project's shim's, which finds this code by them.
FIELDS = {
    "repository": str,          # the shim: where to clone Mishmeret from, said in its refusal
    "mishmeret_commit": str,    # the shim: the commit whose pinned tree every hook runs
    "project": str,             # board_server (the page's title), agents-morning (the morning alert)
    "roles": list,              # board, board_server, agents-lib, agents: [{name, short, colour, page_light, page_dark,
                                # corner, tmux}]
    "page_order": list,         # board_server: the corners' order on the page, by short name
    "operator": str,            # agents (the pane selected last), and the guard and the landing tool when they move
    "board_dir": str,           # board: the Board's record and its files
    "board_port": int,          # board, board_server: the Board's page
    "tmux_session": str,        # agents, agents-lib, agents-morning
    "tmux_conf": str,           # agents
    "claude_projects": str,     # role_usage, agents-lib: Claude Code's transcripts folder
    "agent_files": str,         # agents: each role's agent file, "{role}" in its place, relative to the root
    "python": str,              # agents-lib: the project's Python, relative to the root
    "launchd_prefix": str,      # agents-morning: the launchd jobs' label prefix
    "state_dir": str,           # agents-morning: its night-run marks, logs and launchd output, relative to the root
    "night": dict,              # agents-morning: the night run's knobs (seconds, tokens)
    "sizes": dict,              # size_report: the start-up documents' limits and homes, the status items', the states'
    "start_reads": dict,        # start_reading_report: the briefs that name a START READS line, the logs never on it
    "effort": dict,             # effort_report: {role: [recommended effort, why]} - the roles whose agent files it reads
    "drafts": dict,             # draft_check_hook: which written files are drafts, the check run on each, its two notes,
                                # its timeout in seconds (under the project's own hook timeout, so it fires first)
    "guard": dict,              # role_guard, time_precommit: the trees only the operator changes, the repositories no
                                # role changes in any tree (`foreign`), the remotes never pushed to, the checks whose
                                # status decides a commit, the pre-commit hook's own path
    "land": dict,               # land: the role whose code landing names a plan, the verifier a round goes back to, the
                                # lane check it runs, the live ledger, what a review server loads, the gate's lists
    "budget": dict,             # board, statusline: the plan window's percent at which each session is told once
}
GUARD = {"homes": str, "fallback_roots": list, "trees": list, "foreign": list, "retired_remotes": list, "checks": list,
         "precommit": str}
LAND = {"planned": str, "verifier": str, "lane_check": str, "ledger": str, "server": dict, "gate_sets": dict,
        "gate_env": dict, "hand_run": dict}
SERVER = {"entry": str, "folders": list, "page": str}
# WHAT ONLY SOME PROJECTS HAVE - a Python for the tmux roles, drafts, a list of corpus homes, a pre-commit hook, a live
# ledger, a review server (girsa-architect, MISHMERET-OWN-CLAUDE-ARCHITECT.md in Girsa, 3: a required field only one
# project can fill is that project's field in Mishmeret's code), and repositories no role changes (girsa-verifier's
# review of that plan: a project's config then gains no field at its pin bump). Absent, its reader takes it as off.
OPTIONAL = {"python", "drafts", "guard.homes", "guard.precommit", "guard.foreign", "land.ledger", "land.server",
            "night.finish_command", "night.finish_exit_command"}
# THE PROJECT'S OWN TWO COMMANDS THAT END A SESSION, never a name written in a script (the reviewer, 2026-11-10: a
# session finishes, "land" is a change reaching main; "add finish-and-exit and have the night run use that"):
# `finish_command`, after which the role is started again in its pane - the morning run types it; and
# `finish_exit_command`, after which nothing is started - the night run types it. OPTIONAL: a project with no role in
# tmux has neither run and no such command (Mishmeret's own); the run that finds its command absent stops and says so.
# `landed_quiet` keeps its name: Mishmeret pins itself, so a required key renamed here could not be committed - the
# pinned reader refuses the new config, this one the old.
NIGHT = {"check_every": int, "you_idle": int, "role_idle": int, "landed_quiet": int, "poll": int,
         "context_limit": int, "gap": int, "finish_command": str, "finish_exit_command": str}
# the reports' tables, each key required and no other (as NIGHT); a value is checked by its kind, and `files` (a path:
# [limit in bytes, where a whole block goes]) and `effort` ({role: [level, why]}) row by row
SIZES = {"warn_percent": int, "files": dict, "status_file": str, "item_pattern": str, "item_limit": int,
         "item_home": str, "state_files": str, "state_limit": int, "state_home": str}
START_READS = {"briefs": str, "logs": list}
BUDGET = {"warn_percent": int}
DRAFTS = {"pattern": str, "check": str, "passed": str, "failed": str, "timeout": int}
ROLE_KEYS = {"name": str, "short": str, "colour": str, "page_light": str, "page_dark": str, "corner": bool,
             "tmux": bool}


class ConfigError(Exception):
    pass


def root():
    """The project's repository root: the config file's folder's parent (`<root>/.claude/mishmeret.json`)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(path())))


def path():
    p = os.environ.get("MISHMERET_CONFIG")
    if p:
        return p
    top = os.environ.get("CLAUDE_PROJECT_DIR")
    if not top:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if out.returncode != 0:
            raise ConfigError("MISHMERET_CONFIG is not set and the current folder is in no git repository")
        top = out.stdout.strip()
    return os.path.join(top, ".claude", "mishmeret.json")


def _typed(name, want, value, where, from_env=False):
    if want is int and from_env:
        try:
            return int(value)
        except ValueError:
            raise ConfigError(f"{where}: {name} must be a whole number, not {value!r}") from None
    if not isinstance(value, want) or (want is int and isinstance(value, bool)):
        raise ConfigError(f"{where}: {name} must be {want.__name__}, not {type(value).__name__}")
    return value


def _exact(have, want, where, prefix=""):
    """`have`'s keys are `want`'s, but an OPTIONAL one (named `prefix` + key) may be absent."""
    missing = sorted(k for k in set(want) - set(have) if prefix + k not in OPTIONAL)
    unknown = sorted(set(have) - set(want))
    if missing or unknown:
        raise ConfigError(f"{where}: " + "; ".join(
            ([f"missing {', '.join(missing)}"] if missing else []) + ([f"unknown {', '.join(unknown)}"] if unknown else [])))


_LOADED = {}


def load(p=None):
    """The config, every field checked, the MISHMERET_<FIELD> overrides applied as the environment stands NOW - the
    file is read once per process and path, the overrides on every call (a process that sets one later sees it)."""
    p = p or path()
    if p not in _LOADED:
        try:
            with open(p, encoding="utf-8") as fh:
                _LOADED[p] = json.load(fh)
        except (OSError, ValueError) as e:
            raise ConfigError(f"{p}: {e}") from None
    raw = _LOADED[p]
    if not isinstance(raw, dict):
        raise ConfigError(f"{p}: not a table of fields")
    _exact(raw, FIELDS, p)
    cfg = {}
    for name, want in FIELDS.items():
        env = os.environ.get("MISHMERET_" + name.upper()) if want in (str, int) else None
        if name not in raw and env is None:     # an OPTIONAL field the project has not (_exact let only those through)
            continue
        cfg[name] = _typed(name, want, raw[name] if env is None else env, p, from_env=env is not None)
    _exact(cfg["night"], NIGHT, p + ": night", "night.")
    night = {}
    for k, t in NIGHT.items():
        env = os.environ.get(f"MISHMERET_NIGHT_{k.upper()}")
        if k not in cfg["night"] and env is None:     # an OPTIONAL command the project has not
            continue
        night[k] = _typed("night." + k, t, cfg["night"][k] if env is None else env, p, from_env=env is not None)
    cfg["night"] = night
    for i, r in enumerate(cfg["roles"]):
        if not isinstance(r, dict):
            raise ConfigError(f"{p}: roles[{i}] is not a table")
        _exact(r, ROLE_KEYS, f"{p}: roles[{i}]")
        for k, t in ROLE_KEYS.items():
            _typed(f"roles[{i}].{k}", t, r[k], p)
        # a colour is "" only where the role is not drawn: no tmux pane, no corner on the page
        for k, used in (("colour", r["tmux"]), ("page_light", r["corner"]), ("page_dark", r["corner"])):
            if bool(r[k]) != used:
                raise ConfigError(f"{p}: roles[{i}].{k} must be " + ("a colour" if used else '"" (the role is not drawn)'))
    shorts = {r["short"] for r in cfg["roles"]}
    if sorted(cfg["page_order"]) != sorted(r["short"] for r in cfg["roles"] if r["corner"]) or len(shorts) != len(
            cfg["roles"]):
        raise ConfigError(f"{p}: page_order must name each role with a corner once, by its short name")
    if cfg["operator"] not in {r["name"] for r in cfg["roles"]}:
        raise ConfigError(f"{p}: operator {cfg['operator']!r} is not one of the roles")
    for field, keys in (("sizes", SIZES), ("start_reads", START_READS), ("drafts", DRAFTS), ("guard", GUARD),
                        ("land", LAND), ("budget", BUDGET), ("land.server", SERVER)):
        parent, _, key = field.rpartition(".")
        table = (cfg[parent] if parent else cfg).get(key)
        if table is None:                       # an OPTIONAL table absent
            continue
        _exact(table, keys, f"{p}: {field}", prefix=field + ".")
        for k, t in keys.items():
            if k in table:
                _typed(f"{field}.{k}", t, table[k], p)
    for k in ("planned", "verifier"):
        if cfg["land"][k] not in {r["name"] for r in cfg["roles"]}:
            raise ConfigError(f"{p}: land.{k} {cfg['land'][k]!r} is not one of the roles")
    if "landing" not in cfg["land"]["gate_sets"] or not set(cfg["land"]["gate_env"]) <= set(cfg["land"]["gate_sets"]):
        raise ConfigError(f"{p}: land.gate_sets must hold `landing`, and land.gate_env name only its sets")
    if not 0 < cfg["budget"]["warn_percent"] <= 100:
        raise ConfigError(f"{p}: budget.warn_percent must be 1 to 100, not {cfg['budget']['warn_percent']}")
    _rows(cfg["sizes"]["files"], (int, str), f"{p}: sizes.files")
    _rows(cfg["effort"], (str, str), f"{p}: effort")
    return cfg


def _rows(table, kinds, where):
    """Each value of `table` a list of `kinds`, in order: a file's [limit, home], a role's [effort, why]."""
    for key, row in table.items():
        if not (isinstance(row, list) and len(row) == len(kinds) and all(
                isinstance(v, t) and not isinstance(v, bool) for v, t in zip(row, kinds))):
            raise ConfigError(f"{where}: {key} must be [" + ", ".join(t.__name__ for t in kinds) + f"], not {row!r}")


def expand(p):
    """A config path: `~` expanded; a relative one taken from the project's root."""
    p = os.path.expanduser(p)
    return p if os.path.isabs(p) else os.path.join(root(), p)


def transcripts(tree):
    """Claude Code's folder for the sessions started in `tree`, under the config's claude_projects: the tree's absolute
    path with every character but a letter or digit made "-" - the one rule (the audit's item 5: three, which
    disagreed for a path holding "_" or a claude_projects of the project's own)."""
    return os.path.join(expand(load()["claude_projects"]), re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(tree)))


def role_names(**only):
    """The roles' names in the config's order; `tmux=True` or `corner=True` keeps those alone."""
    return [r["name"] for r in load()["roles"] if all(r[k] == v for k, v in only.items())]


# The shell scripts' names for the fields they read: field, its variable, how its value is written.
SHELL = (("project", "MM_PROJECT", str), ("tmux_session", "MM_SESSION", str), ("tmux_conf", "MM_TMUX_CONF", expand),
         ("claude_projects", "MM_PROJECTS", expand), ("python", "MM_PYTHON", expand),
         ("agent_files", "MM_AGENT_FILES", str), ("launchd_prefix", "MM_LAUNCHD_PREFIX", str), ("state_dir", "MM_STATE_DIR", expand),
         ("operator", "MM_OPERATOR_ROLE", str))


def shell():
    """The fields the shell scripts read, as `NAME=value` lines (each value quoted for the shell): SHELL's, the root,
    the roles tmux starts in the config's order (MM_ROLES) and in the page's (MM_LAYOUT: tmux tiles its panes in the
    order they are made, as the page draws its corners), each one's colour (MM_COLOURS, `name=colour` words), and the
    night run's knobs."""
    cfg = load()
    tmux = [r for r in cfg["roles"] if r["tmux"]]
    by_short = {r["short"]: r for r in tmux}
    pairs = [("MM_ROOT", root())] + [(var, how(cfg[field]) if field in cfg else "") for field, var, how in SHELL]
    pairs.append(("MM_ROLES", " ".join(r["name"] for r in tmux)))
    pairs.append(("MM_LAYOUT", " ".join(by_short[s]["name"] for s in cfg["page_order"] if s in by_short)))
    pairs.append(("MM_COLOURS", " ".join(f"{r['name']}={r['colour']}" for r in tmux)))
    pairs += [(f"MM_NIGHT_{k.upper()}", str(v)) for k, v in cfg["night"].items()]
    return "".join(f"{k}={shlex.quote(v)}\n" for k, v in pairs)


if __name__ == "__main__":
    if sys.argv[1:] == ["--shell"]:
        try:
            sys.stdout.write(shell())
        except ConfigError as e:
            print(f"mishmeret config: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(__doc__.strip())
