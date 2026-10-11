# UML diagrams
PlantUML sources live in `doc/uml/`: `human/` is maintained by hand, `ai/` is generated from the code
(`class-all.puml`, `class-addon-infos.puml`, `packages.puml`).

The generated ones are refreshed **only on explicit request** — they are not part of the normal
change or release flow, and no code change is expected to update them. Run the skill
`/update-uml-diagrams` when you want them brought back in sync: it rebuilds the inventory from `src`,
adds and deletes to match, and checks the result with `plantuml -checkonly` (requires the `plantuml`
CLI: `brew install plantuml`). It never touches `doc/uml/human/`.
