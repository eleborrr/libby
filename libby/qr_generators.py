from PIL import Image
from PIL import ImageDraw
import qrcode
import io
import base64


def _create_qrcode(book_code, id_, url='localhost:5000'):
    img = qrcode.make(f'{url}/{book_code}')
    img = img.resize((165, 165))
    draw = ImageDraw.Draw(img)
    msg = f'#{id_}'
    w, h = draw.textsize(msg)
    draw.text(xy=((165 - w) / 2, 150), text=msg, fill=(0,))
    return img


def _create_qr_list(ids, url='localhost:5000'):
    res = []
    res1 = []
    for i in range((len(ids) + 14) // 15):
        cur = Image.new('RGB', (594, 846), 'white')
        for x in range(5):
            for y in range(3):
                try:
                    book_id = ids[i * 15 + x * 3 + y]
                except IndexError:
                    break
                offset = 165 * y, 165 * x
                cur.paste(_create_qrcode(*book_id, url), offset)
        cur_res = io.BytesIO()
        cur.save(cur_res, format='JPEG')
        x = base64.b64encode(cur_res.getvalue()).decode('utf-8')
        res.append(x)
        res1.append(cur)
    return res, res1


def create_qrcode(book_code, id_, url='localhost:5000'):
    img = _create_qrcode(book_code, id_, url)
    cur_res = io.BytesIO()
    img.save(cur_res, format='JPEG')
    x = base64.b64encode(cur_res.getvalue()).decode('utf-8')
    return x
