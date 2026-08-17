# fastapi-auth-lib

### install dependencies

```shell
pip install -r requirements.txt
```


### Publish to PyPI

```shell
# Build distribution
python -m build

# Check package
twine check dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*
twine upload --repository testpypi dist/* -u __token__ -p TOKEN

# Upload to PyPI
# twine upload dist/*

# install from test pypi
pip install -i https://test.pypi.org/simple/ fastapi-auth-lib==0.1.1
```
