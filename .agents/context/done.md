# Definition of done

A catalog change is complete only when:

- the manifest, asset files, routes, provenance, and local links agree;
- public-safety and skill validators pass with no new exclusions;
- `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, and `pnpm check`
  pass from the pinned offline environment;
- changed behavior has a deterministic fixture or focused regression test;
- the context packet and README explain any changed boundary or command;
- no private runtime, credential, prompt, transcript, path, or generated
  harvest entered the public diff;
- the diff is one coherent concern, reviewed, committed, and pushed to `dev`.

A passing validator does not prove model quality, host registration, provider
availability, deployment, or public adoption. Those remain separately
reviewed claims.
