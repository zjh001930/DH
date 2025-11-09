@echo off
echo Uninstalling existing weaviate-client and dependencies...
pip uninstall -y weaviate-client grpcio protobuf

echo Upgrading pip, setuptools and wheel...
python -m pip install --upgrade pip setuptools wheel

echo Installing a stable version of weaviate-client...
pip install weaviate-client==3.26.2

echo.
echo Weaviate client has been reinstalled with a stable version.
pause