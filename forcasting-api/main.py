from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
import pandas as pd
import io

# =========================
# APP
# =========================
app = FastAPI(title="Vimenca Forecast System")

# =========================
# CORS (IMPORTANTE PARA FRONTEND / CLOUD RUN)
# - Un solo middleware (no duplicar)
# - No usar "*" con allow_credentials=True
# =========================
ALLOWED_ORIGINS = [
    "http://localhost:5174",
    "http://localhost:5175",
    # Si luego tienes dominio real del frontend, agrégalo aquí:
    # "https://tu-frontend.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# (Opcional pero útil) Responder explícitamente a preflight
@app.options("/{path:path}")
async def preflight_handler(path: str, response: Response):
    return Response(status_code=204)

# =========================
# OAUTH2
# =========================
# Recomendado: tokenUrl="token" (sin slash), pero funciona igual
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# =========================
# LOGIN
# =========================
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    IMPORTANTE:
    Este endpoint espera x-www-form-urlencoded:
      username=...&password=...
    (No JSON)
    """
    if form_data.username == "admin" and form_data.password == "vimenca2025":
        return {
            "access_token": "token-secreto-vimenca",
            "token_type": "bearer"
        }

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

        # BigQuery
        client = bigquery.Client()
        table_id = "poc-data-vimenca.ds_data_vimenca.forecast_final"

        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE"
        )

        client.load_table_from_dataframe(
            final_df,
            table_id,
            job_config=job_config
        ).result()

        return {
            "message": "Archivo procesado y cargado en BigQuery",
            "rows": len(final_df)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# VIEW DATA
# =========================
@app.get("/view-data")
async def view_data(token: str = Depends(oauth2_scheme)):
    try:
        client = bigquery.Client()

        query = """
        SELECT *
        FROM `poc-data-vimenca.ds_data_vimenca.forecast_final`
        ORDER BY date DESC, period ASC
        LIMIT 100
        """

        rows = client.query(query).result()
        return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# LOCAL RUN
# =========================
if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
