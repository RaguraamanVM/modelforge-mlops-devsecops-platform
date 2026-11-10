import os

BACKEND_URL = os.getenv("MODELFORGE_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

API_HEADERS = {"X-API-Key": os.getenv("MODELFORGE_API_KEY", "")}

import streamlit as st

st.set_page_config(
    page_title="ModelForge",
    page_icon="🧠",
    layout="wide",
)

st.title("ModelForge")
st.caption("ML Model Registry & Inference Platform")

st.divider()

st.subheader("Dashboard")
st.success("ModelForge frontend initialized successfully!")

st.info("Model Registry, Model Upload, and Inference features coming next.")

st.subheader("Backend Connectivity")

try:
    import requests

    response = requests.get(
        f"{BACKEND_URL}/health",
        timeout=5,
    )
    response.raise_for_status()

    st.success("Backend online — FastAPI is responding!")
    st.json(response.json())

except requests.RequestException as error:
    st.error("Backend unavailable")
    st.caption(str(error))

st.divider()
st.subheader("Registered Models")

try:
    models_response = requests.get(
        f"{BACKEND_URL}/models",
        timeout=5,
    )
    models_response.raise_for_status()
    models = models_response.json()

    if isinstance(models, list):
        st.metric("Total Registered Models", len(models))

        if models:
            st.dataframe(
                models,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No models registered yet.")
    else:
        st.error("Unexpected model-list response format.")

except requests.RequestException as error:
    st.error("Unable to retrieve registered models.")
    st.caption(str(error))
except ValueError:
    st.error("Backend returned invalid JSON.")

st.divider()
st.subheader("Register New Model")

with st.form("register_model_form", clear_on_submit=True):
    model_name = st.text_input(
        "Model name *",
        max_chars=100,
        placeholder="e.g. customer-churn",
    )
    model_version = st.text_input(
        "Version *",
        max_chars=50,
        placeholder="e.g. 1.0",
    )
    model_description = st.text_area("Description")
    model_framework = st.text_input(
        "Framework",
        max_chars=50,
        placeholder="e.g. scikit-learn",
    )

    submitted = st.form_submit_button(
        "Register Model",
        type="primary",
    )

if submitted:
    if not model_name.strip() or not model_version.strip():
        st.warning("Model name and version are required.")
    else:
        payload = {
            "name": model_name.strip(),
            "version": model_version.strip(),
            "description": model_description.strip() or None,
            "framework": model_framework.strip() or None,
        }

        try:
            response = requests.post(
                f"{BACKEND_URL}/models",
                headers=API_HEADERS,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()

            st.success("Model registered successfully!")
            st.json(response.json())
            st.info("Refresh the page to update the model list.")

        except requests.RequestException as error:
            st.error("Model registration failed.")
            if error.response is not None:
                st.code(error.response.text)
            else:
                st.caption(str(error))

# Model Artifact Upload
st.divider()
st.subheader("Upload Model Artifact")

if "models" in locals() and isinstance(models, list) and models:
    model_options = {
        f"{model['name']} (v{model['version']}) — ID {model['id']}": model["id"]
        for model in models
    }

    with st.form("artifact_upload_form"):
        selected_model = st.selectbox(
            "Select registered model",
            options=list(model_options.keys()),
        )

        uploaded_file = st.file_uploader(
            "Choose a model artifact",
            type=["joblib", "pkl"],
        )

        upload_submitted = st.form_submit_button(
            "Upload Artifact",
            type="primary",
        )

    if upload_submitted:
        if uploaded_file is None:
            st.warning("Please select a .joblib or .pkl file.")
        elif uploaded_file.size > 50 * 1024 * 1024:
            st.error("Artifact exceeds the 50 MB limit.")
        else:
            model_id = model_options[selected_model]

            try:
                response = requests.post(
                    f"{BACKEND_URL}/models/{model_id}/artifact",
                    headers=API_HEADERS,
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/octet-stream",
                        )
                    },
                    timeout=120,
                )
                response.raise_for_status()

                st.success("Model artifact uploaded successfully!")
                st.json(response.json())

            except requests.RequestException as error:
                st.error("Artifact upload failed.")
                if error.response is not None:
                    st.code(error.response.text)
                else:
                    st.caption(str(error))
else:
    st.info("Register a model before uploading an artifact.")


# Model Inference
st.divider()
st.subheader("Model Inference")

st.caption(
    "Select a registered model and enter four numeric features "
    "to generate a prediction."
)

if "models" in locals() and isinstance(models, list) and models:
    inference_options = {
        f"{model['name']} (v{model['version']}) — ID {model['id']}": model["id"]
        for model in models
    }

    with st.form("model_inference_form"):
        selected_inference_model = st.selectbox(
            "Select model for inference",
            options=list(inference_options.keys()),
        )

        st.write("Input Features")

        col1, col2 = st.columns(2)

        with col1:
            feature_1 = st.number_input(
                "Feature 1", value=1.0
            )
            feature_2 = st.number_input(
                "Feature 2", value=2.0
            )

        with col2:
            feature_3 = st.number_input(
                "Feature 3", value=3.0
            )
            feature_4 = st.number_input(
                "Feature 4", value=4.0
            )

        predict_submitted = st.form_submit_button(
            "Run Prediction",
            type="primary",
        )

    if predict_submitted:
        model_id = inference_options[selected_inference_model]

        payload = {
            "features": [
                feature_1,
                feature_2,
                feature_3,
                feature_4,
            ]
        }

        try:
            response = requests.post(
                f"{BACKEND_URL}/models/{model_id}/predict",
                headers=API_HEADERS,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()

            st.success("Prediction completed successfully!")
            st.json(result)

        except requests.RequestException as error:
            st.error("Model inference failed.")

            if error.response is not None:
                st.code(error.response.text)
            else:
                st.caption(str(error))

        except ValueError:
            st.error("Backend returned invalid JSON.")

else:
    st.info("Register a model before running inference.")
