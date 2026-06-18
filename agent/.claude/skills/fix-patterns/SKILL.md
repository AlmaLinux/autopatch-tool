# Autopatch Fix Patterns

Common failure modes and how to fix them.

## ActionNotAppliedError in `replace`

The `find` string was not found in the spec file.

**Causes:**
- Upstream changed wording, added/removed whitespace, moved a block
- Upstream removed the line entirely

**Fix:**
1. Search the spec file for similar text using grep/diff
2. If the string changed slightly, update `find` to match the new version
3. If the string seems to have disappeared entirely, find out *why* before removing
   anything (see "Disappeared `find`: dropped vs. moved behind an indirection"). Remove
   an action only when the change it makes is genuinely no longer needed.
4. Preserve the *intent*, not just the text: the action exists to make some value reach
   the build (an env var, a macro, a file). After the fix that value must still reach the
   build at the authoritative point (see "Verify the effect survives").

## Disappeared `find`: dropped vs. moved behind an indirection

A missing `find` has two opposite causes. Removing the action is right for the first and
a silent regression for the second.

**(a) Genuinely dropped / absorbed upstream.** The behaviour the action added is now
unnecessary or already in the spec (e.g. the spec now ships the exact `%if %{race}`
wrappers the action used to insert). -> Remove the action; it is obsolete.

**(b) Re-expressed through an indirection.** The literal you matched was replaced by a
macro, variable, renamed key, or different literal, but the thing the action *controls*
is still there and still needs the AlmaLinux change. The failing `find` is only the
symptom. Example: `export GOAMD64=v3` became `export GOAMD64=%{goamd64}` -- the value now
comes from the `%global goamd64` macro. Deleting the action does NOT keep the old value;
the build silently reverts to upstream's default (x86_64_v2 support quietly lost, with no
error). -> Do NOT delete. Trace where the value is set now and re-target the action there.
For GOAMD64 the correct seam is the macro definition, not each `export`/`go.env` leaf:

    find: |
          %global goamd64 v3
          %global goppc64 power9
    replace: |
          %ifarch x86_64_v2
          %global goamd64 v2
          %else
          %global goamd64 v3
          %endif
          %global goppc64 power9

**Telling (a) from (b):** recover the action's intent from its `replace` value + changelog
line ("force GOAMD64=v2 on x86_64_v2"), then grep the spec for the value it controls
(`GOAMD64`, the package name, the path). Still set somewhere via a macro/variable/new
literal -> case (b), re-target. Genuinely gone and no longer wanted -> case (a), remove.

**Patch the source, not the leaves.** When a value is defined once (`%global`/`%define`)
and consumed in many places (`export`, `go.env`, sub-builds), change it at the single
definition. Env exports override config files (`export GOAMD64=...` beats `go.env`), so
patching only `go.env` while the export keeps the macro default is a no-op.

## Verify the effect survives (not just that the action applied)

`autopatch_validate_config` and a clean `autopatch ... apply` only prove the actions ran
without `ActionNotAppliedError`. They do NOT prove the build outcome is correct: a
half-applied change applies cleanly and still breaks the package silently.

Before writing `success: true`, for every action you removed or changed:
1. State its intent in one line (from its `replace` value + changelog line).
2. Confirm that intent is still realized in the resulting spec -- by a remaining action or
   because upstream now does it. Grep for the controlled value at the point the build
   actually reads it (env export / macro), not just any occurrence.
3. If the changelog still promises an effect your config no longer produces (e.g. "Add
   x86_64_v2 support"), that is a regression -- fix the config, not the changelog.

## ActionNotAppliedError in `delete_line`

The target line is no longer present in the spec.

**Fix:**
1. Check if the line was moved to a different location
2. If the line no longer exists, remove the action (goal already achieved)
3. If the line was reformatted, update the `lines` value to match

## RPMSpecFileParsingError

The spec file structure changed in an incompatible way.

**Subtypes:**
- **Section not found** -- a spec section was renamed or removed. Check `%prep`, `%build`, `%install`, `%files` sections.
- **Patch/Source number duplication** -- another patch/source already uses the same number. Change `number` to the next available, or use `"Latest"`.
- **Macro syntax error** -- malformed RPM macros in the spec. This usually requires manual intervention.

**Fix:**
1. Read the spec file to understand its current structure
2. Adjust config.yaml targets/sections to match the new structure
3. For number conflicts, use `"Latest"` or pick the next unused number

## FileNotFoundError

A file referenced by `add_files` or `run_script` does not exist.

**Fix:**
1. Check if the file was renamed in `files/` or `scripts/`
2. If the file is truly missing, it may need to be regenerated (flag for manual review)
3. Update the `name` field in config.yaml if the file was renamed

## Patch does not apply (context mismatch)

The patch file itself has context lines that no longer match the source.

**IMPORTANT:** Do NOT attempt to fix .patch file contents. Mark in the report as "requires manual patch regeneration" and set `success: false` in agent_result.json.
