# Publish to PyPI
PyPi package: https://pypi.org/project/anki-addons-dataset

Publishing is automated: creating a GitHub release runs `.github/workflows/publish.yml`
(PyPI Trusted Publishing, no API tokens).

One-time setup on [pypi.org](https://pypi.org/manage/account/publishing/): add a Trusted Publisher for
this project pointing at repo `Aleks-Ya/anki-addons-dataset`, workflow `publish.yml`, environment
`pypi` (add it as a "pending publisher" before the first release).

Manual build/publish (fallback):
```bash
uv build                   # creates dist/*.whl and dist/*.tar.gz
uv publish                 # requires a PyPI API token (UV_PUBLISH_TOKEN)
```
Note: builds from a `.dev0` checkout produce a development version; only released (non-`.dev`) tags
yield a clean PyPI version.
