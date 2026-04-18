import os
import uuid
import base64
from backend.models.file_model import (
    create_file, get_file as model_get_file, update_file_status,
    delete_file, save_result, init_db,
    get_all_saved_contracts
)
from backend.services.pdf_service import extract_pdf_text
from backend.services.contract_service import identify_contract_type

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def init_database():
    init_db()


def get_file(file_id: int):
    return model_get_file(file_id)


def save_pdf_temp(file_name: str, file_data: str) -> int:
    file_bytes = base64.b64decode(file_data)
    file_size = len(file_bytes)

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    db_file_id = create_file(file_name, file_path, file_size)

    return db_file_id


def get_pdf_path(file_id: int) -> str:
    file_info = get_file(file_id)
    if file_info and os.path.exists(file_info["file_path"]):
        return file_info["file_path"]
    return None


def confirm_file(file_id: int, contract_type: str = None):
    update_file_status(file_id, "saved", contract_type)


def remove_temp_file(file_id: int):
    delete_file(file_id)


def store_analysis_result(file_id: int, contract_type: str, stance: str, result: dict) -> int:
    return save_result(file_id, contract_type, stance, result)


def save_text_permanent(file_name: str, text_content: str) -> int:
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_content)

    file_size = len(text_content.encode("utf-8"))
    db_file_id = create_file(file_name, file_path, file_size)
    update_file_status(db_file_id, "saved")

    return db_file_id


def get_history_contracts():
    return get_all_saved_contracts()
