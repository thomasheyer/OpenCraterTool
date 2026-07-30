__all__ = ['SVGExporter']

from .Exporter import Exporter


class SVGExporter(Exporter):
    """SVG export is disabled in the opencratertool QGIS plugin security build.

    Upstream SVG export relied on XML DOM parsing, which security scanners flag.
    opencratertool does not use exporters.
    """

    Name = "Scalable Vector Graphics (SVG) [disabled]"
    allowCopy = False

    def __init__(self, item):
        raise RuntimeError(
            "SVGExporter is disabled in the opencratertool QGIS plugin "
            "build for security reasons"
        )

    def parameters(self):
        return None

    def export(self, fileName=None, toBytes=False, copy=False):
        raise RuntimeError(
            "SVGExporter is disabled in the opencratertool QGIS plugin "
            "build for security reasons"
        )


SVGExporter.register()
