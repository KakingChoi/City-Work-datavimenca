# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv
from datetime import timedelta # Importa timedelta para la duración del JWT

import re # Importa re para expresiones regulares

# Cargar variables de entorno del archivo .env
load_dotenv()

# --- INICIALIZACIÓN DE LA APP Y EXTENSIONES ---
app = Flask(__name__)
CORS(app) # Habilita CORS para permitir peticiones desde Vue

# Configuración de la Base de Datos con SQLAlchemy se comentan para usar el secret manager 
#app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#db = SQLAlchemy(app)
# Lee las variables de entorno inyectadas por Cloud Run
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")
db_name = os.environ.get("DB_NAME")
instance_connection_name = "poc-mip-cityworks:us-central1:cityworks-db"

# Construye la cadena de conexión para Cloud SQL usando un socket Unix
# Esto es más seguro y eficiente que usar una IP pública
db_uri = (
    f"mysql+mysqlconnector://{db_user}:{db_pass}@/{db_name}"
    f"?unix_socket=/cloudsql/{instance_connection_name}"
)

# Configura la app de Flask con la nueva cadena de conexión
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Configuración de JWT
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
# Duración del token de acceso: 7 días (ajusta según tus necesidades)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7) 
jwt = JWTManager(app)

# --- CONFIGURACIÓN DE GOOGLE CLOUD ---
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GEMINI_LOCATION")
vertexai.init(project=PROJECT_ID, location=LOCATION)


# --- MODELO DE BASE DE DATOS PARA USUARIOS ---
# Este modelo se mapea a tu tabla 'users' existente de Laravel
class User(db.Model):
    __tablename__ = 'users' # Nombre exacto de la tabla de Laravel
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # Columna de contraseña de Laravel

    # Métodos para manejar la contraseña hasheada de Laravel
    def check_password(self, password):
        return check_password_hash(self.password, password)


# --- ENDPOINTS DE AUTENTICACIÓN ---
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"msg": "Faltan datos"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "El email ya está registrado"}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(name=name, email=email, password=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "Usuario registrado exitosamente"}), 201

@app.route("/api/login", methods=["POST"])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"msg": "Email o contraseña incorrectos"}), 401

    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token)

@app.route("/api/me", methods=["GET"])
@jwt_required()
def me():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    if not user:
        return jsonify({"msg": "Usuario no encontrado"}), 404
        
    return jsonify(id=user.id, name=user.name, email=user.email)


# --- ENDPOINTS DE BIGQUERY Y GEMINI ---
@app.route("/api/bigquery/objects", methods=["GET"]) # Endpoint para listar tablas y vistas
@jwt_required()
def list_bigquery_objects():
    try:
        client = bigquery.Client(project=PROJECT_ID)
        dataset_id = os.getenv("BIGQUERY_DATASET_ID")
        
        all_objects = []
        # bigquery.Client().list_tables lista ambos tipos (tablas y vistas)
        for item in client.list_tables(dataset_id):
            all_objects.append({"id": item.table_id, "type": item.table_type})
        
        return jsonify(all_objects)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bigquery/ask", methods=["POST"])
@jwt_required()
def ask_gemini():
    try:
        question = request.json.get("question")
        dataset_id = os.getenv("BIGQUERY_DATASET_ID")

        if not question:
            return jsonify({"type": "text", "content": "Por favor, proporciona una pregunta."}), 400

        bq_client = bigquery.Client(project=PROJECT_ID)
        
        # Obtener todas las tablas y vistas del dataset para el prompt de Gemini
        all_objects_info = []
        for item in bq_client.list_tables(dataset_id):
            # Para cada objeto, obtener su esquema y añadirlo al contexto de Gemini
            table_ref = bq_client.dataset(dataset_id).table(item.table_id)
            table_obj = bq_client.get_table(table_ref)
            schema_string = ", ".join([f"{field.name}: {field.field_type}" for field in table_obj.schema])
            all_objects_info.append(f"Objeto: {item.table_id} (Tipo: {item.table_type}, Esquema: {schema_string})")
        
        objects_context = "\n".join(all_objects_info)

        model = GenerativeModel(model_name=os.getenv("GEMINI_MODEL_NAME"))
        
        prompt = f"""
        Considerando el dataset de BigQuery '{dataset_id}', que contiene los siguientes objetos (tablas y vistas) con sus respectivos esquemas:
        {objects_context}

        Genera una consulta SQL de BigQuery para responder a la siguiente pregunta: '{question}'.
        La consulta debe seleccionar automáticamente el objeto (tabla o vista) más relevante del dataset basándose en la pregunta y en el esquema proporcionado.
        Asegúrate de que la consulta SQL sea válida y ejecutable en BigQuery.
        Responde **SOLO** con el código SQL, sin explicaciones, formato adicional (como ```sql) o texto introductorio.
        """
        
        response = model.generate_content(prompt)
        sql_query = response.text.strip().replace("```sql", "").replace("```", "")
        
        # Intentar extraer el nombre del objeto (tabla/vista) de la consulta
        # Esta heurística busca patrones comunes de FROM o JOIN.
        match = re.search(r'FROM\s+`?(?:`?\w+`?\.)?`?(?:`?\w+`?\.)?`?(\w+)`?', sql_query, re.IGNORECASE)
        table_or_view_name = None
        if match:
            table_or_view_name = match.group(1) # Primer grupo capturado es el nombre del objeto
        else:
            # Si no se encuentra un FROM directo, buscar SELECT ... FROM (subquery)
            # Esto es una simplificación y puede necesitar ser más robusto.
            subquery_match = re.search(r'SELECT\s+.*?\s+FROM\s+\((.*?)\)', sql_query, re.IGNORECASE | re.DOTALL)
            if subquery_match:
                # Si es una subconsulta, intenta encontrar la tabla dentro de ella.
                sub_sql = subquery_match.group(1)
                sub_match = re.search(r'FROM\s+`?(?:`?\w+`?\.)?`?(?:`?\w+`?\.)?`?(\w+)`?', sub_sql, re.IGNORECASE)
                if sub_match:
                    table_or_view_name = sub_match.group(1)

        # Si aún no se ha encontrado el nombre de la tabla/vista, lanzar un error
        if not table_or_view_name:
            raise ValueError("No se pudo identificar la tabla o vista principal en la consulta SQL generada. La IA podría haber generado una consulta compleja o inesperada.")

        # Verificar que el objeto existe en el dataset antes de ejecutar
        found_object = False
        for item in bq_client.list_tables(dataset_id):
            if item.table_id.lower() == table_or_view_name.lower(): # Comparar sin distinguir mayúsculas/minúsculas
                found_object = True
                break
        
        if not found_object:
            raise ValueError(f"La tabla o vista '{table_or_view_name}' identificada en la consulta SQL no se encontró en el dataset '{dataset_id}'.")


        query_job = bq_client.query(sql_query)
        results = [dict(row) for row in query_job]

        if not results:
            response_data = {
                "type": "text",
                "content": "No se encontraron resultados para tu consulta."
            }
        else:
            headers = list(results[0].keys())
            rows = [list(row.values()) for row in results]
            
            response_data = {
                "type": "table",
                "content": {
                    "headers": headers,
                    "rows": rows
                }
            }
        
        # Añade el SQL generado y el objeto identificado para depuración/información
        response_data['generated_sql'] = sql_query
        response_data['identified_object'] = table_or_view_name

        return jsonify(response_data)

    except Exception as e:
        # Asegura que el error se devuelva en el formato esperado por el frontend
        app.logger.error(f"Error en ask_gemini: {str(e)}") # Log el error en el servidor
        return jsonify({"type": "text", "content": f"Ocurrió un error al procesar tu pregunta: {str(e)}"}), 500

@app.route("/")
def hello():
    return "API funcionando!"
    
# --- INICIAR LA APLICACIÓN ---
if __name__ == '__main__':
    # Crea las tablas de la base de datos si no existen (solo para desarrollo/primera ejecución)
    # Si ya tienes la tabla 'users' de Laravel, puedes omitir esta línea o asegurarte de que
    # no intente crearla si ya existe y no necesitas migraciones de Flask-SQLAlchemy.
    with app.app_context():
        db.create_all() 
    app.run(debug=True, port=5000)