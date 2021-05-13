import numpy as np
import cv2
import glob

# Sondlandırma kriteri:
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Kalibrasyon fonksiyonu:
# "dirpath" = Görüntülerin bulunduğu dizin.
# "prefix" = Görüntülerin ortak ismi.(resim1.jpg, resim2.jpg şeklinde
# ilerlenecekse "resim" yazılır.)
# "square_size" = Satranç tahtasındaki bir karenin uzunluğu.
# "width" = Satranç tahtasının uzun keneranın içinde bulunan nokta sayısı.
# "height" = Satranç tahtasının kısa kenarının içinde bulunan nokta sayısı.
def calibrate(dirpath, prefix, image_format, square_size, width=9, height=6):

    global gray

    # Verilen dizin yolundaki görüntüler için kamera kalibrasyon fonksiyonu
    # uygulanacaktır. (0,0,0), (1,0,0), (2,0,0) ....,(8,6,0) gibi nesne noktaları
    # hazırlanacaktır.
    objp = np.zeros((height*width, 3), np.float32) # Satranç tahtasının
                                                   # koordinatlarının bulunduğu dizi.
    objp[:, :2] = np.mgrid[0:width, 0:height].T.reshape(-1, 2)

    objp = objp * square_size # Koordinatlar, girmiş olduğumuz uzunluk değeri ile çarpılır.

    # Tüm görüntülerden nesne noktalarını ve görüntü noktalarını kaydetmek için
    # objpoints ve imgpoints dizileri kullanılmıştır.
    objpoints = [] # 3 boyutta öngördüğümüz nokta karşılıklarının tutulduğu dizi
    imgpoints = [] # Kameranın aldığı görüntüde satranç tahtasının siyah/beyaz
                   # buluşma koordinatlarının tutulduğu dizi

    if dirpath[-1:] == '/':
        dirpath = dirpath[:-1]

    images = glob.glob(dirpath + '/' + prefix + '*.' + image_format)
    i = 0

    # "images" klasörü içerisinde bulunan resimlerin kalibrasyon için
    # kullanılması:
    for fname in images:
        i += 1
        img = cv2.imread(fname)
        img = cv2.resize(img,(600,480))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Satranç tahtası köşelerinin bulunması, ret değeri satranç tahtasının
        # bulunup bulunmadığını belirtmektedir.
        ret, corners = cv2.findChessboardCorners(gray, (width, height), None)

        # Köşe noktaları bulunursa, iyileştirilmiş görüntü noktalarının eklenmesi:
        if ret:
            objpoints.append(objp)

            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                                                        criteria)
            imgpoints.append(corners2)

            # Köşelerin çizilip gösterilmesi:
            cv2.drawChessboardCorners(img, (width, height), corners2, ret)
            print(i)
            if i == 20:
                cv2.putText(img, "20/20", (5, 20), cv2.FONT_HERSHEY_SIMPLEX,
                                                                0.6, (0, 255, 0), 2)
                cv2.putText(img, "Calibration Completed", (5, 40),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            else:
                cv2.putText(img, str(i)+"/20", (5, 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.imshow("Calibration Image", img)
            cv2.moveWindow("Calibration Image", 620, 15)
            cv2.waitKey(150)

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints,
                                                            gray.shape[::-1], None, None)

    return [ret, mtx, dist, rvecs, tvecs]

# Kamera matrisini ve bozulma katsayılarının verilen yola / dosyaya kaydedilmesi:
def save_coefficients(mtx, dist, path):
    cv_file = cv2.FileStorage(path, cv2.FILE_STORAGE_WRITE)
    cv_file.write("K", mtx)
    cv_file.write("D", dist)
    # note you *release* you don't close() a FileStorage object
    cv_file.release()


# Kamera matrisini ve bozulma katsayılarını yükleme:
def load_coefficients(path):
    # FILE_STORAGE_READ
    cv_file = cv2.FileStorage(path, cv2.FILE_STORAGE_READ)

    # Alınacak türü de belirtmemiz gerektmektedir, aksi takdirde bir matris yerine
    # yalnızca bir File Node nesnesi geri alınır.
    camera_matrix = cv_file.getNode("K").mat()
    dist_matrix = cv_file.getNode("D").mat()

    cv_file.release()
    return [camera_matrix, dist_matrix]

# "calibrate" fonksiyonun çağrılması:
ret, mtx, dist, rvecs, tvecs = calibrate("calibration_images", "img", "jpg", 0.025)

# Kalibrasyon sonuçlarının "camera.yml" ismindeki dosyaya kaydedilmesi:
save_coefficients(mtx, dist, "camera.yml")

# Kalibrasyon sonuçlarının yüklenerek kodlara dahil edilmesi:
camera_matrix, dist_matrix = load_coefficients("camera.yml")

img1 = cv2.imread("calibration_images/img (1).jpg")
img1 = cv2.resize(img1, (720, 480))
img2 = cv2.imread("calibration_images/img (1).jpg")
img2 = cv2.resize(img2, (720, 480))

# Kalibrasyon sonucunda çıkan düzeltme matrislerinin her bir frame
# uygulanması:
h, w = img1.shape[:2]
newcameramtx, roi = cv2.getOptimalNewCameraMatrix(camera_matrix,
dist_matrix, (w, h), 1, (w, h))
dst = cv2.undistort(img1, camera_matrix, dist_matrix, None, newcameramtx)
x, y, w, h = roi
img1 = dst[y:y + h, x:x + w]

cv2.imshow("img1", img1)
cv2.imshow("img2", img2)
cv2.waitKey(0)