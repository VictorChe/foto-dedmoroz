#!/usr/bin/env python3
"""
Создаёт santa.usdz для AR Quick Look (Apple).
Требования: без сжатия (ZIP_STORED), выравнивание данных по 64 байта,
первый файл — USDC (бинарный USD), текстура по относительному пути.
"""
import zipfile
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

SCRIPT_DIR = Path(__file__).resolve().parent
IMAGE_PATH = SCRIPT_DIR / "santa.png"
OUTPUT_USDZ = SCRIPT_DIR / "santa.usdz"

IMG_W, IMG_H = 436, 697
ASPECT = IMG_W / IMG_H
W, H = ASPECT, 1.0
HW, HH = W / 2, H / 2

POINTS = [(-HW, -HH, 0), (-HW, HH, 0), (HW, HH, 0), (HW, -HH, 0)]
UVS = [(0, 0), (0, 1), (1, 1), (1, 0)]


def make_stage():
    stage = Usd.Stage.CreateInMemory()
    stage.SetMetadata("upAxis", "Y")
    root = UsdGeom.Xform.Define(stage, "/root")
    stage.SetDefaultPrim(root.GetPrim())
    root.AddScaleOp().Set(Gf.Vec3f(2, 2, 2))

    mesh = UsdGeom.Mesh.Define(stage, "/root/Plane")
    mesh.CreatePointsAttr(POINTS)
    mesh.CreateFaceVertexCountsAttr([4])
    mesh.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    mesh.CreateExtentAttr([(-HW, -HH, 0), (HW, HH, 0)])
    mesh.CreateDoubleSidedAttr(True)
    # Нормаль смотрит по +Z; fallback-цвет для превью, если материал не подхватится
    mesh.CreateNormalsAttr([(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)])
    mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
    mesh.CreateDisplayColorAttr([(0.95, 0.95, 0.95)])

    primvar_api = UsdGeom.PrimvarsAPI(mesh)
    st = primvar_api.CreatePrimvar(
        "st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex
    )
    st.Set(UVS)

    material = UsdShade.Material.Define(stage, "/root/Material")
    shader = UsdShade.Shader.Define(stage, "/root/Material/PreviewSurface")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.9)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

    st_reader = UsdShade.Shader.Define(stage, "/root/Material/StReader")
    st_reader.CreateIdAttr("UsdPrimvarReader_float2")
    st_reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")

    texture = UsdShade.Shader.Define(stage, "/root/Material/DiffuseTexture")
    texture.CreateIdAttr("UsdUVTexture")
    texture.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath("santa.png"))
    texture.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")
    texture.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
        st_reader.ConnectableAPI(), "result"
    )
    # Прямоугольник с прозрачностью: цвет и альфа из текстуры (без овала, не обрезаем головы/ноги)
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
        texture.ConnectableAPI(), "rgb"
    )
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).ConnectToSource(
        texture.ConnectableAPI(), "a"
    )

    UsdShade.MaterialBindingAPI(mesh.GetPrim()).Bind(material)
    return stage


def pad_extra_for_64_align(offset, filename_len):
    """Размер extra, чтобы (offset + 30 + filename_len + extra) % 64 == 0."""
    header_base = 30 + filename_len
    need = (64 - (offset + header_base) % 64) % 64
    return need


def main():
    stage = make_stage()

    # Корневой слой: USDA для совместимости с превью (Finder/Quick Look), Apple AR тоже принимает
    usda_path = SCRIPT_DIR / "santa_plane.usda"
    stage.Export(str(usda_path))
    usda_data = usda_path.read_bytes()
    usda_path.unlink(missing_ok=True)

    png_data = IMAGE_PATH.read_bytes()

    # USDZ: без сжатия, выравнивание по 64 байта (требование Apple)
    with zipfile.ZipFile(OUTPUT_USDZ, "w", zipfile.ZIP_STORED) as zf:
        # Первый файл — корневой USD (Default Layer)
        name1 = "santa_plane.usda"
        pad1 = pad_extra_for_64_align(0, len(name1))
        zinfo1 = zipfile.ZipInfo(name1)
        zinfo1.extra = b"\x00" * pad1
        zf.writestr(zinfo1, usda_data)

        # Второй файл — текстура; данные должны начинаться с 64-байтной границы
        offset_after_first = 30 + len(name1) + pad1 + len(usda_data)
        name2 = "santa.png"
        pad2 = pad_extra_for_64_align(offset_after_first, len(name2))
        zinfo2 = zipfile.ZipInfo(name2)
        zinfo2.extra = b"\x00" * pad2
        zf.writestr(zinfo2, png_data)

    print("Written:", OUTPUT_USDZ)


if __name__ == "__main__":
    main()
