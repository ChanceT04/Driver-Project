# Experiment log

Record measured game behavior and driver results here so architecture choices can be based on evidence. Keep large captures, logs, and checkpoints in ignored `data/` or `runs/` paths and link their local filenames; never commit the raw files.

## Entry template

```markdown
## YYYY-MM-DD — Short experiment name

- Purpose:
- Code revision:
- Track / car / setup:
- Mode / weather / assists:
- Capture or checkpoint (local path):
- Repetitions / seed:
- Result: measurements with units, including failures and missing data
- Interpretation: what the result supports; separate inference from observation
- Follow-up:
```

Keep results comparable by recording configuration and code revision. Report distributions or repeated outcomes where possible, not only the best lap or a single run. Do not claim an improvement from tests with changed conditions.
