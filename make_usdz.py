#!/usr/bin/env python3
"""
Создаёт santa.usdz с плоскостью в правильном соотношении сторон (436x697),
чтобы изображение не обрезалось в AR Quick Look.
"""
import zipfile
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

SCRIPT_DIR = Path(__file__).resolve().parent
IMAGE_PATH = SCRIPT_DIR / "santa.png"
OUTPUT_USD = SCRIPT_DIR / "santa_plane.usda"
OUTPUT_USDZ = SCRIPT_DIR / "santa.usdz"

# Соотношение сторон изображения (width x height)
IMG_W = 436
IMG_H = 697
ASPECT = IMG_W / IMG_H

# Плоскость: высота 1, ширина = aspect — картинка целиком без обрезки
W, H = ASPECT, 1.0
HW, HH = W / 2, H / 2

# Квад в плоскости XY, центр в начале. Порядок вершин под UV (0,0)-(1,1)
POINTS = [(-HW, -HH, 0), (-HW, HH, 0), (HW, HH, 0), (HW, -HH, 0)]
UVS = [(0, 0), (0, 1), (1, 1), (1, 0)]


def main():
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
    # В архиве файл будет santa.png — ссылаемся так
    texture.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath("santa.png"))
    texture.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
        st_reader.ConnectableAPI(), "result"
    )
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
        texture.ConnectableAPI(), "rgb"
    )

    UsdShade.MaterialBindingAPI(mesh.GetPrim()).Bind(material)

    stage.Export(str(OUTPUT_USD))

    # USDZ = zip: сначала корневой USD, потом ресурсы (для валидного USDZ)
    with zipfile.ZipFile(OUTPUT_USDZ, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUTPUT_USD, "santa_plane.usda")
        zf.write(IMAGE_PATH, "santa.png")

    OUTPUT_USD.unlink()
    print("Written:", OUTPUT_USDZ)


if __name__ == "__main__":
    main()
