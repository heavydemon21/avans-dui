import sensor, image, time, math

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
clock = time.clock()

"""
returns hsv tuple for rgb input tuple
"""
def rgb2hsv(rgb):
    r, g, b = rgb
    maxc = max(r, g, b)
    minc = min(r, g, b)
    rangec = (maxc-minc)
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = rangec / maxc
    rc = (maxc-r) / rangec
    gc = (maxc-g) / rangec
    bc = (maxc-b) / rangec
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return (h, s, v)

while(True):
    clock.tick()
    img = sensor.snapshot()
    ## todo: downsample img
    original = img.copy(copy_to_fb=True)
    img = img.to_grayscale()
    for blob in img.find_blobs([(0, 60)], pixels_threshold=100):
        aspect = blob.h() / blob.w()
        if abs(aspect - 2.2) > 0.5: continue
        lights = (
            (round(blob.x() + blob.w() / 2), round(blob.y() + 0.8 * blob.h())),
            (round(blob.x() + blob.w() / 2), round(blob.y() + 0.5 * blob.h())),
            (round(blob.x() + blob.w() / 2), round(blob.y() + 0.2 * blob.h())),
        )

        light_status = 0
        for i, light in enumerate(lights):
            r, g, b = original.get_pixel(light[0], light[1])
            h, s, v = rgb2hsv(((r/255),(g/255),(b/255),))
            if s < 0.65: continue
            # if v < 0.3: continue
            if i == 0 and abs(h - 0.50) < 0.45: continue
            if i == 1 and abs(h - 0.05) > 0.1: continue
            if i == 2 and abs(h - 0.40) > 0.1: continue
            light_status = i + 1
            print((h,s,v,))
            break
        if light_status == 0:
            continue

        img.draw_rectangle(blob.rect())
        img.draw_circle(lights[light_status-1][0], lights[light_status-1][1], 2)
        print(("", "rood", "geel", "groen")[light_status])
