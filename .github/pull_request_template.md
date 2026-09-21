## What does this change do?

<!-- Briefly describe the change and why it's needed. -->

## How was this tested?

<!--
Be specific: which commands did you run, what were the actual results?
e.g. `pytest tests/ -v` -> 557 passed, 2 skipped
     `cargo test -p streampdf-core --release --all-features` -> 23 passed
-->

## Checklist

- [ ] `pytest tests/` passes locally
- [ ] `cargo test -p streampdf-core --release --all-features` passes locally (the
      workspace-level `python` crate is a PyO3 extension module and isn't
      runnable as a standalone test binary on macOS — see README's Known Issues)
- [ ] I did not fabricate or assume test/benchmark results I didn't actually run
- [ ] Docs (README.md / docs/) updated if behavior, status, or claims changed
- [ ] No hedge language ("planned", "may", "should work") used to describe
      something that doesn't actually work or wasn't actually tested
