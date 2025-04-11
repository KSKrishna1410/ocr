import cv2
import numpy as np
import os
import paramiko
from typing import List, Tuple


class OCRBoxDrawer:
    def __init__(self, image_path: str, ocr_data: List[Tuple[List[List[int]], Tuple[str, float]]]):
        self.image_path = image_path
        self.ocr_data = ocr_data
        self.image = cv2.imread(image_path)
        self.box_color = (0, 255, 0)
        self.text_color = (255, 0, 0)
        self.thickness = 2
        self.font_scale = 0.5
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_boxes(self):
        for points, (text, conf) in self.ocr_data:
            points = np.array(points, dtype=np.int32)
            cv2.polylines(self.image, [points], isClosed=True, color=self.box_color, thickness=self.thickness)
            # x, y = points[0]
            # cv2.putText(self.image, text, (x, y - 10), self.font, self.font_scale, self.text_color, 1, cv2.LINE_AA)
        return self.image

    def save_image(self, output_path: str):
        cv2.imwrite(output_path, self.image)
        return output_path


class TableDetector:
    def __init__(self, ocr_data: List[Tuple[List[List[int]], Tuple[str, float]]]):
        self.ocr_data = ocr_data

    def get_table_region(self):
        # Extract bounding boxes and group them
        boxes = [np.array(polygon, dtype=np.int32) for polygon, _ in self.ocr_data]
        all_points = np.vstack([box for box in boxes])
        x, y, w, h = cv2.boundingRect(all_points)
        return (x, y, x + w, y + h)  # top-left and bottom-right

    def draw_table_box(self, image):
        x1, y1, x2, y2 = self.get_table_region()
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)  # red box
        return image


class SFTPUploader:
    def __init__(self, host, port, username, password, sftp_folder):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sftp_folder = sftp_folder

    def upload_file(self, local_path: str, remote_filename: str):
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        sftp.chdir(self.sftp_folder)
        sftp.put(local_path, remote_filename)

        sftp.close()
        transport.close()
        print(f"Uploaded {local_path} to SFTP as {remote_filename}")
