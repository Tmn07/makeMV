import argparse
import re
import subprocess
import os
import sys
from os import makedirs
import json
import requests

from utils import print_byformat, to1080P, isImage

# build
# pyinstaller.exe -F --add-data "./tools/*;./tools/" makeMV.py

# test
# python.exe makeMV.py 1992431933
# python.exe makeMV.py 2004994198 -p F:/Dev/MakeMV/result/cover.jpg
# python.exe makeMV.py 1971659505 -p F:/Dev/MakeMV/result/givemesomemore
# makeMV.exe 1992431933

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

ffmpeg_exe = resource_path("./tools/ffmpeg.exe")
ass_template = resource_path("./tools/ass_template.txt")


# TODO：重构代码，异常捕获 尝试最佳实践。分阶段、分异常类型进行捕获或者抛出自定义错误类型，在全局上捕获？

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
pictrue_flag = 0 # 单张图片
pictrue_list = []
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
        to1080P(origin_pic, pic_name)
        print('change picture to 1080P')
    except Exception as e:
        print('no album_pic')
else:
    if os.path.exists(args.picture):
        if os.path.isfile(args.picture): # 输入单张图片
            # TODO 判断单张图片类型 捕获异常
            origin_pic = args.picture
            pic_name = base_dir + 'cover.jpg'
            to1080P(origin_pic, pic_name)
            print('change picture to 1080P')
        elif os.path.isdir(args.picture): # 输入为路径时，遍历该路径下图片
            pictrue_flag = 1 # 多张图片
            pic_path = args.picture
            num = 1
            for file in os.listdir(pic_path):
                if isImage(file):
                    origin_pic = pic_path+'/'+file
                    pic_name = base_dir + f'cover{num}.jpg'
                    to1080P(origin_pic, pic_name)
                    pictrue_list.append(pic_name)
                    num += 1
                    print(f'change {file} to {pic_name}')
            pic_name = base_dir + 'cover%01d.jpg'
    else:
        print('图片路径不对')
        exit(0)





# 下载音频
# TODO：如何获取320K的音频
# TODO: 有些歌无法下载，提供错误信息 如4954431
download_url = f"http://music.163.com/song/media/outer/url?id={mid}.mp3"
music_file = base_dir + f'{music_name}.mp3'
r = requests.get(download_url)
with open(music_file, 'wb') as f:
    f.write(r.content)
    print(f'download {music_file}')


# 获取长度
def get_length(music_file):
    process = subprocess.Popen([ffmpeg_exe, '-i', music_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
    # 有些歌词里只有作曲信息..
    if jsondata['lrc']['lyric'] == "":
        print("指定曲目未有歌词")
        exit(0)
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
# music_ass = f'{music_name}.ass'
music_ass = base_dir + f'music.ass'
f = open(ass_template)
ass_header = f.read()
f.close()

times.sort()
num = 0
st_list = []
et_list = []
content_list = []
num_type_list = []
with open(music_ass, 'w', encoding='utf-8') as f:
    f.write(ass_header)
    pretime = times[0]
    for ind in range(1, len(times) + 1):
        num += 1
        num_type = "odd" if num % 2 == 1 else "even"
        start_time = pretime[1:-2]
        # 用于处理最后一条歌词信息
        if ind == len(times):
            end_time = final_time
        else:
            end_time = times[ind][1:-2]
            pretime = times[ind]
        content = result[times[ind - 1]]

        line = f"Dialogue: 0,0:{start_time},0:{end_time},{num_type},,0,0,0,,{content}\n"
        st_list.append(start_time)
        et_list.append(end_time)
        content_list.append(content)
        num_type_list.append(num_type)
        f.write(line)

print(f'generate {music_ass}')

# 处理时间轴
from utils import forwardTime, backwardTime
for ind in range(len(st_list)-1, 0, -1):
    st = st_list[ind-1]
    et = et_list[ind-1]
    st_list[ind] = forwardTime(st, et)
    et_list[ind] = backwardTime(et_list[ind])

process_music_ass = base_dir + f'process_music.ass'
with open(process_music_ass, 'w', encoding='utf-8') as f:
    f.write(ass_header)
    for i in range(len(st_list)):
        start_time = st_list[i]
        end_time = et_list[i]
        num_type = num_type_list[i]
        content = content_list[i]
        line = f"Dialogue: 0,0:{start_time},0:{end_time},{num_type},,0,0,0,,{content}\n"
        f.write(line)

print(f'generate {process_music_ass}')

music_ass = process_music_ass


# TODO：更高效率的制作一图流视频，视频帧率不用那么高？
mv_file = base_dir + music_name + '.mp4'



if pictrue_flag==0:
    cmd = f'{ffmpeg_exe} -r 30 -f image2 -loop 1 -i "{pic_name}" -i "{music_file}" -s 1920x1080 -t {video_time} -vcodec libx264 -acodec copy -b:a 128K -vf "ass={music_ass}" -y "{mv_file}" -v quiet -stats'
else:
    # 不渐变
    tmp_file = base_dir + 'slide' + '.mp4'
    # cmd0 = f'ffmpeg -r 0.1 -f image2 -loop 1 -i "{pic_name}" -i "{music_file}" -r 30 -s 1920x1080 -t {video_time} -vcodec libx264 -acodec copy -b:a 128K -y "{tmp_file}" -v quiet -stats'
    # print('now running this command')
    # print(cmd0)
    # subprocess.run(cmd0)
    # cmd = f'ffmpeg -i {tmp_file} -vf "ass={music_ass}" -y "{mv_file}" -v quiet -stats'

    # 生成渐变视频片段
    cmd0 = f'{ffmpeg_exe} '
    cmd_list = []
    for num, pic_name in enumerate(pictrue_list):
        cmd0 += f'-loop 1 -t 10 -i {pic_name} '
        cmd_list.append(f'[{num}:v]fade=t=in:st=0:d=1,fade=t=out:st=9:d=1[v{num}]; ')
    cmd0 += '-filter_complex "'
    cmd_ = ''
    for num in range(len(cmd_list)):
        cmd0 += cmd_list[num]
        cmd_ += f'[v{num}]'
    cmd0 += cmd_
    cmd0 += f'concat=n={num+1}:v=1:a=0,format=yuv420p[v]" -map "[v]" -y "{tmp_file}" -v quiet -stats'
    print('now running this command')
    print(cmd0)
    subprocess.run(cmd0)

    cmd = f'{ffmpeg_exe} -stream_loop -1 -i "{tmp_file}" -i  "{music_file}" -t {video_time} -vf "ass={music_ass}" -y "{mv_file}" -v quiet -stats'
    # 'ffmpeg.exe \
    # -stream_loop -1 -i slide.mp4 \
    # -i "1971659505/Give me some more....mp3" \
    # -vf "ass=1971659505/music.ass" \
    # -shortest -map 0:v:0 -map 1:a:0 \
    # -y tmp.mp4
    # '


print('now running this command')
print(cmd)

try:
    subprocess.run(cmd)
    content = f'Congratulations! Now get your MV in {mv_file}'
    print_byformat(content)
except Exception as e:
    print(e)