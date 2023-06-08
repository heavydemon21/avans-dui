import sensor, image, time

sensor.reset()                      # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565) # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.HVGA)   # Set frame size to QVGA (320x240)
sensor.skip_frames(time = 2000)     # Wait for settings take effect.
clock = time.clock()                # Create a clock object to track the FPS.


def init_kpts(str):
    temp_img = image.Image(f"./{str}.jpg", copy_to_fb=True)
    temp_img.to_grayscale()
    kpts = temp_img.find_keypoints(max_keypoints=128, threshold=kpts_threshold, corner_detector=kpts_corner, scale_factor=1.2)
    return kpts

speed = init_kpts("speed")
stop = init_kpts("stop")
car = init_kpts("image")

def match_kpts(kpts0, kpts1):
    if kpts0 is not None and kpts1 is not None:
        match = image.match_descriptor(kpts0, kpts1, threshold=70)
        #print("matched:%d dt:%d"%(match.count(), match.theta()))
        if match.count() > 0:
            print(match.count())
        return match.count() > 0
    else:
        return 0

def read_red_sign(val, img, kpts):
    data = 0x00
    if match_kpts(kpts, stop):
        #img.draw_rectangle(val.rect())
        #img.draw_cross(match.cx(), match.cy(), size=10)
        #print("stop")
        return 0x01
    if match_kpts(kpts, speed):
        img.draw_rectangle(val.rect())
        #print("speed")
        return 0x02
    if match_kpts(kpts, car):
        img.draw_rectangle(val.rect())
        #print("car")
        return 0x03

#def read_red_sign(val, img, kpts):

def sign_detection(img):
    ######## Detect signs

    blobs_r = img.find_blobs([(0, 100, 25, 63, -128, 127)])
    blobs_b = img.find_blobs([(0, 29, 11, -128, -31, -5)])
    #print(f"old: { len(blobs_r) + len(blobs_b) }")

    blobs_r[:] = [b for b in blobs_r if (b.convexity() < 0.7 and b.area() > 64)]
    blobs_b[:] = [b for b in blobs_b if (b.convexity() < 0.7 and b.area() > 64)]
    #print(f"new: { len(blobs_r) + len(blobs_b) }")


    ######## Read signs
    img = img.to_grayscale()

    if(len(blobs_r) > 0 or len(blobs_b) > 0):
        kpts_img = img.find_keypoints(max_keypoints=255, threshold=kpts_threshold, corner_detector=kpts_corner)

        for index, b in enumerate(blobs_r):
            sign_buffer = read_red_sign(b, img, kpts_img)

        #for index, b in enumerate(blobs_b):
            #sign_buffer = read_blu_sign(b, img, kpts_img)
    return sign_buffer
