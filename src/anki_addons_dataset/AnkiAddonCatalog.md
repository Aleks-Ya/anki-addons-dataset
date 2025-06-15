# Anki Addon Catalog for Programmers

## Dataset structure
- dataset-metadata.json
- anki-addons-dataset.json
- anki-addons-dataset.md
- anki-addons-dataset.xlsx
- raw
    - 1-anki-web
        - html
            - addons.html
            - addon
                - {addon-id}.html
        - json
            - addon
                - {addon-id}.json
    - 2-github
        - {user}
            - {repo}
                - languages.json
    - 3-enricher
        - addon
            - {addon-id}.json
    - 4-overrider
        - overrides.yaml