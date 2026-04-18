from fastapi import FastAPI
from backend.api.analyze import router as analyze_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="合同审查Agent")

# ======================
# ⭐ CORS（前后端联调必需）
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(analyze_router)

# 测试接口
@app.get("/")
def root():
    return {"msg": "合同审查Agent运行成功"}