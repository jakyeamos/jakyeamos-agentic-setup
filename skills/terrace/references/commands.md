# Terrace Command Map

Use this table when the user names a precise Terrace action instead of freeform workflow intent.

| Intent | Command |
| --- | --- |
| Write senior-cycle alignment intent for a feature | `terrace align $ARGUMENTS` |
| Check artifacts and protected baselines | `terrace audit` |
| Plan the next phase and stop at blockers or agent handoff | `terrace autonomous` |
| Append a backlog item | `terrace backlog add "$ARGUMENTS"` |
| List backlog items | `terrace backlog list` |
| Run audit plus protected-change enforcement | `terrace ci check $ARGUMENTS` |
| Write cleanup contract for flags, temporary code, and docs | `terrace cleanup $ARGUMENTS` |
| Discover project quality scripts and command mappings | `terrace commands discover` |
| Run the GSD-compatible phase completion alias | `terrace complete-phase $ARGUMENTS` |
| Show the latest Terrace corpus report summary | `terrace corpus report` |
| Run the local Terrace corpus evaluator | `terrace corpus run $ARGUMENTS` |
| Record architecture decisions and maintainability intent | `terrace design $ARGUMENTS` |
| Route natural-language agent intent | `terrace do "$ARGUMENTS"` |
| Check Terrace installation health | `terrace doctor` |
| Run the GSD-compatible phase execution alias | `terrace execute-phase $ARGUMENTS` |
| Run a complete phase lifecycle | `terrace execute-phase-complete $ARGUMENTS` |
| Show the top-level command list | `terrace --help` |
| Summarize migrated phases, sessions, decisions, and quick tasks | `terrace history` |
| Initialize Terrace state | `terrace init` |
| Write edge-case and failure-mode interrogation | `terrace interrogate $ARGUMENTS` |
| Write repo-derived codebase map | `terrace map-codebase` |
| Initialize Terrace from a source PRD | `terrace new-project $ARGUMENTS` |
| Find the next workflow action | `terrace next` |
| Write feature observability and rollback intent | `terrace observe $ARGUMENTS` |
| Complete a phase | `terrace phase complete $ARGUMENTS` |
| Enter execution for a phase | `terrace phase execute $ARGUMENTS` |
| List roadmap phases | `terrace phase list` |
| Write a phase plan artifact | `terrace phase plan $ARGUMENTS` |
| Write a phase review artifact | `terrace phase review $ARGUMENTS` |
| Show a roadmap phase | `terrace phase show $ARGUMENTS` |
| Write a phase validation artifact | `terrace phase validate $ARGUMENTS` |
| Run the GSD-compatible phase planning alias | `terrace plan-phase $ARGUMENTS` |
| Migrate legacy GSD artifacts | `terrace port gsd` |
| Inventory legacy GSD artifacts without writing state | `terrace port gsd --dry-run` |
| Import a feature PRD | `terrace prd import $ARGUMENTS` |
| Install a preset | `terrace preset install $ARGUMENTS` |
| List installed presets | `terrace preset list` |
| Complete a quick task | `terrace quick complete $ARGUMENTS` |
| Execute a quick task | `terrace quick execute $ARGUMENTS` |
| List migrated quick-task history | `terrace quick list` |
| Plan a quick task | `terrace quick plan "$ARGUMENTS"` |
| Show one migrated quick task | `terrace quick show $ARGUMENTS` |
| Reconstruct paused workflow context | `terrace resume` |
| Run the GSD-compatible phase review alias | `terrace review-phase $ARGUMENTS` |
| Explain a rule | `terrace rule explain $ARGUMENTS` |
| List installed rule packs | `terrace rule list` |
| Set default phase effort | `terrace settings effort $ARGUMENTS` |
| Show current settings | `terrace settings show` |
| Run read-only release readiness checks | `terrace ship check` |
| Write a release-readiness summary | `terrace ship prepare` |
| Compute a stable spec hash | `terrace spec hash --file $ARGUMENTS` |
| Validate governance artifacts | `terrace spec validate` |
| Write a behavior-first test plan | `terrace test-plan $ARGUMENTS` |
| Write UI source and target diff context | `terrace ui diff $ARGUMENTS` |
| Capture a Stitch design import | `terrace ui import-stitch $ARGUMENTS` |
| Plan a design-driven UI refresh | `terrace ui plan-refresh $ARGUMENTS` |
| Run the GSD-compatible phase validation alias | `terrace validate-phase $ARGUMENTS` |
| Write production success signals and rollback conditions | `terrace validate-prod $ARGUMENTS` |
| Print installed version | `terrace --version` |
