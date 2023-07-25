import glob
import os
import sys
import datetime
import ffmpeg_streaming
from ffmpeg_streaming import Formats, Bitrate, Representation, Size
from ffmpeg_streaming._utiles import cnv_options_to_args
from ffmpeg_streaming._process import Process

if len(sys.argv) != 2:
    sys.exit("请传入视频路径")
video_file = sys.argv[1]


def monitor(ffmpeg, duration, time_, time_left, process):
    per = round(time_ / duration * 100)
    sys.stdout.write(
        "\r视频转码切片 |%s%s| %s%% [%s]" %
        ('█' * per, ' ' * (100 - per), per, datetime.timedelta(seconds=int(time_left)))
    )
    sys.stdout.flush()


video = ffmpeg_streaming.input(video_file)

_1080p = Representation(Size(1920, 1080), Bitrate(3000 * 1024, 128 * 1024))
_720p = Representation(Size(1280, 720), Bitrate(1500 * 1024, 128 * 1024))
_480p = Representation(Size(854, 480), Bitrate(500 * 1024, 128 * 1024))

hls = video.hls(Formats.h264("h264_nvenc"))
hls.representations(_1080p, _720p, _480p)
hls.output(monitor=monitor)

sys.stdout.flush()
print("\r\n视频处理完毕")


def preview_command_builder(video_file, count=15):
    root = os.path.splitext(video_file)[0]
    outfile = os.path.join(root, "preview.mp4")
    dirname = os.path.join(root, "streams", "480p")
    streams = glob.glob(os.path.join(dirname, "*.ts"))
    length = len(streams) / (count + 1)

    if os.path.exists(outfile):
        os.remove(outfile)

    streams = [os.path.join(dirname, str(int((i + 1) * length)) + ".ts") for i in range(count)]
    count = len(streams)
    args = ["ffmpeg"]

    for ts in streams:
        args.append("-i")
        args.append(ts)

    args += cnv_options_to_args({
        "filter_complex": f'"{"".join([f"[{i}:v]trim=duration=1,scale=320:-1[outv{i}];" for i in range(count)])} {"".join([f"[outv{i}]" for i in range(count)])}concat=n={count}:v=1:a=0"',
        "c:v": "libx264",
        "an": outfile
    })
    return " ".join(args).replace("\\", "/")


with Process(hls, preview_command_builder(video_file)) as process:
    pipe, err = process.run()

print("预览视频生成完毕")
