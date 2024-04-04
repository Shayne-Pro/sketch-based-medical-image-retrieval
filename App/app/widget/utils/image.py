def calc_window_width_level(image):
    min, max = image.GetScalarRange()
    ww = max
    wl = (max - min) // 2
    return ww, wl
