# Usa una imagen oficial de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de dependencias
COPY requirements.txt requirements.txt

# Instala las dependencias
RUN pip install -r requirements.txt

# Copia todo el código de la API al contenedor
COPY . .

# Comando para ejecutar la aplicación con Gunicorn.
# Cloud Run establece la variable de entorno PORT automáticamente.
# Reemplaza "app:app" con "nombre_archivo_principal:nombre_variable_flask"
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app