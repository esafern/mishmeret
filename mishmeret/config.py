"""THE ONE READER OF A PROJECT'S MISHMERET CONFIG (design-study/STEP-MISHMERET-MOVE-PLAN.md in Girsa, section 1).

The mechanism names no project. What is the project's - its roles and their colours, the operator's name, the Board's
folder and port, the tmux session, where Claude Code keeps its transcripts, the night run's knobs - is in the
project's `.claude/mishmeret.json`, read here and nowhere else:

    MISHMERET_CONFIG    the config file's path (the project's shim sets it); unset, `<root>/.claude/mishmeret.json`,
                        the root from $CLAUDE_PROJECT_DIR, else `git rev-parse --show-toplevel` in the current folder
    MISHMERET_<FIELD>   overrides one field, MISHMERET_<FIELD>_<KEY> one key of a table field (an int field's value
                        read as an int) - the one rule in place of a variable per knob

A field missing from the file, or one the file has that FIELDS does not list, is an error (ConfigError) - never a
default (Lesson 21 in Girsa: a loader that raises over one that returns nothing). The project's shim runs the one
pinned commit its config names, so the code and the config it reads change together, in one commit of the project.

    python3 config.py --shell    prints the fields the shell scripts read, as `NAME=value` lines for `eval`
"""
import json
import os
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
}
NIGHT = {"check_every": int, "you_idle": int, "role_idle": int, "landed_quiet": int, "poll": int,
         "context_limit": int, "gap": int}
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


def _exact(have, want, where):
    missing, unknown = sorted(set(want) - set(have)), sorted(set(have) - set(want))
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
        cfg[name] = _typed(name, want, raw[name] if env is None else env, p, from_env=env is not None)
    _exact(cfg["night"], NIGHT, p + ": night")
    night = {}
    for k, t in NIGHT.items():
        env = os.environ.get(f"MISHMERET_NIGHT_{k.upper()}")
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
    return cfg


def expand(p):
    """A config path: `~` expanded; a relative one taken from the project's root."""
    p = os.path.expanduser(p)
    return p if os.path.isabs(p) else os.path.join(root(), p)


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
    pairs = [("MM_ROOT", root())] + [(var, how(cfg[field])) for field, var, how in SHELL]
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
