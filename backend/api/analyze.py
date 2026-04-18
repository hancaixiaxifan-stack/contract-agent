from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import uuid
import base64

from backend.services.contract_service import analyze_contract, identify_contract_type
from backend.services.pdf_service import extract_pdf_text
from backend.services.file_service import (
    init_database, save_pdf_temp, get_pdf_path,
    confirm_file, remove_temp_file, store_analysis_result,
    save_text_permanent, get_history_contracts, get_file,
    delete_file
)

router = APIRouter()

init_database()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================
# 1. 请求模型
# =========================
class AnalyzeRequest(BaseModel):
    text: str
    config: Optional[Dict[str, Any]] = None


class IdentifyRequest(BaseModel):
    text: Optional[str] = None
    file_data: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None


class AnalyzeFullRequest(BaseModel):
    file_id: Optional[int] = None
    text: str
    contract_type: str
    stance: str = "employer"
    penalty: bool = True
    confidentiality: bool = True
    payment: bool = True
    dispute: bool = True
    liability: bool = True
    termination: bool = False
    non_compete: bool = False
    privacy: bool = False
    ip_ownership: bool = False
    force_majeure: bool = False
    working_hours: bool = False
    social_insurance: bool = False
    delivery: bool = False
    interest_rate: bool = False
    warranty: bool = False

 
# =========================
# 2. 合同类型识别接口
# =========================
@router.post("/identify-contract")
async def identify_contract(req: IdentifyRequest):
    text = ""
    file_id = None

    if req.text:
        text = req.text
    elif req.file_data and req.file_name:
        if req.file_type == "pdf" or req.file_name.endswith(".pdf"):
            file_id = save_pdf_temp(req.file_name, req.file_data)
            file_path = get_pdf_path(file_id)
            text = extract_pdf_text(file_path) if file_path else ""
        else:
            file_bytes = base64.b64decode(req.file_data)
            text = file_bytes.decode("utf-8", errors="ignore")

    if not text:
        return {
            "file_name": req.file_name or "未知文件",
            "contract_type": "无法识别",
            "error": "未提供文本或文件内容"
        }

    result = identify_contract_type(text)

    return {
        "file_id": file_id,
        "file_name": req.file_name or "未知文件",
        "contract_type": result.get("contract_type", "未知合同类型"),
        "recommended_checks": result.get("recommended_checks", []),
        "text_preview": text[:500] if len(text) > 500 else text,
        "full_text": text
    }


# =========================
# 3. 文本分析接口
# =========================
@router.post("/analyze")
def analyze(req: AnalyzeRequest):

    config = req.config or {
        "penalty": True,
        "confidentiality": True,
        "payment": True,
        "dispute": True,
        "liability": True
    }

    result = analyze_contract(req.text, config)
    return result


# =========================
# 4. PDF上传分析接口
# =========================
@router.post("/analyze-pdf")
async def analyze_pdf(
    file: UploadFile = File(...),
    penalty: bool = True,
    confidentiality: bool = True,
    payment: bool = True,
    dispute: bool = True,
    liability: bool = True,
    stance: str = "employer"
):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    text = extract_pdf_text(file_path)

    config = {
        "penalty": penalty,
        "confidentiality": confidentiality,
        "payment": payment,
        "dispute": dispute,
        "liability": liability,
        "stance": stance
    }

    result = analyze_contract(text, config)

    return {
        "text_preview": text[:800],
        "result": result
    }


# =========================
# 5. 完整分析接口（用于result-detail页面）
# =========================
@router.post("/analyze-full")
async def analyze_full(req: AnalyzeFullRequest):
    try:
        config = {
            "penalty": req.penalty,
            "confidentiality": req.confidentiality,
            "payment": req.payment,
            "dispute": req.dispute,
            "liability": req.liability,
            "termination": req.termination,
            "non_compete": req.non_compete,
            "privacy": req.privacy,
            "ip_ownership": req.ip_ownership,
            "force_majeure": req.force_majeure,
            "working_hours": req.working_hours,
            "social_insurance": req.social_insurance,
            "delivery": req.delivery,
            "interest_rate": req.interest_rate,
            "warranty": req.warranty,
            "stance": req.stance,
            "contract_type": req.contract_type
        }

        result = analyze_contract(req.text, config)

        if req.file_id:
            store_analysis_result(req.file_id, req.contract_type, req.stance, result)

        return {
            "file_id": req.file_id,
            "contract_type": req.contract_type,
            "result": result
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "file_id": req.file_id,
            "contract_type": req.contract_type,
            "result": {
                "risks": [],
                "summary": f"分析出错: {str(e)}"
            }
        }


# =========================
# 6. 确认保存（结果页点击"是"）
# =========================
@router.post("/confirm-save")
async def confirm_save(file_id: int, contract_type: str = None):
    try:
        confirm_file(file_id, contract_type)
        return {"success": True, "message": "已保存"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# =========================
# 7. 删除临时文件（结果页点击"否"或超时）
# =========================
@router.post("/delete-temp")
async def delete_temp(file_id: int):
    try:
        remove_temp_file(file_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


# =========================
# 8. 获取PDF文件
# =========================
@router.get("/pdf/{file_id}")
async def get_pdf(file_id: int):
    file_path = get_pdf_path(file_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, media_type="application/pdf")


# =========================
# 9. 保存文本合同
# =========================
class SaveTextRequest(BaseModel):
    file_name: str
    text_content: str
    contract_type: Optional[str] = None
    stance: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None


@router.post("/save-text")
async def save_text(req: SaveTextRequest):
    try:
        file_id = save_text_permanent(req.file_name, req.text_content)
        if req.contract_type and req.result_data:
            store_analysis_result(file_id, req.contract_type, req.stance or "employee", req.result_data)
        return {"success": True, "file_id": file_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.get("/history")
async def get_history():
    try:
        contracts = get_history_contracts()
        return {"success": True, "contracts": contracts}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.delete("/contract/{file_id}")
async def delete_contract(file_id: int):
    try:
        delete_file(file_id)
        return {"success": True}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.get("/text/{file_id}")
async def get_text(file_id: int):
    file_info = get_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    try:
        with open(file_info["file_path"], "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/pdf-content/{file_id}")
async def get_pdf_content(file_id: int):
    file_info = get_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    try:
        with open(file_info["file_path"], "rb") as f:
            content = f.read()
        import base64
        return {"success": True, "content": base64.b64encode(content).decode()}
    except Exception as e:
        return {"success": False, "error": str(e)}
