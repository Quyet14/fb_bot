# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.scheduler import _lay_cau_hinh_hien_tai
from app.crud import update_settings
from app.dependencies import get_user_id

router = APIRouter(prefix="/settings", tags=["Cau hinh"])


@router.get("/", response_model=schemas.AppSettingsOut)
def xem_cau_hinh(db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return _lay_cau_hinh_hien_tai(db, user_id=user_id)


@router.put("/", response_model=schemas.AppSettingsOut)
def sua_cau_hinh(data: schemas.AppSettingsUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    _lay_cau_hinh_hien_tai(db, user_id=user_id)  # dam bao da co dong cau hinh
    return update_settings(db, data, user_id=user_id)


@router.post("/select-image-dir")
def chon_thu_muc_anh(user_id: str = Depends(get_user_id)):
    try:
        import subprocess

        ps = r"""
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = 'Chon thu muc anh'
$dialog.ShowNewFolderButton = $true
$result = $dialog.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  Write-Output $dialog.SelectedPath
}
"""
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-STA", "-Command", ps],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout or "").strip())
        path = (completed.stdout or "").strip()
        return {"path": path or ""}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Khong mo duoc hop thoai chon thu muc: {exc}")


@router.get("/select-image-dir/status")
def trang_thai_chon_thu_muc(user_id: str = Depends(get_user_id)):
    return {"method": "powershell-winforms", "timeout_seconds": 300}
