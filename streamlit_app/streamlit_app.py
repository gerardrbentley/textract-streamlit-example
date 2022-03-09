import io
import json
from typing import Tuple

import boto3
import streamlit as st
from PIL import Image, ImageDraw, ImageOps
from pydantic import BaseSettings
from datetime import datetime

from textract_detect_model import TextractDetectModel

st.set_page_config(
    page_title="Document Scanner",
    page_icon=":computer:",
    layout="wide",
)


class Settings(BaseSettings):
    """Handles fetching configuration from environment variables and secrets.
    Type-hinting for config as a bonus"""

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_bucket_name: str
    aws_region: str

    s3_folder: str = 'test'
    s3_doc_prefix: str = 'doc'


def main():
    """Main Streamlit App Entrypoint"""
    settings = Settings()

    textract_client = boto3.client(
        "textract",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    s3_client = boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    st.title("Document Scanner :computer:")
    st.header(
        "Never type data from a document again! "
        "Upload your document and get the text out to copy or edit!"
    )
    with st.form("Document Upload", clear_on_submit=True):
        document_folder = st.selectbox("Document Folder", ["Invoices", "Reports", "Origination", "Taxes"])
        document_type = st.selectbox("Document Type", ["invoice", "report", "application", "1098"])

        uploaded_data = st.file_uploader(
            "Choose an image",
            type=["png", "jpg", "jpeg"],  # TODO: Fix PDF. No Pillow handling, use filenames
        )
        submitted = st.form_submit_button("Upload!")

    if submitted and uploaded_data is not None:
        with st.spinner("Loading Image Bytes"):
            # Grab utc timestamp for filenaming
            ts = datetime.utcnow().strftime("%Y_%m_%d_%H_%M_%S")
            filename = f"{document_folder}/{document_type}_{ts}.png"

            s3_path, image = load_image_to_s3(s3_client, uploaded_data, settings.aws_bucket_name, filename)
            uploaded_data = None
        st.success(f"Uploaded file to s3 as {filename}")
        with st.spinner("Detecting Text in the image"):
            response = textract_detect_text(textract_client, s3_path, settings.aws_bucket_name)
            textractResponse = TextractDetectModel(**response)
            extracted_text = [
                block.Text
                for block in textractResponse.Blocks
                if block.BlockType == "LINE"
            ]

        st.success(f"Found {len(extracted_text)} Lines of text!")

        with st.spinner("Drawing detected boxes"):
            painted_image = draw_bboxes(textractResponse, image)

        col1, col2 = st.columns(2)
        col1.header("Detected Text Boxes")
        col1.image(
            painted_image,
            use_column_width=True,
        )
        col2.header("Extracted Lines of Text")
        paragraph_text = col2.text_area(
            "(Edit any Errors)",
            "\n".join(extracted_text),
            height=10 * len(extracted_text),
        )
        col2.download_button(
            label="Download text paragraph",
            data=paragraph_text,
            file_name=f"{s3_path.replace('.png', '')}_text.txt",
        )
        extracted_text_data = json.dumps(extracted_text, indent=4, ensure_ascii=True)
        col2.download_button(
            label="Download list of original text lines",
            data=extracted_text_data,
            file_name=f"{s3_path.replace('.png', '')}_lines.json",
            mime="text/json",
        )

        with st.expander("Show Raw Image and Response", expanded=False):
            st.header("Raw Image")
            st.image(
                image,
                use_column_width=True,
            )

            st.header("Raw response")
            response_data = json.dumps(response, indent=4, ensure_ascii=True)
            st.download_button(
                label="Download Response",
                data=response_data,
                file_name=f"{s3_path.replace('.png', '')}_response.json",
                mime="text/json",
            )
            st.write(response)


@st.cache(hash_funcs={"botocore.client.S3": id})
def load_image_to_s3(
    s3_client, uploaded_data: bytes, bucketname: str, filename: str
) -> Tuple[str, Image.Image]:
    image = Image.open(uploaded_data)
    # Handle rotations if necessary
    image = ImageOps.exif_transpose(image)
    image_file_obj = io.BytesIO()
    image.save(image_file_obj, "PNG")
    image_file_obj.seek(0)

    s3_client.upload_fileobj(image_file_obj, bucketname, filename)
    return filename, image


@st.cache(hash_funcs={"botocore.client.Textract": id})
def textract_detect_text(textract_client, filename: str, bucket_name: str) -> dict:
    """Takes a filename of s3 image object.
    Tries to return response from AWS Textract detect_document_text API on the image str
    See docs for more: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract.html#Textract.Client.detect_document_text  # noqa: E501

    Args:
        filename (str): s3 path to image

    Returns:
        dict: List of text detections, geometry of the detections, and metadata
    """
    response = textract_client.detect_document_text(
        Document={
            "S3Object": {
                "Bucket": bucket_name,
                "Name": filename,
            }
        }
    )
    return response


def draw_bboxes(response: TextractDetectModel, image: Image) -> Image:
    image_w, image_h = image.size
    painted_image = image.copy()
    canvas = ImageDraw.Draw(painted_image)
    for detection in response.Blocks:
        if detection.BlockType == "LINE":
            aws_bbox = detection.Geometry.BoundingBox
            top_left_x = aws_bbox.Left * image_w
            top_left_y = aws_bbox.Top * image_h
            box_width = aws_bbox.Width * image_w
            box_height = aws_bbox.Height * image_h
            bot_right_x = top_left_x + box_width
            bot_right_y = top_left_y + box_height
            canvas.rectangle(
                (top_left_x, top_left_y, bot_right_x, bot_right_y),
                outline="Red",
                width=3,
            )
    return painted_image



if __name__ == "__main__":
    main()
