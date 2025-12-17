from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import bigquery
import pandas as pd
import io

app = FastAPI(title="Vimenca Forecast System")

# Configuración de seguridad simplificada
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- 1. SISTEMA DE LOGIN (SIMPLIFICADO) ---
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Aquí puedes conectar con tu base de datos de usuarios
    if form_data.username == "admin" and form_data.password == "vimenca2025":
        return {"access_token": "token-secreto-vimenca", "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")

# --- 2. PROCESAMIENTO DEL ARCHIVO ---
@app.post("/upload-forecast")
async def upload_forecast(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    try:
        content = await file.read()
        excel_file = io.BytesIO(content)
        
        # Leemos las 3 pestañas del único Excel
        df_calls = pd.read_excel(excel_file, sheet_name='Origins')
        df_aht = pd.read_excel(excel_file, sheet_name='Origins2')
        df_fte = pd.read_excel(excel_file, sheet_name='Origins3')

        def melt_data(df, label):
            m = df.melt(id_vars=['Period'], var_name='date', value_name=label)
            m['date'] = pd.to_datetime(m['date'], errors='coerce').dt.date
            return m.dropna(subset=['date'])

        # Verticalizamos y unimos
        calls = melt_data(df_calls, 'calls_forecast')
        aht = melt_data(df_aht, 'aht_forecast')
        fte = melt_data(df_fte, 'fte_required')

        final_df = calls.merge(aht, on=['Period', 'date']).merge(fte, on=['Period', 'date'])
        final_df.rename(columns={'Period': 'period'}, inplace=True)

        # Envío a BigQuery
        client = bigquery.Client()
        table_id = "poc-data-vimenca.ds_data_vimenca.forecast_final"
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        client.load_table_from_dataframe(final_df, table_id, job_config=job_config).result()

        return {"message": "Archivo procesado y cargado en BigQuery", "rows": len(final_df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. MOSTRAR DATOS DE BIGQUERY ---
@app.get("/view-data")
async def get_data(token: str = Depends(oauth2_scheme)):
    try:
        client = bigquery.Client()
        query = "SELECT * FROM `TU_PROJECT_ID.ds_data_vimenca.forecast_final` ORDER BY date DESC, period ASC LIMIT 100"
        query_job = client.query(query)
        results = query_job.result()
        
        data = [dict(row) for row in results]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)