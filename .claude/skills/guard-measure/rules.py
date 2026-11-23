"""The Bash rules the hook runs on a command (role_guard.check), in its order: the one list decide.py and probe.py judge
by (girsa-verifier's LOW 1 on 59f84a2 - each had its own, and probe.py asked one rule of five). tests/test_guard_measure.py
reads check()'s own calls and fails when a rule is in neither RULES nor LEFT_OUT."""
import inspect

RULES = ("refusal", "tmux_refusal", "copy_refusal", "check_status_refusal", "piped_check_refusal")
# what check() also calls, and why a measure leaves it out
LEFT_OUT = {"time_refusal": "judged against the clock - the same code on both sides of rule 45",
            "pin_refusal": "the file tools', not a command's", "edit_refusal": "the file tools', not a command's"}


def judge(rg, role, command, cwd, read, fakes=None):
    """The first refusal RULES give `command` as `role` from `cwd`, or None. `rg` is the guard module measured: a rule
    it lacks (an older commit's) is not asked. `fakes`: the placeholder predicates of a probe (main_tree, project_tree,
    guarded, is_worktree), each passed to the rules that take it."""
    fakes = fakes or {}
    for name in RULES:
        rule = getattr(rg, name, None)
        if rule is None:
            continue
        takes = inspect.signature(rule).parameters
        more = {k: v for k, v in fakes.items() if k in takes}
        if "read" in takes:
            more["read"] = read
        why = rule(role, command, cwd, **more) if name == "refusal" else rule(command, cwd, **more)
        if why:
            return why
    return None
