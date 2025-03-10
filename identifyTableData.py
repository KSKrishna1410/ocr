# wget https://paddleocr.bj.bcebos.com/whl/layoutparser-0.0.0-py3-none-any.whl
# pip install -U layoutparser-0.0.0-py3-none-any.whl
import cv2
import layoutparser as lp
import shutil
destination_folder = "C:/Users/nisha/Downloads/"

def detectImage(filepath, filename):
    # filepath ="/content/sample_data/medplus-1.png"
    image = cv2.imread(filepath)
    image = image[..., ::-1]

    # load model
    model = lp.PaddleDetectionLayoutModel(config_path="lp://PubLayNet/ppyolov2_r50vd_dcn_365e_publaynet/config",
                                    threshold=0.5,
                                    label_map={0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"},
                                    enforce_cpu=False,
                                    enable_mkldnn=True)

    # model = lp.PaddleDetectionLayoutModel(
    #     config_path="lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config",
    #     label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
    #     enforce_cpu=False,
    # )
    # model = lp.PaddleDetectionLayoutModel(
    #     config_path="C:/path_to_model/ppyolov2_r50vd_dcn_365e_publaynet/config",
    #     label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
    #     enforce_cpu=False,
    #     enable_mkldnn=True
    # )


    # detect
    layout = model.detect(image)

    layout

    for l in layout:
        if l.type == 'Table':
            x_1 = int(l.block.x_1)
            y_1 = int(l.block.y_1)
            x_2 = int(l.block.x_2)
            y_2 = int(l.block.y_2)

    print(x_1,y_1,x_2,y_2)

    im = cv2.imread(filepath)
    source_file = f"{filename}_ext_im.jpg"
    cv2.imwrite(source_file,im[y_1:y_2,x_1:x_2])
    
    # from google.colab import files

    # # Download the saved image to your local machine
    # files.download('ext_im.jpg')
    shutil.move(source_file, destination_folder + source_file)

    print(f"File saved to {destination_folder + source_file}")
    """# Text detection and Recognition

    """
    return None