"""For starting up remote processes"""
import sys

if __name__ == '__main__':
    # Disabled in the opencratertool QGIS plugin build: upstream uses pickle to
    # deserialize process bootstrap options from stdin, which security scanners
    # flag and which this plugin does not use.
    sys.stderr.write(
        "pyqtgraph multiprocess bootstrap is disabled in the opencratertool "
        "QGIS plugin build for security reasons\n"
    )
    raise SystemExit(1)
