"""Copy the CS calculation DEM to a standalone elevation GeoTIFF."""
from pathlib import Path

from .progress import check_cancel, report


def export_merged_dem(source, destination, gdal, feedback=None):
    """Copy the aligned, unsmoothed DEM; do not resample or colorize again.

    A temporary sibling is renamed only after Translate and FlushCache succeed.
    The caller owns a fresh run directory, so existing outputs are rejected.
    """
    destination = Path(destination)
    partial = destination.with_name(destination.stem + '.partial.tif')
    if destination.exists() or partial.exists():
        raise FileExistsError(f'DEM output already exists: {destination}')
    check_cancel(feedback)

    def progress(fraction, message, data):
        if feedback is not None:
            feedback.setProgress(5 + fraction * 5)
            return 0 if feedback.isCanceled() else 1
        return 1

    result = None
    try:
        result = gdal.Translate(
            str(partial), str(source), format='GTiff',
            creationOptions=[
                'TILED=YES', 'COMPRESS=DEFLATE', 'PREDICTOR=3',
                'BIGTIFF=IF_SAFER',
            ], callback=progress,
        )
        if result is None:
            check_cancel(feedback)
            raise RuntimeError('Merged DEM GeoTIFF export failed')
        if result.RasterCount != 1:
            raise ValueError('Expected a single-band elevation DEM')
        status = result.FlushCache()
        if status not in (None, 0):
            raise RuntimeError("Merged DEM GeoTIFF flush failed")
        result = None
        check_cancel(feedback)
        partial.rename(destination)
    except BaseException:
        result = None
        partial.unlink(missing_ok=True)
        raise
    report(feedback, f'Merged elevation DEM: {destination}')
    return destination
