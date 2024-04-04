def calc_window_width_level(image):
    """Calculates window width and level of image.

    Args:
        image: vtkImageData.

    Returns:
        ww: window width.
        wl: window level.
    """
    min, max = image.GetScalarRange()
    ww = max
    wl = (max - min) // 2
    return ww, wl


def convert_image(image, ww, wl, scale=255.0):
    min_val = wl - ww // 2
    max_val = wl + ww // 2

    image[image < min_val] = min_val
    image[image > max_val] = max_val
    image -= min_val
    image /= ww
    image *= scale

    return image
