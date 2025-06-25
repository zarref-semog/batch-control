from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime
import os

def converter_data(data_str):
    """
    Converte uma string de data do formato "dd/mm/aaaa" para "aaaa-mm-dd".
    """
    data_obj = datetime.strptime(data_str, "%d/%m/%Y")
    return data_obj.strftime("%Y-%m-%d")

def save_resized_image(file, upload_folder):
    filename = secure_filename(file.filename)
    path = os.path.join(upload_folder, filename)
    name, ext = os.path.splitext(filename)
    count = 1
    while os.path.exists(path):
        filename = f"{name}_{count}{ext}"
        path = os.path.join(upload_folder, filename)
        count += 1

    img = Image.open(file.stream)
    if img.height > img.width:
        img = img.rotate(90, expand=True)

    width_percent = 800 / float(img.size[0])
    height = int((float(img.size[1]) * width_percent))
    resized = img.resize((800, height), Image.Resampling.LANCZOS)
    resized.save(path)

    return filename
