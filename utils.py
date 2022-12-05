from PIL import Image
from datetime import datetime, timedelta

# TODO: 日文字符不等距..
def print_byformat(content):
    content = "│" + content + "│"
    print("┌"+(len(content)-2)*'─'+"┐")
    print(content)
    print("└" + (len(content) - 2) * '─' + "┘")


def forwardTime(st, et):
    # 在上一行歌词中一半时显示
    # et = "0:00:02.10"
    # st = "0:00:03.60"
    et = datetime.strptime(et, '%M:%S.%f')
    st = datetime.strptime(st, '%M:%S.%f')
    next_st = et + (st - et) / 2
    next_st = next_st.strftime('%M:%S.%f')[1:-4]
    return next_st

def backwardTime(et):
    # 显示延迟3毫秒
    # et = "00:02.10"
    et = datetime.strptime(et, '%M:%S.%f')
    delay = timedelta(microseconds=300000)
    next_et = et + delay
    next_et = next_et.strftime('%M:%S.%f')[1:-4]
    return next_et
def isImage(pic_file:str):
    format = ['jpg', 'jpeg', 'png', 'JPG', 'JPEG', 'PNG']
    for ext in format:
        if pic_file.endswith(ext):
            return 1
    return 0

def pad_image(image, target_size):
    """
    :param image: input image
    :param target_size: a tuple (num,num)
    :return: new image
    """
    iw, ih = image.size  # 原始图像的尺寸
    w, h = target_size  # 目标图像的尺寸

    # print("original size: ", (iw, ih))
    # print("new size: ", (w, h))

    scale = min(w / iw, h / ih)  # 转换的最小比例

    # 保证长或宽，至少一个符合目标图像的尺寸 0.5保证四舍五入
    nw = int(iw * scale + 0.5)
    nh = int(ih * scale + 0.5)

    # print("now nums are: ", (nw, nh))

    image = image.resize((nw, nh), Image.BICUBIC)  # 更改图像尺寸，双立法插值效果很好
    # image.show()
    new_image = Image.new('RGB', target_size, (0, 0, 0))  # 生成黑色图像
    # // 为整数除法，计算图像的位置
    new_image.paste(image, ((w - nw) // 2, (h - nh) // 2))  # 将图像填充为中间图像，两侧为黑色的样式
    # new_image.show()

    return new_image

def main():
    img_path = 'F:\Dev\lrc2srt\カナデトモスソラ (feat. 宵崎奏&朝比奈まふゆ&東雲絵名&暁山瑞希&巡音ルカ).png'
    image = Image.open(img_path)
    size = (1920, 1080)
    # pad_image(image, size)  # 填充图像
    newImage = pad_image(image, size)
    newImage.save(r"F:\Dev\lrc2srt\test.png")

def to1080P(origin, pic_name):
    image = Image.open(origin)
    size = (1920, 1080)
    newImage = pad_image(image, size)
    newImage.save(pic_name)

if __name__ == '__main__':
    main()