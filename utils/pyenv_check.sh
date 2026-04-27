#!/bin/bash
echo "--- Verificando Instalación ---"
which pyenv > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ pyenv está en el PATH"
else
    echo "❌ pyenv NO se encuentra. Revisa el paso 1."
    exit 1
fi

echo "--- Versión de Python activa ---"
python_ver=$(python --version)
pyenv_ver=$(pyenv version-name)
echo "Python dice: $python_ver"
echo "Pyenv dice: $pyenv_ver"

if [[ "$python_ver" == *"$pyenv_ver"* ]]; then
    echo "✅ Éxito: El Python del sistema ha sido sobrescrito por pyenv."
else
    echo "⚠️  Atención: Sigues usando el Python del sistema."
fi