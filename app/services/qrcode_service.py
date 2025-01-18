from base64 import b64encode
from io import BytesIO
import qrcode


class QRcodeService:
   
    @classmethod
    def gerar_qrcode(self, url):

        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        return b64encode(img_io.read()).decode('utf-8')


        

