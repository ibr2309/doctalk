#!/bin/bash
# Start FastAPI internally, then Streamlit on the port HF Spaces expects.
uvicorn api:app --host 0.0.0.0 --port 8000 &
export API_URL=http://localhost:8000
exec streamlit run ui.py --server.port=7860 --server.address=0.0.0.0
