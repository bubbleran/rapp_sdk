# API Documentation

The BR-RApp SDK uses [`pydoc-markdown`](https://pydoc-markdown.readthedocs.io/) to generate API documentation directly from Python docstrings.

##Generating the Documentation

To build the API reference locally, run:

```bash
pip3 install pydoc-markdown
cd docs
pydoc-markdown
```

## Output Location
The generated documentation will be available at:
```bash
br-rapp-sdk/docs/build/docs/content/api-reference
