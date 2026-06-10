from core.layout_config import DEFAULT_IMAGE_PATH

from .image import ImageWidget


class DotMatrixArtWidget(ImageWidget):
    """
    点阵主视觉组件
    默认将图片渲染为主题色剪影，适合作为人物/物体像素轮廓。
    """

    DEFAULT_CSS = """
    DotMatrixArtWidget {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, image_path: str = None, **kwargs):
        kwargs.setdefault("image_display_mode", "fill")
        kwargs.setdefault("image_render_mode", "pixel")
        kwargs.setdefault("image_effect_mode", "silhouette")
        kwargs.setdefault("image_effect_threshold", 0.0)
        super().__init__(image_path=image_path or DEFAULT_IMAGE_PATH, **kwargs)
        self._title = "DOT MATRIX ART"
        self.border_title = " [ DOT MATRIX ART ] "
