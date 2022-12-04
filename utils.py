from PIL import Image


# TODO: 日文字符不等距..
def print_byformat(content):
    content = "│" + content + "│"
    print("┌"+(len(content)-2)*'─'+"┐")
    print(content)
    print("└" + (len(content) - 2) * '─' + "┘")


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