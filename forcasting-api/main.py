from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
import pandas as pd
import io
import os

# =========================
# CONFIG
# =========================
# Puedes dejarlo fijo así, o pasarlo por variable de entorno.
SERVICE_ACCOUNT_KEY_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "poc-data-vimenca-9870db584951.json"
)

BQ_TABLE_ID = "poc-data-vimenca.ds_data_vimenca.forecast_final"

# =========================
# APP
# =========================
app = FastAPI(title="Vimenca Forecast System")

# =========================
# CORS
# =========================
ALLOWED_ORIGINS = [
    "http://localhost:5174",
    "http://localhost:5175",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.options("/{path:path}")
async def preflight_handler(path: str, response: Response):
    return Response(status_code=204)

# =========================
# OAUTH2
# =========================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# =========================
# HELPERS
# =========================
def get_bq_client() -> bigquery.Client:
    """
    Crea un cliente de BigQuery usando SIEMPRE la key indicada.
    """
    if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
        raise HTTPException(
            status_code=500,
            detail=f"No se encontró el archivo de credenciales: {SERVICE_ACCOUNT_KEY_PATH}"
        )

    try:
        return bigquery.Client.from_service_account_json(SERVICE_ACCOUNT_KEY_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando cliente BigQuery: {str(e)}")

# =========================
# LOGIN
# =========================
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "vimenca2025":
        return {"access_token": "token-secreto-vimenca", "token_type": "bearer"}

    raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")

# =========================
# UPLOAD FORECAST
# =========================
@app.post("/upload-forecast")
async def upload_forecast(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    try:
        content = await file.read()
        excel_file = io.BytesIO(content)

        # Leer hojas
        df_calls = pd.read_excel(excel_file, sheet_name="Origins")
        df_aht = pd.read_excel(excel_file, sheet_name="Origins2")
        df_fte = pd.read_excel(excel_file, sheet_name="Origins3")

        def melt_data(df: pd.DataFrame, label: str) -> pd.DataFrame:
            m = df.melt(
                id_vars=["Period"],
                var_name="date",
                value_name=label
            )
            m["date"] = pd.to_datetime(m["date"], errors="coerce").dt.date
            return m.dropna(subset=["date"])

        calls = melt_data(df_calls, "calls_forecast")
        aht = melt_data(df_aht, "aht_forecast")
        fte = melt_data(df_fte, "fte_required")

        final_df = (
            calls
            .merge(aht, on=["Period", "date"])
            .merge(fte, on=["Period", "date"])
        )

        final_df.rename(columns={"Period": "period"}, inplace=True)

        # BigQuery (USANDO KEY)
        client = get_bq_client()

        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

        client.load_table_from_dataframe(
            final_df,
            BQ_TABLE_ID,
            job_config=job_config
        ).result()

        return {
            "message": "Archivo procesado y cargado en BigQuery",
            "rows": len(final_df)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# VIEW DATA
# =========================
@app.get("/view-data")
async def view_data(token: str = Depends(oauth2_scheme)):
    try:
        client = get_bq_client()

        query = f"""
        SELECT *
        FROM `{BQ_TABLE_ID}`
        ORDER BY date DESC, period ASC
        LIMIT 100
        """

        rows = client.query(query).result()
        return [dict(row) for row in rows]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# LOCAL RUN
# =========================
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
