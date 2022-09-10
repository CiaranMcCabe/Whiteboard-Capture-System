import cv2
import numpy as np
import time

path = 'C:/Users/User/Images/'
boxpath = 'C:/Users/User/Images/GridImages/'
start = 0
x, y, w, h = 0, 0, 0, 0
foregrnd = 0
count = 0
board = []

def VideoCap():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1920)
    cap.set(4, 1080)

    while True:
        success, img = cap.read()
        cv2.imshow("Video", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyWindow('Video')
            break
    frame = cap.read()[1]
    if start == 0:
        cv2.imwrite(str(path)+'prime.png', frame)
    else:
        cv2.imwrite(str(path)+'frame.png', frame)
        prime = cv2.imread(str(path)+'prime.png', 0)
        sub = cv2.subtract(prime,frame)
        subgrey = cv2.cvtColor(sub, cv2.COLOR_BAYER_BG2GRAY)
        ret, thrsh = cv2.threshold(subgrey, 75, 255, cv2.THRESH_BINARY)
        if cv2.countNonZero(thrsh) > 1000:
            foregrnd = 1
        else:
            foregrnd = 0
    return frame, foregrnd


def ContourDet(frame, start, x, y, w, h, board):
    imgBlur = cv2.bilateralFilter(frame, 7, 15, 15)
    imgCanny = cv2.Canny(imgBlur, 10, 100)

    kernel = np.ones((5, 5), np.uint8)
    imgDil = cv2.morphologyEx(imgCanny, cv2.MORPH_CLOSE, kernel)

    contours, hierarchy = cv2.findContours(imgDil, 1, 2)
    area = 0
    if start == 0:
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            imgCont = cv2.rectangle(imgBlur, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if area < (w * h):
                area = w * h
                board = cnt
        x, y, w, h = cv2.boundingRect(board)
        cv2.imwrite(str(path)+ 'contours.png', imgCont)
    peri = cv2.arcLength (board, True)
    corners = cv2.approxPolyDP (board, 0.06*peri, True) 
    n = corners.ravel()
    coords = ([n[0],n[1]], [n[2],n[3]], [n[4],n[5]], [n[6], n[71]],) 
    sort1 = sorted (coords, key=lambda x: x[0])
    lcorners = (sort1[0], sort1[1])
    rcorners = (sort1[2], sort1[3]) 
    leftsort = sorted (lcorners, key=lambda x: x[1]) 
    rightsort = sorted (rcorners, key=lambda x: x[1]) 
    print(leftsort, rightsort)
    pts1 = np. float32 ([leftsort[0], rightsort[0], rightsort[1], leftsort[1]]) 
    pts2 = np. float32([[0, 0], [w, 0], [w, h], [0, h]])
    M = cv2.getPerspectiveTransform (pts1, pts2) 
    imgCrop = cv2.warpPerspective (frame, M, (w, h)) 
    cv2.imwrite (str(path) + 'crop.png', imgCrop) 
    return x, y, w, h, board


def cleanimage():
    img = cv2.imread(str(path)+'crop.png', 0)
    imgBW = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 21, 5)
    noise = cv2.fastNlMeansDenoising(imgBW, None, 50, 7, 51)
    cv2.imwrite(str(path)+ 'noise.png', noise)
    return


def gridimage(start, change, nochange):
    noise = cv2.imread(str(path)+'noise.png', 0)
    ni = np.array(noise)
    height, width = ni.shape[:2]
    boxesH = 25
    boxesW = 44

    for i in range(boxesW):
        for x in range(boxesH):
            this = ni[x * height // boxesH:(x + 1) * height // boxesH,
                       i * width // boxesW:(i + 1) * width // boxesW]
            if start == 0:
                cv2.imwrite(f'{str(boxpath)}box-{i}-{x}.png', this)
            else:
                this_array = np.array(this)
                prev = cv2.imread(f'{str(boxpath)}box-{i}-{x}.png', 0)
                prev_array = np.array(prev)
                if abs(np.mean(this_array) - np.mean(prev_array)) > 20:
                    change += 1
                else:
                    nochange += 1
                cv2.imwrite(str(boxpath)+f'box-{i}-{x}.png', this)
    start += 1
    if change > 5:
        cv2.imwrite(str(path) + f'final-{count}.png', noise)
        count += 1
    return start, count

try:
    while True:
        frame, foregrnd = VideoCap()
        if foregrnd == 0:
            x, y, w, h, board = ContourDet(frame, start, x, y, w, h, board)
            cleanimage()
            start = gridimage(start, 0, 0)
        else:
            print('Object blocking view of whiteboard')
        time.sleep(2)
except KeyboardInterrupt:
    pass
