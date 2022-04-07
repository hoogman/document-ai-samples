from io import BytesIO
from PIL import Image

def convert_doc_to_pdf(file_blob):

    converted_doc = bytes()
    file_bytes = BytesIO(file_blob)

    im = Image.open(file_bytes)

    if im.mode == "LA":
        im = im.convert('RGB' + im.mode[1:])

    if im.mode == "RGBA":
        print('Converting RGBA image to RGB')
        im = convert_rgba_to_rgb(im)

    output = BytesIO()
    im.save(output, 'PDF', quality=100)
    
    output.seek(0)
    #im.save(converted_doc, 'PDF')

    return output.read()

def convert_rgba_to_rgb(image_object):

    new_image = Image.new('RGB', image_object.size, (255,255,255))
    new_image.paste(image_object, mask=image_object.split()[3])

    return new_image