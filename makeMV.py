import argparse
import re
import subprocess
from os import makedirs

import json
import requests

from utils import print_byformat, to1080P

parser = argparse.ArgumentParser(description='欢迎使用全自动MV生成脚本beta版', add_help=False)
parser.add_argument("-h", "--help", action="help", help="查看帮助信息")
parser.add_argument("id", help="提供网易云音乐id", type=str)
parser.add_argument("-p", "--picture", help="提供MV图片，若无则会使用默认的专辑封面", type=str)

args = parser.parse_args()
# print(args)

mid = args.id
# https://music.163.com/song?id=1971659505&userid=6369098302
# mid = '1971659505'

http_header = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
}

# 获取歌曲信息
# http://music.163.com/api/song/detail/?id=1993092158&ids=[1993092158]
info_url = f"http://music.163.com/api/song/detail/?id={mid}&ids=[{mid}]"
r = requests.get(info_url, headers=http_header)
info = r.json()
music_name = info['songs'][0]['name']
print(f'get info {music_name=}')

# base_dir = music_name[:10]+"/"
base_dir = mid+"/"
makedirs(base_dir, exist_ok=True)
# base_dir = mid+"/"

# 下载album封面
# TODO: 不支持jpeg?
if not args.picture:
    try:
        album_pic = info['songs'][0]['album']['picUrl']
        pic_suffix = album_pic.split('.')[-1]
        # pic_suffix = 'png'
        pic_name = base_dir +'cover.'+pic_suffix
        with open(pic_name, 'wb') as f:
            r = requests.get(album_pic)
            f.write(r.content)
        print(f'download album picture {pic_name}')
        origin_pic = pic_name

    except Exception as e:
        print('no album_pic')
else:
    origin_pic = args.picture
    pic_name = base_dir + 'cover.jpg'
    # pic_name = args.picture


to1080P(origin_pic, pic_name)
print('change picture to 1080P')

# 下载音频
# TODO：如何获取320K的音频
# TODO: 有些歌无法下载，提供错误信息
download_url = f"http://music.163.com/song/media/outer/url?id={mid}.mp3"
music_file = base_dir + f'{music_name}.mp3'
r = requests.get(download_url)
with open(music_file, 'wb') as f:
    f.write(r.content)
    print(f'download {music_file}')


# 获取长度
def get_length(music_file):
    process = subprocess.Popen(['ffmpeg', '-i', music_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    result = re.findall("Duration:.*?,", str(stdout))[0]
    return result[13:-1]


final_time = get_length(music_file)
video_time = int(final_time[:2])*60+int(final_time[3:5])+1
print(f'this music durataion {final_time}')

# 下载lrc
lrc_url = f"http://music.163.com/api/song/lyric?os=pc&id={mid}&lv=-1"
music_lrc = base_dir + f'{music_name}.lrc'

r = requests.get(lrc_url, headers=http_header)
jsondata = json.loads(r.text)

with open(music_lrc, 'w', encoding='utf-8') as f:
    f.write(jsondata['lrc']['lyric'])
    # if jsondata['tlyric'].get('lyric'):
    #     f.write(jsondata['tlyric']['lyric'])
    # else:
    #     print('no translate version')
    print(f'download {music_lrc}')

# 读取lrc，处理歌词文件
f = open(music_lrc, 'r', encoding='utf-8')
data = f.read()

translate = 0  # 是否保留中文翻译，做MV时不建议保留中文
K = 1  # 伪K轴，即是否进行奇偶定位
# 视频分辨率为1920*1080，在不同分辨率视频下可能需要调整。
positions = ["{\pos(60,880)}", "{\pos(1860,1000)}"]  # 奇偶位置

count = 0
result = {}
times = []
for line in data.split('\n'):
    # 00:09.36
    match_list = re.findall('\[\d*?:\d*?\.\d*?]', line)
    if match_list:
        for m in match_list:
            # print(m)
            tmp = result.get(m)
            if tmp != None:
                if tmp == "" or line[len(line) - line[::-1].index(']'):] == "//":  ## qq music中 翻译空白区 与 部分不翻译时用//来替代
                    continue
                else:
                    # lrc
                    if translate:
                        result[m] = tmp + "\n" + line[len(line) - line[::-1].index(']'):]
            else:
                content = line[line.index(']') + 1:]
                if content:
                    if K:
                        offset = positions[count]
                        count = 1 if count == 0 else 0
                    else:
                        offset = ''
                    result[m] = offset + line[line.index(']') + 1:]
                    times.append(m)
    else:
        continue


# 生成ass字幕
# TODO：平移时间轴
# music_ass = f'{music_name}.ass'
music_ass = base_dir + f'music.ass'
f = open('ass_template.txt')
ass_header = f.read()
f.close()

times.sort()
num = 0
with open(music_ass, 'w', encoding='utf-8') as f:
    f.write(ass_header)
    pretime = times[0]
    # for ind in range(1,len(times)):
    for ind in range(1, len(times) + 1):
        num += 1
        num_type = "odd" if num % 2 == 1 else "even"
        start_time = pretime[1:-2]
        # f2.write(str(ind) + "\n")
        # 用于处理最后一条歌词信息
        if ind == len(times):
            end_time = final_time
        else:
            end_time = times[ind][1:-2]
            pretime = times[ind]
        content = result[times[ind - 1]]

        line = f"Dialogue: 0,0:{start_time},0:{end_time},{num_type},,0,0,0,,{content}\n"
        # print(line)
        f.write(line)

    # lrc
    # for t in times:
    #     f.write(t + result[t] + "\n")

print(f'generate {music_ass}')
# print('please run the command next line to make MV')
# # TODO：更高效率的制作一图流视频，如何制作多图循环视频
# print(f'ffmpeg -r 30 -f image2 -loop 1 -i tenka_p_ssr6_f.png -i "{music_file}" -s 1920x1080 -t {video_time} -vcodec libx264 -acodec copy -b:a 128K  -y xxx.mp4')
# print(f'ffmpeg -i xxx.mp4 -vf "ass={music_ass}" result.mp4')

mv_file = base_dir + music_name + '.mp4'
# cmd = f'ffmpeg -r 30 -f image2 -loop 1 -i "{pic_name}" -i "{music_file}" -s 1920x1080 -t {video_time} -vcodec libx264 -acodec copy -b:a 128K -vf "ass={music_ass}" -y "{mv_file}" '
cmd = f'ffmpeg -r 30 -f image2 -loop 1 -i "{pic_name}" -i "{music_file}" -s 1920x1080 -t {video_time} -vcodec libx264 -acodec copy -b:a 128K -vf "ass={music_ass}" -y "{mv_file}" -v quiet -stats'
print('now running this command')
print(cmd)

# TODO：异常处理?
try:
    subprocess.run(cmd)
    content = f'Congratulations! Now get your MV in {mv_file}'
    print_byformat(content)
except Exception as e:
    print(e)