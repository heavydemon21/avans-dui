import sensor, image, time
from pyb import Pin, delay, udelay

zumo_tx = Pin("PA10", Pin.IN)
zumo_rx = Pin("PA9", Pin.OUT_PP)

def uart_send(byte):
    zumo_rx.value(0)
    udelay(1000)
    for x in range(8):
        bit = (byte & (1 << 7)) >> 7
        byte <<= 1
        zumo_rx.value(bit)
        udelay(1000)
    zumo_rx.value(1)

__uart_buffer = bytearray()
def uart_flush():
    global __uart_buffer
    #print("UART FLUSH START")
    for byte in __uart_buffer:
        ##print(f"BYTE 0x{byte:02X}")
        uart_send(byte) # dit is de oplossing
        udelay(2000)
        uart_send(byte)
        udelay(2000)
        #uart_send(byte)
        #udelay(2000)
    __uart_buffer = bytearray()

def tx_irq_handler(pin):
    if pin is zumo_tx:
        uart_flush()

zumo_tx.irq(trigger = Pin.IRQ_RISING, handler = tx_irq_handler)

def uart_buffer(i):
    global __uart_buffer
    __uart_buffer.append(i)

def straight_lines(img, roi):
    num=25
    thresholds = (100, 150)
    img_XStride=2  # sizeof x pixels
    img_YStride=1 # sizeof y pixels
    img_threshold=3500
    img_thetaMargin=num
    img_rhoMargin=num

    img.crop(roi=roi)
    img.gaussian(4)
    # grayscale image
    imgBin = img.to_grayscale()

    # find edges in image
    edges = imgBin.find_edges(image.EDGE_CANNY,threshold=thresholds)

    # find different lines in image
    lines = edges.find_lines(x_stride=img_XStride,y_stride=img_YStride,threshold=img_threshold,
    theta_margin=img_thetaMargin,rho_margin=img_rhoMargin)

    return lines

#def horizontal_lines(img,roi):
    #num=5
    #thresholds = (80, 200)
    #img_XStride=2 # sizeof x pixels
    #img_YStride=30 # sizeof y pixels
    #img_threshold=2000
    #img_thetaMargin=num
    #img_rhoMargin=num
    ## grayscale image
    #imgBin = img.to_grayscale(roi=roi)

    ## find edges in image
    #edges = imgBin.find_edges(image.EDGE_CANNY,threshold=thresholds)

    ## find different lines in image
    #lines = edges.find_lines(roi=roi,x_stride=img_XStride,y_stride=img_YStride,threshold=img_threshold,
    #theta_margin=img_thetaMargin,rho_margin=img_rhoMargin)

    #return lines


sensor.reset()                      # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565) # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.HVGA)   # Set frame size to QVGA (320x240)
sensor.skip_frames(time = 2000)     # Wait for settings take effect.

# zumo constants
DUI_CMD_SIGN_START =0x01
DUI_CMD_SIGN_END =0x0f
DUI_CMD_SPEED_START =0x10
DUI_CMD_SPEED_END =0x1f
DUI_CMD_STEER_START =0x20
DUI_CMD_STEER_END =0xff

# constants for steering
STEERING_FACTOR = 0.1
MAX_STEERING_ANGLE = 1
leftCorner=False
rightCorner=False
clock = time.clock()                # Create a clock object to track the FPS.
count = 0
speed = DUI_CMD_SPEED_END

if __name__ == "__main__":
    while(True):
        speed = DUI_CMD_SPEED_START
        #uart_buffer(speed)

        clock.tick()                    # Update the FPS clock.

        #img = image.Image("/rtVerkeersborden.class/00027.jpg")         # Take a picture and return the image.
        img = sensor.snapshot()


        # copy image to frame buffer
        #roiImg = img.copy(copy_to_fb=True)

        #lines = horizontal_lines(roiImg, (0,0,480,60))
        lines = straight_lines(img, (0,60,480,150))

        left_line = None
        right_line = None
        middle_line = None
        for l in lines:
            length = l.theta()
            #img.draw_line(l.line(), color=100,thickness=3)

            if length > 85 and length < 95:
                middle_line = l
                #roiImg.draw_line(l.line(), color=150,thickness=3)

                ##print("rho {} mag {} length {}".format(l.rho(),l.magnitude(),l.length()))
            else:
                if length < 55 and length > 25:
                    left_line = l
                    #img.draw_line(l.line(), color=100,thickness=3)
                elif length < 135 and length > 115:
                    right_line = l
                    #img.draw_line(l.line(), color=50,thickness=3)


        # Calculate the different steering angle.
        left_theta=0
        right_theta=0
        steering_angle = 0.0

        if left_line and right_line:
            leftCorner=False
            rightCorner=False
            count = 0
            left_theta = left_line.theta()
            right_theta = right_line.theta()
            left_length = left_line.length()
            right_length = right_line.length()
            speed = DUI_CMD_SPEED_END

            sensitivity = (left_length + right_length) / 2 -90 # You can adjust this factor as needed

            steering_error = (left_theta + right_theta) / 2 - 89
            steering_angle = sensitivity * steering_error

            if steering_angle < 0:
                steering_angle = max(steering_angle, -1)
            else:
                steering_angle = min(steering_angle, 1)

            steering_angle = steering_angle
        else:
            count = count + 1

            if count > 5:

                if (right_line and not left_line) or leftCorner:
                    speed = DUI_CMD_SPEED_END
                    leftCorner=True
                    steering_angle = -MAX_STEERING_ANGLE
                elif (left_line and not right_line) or rightCorner:
                    rightCorner=True
                    steering_angle = MAX_STEERING_ANGLE
                else:
                    if leftCorner or rightCorner:
                        steering_angle = steering_angle
                        speed = 0x1f

        #print("steer {} speed {}".format(steering_angle,speed))

        #print("steer {} ".format(steering_angle))
            #print("steer {} sens {} err {}".format(steering_angle,sensitivity, steering_error))

        # steering angle byte calculation
        steerByte = int((steering_angle + 1.0) * (DUI_CMD_STEER_END - DUI_CMD_STEER_START) / 2 + DUI_CMD_STEER_START)
        #print("steer {} steerByte {} ".format(steering_angle,steerByte))

        # sending data:
        uart_buffer(steerByte)
        uart_buffer(speed)




