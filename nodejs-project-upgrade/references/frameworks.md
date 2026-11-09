# Framework and tool notes

Read the official migration guide for every major. These notes cover what usually breaks in these
projects and how to prove the upgrade works. Section names match the survey's group notes.

## Next.js
- Guides: nextjs.org/docs/app/guides/upgrading. Codemods: `npx @next/codemod@latest <transform> .`. Review every codemod diff.
- Upgrade `next` and `eslint-config-next` together, and keep React within Next's peer range.
- GarageERP builds with `next build --webpack`. Check the flag still exists and that Turbopack hasn't become required.
- `next.config.ts` options, middleware/proxy (`proxy.ts` in GarageERP), caching defaults and `next/font` all change between majors.
- `next/font/google` downloads fonts at build time. A sandbox without network fails the build; that's not an incompatibility.
- Verify: `npm run build`, the e2e suite, the container build, and that the standalone output still starts (`node server.js` in the runtime stage).

## React
- Upgrade `react`, `react-dom`, `@types/react` and `@types/react-dom` together. Check libraries with React peers (`@base-ui/react`, `lucide-react`, Radix).
- Verify: typecheck, unit tests and e2e. Watch hydration warnings in the browser console during e2e.

## Vite
- Plugins (`@vitejs/plugin-react`, `@tailwindcss/vite`) must support the new Vite major. Upgrade them in the same group.
- Check `vite.config.ts` options and that the built output is equivalent. For static sites, diff the `dist/` file list, and for MarcelKocian the exported nginx tree.
- Vitest bundles Vite internally, so check that the Vitest version supports the new Vite major.

## ESLint
- Flat config (`eslint.config.mjs`) is already used. Majors remove rules, change defaults, and drop older Node versions.
- Upgrade `eslint`, `@eslint/js`, `typescript-eslint` and `eslint-config-next` together, and check each plugin's peer range first. `eslint-config-next` often lags a new ESLint major, so defer the ESLint major until it catches up.
- Verify: `npm run lint` has no new errors. New warnings are fine but get listed.

## Vitest
- `vitest` and `@vitest/coverage-v8` / `@vitest/ui` must be the **same exact version**.
- Majors change config (`workspace` → `projects`, StratDesk uses `--project unit`/`integration`), mocks and pool defaults.
- Verify: the unit tests and integration suites (Docker or test-DB based) both pass, and the test count didn't drop. A silent drop means the config stopped matching files.

## Playwright
- `@playwright/test` and the browsers must match: run `npx playwright install` after each bump. Any Playwright Docker image tag must match the package version exactly.
- Screenshot baselines (ParkourTop, DrezuraTop) can shift from browser rendering changes. A pixel diff is a **finding to report**. Updating baselines needs the owner's approval.
- Verify: the full e2e suite on all configured projects (desktop and phone).

## Tailwind CSS
- Tailwind 4 is CSS-first (`@import "tailwindcss"`, `@tailwindcss/postcss` or `@tailwindcss/vite`). Keep `tailwindcss` and `@tailwindcss/*` on the same version.
- Utilities get renamed between majors. Check the built CSS size and do a visual pass in e2e.

## TypeScript
- Upgrade TypeScript as its own group. New strictness surfaces real type errors, so fix them; don't loosen `tsconfig`.
- TypeScript 7 is the native (Go) compiler. Tools that import the `typescript` JS API (ESLint parsers, ts-node, tsx, build scripts) may need their own updates or may lag behind. Check `typescript-eslint` support before upgrading.
- Verify: `npm run typecheck` and `npm run build`.

## Zod
- Zod 4 changes error formatting, `.default()`/`.optional()` behaviour and some method names. Projects that validate config with zod (DrezuraTop and ParkourTop YAML rules, API inputs in the Next.js apps) need their validation tests and error-message assertions reviewed.
- Verify: DrezuraTop `npm run validate-rules`, the unit tests, and that invalid input is still rejected.

## Drizzle
- `drizzle-orm` and `drizzle-kit` move together. A kit major can change generated migration SQL. **Never** generate or apply migrations as part of a dependency upgrade.

## Node.js
- Read the Node release notes for every major between the old version and the target: removed APIs, OpenSSL changes, `fetch`/undici behaviour, and the npm major bundled with it.
- Native modules (`pg-native`, `sharp`, `bcrypt`, canvas) need prebuilt binaries for the new ABI on **linux/amd64 musl**. Check that `npm ci` inside the Docker build doesn't fall back to compiling.
- `@types/node` follows the runtime major. TypeScript may surface new type errors.
- Verify: the full container build plus a smoke test, and the unit tests on the Mac with the new version (`nvm use` / `fnm use`).

## Alpine
- An Alpine bump changes musl and OpenSSL versions. For GarageERP (Node copied into `alpine:3.x`), the Node binary must run on the target Alpine. Smoke-test the runtime image, not only the build.
- nginx-unprivileged images: re-check the `nginx -t` exec check (`release.py` smoke runs it) and the CSP and headers config.
