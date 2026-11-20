from pathlib import Path
import tempfile

import streamlit as st
import torch

from spillguard_inference import load_model, predict_single_image

DEFAULT_MODEL_PATH = Path("processed_dataset/best_efficientnet_b0_spillguard.pth")
DEFAULT_THRESHOLD = 0.5

st.set_page_config(page_title="SpillGuard", page_icon="🛢️", layout="wide")


@st.cache_resource
def get_model(model_path: str):
    model_path = Path(model_path)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(model_path, device)
    return model, device


st.title("SpillGuard")
st.caption("Upload a SAR image patch to run Oil vs No-Oil inference.")

with st.sidebar:
    st.header("Settings")
    model_path = st.text_input(
        "Model checkpoint path",
        value=str(DEFAULT_MODEL_PATH),
        help="Relative or absolute path to the trained SpillGuard checkpoint.",
    )
    threshold = st.slider(
        "Prediction threshold",
        min_value=0.05,
        max_value=0.95,
        value=DEFAULT_THRESHOLD,
        step=0.01,
        help="Probability threshold used to decide whether the image is classified as Oil.",
    )

uploaded_file = st.file_uploader(
    "Choose an image",
    type=["png", "jpg", "jpeg", "bmp", "tif", "tiff"],
    help="Upload one SAR image patch for inference.",
)

if uploaded_file is not None:
    image_bytes = uploaded_file.read()
    file_name = uploaded_file.name

    if not image_bytes:
        st.error("The uploaded file is empty.")
    else:
        with tempfile.NamedTemporaryFile(suffix=Path(file_name).suffix) as temp_file:
            temp_file.write(image_bytes)
            temp_file.flush()
            try:
                model, device = get_model(model_path)
                result = predict_single_image(model, temp_file.name, device, threshold=threshold)
            except Exception as exc:
                st.error(f"Inference failed: {exc}")
                st.stop()

        st.subheader("Prediction")
        st.image(image_bytes, caption=f"Input image: {file_name}", use_container_width=True)

        probability = result["probability"]
        predicted_label = result["predicted_label"]
        confidence = probability if predicted_label == "Oil" else 1 - probability

        col1, col2, col3 = st.columns(3)
        col1.metric("Class", predicted_label)
        col2.metric("Oil probability", f"{probability:.4f}")
        col3.metric("Confidence", f"{confidence:.4f}")

        st.progress(min(1.0, max(0.0, probability)))
        st.write("Prediction payload:")
        st.json(
            {
                "image": result["image"],
                "predicted_label": result["predicted_label"],
                "probability": result["probability"],
                "threshold": result["threshold"],
            }
        )

else:
    st.info("Upload an image to start a prediction.")
