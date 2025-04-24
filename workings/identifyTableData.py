
# pip install "paddleocr>=2.0.1"
# pip install "paddlepaddle>=2.3"
# pip install "paddlepaddle-gpu>=2.3"
# git clone https://github.com/PaddlePaddle/PaddleDetection.git
# cd PaddleDetection
# pip install -r requirements.txt
# pip install https://paddleocr.bj.bcebos.com/whl/layoutparser-0.0.0-py3-none-any.whl

import os
import cv2
import layoutparser as lp
import shutil

# destination_folder = "/workspace/nishanth/newprj/paddleOCRKey/tabDetected/"
layoutOutput = []

def detectImage(filepath, filename,output_folder):
    # filepath ="/content/sample_data/medplus-1.png"
    image = cv2.imread(filepath)
    image = image[..., ::-1]

    # load model
    model = lp.PaddleDetectionLayoutModel(config_path="lp://PubLayNet/ppyolov2_r50vd_dcn_365e_publaynet/config",
                                    threshold=0.5,
                                    label_map={0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"},
                                    enforce_cpu=False,
                                    enable_mkldnn=True)


    # detect
    layout = model.detect(image)

    print('detected Layout -----> ' , layout)
    tableExists = False
    listExists = False
    tableBox = None
    listBox = None
    for l in layout:
        if l.type == 'Table':
            tableExists = True
            x_1 = int(l.block.x_1)
            y_1 = int(l.block.y_1)
            x_2 = int(l.block.x_2)
            y_2 = int(l.block.y_2)
            tableBox = [x_1,y_1,x_2,y_2]
        elif l.type == 'List':
            listExists = True
            x_1 = int(l.block.x_1)
            y_1 = int(l.block.y_1)
            x_2 = int(l.block.x_2)
            y_2 = int(l.block.y_2)
            listBox = [x_1,y_1,x_2,y_2]
    if(tableExists):
        print("✔ Table exists")
        print(tableBox)
        im = cv2.imread(filepath)
        source_file = f"{filename}_table_img.jpg"
        cropped_im = im[y_1:y_2, x_1:x_2]
        if cropped_im.size == 0:
            print("Error: Cropped image is empty. Check the coordinates.")
            return
        cv2.imwrite(source_file, cropped_im)
        
        # Ensure destination folder exists
        os.makedirs(output_folder, exist_ok=True)

        # Move the file
        destination_path = os.path.join(output_folder, source_file)
        shutil.move(source_file, destination_path)

        print(f"File saved to {destination_path}")
        """# Text detection and Recognition

        """
    else: 
        print(f"❌ No table found in this   ---->  {filename}")
    layoutOutput.append({
        "file_name": filename,
        "layout": layout,
        "tableExists": tableExists,
        "tableBox": tableBox,
        "listExists": listExists,
        "listBox":listBox
        
    })
    print('Detected layoutOutput --------->' , layoutOutput)
    return layoutOutput


# Example usage
# image_path = "/workspace/nishanth/newprj/paddleOCRKey/docs/axis_stmt.png"
# detected_tables = detectImage(image_path, 'axis_stmt')
