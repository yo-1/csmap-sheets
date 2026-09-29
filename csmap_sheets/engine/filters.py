"""SciPy acceleration when available, NumPy-only fallback otherwise."""
import numpy as np


def numpy_gaussian(a, sigma, radius, **kwargs):
    if sigma == 0 or radius == 0:
        return np.asarray(a, dtype=float).copy()
    x=np.arange(-radius,radius+1,dtype=float)
    weights=np.exp(-0.5*(x/sigma)**2)
    weights/=weights.sum()
    result=np.asarray(a,dtype=float)
    for axis in (0,1):
        padding=[(0,0),(0,0)]
        padding[axis]=(radius,radius)
        padded=np.pad(result,padding,mode='constant')
        filtered=np.zeros_like(result)
        for offset,weight in enumerate(weights):
            slices=[slice(None),slice(None)]
            slices[axis]=slice(offset,offset+result.shape[axis])
            filtered+=weight*padded[tuple(slices)]
        result=filtered
    return result


def numpy_valid_minimum(a, size, **kwargs):
    """Binary minimum filter, constant-zero exterior, odd square support."""
    if size % 2 != 1 or size < 1:
        raise ValueError('Odd positive filter size required')
    radius=size//2
    padded=np.pad(np.asarray(a,dtype=np.int64),radius,mode='constant')
    integral=np.pad(padded,((1,0),(1,0)),mode='constant').cumsum(0).cumsum(1)
    sums=integral[size:,size:]-integral[:-size,size:]-integral[size:,:-size]+integral[:-size,:-size]
    return (sums==size*size).astype(np.uint8)


try:
    import scipy
    from scipy.ndimage import gaussian_filter, minimum_filter
    import inspect
    if 'radius' not in inspect.signature(gaussian_filter).parameters:
        raise ImportError('SciPy lacks radius support')
    BACKEND='SciPy '+scipy.__version__
except (ImportError, OSError):
    gaussian_filter=numpy_gaussian
    minimum_filter=numpy_valid_minimum
    BACKEND='NumPy fallback '+np.__version__
