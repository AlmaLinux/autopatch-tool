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
3. If the string disappeared entirely, remove the action or replace with a new equivalent
4. Always preserve the replacement semantics -- the `replace` value should still make sense

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
